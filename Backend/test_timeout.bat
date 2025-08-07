@echo off
REM Quick test script for job timeout management
REM Usage: test_timeout.bat

echo =======================================================
echo            PrintSmart Job Timeout Test
echo =======================================================

cd /d "c:\printerAutomation\printSmart\Backend"

echo.
echo 1. Testing with DRY RUN mode (no changes):
echo -------------------------------------------------------
python manage.py manage_job_timeouts --dry-run --verbose --pending-timeout 1

echo.
echo.
echo 2. Testing with TEST MODE (updates jobs but no refunds):
echo -------------------------------------------------------
python manage.py manage_job_timeouts --test-mode --verbose --pending-timeout 1

echo.
echo.
echo 3. Checking current job status:
echo -------------------------------------------------------
python manage.py shell -c "from print_jobs.models import PrintJob; jobs = PrintJob.objects.filter(status='pending'); print(f'Pending jobs: {jobs.count()}'); jobs = PrintJob.objects.filter(status='cancelled'); print(f'Cancelled jobs: {jobs.count()}')"

echo.
echo Test completed. Check the results above.
pause
