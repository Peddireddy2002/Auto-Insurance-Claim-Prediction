@echo off
REM 🎓 Student Project Installation Script (Windows)
REM Claim Processing Automation with Machine Learning

echo 🎓 STUDENT PROJECT: Claim Processing Automation
echo ===============================================
echo Setting up your development environment on Windows...

REM Check Python version
echo.
echo 🐍 Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://python.org and try again.
    pause
    exit /b 1
)

python --version
echo ✅ Python found!

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
python -m venv venv
if %errorlevel% equ 0 (
    echo ✅ Virtual environment created!
) else (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install required packages
echo.
echo 📚 Installing Python packages...
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo ✅ All packages installed successfully!
) else (
    echo ❌ Package installation failed
    pause
    exit /b 1
)

REM Create necessary directories
echo.
echo 📁 Creating project directories...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "data\processed" mkdir data\processed
if not exist "data\models" mkdir data\models
if not exist "backup" mkdir backup
if not exist "tests" mkdir tests
if not exist "tests\test_uploads" mkdir tests\test_uploads

REM Copy environment file
echo.
echo 🔐 Setting up environment configuration...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo ✅ Environment file created! Please edit .env with your API keys.
) else (
    echo ✅ Environment file already exists.
)

REM Check for Jupyter
echo.
echo 📊 Checking Jupyter installation...
jupyter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📚 Installing Jupyter...
    pip install jupyter
) else (
    echo ✅ Jupyter found!
)

echo.
echo 🎉 INSTALLATION COMPLETE!
echo =========================
echo.
echo 🚀 Quick Start Options:
echo.
echo 1. 📊 Run Jupyter Notebook Demo (Recommended for students):
echo    jupyter notebook machine_learning_demo.ipynb
echo.
echo 2. 🎬 Run Quick Demo Script:
echo    python demo_script.py
echo.
echo 3. 🌐 Start Web Application:
echo    python main.py
echo    Then visit: http://localhost:8000/docs
echo.
echo 📚 Documentation:
echo    - STUDENT_PROJECT_GUIDE.md (Start here!)
echo    - ML_README.md (ML-specific docs)
echo    - README.md (Complete documentation)
echo.
echo 💡 Student Tips:
echo    - Always activate virtual environment: venv\Scripts\activate
echo    - Start with the Jupyter notebook for hands-on learning
echo    - Check STUDENT_PROJECT_GUIDE.md for project requirements
echo    - Add your OpenAI API key to .env for full LLM functionality
echo.
echo ⚠️ Windows-specific notes:
echo    - Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
echo    - You may need to add Tesseract to your PATH
echo    - Use Command Prompt or PowerShell to run commands
echo.
echo 🆘 Need help? Check the troubleshooting section in STUDENT_PROJECT_GUIDE.md
echo.
echo Happy coding! 🚀
echo.
pause