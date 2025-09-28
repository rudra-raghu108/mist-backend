@echo off
echo Starting MIST AI Backend Development Server...
echo.

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy env.example .env
    echo Please edit .env file with your configuration before starting the server.
    echo.
)

REM Check if node_modules exists
if not exist node_modules (
    echo Installing dependencies...
    npm install
    echo.
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Start development server
echo Starting development server...
npm run dev


