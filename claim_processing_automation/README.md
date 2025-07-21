# 🚗 Advanced Claim Processing Automation System

An enterprise-grade insurance claim processing automation system that leverages OCR, LLM agents, fraud detection, and automated payment processing to streamline insurance claim workflows.

## 🌟 Features

### Core Functionality
- **📄 PDF Upload & Processing**: Automated document upload with validation
- **🔍 OCR Extraction**: Advanced text extraction using Pytesseract with image preprocessing
- **🤖 LLM Agent Processing**: Intelligent data extraction using LangChain and OpenAI GPT-4
- **✅ Comprehensive Validation**: Multi-layer validation with fraud detection
- **💳 Payment Processing**: Automated payment routing through Stripe integration
- **📊 Analytics Dashboard**: Real-time claim processing insights

### Advanced Features
- **🛡️ Fraud Detection**: AI-powered fraud indicator analysis
- **🔄 Workflow Automation**: Automated claim routing based on risk scores
- **📈 Risk Assessment**: Comprehensive risk scoring algorithms
- **🏪 User Management**: Multi-user support with role-based access
- **📱 RESTful API**: Complete API for integration with external systems
- **🔐 Security**: JWT authentication, rate limiting, and data encryption

## 🏗️ Architecture

```
├── backend/
│   ├── api/              # FastAPI endpoints
│   ├── services/         # Business logic services
│   ├── models/           # Database models
│   └── middleware/       # Custom middleware
├── utils/
│   ├── pdf_processor.py  # OCR and PDF processing
│   ├── llm_agent.py      # LangChain LLM integration
│   └── validators.py     # Validation and fraud detection
├── config/
│   └── settings.py       # Configuration management
├── frontend/             # Web interface (future)
└── tests/               # Test suite
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL or SQLite
- Redis (for background tasks)
- Tesseract OCR
- OpenAI API key
- Stripe account

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd claim_processing_automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr poppler-utils libmagic1
   
   # macOS
   brew install tesseract poppler libmagic
   
   # Windows
   # Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   # Download and install Poppler from: https://blog.alivate.com.au/poppler-windows/
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/claim_processing
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Security
SECRET_KEY=your_super_secret_jwt_key_here

# File Processing
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg

# OCR Configuration
TESSERACT_CMD=/usr/bin/tesseract
POPPLER_PATH=/usr/bin

# Business Rules
MAX_CLAIM_AMOUNT=100000.0
AUTO_APPROVE_THRESHOLD=1000.0
MANUAL_REVIEW_THRESHOLD=50000.0
```

## 📖 API Documentation

### Core Endpoints

#### Upload Document
```http
POST /api/v1/claims/upload
Content-Type: multipart/form-data

file: <PDF or image file>
document_type: "insurance_card" | "accident_report" | "police_report" | etc.
claim_id: <optional existing claim ID>
```

#### Submit Claim
```http
POST /api/v1/claims/submit
Content-Type: application/json

{
  "claimant_name": "John Doe",
  "claimant_email": "john@example.com",
  "claimant_phone": "+1-555-123-4567",
  "incident_date": "2024-01-15",
  "incident_location": "Main St & 1st Ave",
  "incident_description": "Rear-end collision at traffic light",
  "claim_amount": 5000.00,
  "policy_number": "POL-123456789"
}
```

#### Check Claim Status
```http
GET /api/v1/claims/{claim_id}/status
```

#### Validate Claim
```http
POST /api/v1/claims/{claim_id}/validate
```

#### Approve Claim
```http
POST /api/v1/claims/{claim_id}/approve
```

#### List Claims
```http
GET /api/v1/claims?skip=0&limit=20&status=submitted
```

### Interactive API Documentation
Visit `http://localhost:8000/docs` for the complete Swagger UI documentation.

## 🔄 Workflow

1. **Document Upload**: User uploads claim documents (PDFs, images)
2. **OCR Processing**: System extracts text using Pytesseract with preprocessing
3. **Document Classification**: LLM classifies document type
4. **Data Extraction**: LLM extracts structured data from text
5. **Validation**: Multi-layer validation including fraud detection
6. **Risk Assessment**: AI-powered risk scoring
7. **Routing**: Automatic routing based on amount and risk score
8. **Payment Processing**: Stripe integration for approved claims

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Configurable request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **File Validation**: Secure file upload with type and size validation
- **Fraud Detection**: AI-powered fraud indicator analysis
- **Audit Logging**: Complete audit trail for all operations

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v --cov=.
```

## 📊 Monitoring & Analytics

### Dashboard Metrics
- Total claims processed
- Claims by status distribution
- Average claim amounts
- Fraud detection rates
- Processing times
- Payment success rates

### Health Checks
```http
GET /health
```

## 🔧 Development

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t claim-processing-automation .

# Run container
docker run -p 8000:8000 --env-file .env claim-processing-automation
```

### Production Considerations
- Use PostgreSQL for production database
- Configure Redis for session storage and caching
- Set up load balancing for high availability
- Enable HTTPS with SSL certificates
- Configure monitoring and alerting
- Set up automated backups
- Use environment-specific configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Tesseract not found**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from official repository
```

**Poppler not found**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

**Database connection issues**
- Verify DATABASE_URL in .env
- Ensure PostgreSQL is running
- Check firewall settings

### Getting Help
- Check the [documentation](http://localhost:8000/docs)
- Review [GitHub Issues](issues)
- Join our [Discord community](discord-link)

## 🗺️ Roadmap

### Version 2.0
- [ ] React frontend dashboard
- [ ] Real-time notifications
- [ ] Advanced machine learning models
- [ ] Multi-language support
- [ ] Mobile application

### Version 2.1
- [ ] Blockchain integration for audit trails
- [ ] Advanced reporting and analytics
- [ ] Third-party insurance API integrations
- [ ] Automated document generation

---

Built with ❤️ using FastAPI, LangChain, and Stripe