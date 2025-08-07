# PowerShell script to setup Django database
Write-Host "🚀 Setting up PrintSmart Database..." -ForegroundColor Green

# Change to Backend directory
Set-Location "c:\printerAutomation\printSmart\Backend"

# Run database setup
Write-Host "Running database setup..." -ForegroundColor Yellow
python setup_database.py

# Try to run Django server
Write-Host "Starting Django server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "manage.py", "runserver" -NoNewWindow -PassThru

Write-Host "✅ Setup completed!" -ForegroundColor Green
Write-Host "Server should be running at http://127.0.0.1:8000" -ForegroundColor Cyan
