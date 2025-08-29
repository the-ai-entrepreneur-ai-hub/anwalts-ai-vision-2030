@echo off
echo Starting AnwaltsAI Locally (No Docker)...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed (optional for serving frontend)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Node.js not found. Will use Python HTTP server for frontend.
)

echo.
echo ================================================
echo Setting up Backend...
echo ================================================

REM Navigate to backend directory
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Set environment variables for local development
set DATABASE_URL=sqlite:///./anwalts_ai.db
set REDIS_URL=redis://localhost:6379/0
set TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720
set JWT_SECRET_KEY=local-development-jwt-secret-key
set ENVIRONMENT=development
set CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500

echo.
echo Starting FastAPI backend server...
start "AnwaltsAI Backend" python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Go back to root and start frontend
cd ..

echo.
echo ================================================
echo Setting up Frontend...
echo ================================================

REM Start a simple HTTP server for frontend
cd Client
echo Starting frontend HTTP server...
start "AnwaltsAI Frontend" python -m http.server 3000

echo.
echo ================================================
echo AnwaltsAI Started Successfully!
echo ================================================
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open the application...
pause >nul

REM Open in browser
start http://localhost:3000

echo.
echo To stop the servers, close the terminal windows
echo or press Ctrl+C in each terminal
pause