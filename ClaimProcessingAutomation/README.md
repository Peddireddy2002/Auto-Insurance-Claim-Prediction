# Claim ProcessingAutomation

A modular system for automating claim processing from PDF upload to payment routing.

## Features
- User history tracking
- PDF upload and OCR extraction (Pytesseract)
- LLM-powered JSON conversion (LangChain)
- Data validation
- Routing to Stripe for payment

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Folder Structure
- `app/` - Main application code
- `requirements.txt` - Python dependencies
- `README.md` - Project overview