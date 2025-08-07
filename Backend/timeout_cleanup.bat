@echo off
REM Automated Print Job Timeout Management
REM For Windows Task Scheduler (run every 5 minutes)
REM 
REM Usage:
REM   timeout_cleanup.bat           - Production mode (with refunds)
REM   timeout_cleanup.bat test      - Test mode (no refunds)
REM   timeout_cleanup.bat dry-run   - Dry run mode (no changes)

cd /d "c:\printerAutomation\printSmart\Backend"

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Determine mode based on first argument
set MODE=%1
if "%MODE%"=="test" (
    set ARGS=--test-mode --pending-timeout 30 --processing-timeout 60
    echo [%date% %time%] Running job timeout management in TEST MODE... >> logs\timeout_cleanup.log
) else if "%MODE%"=="dry-run" (
    set ARGS=--dry-run --verbose --pending-timeout 30 --processing-timeout 60
    echo [%date% %time%] Running job timeout management in DRY RUN MODE... >> logs\timeout_cleanup.log
) else (
    set ARGS=--pending-timeout 30 --processing-timeout 60
    echo [%date% %time%] Running job timeout management in PRODUCTION MODE... >> logs\timeout_cleanup.log
)

REM Run job timeout management
python manage.py manage_job_timeouts %ARGS% >> logs\timeout_cleanup.log 2>&1

REM Check exit code
if %errorlevel% equ 0 (
    echo [%date% %time%] Job timeout management completed successfully >> logs\timeout_cleanup.log
) else (
    echo [%date% %time%] Job timeout management failed >> logs\timeout_cleanup.log
)

echo --- >> logs\timeout_cleanup.log
