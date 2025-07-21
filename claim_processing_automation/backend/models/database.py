from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


Base = declarative_base()


class ClaimStatus(PyEnum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class DocumentType(PyEnum):
    INSURANCE_CARD = "insurance_card"
    DRIVERS_LICENSE = "drivers_license"
    ACCIDENT_REPORT = "accident_report"
    POLICE_REPORT = "police_report"
    MEDICAL_REPORT = "medical_report"
    REPAIR_ESTIMATE = "repair_estimate"
    PHOTOS = "photos"
    OTHER = "other"


class PaymentStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="user")
    user_history = relationship("UserHistory", back_populates="user")


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Claim Details
    incident_date = Column(DateTime(timezone=True), nullable=False)
    incident_location = Column(String(500))
    incident_description = Column(Text)
    claim_amount = Column(Float, nullable=False)
    
    # Status and Processing
    status = Column(Enum(ClaimStatus), default=ClaimStatus.SUBMITTED)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # AI Processing Results
    extracted_data = Column(JSON)  # OCR and LLM extracted data
    confidence_score = Column(Float)  # AI confidence in extraction
    validation_results = Column(JSON)  # Validation check results
    fraud_score = Column(Float)  # Fraud detection score
    
    # Processing Metadata
    processing_notes = Column(Text)
    assigned_adjuster = Column(String(255))
    estimated_processing_time = Column(Integer)  # in hours
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="claims")
    documents = relationship("Document", back_populates="claim")
    payments = relationship("Payment", back_populates="claim")
    claim_history = relationship("ClaimHistory", back_populates="claim")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # OCR Processing
    ocr_text = Column(Text)
    ocr_confidence = Column(Float)
    ocr_processed_at = Column(DateTime(timezone=True))
    
    # LLM Processing
    llm_extracted_data = Column(JSON)
    llm_confidence = Column(Float)
    llm_processed_at = Column(DateTime(timezone=True))
    
    # Validation
    is_valid = Column(Boolean)
    validation_errors = Column(JSON)
    
    # Metadata
    upload_ip = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="documents")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    
    # Payment Details
    stripe_payment_intent_id = Column(String(255), unique=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Payment Method
    payment_method = Column(String(50))  # card, bank_transfer, etc.
    last_four = Column(String(4))  # Last 4 digits of card/account
    
    # Processing
    processed_at = Column(DateTime(timezone=True))
    stripe_response = Column(JSON)
    failure_reason = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="payments")


class ClaimHistory(Base):
    __tablename__ = "claim_history"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    
    # Change Information
    previous_status = Column(Enum(ClaimStatus))
    new_status = Column(Enum(ClaimStatus))
    changed_by = Column(String(255))  # User ID or system
    change_reason = Column(String(500))
    notes = Column(Text)
    
    # Additional Data
    changed_fields = Column(JSON)  # Track which fields changed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_history")


class UserHistory(Base):
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity Information
    action = Column(String(100), nullable=False)  # login, upload, submit_claim, etc.
    resource = Column(String(100))  # claim_id, document_id, etc.
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Additional Data
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_history")


class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions and Limits
    permissions = Column(JSON)  # List of allowed operations
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    
    # Usage Tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


def generate_claim_number() -> str:
    """Generate a unique claim number."""
    import time
    timestamp = str(int(time.time()))
    random_part = str(uuid.uuid4().hex)[:8].upper()
    return f"CLM-{timestamp[-6:]}-{random_part}"