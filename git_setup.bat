@echo off
echo Setting up Git repository for PrintSmart...
echo.

REM Change to project directory
cd /d "c:\Users\mukil\Desktop\Projects\printSmart"

REM Check if git is already initialized
if exist ".git" (
    echo Git repository already exists, checking status...
) else (
    echo Initializing new Git repository...
    git init
)

echo.
echo Adding all files to staging area...
git add .

echo.
echo Checking git status...
git status

echo.
echo Creating initial commit...
git commit -m "Initial commit: PrintSmart Django backend with comprehensive file processing, print jobs, payments, and user management"

echo.
echo Checking for remote repository...
git remote -v

echo.
echo Git setup completed successfully!
echo Repository is ready for push to remote origin when configured.
echo.
echo To add a remote repository, use:
echo git remote add origin [YOUR_REPOSITORY_URL]
echo git branch -M main
echo git push -u origin main

pause
