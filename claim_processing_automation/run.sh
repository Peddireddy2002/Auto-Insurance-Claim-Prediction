#!/bin/bash

# Advanced Claim Processing Automation System
# Startup Script

set -e

echo "🚗 Starting Advanced Claim Processing Automation System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required environment variables
required_vars=("OPENAI_API_KEY" "STRIPE_SECRET_KEY" "DATABASE_URL" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env file"
        exit 1
    fi
done

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads logs static

# Check system dependencies
echo "🔍 Checking system dependencies..."

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract OCR is not installed. Please install it:"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
    echo "   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    exit 1
fi

# Check if Python dependencies are installed
echo "📦 Checking Python dependencies..."
if ! python -c "import fastapi, uvicorn, pytesseract, stripe, langchain" &> /dev/null; then
    echo "❌ Some Python dependencies are missing. Installing..."
    pip install -r requirements.txt
fi

# Run database migrations (if using alembic)
if [ -f "alembic.ini" ]; then
    echo "🗃️  Running database migrations..."
    alembic upgrade head
fi

# Start the application
echo "🚀 Starting the application..."
echo "📖 API Documentation will be available at: http://localhost:${PORT:-8000}/docs"
echo "💓 Health check available at: http://localhost:${PORT:-8000}/health"
echo ""

if [ "$1" = "dev" ]; then
    echo "🔧 Starting in development mode with auto-reload..."
    python -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload --log-level debug
elif [ "$1" = "prod" ]; then
    echo "🏭 Starting in production mode..."
    python -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers 4 --log-level info
else
    echo "🎯 Starting in standard mode..."
    python main.py
fi