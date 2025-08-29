@echo off
echo ===============================================
echo   AnwaltsAI - Quick Start Script
echo ===============================================
echo.

REM Check if we're in the right directory
if not exist "backend\ai_service.py" (
    echo ERROR: Please run this from the Law Firm Vision 2030 directory
    echo Current directory should contain backend\ folder
    pause
    exit /b 1
)

echo [1/5] Checking Together API configuration...
if not exist "backend\.env" (
    echo WARNING: No .env file found
    echo.
    echo Please create backend\.env with your Together API key:
    echo TOGETHER_API_KEY=your_key_here
    echo.
    echo You can get a key from: https://api.together.xyz/
    echo.
    pause
)

echo [2/5] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [3/5] Quick API check...
cd ..
python quick_api_test.py

echo [4/5] Starting simple backend server...
echo Backend will start on: http://localhost:5001
echo Using simple backend (no database required)
echo.
start /B python simple_backend.py

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo [5/5] Starting frontend server...
echo Frontend will serve on: http://localhost:3000
echo This includes dashboard, generator, and all components
echo.
start /B python frontend_server.py

echo Waiting for frontend server...
timeout /t 2 /nobreak > nul

echo.
echo ===============================================
echo   AnwaltsAI Started Successfully!
echo ===============================================
echo.
echo Backend API: http://localhost:5001
echo Frontend App: http://localhost:3000
echo Dashboard: http://localhost:3000/dashboard
echo Generator: http://localhost:3000/generator
echo.
echo Login: admin@anwalts-ai.com / admin123
echo.
echo To stop: Close this window or Ctrl+C
echo Browser should auto-open to frontend
echo.
pause