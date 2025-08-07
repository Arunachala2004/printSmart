@echo off
title PrintSmart Diagnostic and Repair Tool
color 0A

echo.
echo ================================
echo  PRINTSMART DIAGNOSTIC TOOL
echo ================================
echo.
echo This tool will diagnose and fix common issues with your Django application.
echo.

cd /d "%~dp0"

echo Running diagnostic script...
echo.
python diagnose.py

echo.
echo ================================
echo  NEXT STEPS
echo ================================
echo.
echo If all checks passed, you can now:
echo 1. Run: python manage.py runserver
echo 2. Open: http://127.0.0.1:8000 in your browser
echo 3. Login with username: admin, password: admin123
echo.
echo If there were errors, please review the output above.
echo.

pause
echo.
echo Would you like to start the Django server now? (Y/N)
set /p choice="Enter your choice: "

if /i "%choice%"=="Y" (
    echo.
    echo Starting Django development server...
    echo Press Ctrl+C to stop the server when done.
    echo.
    python manage.py runserver
) else (
    echo.
    echo You can start the server later by running: python manage.py runserver
)

pause
