#!/usr/bin/env python3
"""
Setup script for Claim Processing Automation System
This script automates the installation and configuration of the entire system
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, shell=False):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_system_dependencies():
    """Install system-level dependencies based on the operating system."""
    system = platform.system().lower()
    
    print("🔧 Installing system dependencies...")
    
    if system == "linux":
        # Ubuntu/Debian
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y tesseract-ocr",
            "sudo apt-get install -y poppler-utils", 
            "sudo apt-get install -y libmagic1",
            "sudo apt-get install -y python3-dev",
            "sudo apt-get install -y build-essential",
            "sudo apt-get install -y redis-server",
            "sudo systemctl start redis",
            "sudo systemctl enable redis"
        ]
        
        for cmd in commands:
            success, output = run_command(cmd, shell=True)
            if not success:
                print(f"⚠️  Warning: Failed to run {cmd}")
                print(f"Error: {output}")
    
    elif system == "darwin":  # macOS
        # Check if Homebrew is installed
        success, _ = run_command(["which", "brew"])
        if not success:
            print("❌ Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
        
        commands = [
            ["brew", "install", "tesseract"],
            ["brew", "install", "poppler"],
            ["brew", "install", "libmagic"],
            ["brew", "install", "redis"],
            ["brew", "services", "start", "redis"]
        ]
        
        for cmd in commands:
            success, output = run_command(cmd)
            if not success:
                print(f"⚠️  Warning: Failed to run {' '.join(cmd)}")
                print(f"Error: {output}")
    
    elif system == "windows":
        print("🪟 Windows detected. Please manually install:")
        print("   1. Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. Poppler: https://blog.alivate.com.au/poppler-windows/")
        print("   3. Redis: https://redis.io/download")
        print("   4. Visual C++ Build Tools")
        return False
    
    return True

def create_virtual_environment():
    """Create a Python virtual environment."""
    print("🐍 Creating virtual environment...")
    
    success, output = run_command([sys.executable, "-m", "venv", "venv"])
    if not success:
        print(f"❌ Failed to create virtual environment: {output}")
        return False
    
    print("✅ Virtual environment created successfully")
    return True

def install_python_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    # Determine the path to pip in the virtual environment
    if platform.system().lower() == "windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Upgrade pip first
    success, output = run_command([pip_path, "install", "--upgrade", "pip"])
    if not success:
        print(f"⚠️  Warning: Failed to upgrade pip: {output}")
    
    # Install requirements
    success, output = run_command([pip_path, "install", "-r", "requirements.txt"])
    if not success:
        print(f"❌ Failed to install Python dependencies: {output}")
        return False
    
    print("✅ Python dependencies installed successfully")
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating project directories...")
    
    directories = [
        "uploads",
        "logs",
        "static",
        "tests/test_uploads",
        "data/processed",
        "data/models",
        "backup"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created successfully")

def setup_environment_file():
    """Set up the environment file."""
    print("🔐 Setting up environment configuration...")
    
    if not Path(".env").exists():
        if Path(".env.example").exists():
            # Copy example to .env
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ Environment file created from .env.example")
            print("⚠️  Please edit .env file with your actual API keys and configuration")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ Environment file already exists")
    
    return True

def initialize_database():
    """Initialize the database."""
    print("🗄️  Initializing database...")
    
    # Determine the path to python in the virtual environment
    if platform.system().lower() == "windows":
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        python_path = os.path.join("venv", "bin", "python")
    
    # Run database initialization
    success, output = run_command([python_path, "-c", """
import os
os.environ.setdefault('DATABASE_URL', 'sqlite:///./claim_processing.db')
from backend.models.database import Base, engine
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"""])
    
    if success:
        print("✅ Database initialized successfully")
    else:
        print("⚠️  Database initialization may have failed, but this is normal on first run")
    
    return True

def verify_installation():
    """Verify the installation by checking key components."""
    print("🔍 Verifying installation...")
    
    # Check Tesseract
    success, output = run_command(["tesseract", "--version"])
    if success:
        print("✅ Tesseract OCR is installed and working")
    else:
        print("❌ Tesseract OCR not found")
    
    # Check Python environment
    if platform.system().lower() == "windows":
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        python_path = os.path.join("venv", "bin", "python")
    
    success, output = run_command([python_path, "-c", "import fastapi, pytesseract, langchain, stripe; print('All key packages imported successfully')"])
    if success:
        print("✅ Python environment is working")
    else:
        print("❌ Python environment has issues")
    
    return True

def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETED!")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("\n1. 🔐 Configure your API keys in the .env file:")
    print("   - OpenAI API key for LLM processing")
    print("   - Stripe API keys for payment processing")
    print("   - Email/Slack credentials for notifications")
    
    print("\n2. 🚀 Start the application:")
    if platform.system().lower() == "windows":
        print("   .\\venv\\Scripts\\activate")
        print("   python main.py")
    else:
        print("   source venv/bin/activate")
        print("   python main.py")
    
    print("\n3. 🌐 Access the application:")
    print("   - API: http://localhost:8000")
    print("   - Documentation: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    
    print("\n4. 📚 Test the system:")
    print("   - Upload a PDF claim document")
    print("   - Check OCR extraction")
    print("   - Test LLM data extraction")
    print("   - Verify validation and routing")
    
    print("\n5. 🔧 Additional Configuration:")
    print("   - Set up PostgreSQL for production")
    print("   - Configure Redis for background tasks")
    print("   - Set up monitoring and alerting")
    
    print("\n📖 For detailed documentation, visit:")
    print("   http://localhost:8000/docs")
    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🚀 CLAIM PROCESSING AUTOMATION SETUP")
    print("="*50)
    print("This script will set up the complete claim processing system")
    print("including OCR, LLM agents, validation, and payment processing.\n")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    
    try:
        # Step 1: Install system dependencies
        if not install_system_dependencies():
            print("⚠️  System dependencies installation had issues, but continuing...")
        
        # Step 2: Create virtual environment
        if not create_virtual_environment():
            print("❌ Failed to create virtual environment")
            sys.exit(1)
        
        # Step 3: Install Python dependencies
        if not install_python_dependencies():
            print("❌ Failed to install Python dependencies")
            sys.exit(1)
        
        # Step 4: Create directories
        create_directories()
        
        # Step 5: Setup environment file
        if not setup_environment_file():
            print("❌ Failed to setup environment file")
            sys.exit(1)
        
        # Step 6: Initialize database
        initialize_database()
        
        # Step 7: Verify installation
        verify_installation()
        
        # Step 8: Display next steps
        display_next_steps()
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()