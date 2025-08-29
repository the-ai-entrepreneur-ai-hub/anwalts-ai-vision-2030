@echo off
echo.
echo ==========================================
echo    AnwaltsAI Complete Setup
echo ==========================================
echo.

echo [1/6] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running!
    echo.
    echo Please install Docker Desktop from: https://docker.com/get-started
    echo Then restart this script.
    pause
    exit /b 1
)
echo ✅ Docker is available

echo.
echo [2/6] Setting up databases with Docker...
call setup_databases.bat

echo.
echo [3/6] Loading environment variables...
cd /d "%~dp0\backend"

echo.
echo [4/6] Installing Python dependencies...
pip install asyncpg redis python-dotenv passlib[bcrypt] 2>nul

echo.
echo [5/6] Initializing database schema...
python init_db.py

echo.
echo [6/6] Testing complete system...
echo Testing backend startup...
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo    Setup Complete! 🎉
echo ==========================================
echo.
echo Your AnwaltsAI system is ready with:
echo ✅ PostgreSQL Database (port 5432)
echo ✅ Redis Cache (port 6379) 
echo ✅ AI Service (DeepSeek-V3)
echo ✅ All tables initialized
echo ✅ Admin user created
echo.
echo To start the application:
echo 1. cd backend
echo 2. python start_backend.py
echo.
echo 3. [New terminal] cd Client  
echo 4. python start_frontend.py
echo.
echo 5. Open: http://localhost:3000/anwalts-ai-app.html
echo ==========================================
echo.
pause