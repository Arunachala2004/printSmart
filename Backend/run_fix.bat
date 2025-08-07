@echo off
echo Setting up PrintSmart Database...
cd /d "c:\printerAutomation\printSmart\Backend"

echo.
echo Running Python database setup script...
python manual_fix.py

echo.
echo Starting Django development server...
python manage.py runserver

pause
