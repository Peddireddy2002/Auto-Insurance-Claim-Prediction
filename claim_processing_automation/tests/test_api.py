import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

# Import the app and dependencies
from main import app, get_db
from backend.models.database import Base

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


class TestAPI:
    """Test class for API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_submit_claim(self):
        """Test claim submission."""
        claim_data = {
            "claimant_name": "John Doe",
            "claimant_email": "john@example.com",
            "claimant_phone": "+1-555-123-4567",
            "incident_date": "2024-01-15",
            "incident_location": "Main St & 1st Ave",
            "incident_description": "Rear-end collision at traffic light",
            "claim_amount": 5000.00,
            "policy_number": "POL-123456789"
        }
        
        response = client.post("/api/v1/claims/submit", json=claim_data)
        assert response.status_code == 200
        data = response.json()
        assert "claim_id" in data
        assert "claim_number" in data
        assert data["status"] == "submitted"
    
    def test_list_claims(self):
        """Test listing claims."""
        response = client.get("/api/v1/claims")
        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert "total" in data
        assert isinstance(data["claims"], list)
    
    def test_get_claim_status_not_found(self):
        """Test getting status of non-existent claim."""
        response = client.get("/api/v1/claims/99999/status")
        assert response.status_code == 404
    
    @patch('utils.pdf_processor.pdf_processor.validate_file')
    @patch('utils.pdf_processor.pdf_processor.extract_text_from_pdf')
    @patch('utils.llm_agent.llm_agent.classify_document')
    @patch('utils.llm_agent.llm_agent.extract_claim_data')
    @patch('utils.validators.claim_validator.validate_claim')
    def test_document_upload(self, mock_validate, mock_extract, mock_classify, mock_extract_text, mock_validate_file):
        """Test document upload with mocked dependencies."""
        
        # Mock the dependencies
        mock_validate_file.return_value = {"valid": True, "file_type": "pdf"}
        mock_extract_text.return_value = {
            "text": "Sample insurance document text",
            "confidence": 0.95,
            "method_used": "direct_text_extraction"
        }
        mock_classify.return_value = {
            "document_type": "insurance_card",
            "confidence": 0.9
        }
        mock_extract.return_value = {
            "claimant_name": "John Doe",
            "policy_number": "POL-123456",
            "confidence_score": 0.85
        }
        
        # Mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validation_result.to_dict.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        mock_validate.return_value = mock_validation_result
        
        # Create a test file
        test_file = ("test.pdf", b"fake pdf content", "application/pdf")
        
        response = client.post(
            "/api/v1/claims/upload",
            files={"file": test_file},
            data={"document_type": "insurance_card"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        assert "extraction_result" in data
        assert "classification" in data
        assert "extracted_data" in data
        assert "validation" in data
    
    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoint."""
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_claims" in data
        assert "status_distribution" in data
        assert "average_claim_amount" in data
        assert "total_payments_processed" in data
        assert "high_risk_claims" in data
        assert "fraud_detection_rate" in data
    
    def test_invalid_claim_submission(self):
        """Test claim submission with invalid data."""
        invalid_claim_data = {
            "claimant_name": "",  # Empty name should fail validation
            "claim_amount": -100  # Negative amount should fail
        }
        
        response = client.post("/api/v1/claims/submit", json=invalid_claim_data)
        assert response.status_code == 422  # Unprocessable Entity
    
    @patch('backend.services.payment_service.payment_processor.handle_webhook')
    def test_stripe_webhook(self, mock_handle_webhook):
        """Test Stripe webhook handling."""
        mock_handle_webhook.return_value = {"success": True}
        
        # Mock webhook payload
        payload = '{"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}'
        headers = {"stripe-signature": "test_signature"}
        
        response = client.post(
            "/api/v1/payments/webhook",
            content=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["received"] is True


class TestValidation:
    """Test validation functionality."""
    
    def test_email_validation(self):
        """Test email validation in validators."""
        from utils.validators import claim_validator
        
        valid_data = {
            "claimant_name": "John Doe",
            "claimant_email": "john@example.com",
            "incident_date": "2024-01-15",
            "claim_amount": 5000.0,
            "incident_description": "Test incident"
        }
        
        result = claim_validator.validate_claim(valid_data)
        assert result.is_valid is True
        
        # Test invalid email
        invalid_data = valid_data.copy()
        invalid_data["claimant_email"] = "invalid-email"
        
        result = claim_validator.validate_claim(invalid_data)
        assert result.is_valid is False
        assert any("email" in error["message"].lower() for error in result.errors)


class TestOCRProcessing:
    """Test OCR processing functionality."""
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_text_extraction(self, mock_image_to_data, mock_image_to_string):
        """Test text extraction from images."""
        from utils.pdf_processor import pdf_processor
        from PIL import Image
        import numpy as np
        
        # Mock tesseract responses
        mock_image_to_string.return_value = "Sample extracted text"
        mock_image_to_data.return_value = {
            'conf': ['95', '90', '85']
        }
        
        # Create a dummy image
        dummy_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        dummy_image.save("test_image.png")
        
        try:
            result = pdf_processor.extract_text_from_image("test_image.png")
            assert "text" in result
            assert result["text"] == "Sample extracted text"
            assert "confidence" in result
        finally:
            import os
            if os.path.exists("test_image.png"):
                os.remove("test_image.png")


# Pytest configuration
def pytest_configure():
    """Configure pytest."""
    pytest.asyncio_mode = "auto"


# Clean up after tests
def teardown_module():
    """Clean up test database."""
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")