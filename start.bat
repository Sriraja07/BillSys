@echo off
echo ⚡ Electrical Billing Software
echo ===============================
echo.
echo Starting application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Dependencies OK
echo.
echo 🚀 Launching Electrical Billing Software...
echo.
echo Note: A desktop window will open shortly.
echo Close this window to stop the application.
echo.

REM Start the desktop application
python desktop_app.py

echo.
echo Application closed.
pause 