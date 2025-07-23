#!/bin/bash

# 🎓 Student Project Installation Script
# Claim Processing Automation with Machine Learning

echo "🎓 STUDENT PROJECT: Claim Processing Automation"
echo "==============================================="
echo "Setting up your development environment..."

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.9+ and try again."
    exit 1
fi

echo "✅ Python 3 found!"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
if [ $? -eq 0 ]; then
    echo "✅ Virtual environment created!"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "📚 Installing Python packages..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ All packages installed successfully!"
else
    echo "❌ Package installation failed"
    exit 1
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p uploads logs data/processed data/models backup tests/test_uploads

# Copy environment file
echo "🔐 Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Environment file created! Please edit .env with your API keys."
else
    echo "✅ Environment file already exists."
fi

# Check system dependencies
echo "🔍 Checking system dependencies..."

# Check for Tesseract
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract OCR found: $(tesseract --version | head -n1)"
else
    echo "⚠️ Tesseract OCR not found. Install it for OCR functionality:"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
    echo "   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Check for Jupyter
echo "📊 Checking Jupyter installation..."
if command -v jupyter &> /dev/null; then
    echo "✅ Jupyter found!"
else
    echo "📚 Installing Jupyter..."
    pip install jupyter
fi

echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "========================="
echo ""
echo "🚀 Quick Start Options:"
echo ""
echo "1. 📊 Run Jupyter Notebook Demo (Recommended for students):"
echo "   jupyter notebook machine_learning_demo.ipynb"
echo ""
echo "2. 🎬 Run Quick Demo Script:"
echo "   python demo_script.py"
echo ""
echo "3. 🌐 Start Web Application:"
echo "   python main.py"
echo "   Then visit: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   - STUDENT_PROJECT_GUIDE.md (Start here!)"
echo "   - ML_README.md (ML-specific docs)"
echo "   - README.md (Complete documentation)"
echo ""
echo "💡 Student Tips:"
echo "   - Always activate virtual environment: source venv/bin/activate"
echo "   - Start with the Jupyter notebook for hands-on learning"
echo "   - Check STUDENT_PROJECT_GUIDE.md for project requirements"
echo "   - Add your OpenAI API key to .env for full LLM functionality"
echo ""
echo "🆘 Need help? Check the troubleshooting section in STUDENT_PROJECT_GUIDE.md"
echo ""
echo "Happy coding! 🚀"