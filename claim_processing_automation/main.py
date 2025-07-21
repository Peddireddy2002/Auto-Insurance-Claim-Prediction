import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Local imports
from config.settings import settings
from backend.models.database import Base, engine, generate_claim_number
from backend.services.payment_service import payment_processor
from utils.pdf_processor import pdf_processor
from utils.llm_agent import llm_agent
from utils.validators import claim_validator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ClaimSubmissionRequest(BaseModel):
    claimant_name: str
    claimant_email: Optional[str] = None
    claimant_phone: Optional[str] = None
    incident_date: str
    incident_location: Optional[str] = None
    incident_description: str
    claim_amount: float
    policy_number: Optional[str] = None


class ClaimResponse(BaseModel):
    claim_id: int
    claim_number: str
    status: str
    message: str


class ProcessingStatusResponse(BaseModel):
    claim_id: int
    status: str
    progress: Dict[str, Any]
    estimated_completion: Optional[str] = None


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    risk_score: float
    fraud_indicators: List[Dict[str, Any]]


# Database dependency
def get_db():
    """Get database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create upload directory
    os.makedirs(settings.upload_folder, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced Claim Processing Automation System with OCR, LLM, and Payment Processing",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

# Mount static files
if os.path.exists("./static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "database": "connected",
            "llm": "operational",
            "payment": "operational"
        }
    }


@app.post("/api/v1/claims/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    claim_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for claim processing.
    
    Args:
        file: Uploaded file (PDF, image)
        document_type: Type of document being uploaded
        claim_id: Optional existing claim ID
        db: Database session
    
    Returns:
        Dictionary containing processing results
    """
    try:
        # Validate file
        file_content = await file.read()
        file_path = os.path.join(settings.upload_folder, file.filename)
        
        # Save file temporarily
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Validate file
        validation_result = pdf_processor.validate_file(file_path)
        if not validation_result["valid"]:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            extraction_result = pdf_processor.extract_text_from_pdf(file_path)
        else:
            extraction_result = pdf_processor.extract_text_from_image(file_path)
        
        if not extraction_result["text"]:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="No text could be extracted from the document")
        
        # Classify document
        classification = llm_agent.classify_document(extraction_result["text"])
        
        # Extract structured data
        extracted_data = llm_agent.extract_claim_data(
            extraction_result["text"], 
            classification["document_type"]
        )
        
        # Validate extracted data
        validation = claim_validator.validate_claim(extracted_data)
        
        # Store results
        from backend.models.database import Document, DocumentType
        
        document = Document(
            claim_id=claim_id,
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=file.content_type,
            document_type=DocumentType(classification["document_type"]),
            ocr_text=extraction_result["text"],
            ocr_confidence=extraction_result.get("confidence", 0.0),
            llm_extracted_data=extracted_data,
            llm_confidence=extracted_data.get("confidence_score", 0.0),
            is_valid=validation.is_valid,
            validation_errors=validation.to_dict()
        )
        
        db.add(document)
        db.commit()
        
        return {
            "success": True,
            "document_id": document.id,
            "extraction_result": extraction_result,
            "classification": classification,
            "extracted_data": extracted_data,
            "validation": validation.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error processing document upload: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/claims/submit", response_model=ClaimResponse)
async def submit_claim(
    claim_data: ClaimSubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a new insurance claim.
    
    Args:
        claim_data: Claim submission data
        db: Database session
    
    Returns:
        ClaimResponse with claim details
    """
    try:
        from backend.models.database import Claim, ClaimStatus, User
        
        # Generate claim number
        claim_number = generate_claim_number()
        
        # Create claim record
        claim = Claim(
            claim_number=claim_number,
            user_id=1,  # This would come from authentication
            incident_date=claim_data.incident_date,
            incident_location=claim_data.incident_location,
            incident_description=claim_data.incident_description,
            claim_amount=claim_data.claim_amount,
            status=ClaimStatus.SUBMITTED,
            extracted_data=claim_data.dict()
        )
        
        db.add(claim)
        db.commit()
        
        logger.info(f"Claim {claim_number} submitted successfully")
        
        return ClaimResponse(
            claim_id=claim.id,
            claim_number=claim_number,
            status="submitted",
            message="Claim submitted successfully and is being processed"
        )
        
    except Exception as e:
        logger.error(f"Error submitting claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/claims/{claim_id}/status", response_model=ProcessingStatusResponse)
async def get_claim_status(claim_id: int, db: Session = Depends(get_db)):
    """
    Get the processing status of a claim.
    
    Args:
        claim_id: Claim ID
        db: Database session
    
    Returns:
        ProcessingStatusResponse with current status
    """
    try:
        from backend.models.database import Claim
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Calculate progress
        progress = {
            "submitted": True,
            "documents_processed": len(claim.documents) > 0,
            "validation_complete": claim.validation_results is not None,
            "payment_processed": len(claim.payments) > 0 and any(
                p.status == "completed" for p in claim.payments
            )
        }
        
        return ProcessingStatusResponse(
            claim_id=claim_id,
            status=claim.status.value,
            progress=progress,
            estimated_completion="2-3 business days"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/claims/{claim_id}/validate", response_model=ValidationResponse)
async def validate_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    Validate a claim and perform fraud detection.
    
    Args:
        claim_id: Claim ID
        db: Database session
    
    Returns:
        ValidationResponse with validation results
    """
    try:
        from backend.models.database import Claim
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Perform validation
        validation_result = claim_validator.validate_claim(claim.extracted_data or {})
        
        # Update claim with validation results
        claim.validation_results = validation_result.to_dict()
        claim.fraud_score = validation_result.risk_score
        db.commit()
        
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            risk_score=validation_result.risk_score,
            fraud_indicators=validation_result.fraud_indicators
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/claims/{claim_id}/approve")
async def approve_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    Approve a claim for payment.
    
    Args:
        claim_id: Claim ID
        db: Database session
    
    Returns:
        Approval confirmation
    """
    try:
        from backend.models.database import Claim, ClaimStatus
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Update claim status
        claim.status = ClaimStatus.APPROVED
        claim.approved_at = asyncio.get_event_loop().time()
        db.commit()
        
        # Initiate payment processing if amount is below auto-approve threshold
        if claim.claim_amount <= settings.auto_approve_threshold:
            payment_result = await payment_processor.process_claim_payment(
                db=db,
                claim_id=claim_id,
                amount=claim.claim_amount
            )
            
            return {
                "success": True,
                "message": "Claim approved and payment initiated",
                "claim_id": claim_id,
                "payment_result": payment_result
            }
        else:
            return {
                "success": True,
                "message": "Claim approved, requires manual payment authorization",
                "claim_id": claim_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payments/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Webhook processing confirmation
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        result = await payment_processor.handle_webhook(
            payload=payload.decode('utf-8'),
            sig_header=sig_header
        )
        
        if result["success"]:
            return {"received": True}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/claims")
async def list_claims(
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List claims with pagination and filtering.
    
    Args:
        skip: Number of claims to skip
        limit: Maximum number of claims to return
        status: Optional status filter
        db: Database session
    
    Returns:
        List of claims
    """
    try:
        from backend.models.database import Claim, ClaimStatus
        
        query = db.query(Claim)
        
        if status:
            query = query.filter(Claim.status == ClaimStatus(status))
        
        claims = query.offset(skip).limit(limit).all()
        
        return {
            "claims": [
                {
                    "id": claim.id,
                    "claim_number": claim.claim_number,
                    "status": claim.status.value,
                    "claim_amount": claim.claim_amount,
                    "incident_date": claim.incident_date,
                    "created_at": claim.created_at,
                    "fraud_score": claim.fraud_score
                }
                for claim in claims
            ],
            "total": query.count(),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing claims: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Get dashboard analytics and statistics.
    
    Args:
        db: Database session
    
    Returns:
        Dashboard analytics data
    """
    try:
        from backend.models.database import Claim, ClaimStatus, Payment
        from sqlalchemy import func
        
        # Total claims
        total_claims = db.query(Claim).count()
        
        # Claims by status
        status_counts = db.query(
            Claim.status, func.count(Claim.id)
        ).group_by(Claim.status).all()
        
        # Average claim amount
        avg_claim_amount = db.query(func.avg(Claim.claim_amount)).scalar() or 0
        
        # Total payments
        total_payments = db.query(func.sum(Payment.amount)).scalar() or 0
        
        # High-risk claims (fraud score > 0.7)
        high_risk_claims = db.query(Claim).filter(Claim.fraud_score > 0.7).count()
        
        return {
            "total_claims": total_claims,
            "status_distribution": dict(status_counts),
            "average_claim_amount": float(avg_claim_amount),
            "total_payments_processed": float(total_payments),
            "high_risk_claims": high_risk_claims,
            "fraud_detection_rate": (high_risk_claims / total_claims * 100) if total_claims > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )