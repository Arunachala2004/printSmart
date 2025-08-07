@echo off
echo Starting PrintSmart Django Server...
echo.

echo Checking Python installation...
python --version

echo.
echo Checking Django installation...
python -c "import django; print('Django version:', django.get_version())"

echo.
echo Running Django system check...
python manage.py check

echo.
echo Applying migrations...
python manage.py migrate

echo.
echo Starting development server...
python manage.py runserver 127.0.0.1:8000

pause
