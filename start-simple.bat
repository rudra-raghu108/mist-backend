@echo off
echo ========================================
echo SRM Guide Bot - Simple Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if requirements are installed
if not exist venv\Lib\site-packages\fastapi (
    echo Installing dependencies...
    pip install -r requirements-simple.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Try: pip install --upgrade pip
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy env-simple.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your OpenAI API key
    echo Get your API key from: https://platform.openai.com/
    echo.
    pause
)

REM Create logs directory
if not exist logs mkdir logs

echo.
echo ========================================
echo Starting SRM Guide Bot Backend...
echo ========================================
echo Backend will be available at: http://localhost:8000
echo API docs will be at: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the backend
python main.py

