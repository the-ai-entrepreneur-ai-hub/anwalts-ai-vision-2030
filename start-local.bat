@echo off
echo Starting AnwaltsAI Local Development Environment...

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Start the application
echo Starting services with docker-compose...
docker-compose up -d

echo.
echo ================================================
echo AnwaltsAI Local Development Started!
echo ================================================
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo Database: localhost:5432
echo Redis: localhost:6379
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f
echo ================================================

REM Wait a moment for services to start
timeout /t 5 /nobreak >nul

REM Open the application in browser
start http://localhost:3000

pause