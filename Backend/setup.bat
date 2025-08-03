@echo off
echo ========================================
echo PrintSmart Backend Setup Script
echo ========================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Run the Python setup script
echo Running Python setup script...
python setup_project.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start development:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Update .env file with your settings
echo 3. Create superuser: python manage.py createsuperuser
echo 4. Run server: python manage.py runserver
echo.
pause
