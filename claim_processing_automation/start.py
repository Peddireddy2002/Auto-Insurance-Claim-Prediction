#!/usr/bin/env python3
"""
Quick Start Script for Claim Processing Automation System
This script provides easy commands to run, test, and manage the application
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def run_command(command, shell=False, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=shell, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(command) if isinstance(command, list) else command}")
        print(f"Error: {e}")
        return False

def get_python_path():
    """Get the path to Python in the virtual environment."""
    if platform.system().lower() == "windows":
        return os.path.join("venv", "Scripts", "python")
    else:
        return os.path.join("venv", "bin", "python")

def check_environment():
    """Check if the environment is properly set up."""
    if not Path("venv").exists():
        print("❌ Virtual environment not found. Please run setup.py first:")
        print("   python setup.py")
        return False
    
    if not Path(".env").exists():
        print("❌ Environment file not found. Please run setup.py first:")
        print("   python setup.py")
        return False
    
    return True

def start_application():
    """Start the main application."""
    print("🚀 Starting Claim Processing Automation System...")
    
    if not check_environment():
        return False
    
    python_path = get_python_path()
    
    # Start the application
    try:
        subprocess.run([python_path, "main.py"])
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    
    return True

def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    
    if not check_environment():
        return False
    
    python_path = get_python_path()
    
    # Run pytest
    success = run_command([python_path, "-m", "pytest", "tests/", "-v", "--cov=."])
    
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return success

def install_dependencies():
    """Install or update dependencies."""
    print("📦 Installing/updating dependencies...")
    
    python_path = get_python_path()
    
    # Upgrade pip
    run_command([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    success = run_command([python_path, "-m", "pip", "install", "-r", "requirements.txt"])
    
    if success:
        print("✅ Dependencies installed successfully")
    else:
        print("❌ Failed to install dependencies")
    
    return success

def setup_database():
    """Initialize or reset the database."""
    print("🗄️  Setting up database...")
    
    if not check_environment():
        return False
    
    python_path = get_python_path()
    
    # Initialize database
    success = run_command([python_path, "-c", """
import os
from pathlib import Path
from backend.models.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)
print('✅ Database initialized successfully')
"""])
    
    return success

def check_system():
    """Check system dependencies and configuration."""
    print("🔍 Checking system configuration...")
    
    checks = []
    
    # Check Python version
    if sys.version_info >= (3, 9):
        checks.append("✅ Python version: " + sys.version.split()[0])
    else:
        checks.append("❌ Python version: " + sys.version.split()[0] + " (requires 3.9+)")
    
    # Check Tesseract
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            checks.append("✅ Tesseract OCR: " + version)
        else:
            checks.append("❌ Tesseract OCR: Not found")
    except FileNotFoundError:
        checks.append("❌ Tesseract OCR: Not installed")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        checks.append("✅ Redis: Connected")
    except:
        checks.append("⚠️  Redis: Not connected (optional for basic functionality)")
    
    # Check virtual environment
    if Path("venv").exists():
        checks.append("✅ Virtual environment: Found")
    else:
        checks.append("❌ Virtual environment: Not found")
    
    # Check environment file
    if Path(".env").exists():
        checks.append("✅ Environment file: Found")
    else:
        checks.append("❌ Environment file: Not found")
    
    # Display results
    print("\n" + "="*50)
    print("SYSTEM STATUS:")
    print("="*50)
    for check in checks:
        print(check)
    print("="*50)
    
    return True

def show_logs():
    """Show application logs."""
    log_file = Path("logs/app.log")
    
    if log_file.exists():
        print("📋 Application logs (last 50 lines):")
        print("="*50)
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-50:]:
                print(line.strip())
    else:
        print("❌ Log file not found")

def create_sample_data():
    """Create sample data for testing."""
    print("📊 Creating sample data...")
    
    if not check_environment():
        return False
    
    python_path = get_python_path()
    
    # Create sample data
    success = run_command([python_path, "-c", """
import json
from pathlib import Path

# Create sample claim data
sample_claims = [
    {
        "claimant_name": "John Doe",
        "claimant_email": "john.doe@example.com",
        "claimant_phone": "+1-555-123-4567",
        "incident_date": "2024-01-15",
        "incident_location": "Main St & 1st Ave, Anytown, USA",
        "incident_description": "Rear-end collision at traffic light",
        "claim_amount": 2500.00,
        "policy_number": "POL-123456789"
    },
    {
        "claimant_name": "Jane Smith",
        "claimant_email": "jane.smith@example.com",
        "claimant_phone": "+1-555-987-6543",
        "incident_date": "2024-01-20",
        "incident_location": "Highway 101, Mile Marker 45",
        "incident_description": "Single vehicle accident due to weather conditions",
        "claim_amount": 8750.00,
        "policy_number": "POL-987654321"
    }
]

# Save sample data
Path("data").mkdir(exist_ok=True)
with open("data/sample_claims.json", "w") as f:
    json.dump(sample_claims, f, indent=2)

print("✅ Sample data created in data/sample_claims.json")
"""])
    
    return success

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Claim Processing Automation - Quick Start")
    parser.add_argument("command", nargs="?", default="start", 
                       choices=["start", "test", "install", "setup-db", "check", "logs", "sample-data"],
                       help="Command to execute")
    
    args = parser.parse_args()
    
    print("🏥 CLAIM PROCESSING AUTOMATION")
    print("="*40)
    
    if args.command == "start":
        start_application()
    elif args.command == "test":
        run_tests()
    elif args.command == "install":
        install_dependencies()
    elif args.command == "setup-db":
        setup_database()
    elif args.command == "check":
        check_system()
    elif args.command == "logs":
        show_logs()
    elif args.command == "sample-data":
        create_sample_data()
    else:
        print("❌ Unknown command. Available commands:")
        print("   start      - Start the application")
        print("   test       - Run tests")
        print("   install    - Install dependencies")
        print("   setup-db   - Initialize database")
        print("   check      - Check system status")
        print("   logs       - Show application logs")
        print("   sample-data- Create sample test data")

if __name__ == "__main__":
    main()