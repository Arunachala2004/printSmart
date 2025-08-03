# PrintSmart Backend Setup Script (PowerShell)
# This script sets up the entire Django backend project

param(
    [switch]$SkipVenv,
    [switch]$Force
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PrintSmart Backend Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Function to check if command exists
function Test-Command {
    param($CommandName)
    return [bool](Get-Command -Name $CommandName -ErrorAction SilentlyContinue)
}

# Check if Python is installed
if (-not (Test-Command "python")) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    exit 1
}

# Display Python version
$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv") -or $Force) {
    if ($Force -and (Test-Path "venv")) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    }
    
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
if (-not $SkipVenv) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
        Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
        exit 1
    }
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Run the Python setup script
Write-Host "Running Python setup script..." -ForegroundColor Yellow
python setup_project.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start development:" -ForegroundColor Cyan
    Write-Host "1. Activate virtual environment: venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "2. Update .env file with your settings" -ForegroundColor White
    Write-Host "3. Create superuser: python manage.py createsuperuser" -ForegroundColor White
    Write-Host "4. Run server: python manage.py runserver" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "Setup failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

# Option to create superuser immediately
$createSuperuser = Read-Host "Would you like to create a superuser now? (y/N)"
if ($createSuperuser -eq "y" -or $createSuperuser -eq "Y") {
    Write-Host "Creating superuser..." -ForegroundColor Yellow
    python manage.py createsuperuser
}

# Option to start development server
$startServer = Read-Host "Would you like to start the development server? (y/N)"
if ($startServer -eq "y" -or $startServer -eq "Y") {
    Write-Host "Starting development server..." -ForegroundColor Yellow
    Write-Host "Server will be available at: http://127.0.0.1:8000/" -ForegroundColor Green
    Write-Host "Admin panel: http://127.0.0.1:8000/admin/" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    python manage.py runserver
}
