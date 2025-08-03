#!/usr/bin/env python3
"""
PrintSmart Backend Setup Script
This script sets up the entire Django backend project with all required dependencies and configurations.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def create_requirements_txt():
    """Create requirements.txt with all necessary dependencies"""
    requirements = """
# Django and REST Framework
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.3

# Authentication & JWT
djangorestframework-simplejwt==5.3.0
PyJWT==2.8.0

# Database
psycopg2-binary==2.9.7

# File Processing
PyMuPDF==1.23.8
python-docx==0.8.11
Pillow==10.0.1
opencv-python==4.8.1.78

# Password Hashing
bcrypt==4.0.1

# Payment Integration
razorpay==1.4.1

# Environment Variables
python-decouple==3.8

# Logging and Monitoring
structlog==23.2.0

# Development Tools
django-debug-toolbar==4.2.0

# Task Queue (Optional for heavy operations)
celery==5.3.4
redis==5.0.1

# Print Management (Windows)
pywin32==306

# HTTP Requests
requests==2.31.0

# Validation
marshmallow==3.20.1

# Testing
pytest==7.4.3
pytest-django==4.5.2

# WSGI Server
gunicorn==21.2.0

# Static Files
whitenoise==6.6.0
""".strip()
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created requirements.txt")

def create_project_structure():
    """Create the Django project and apps structure"""
    commands = [
        ("pip install Django djangorestframework", "Installing Django and DRF"),
        ("django-admin startproject printsmart_backend .", "Creating Django project"),
        ("python manage.py startapp users", "Creating users app"),
        ("python manage.py startapp files", "Creating files app"),
        ("python manage.py startapp print_jobs", "Creating print_jobs app"),
        ("python manage.py startapp payments", "Creating payments app"),
        ("python manage.py startapp core", "Creating core app for shared utilities"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Failed to execute: {command}")
            return False
    
    return True

def setup_virtual_environment():
    """Setup virtual environment if not already active"""
    if os.environ.get('VIRTUAL_ENV'):
        print("✅ Virtual environment already active")
        return True
    
    venv_path = "venv"
    if not os.path.exists(venv_path):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # For Windows
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        print(f"🔄 Please run: {activate_script}")
        print("🔄 Then run this script again")
        return False
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")
        print(f"🔄 Please run: source {activate_script}")
        print("🔄 Then run this script again")
        return False

def install_dependencies():
    """Install all project dependencies"""
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing project dependencies"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def create_directory_structure():
    """Create additional directory structure"""
    directories = [
        "media/uploads/temp",
        "media/uploads/processed",
        "media/uploads/thumbnails",
        "static/css",
        "static/js",
        "static/images",
        "logs",
        "templates",
        "scripts",
        "docs",
        "tests",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file template"""
    env_content = """
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_NAME=printsmart_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Razorpay Configuration
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# File Upload Settings
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=pdf,docx,jpg,jpeg,png

# Print Settings
DEFAULT_PRINTER_NAME=your-default-printer

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Logging
LOG_LEVEL=INFO
""".strip()
    
    with open(".env.template", "w") as f:
        f.write(env_content)
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
    
    print("✅ Created .env template and .env file")

def create_gitignore():
    """Create comprehensive .gitignore file"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Media files
media/uploads/
!media/uploads/.gitkeep

# Static files
staticfiles/
!static/.gitkeep

# Environment variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
.pytest_cache/
htmlcov/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Logs
logs/
*.log

# Razorpay
razorpay_keys.py
""".strip()
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("✅ Created .gitignore file")

def main():
    """Main setup function"""
    print("🚀 PrintSmart Backend Setup Script")
    print("=" * 50)
    
    # Check if virtual environment is active
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Virtual environment not detected")
        setup_virtual_environment()
        return
    
    # Create requirements.txt
    create_requirements_txt()
    
    # Install dependencies first
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Create project structure
    if not create_project_structure():
        print("❌ Failed to create project structure")
        return
    
    # Create directories
    create_directory_structure()
    
    # Create configuration files
    create_env_file()
    create_gitignore()
    
    # Run initial Django setup
    setup_commands = [
        ("python manage.py makemigrations", "Creating initial migrations"),
        ("python manage.py migrate", "Running initial migrations"),
        ("python manage.py collectstatic --noinput", "Collecting static files"),
    ]
    
    for command, description in setup_commands:
        run_command(command, description)
    
    print("\n🎉 PrintSmart Backend Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Update .env file with your actual configuration values")
    print("2. Run: python manage.py createsuperuser")
    print("3. Run: python manage.py runserver")
    print("4. Visit: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    main()
