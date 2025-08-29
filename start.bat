@echo off
echo ===============================================
echo  AnwaltsAI Full-Stack Deployment
echo ===============================================
echo.

echo [1/4] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop and try again.
    pause
    exit /b 1
)
echo ✅ Docker is installed

echo.
echo [2/4] Building and starting services...
docker-compose up -d --build

echo.
echo [3/4] Waiting for services to be ready...
timeout /t 10 /nobreak > nul

echo.
echo [4/4] Checking service health...
echo Backend: http://localhost:8000/health
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs

echo.
echo ===============================================
echo  🚀 AnwaltsAI is starting up!
echo ===============================================
echo.
echo Open these URLs in your browser:
echo - Frontend: http://localhost:3000
echo - API Documentation: http://localhost:8000/docs
echo - Backend Health: http://localhost:8000/health
echo.
echo To stop the services, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo.
pause