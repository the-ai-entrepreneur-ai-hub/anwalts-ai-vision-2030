@echo off
echo Setting up AnwaltsAI Local Development Environment...

REM Create a simple .env file for local development
echo Creating local environment configuration...
echo DATABASE_URL=sqlite:///./anwalts_ai.db > .env.local
echo REDIS_URL=redis://localhost:6379/0 >> .env.local
echo TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720 >> .env.local
echo JWT_SECRET_KEY=local-development-jwt-secret-key >> .env.local
echo ENVIRONMENT=development >> .env.local
echo CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500 >> .env.local

REM Create requirements.txt if it doesn't exist
if not exist "backend\requirements.txt" (
    echo Creating requirements.txt...
    echo fastapi==0.104.1 > backend\requirements.txt
    echo uvicorn[standard]==0.24.0 >> backend\requirements.txt
    echo sqlalchemy==2.0.23 >> backend\requirements.txt
    echo databases[sqlite]==0.8.0 >> backend\requirements.txt
    echo python-multipart==0.0.6 >> backend\requirements.txt
    echo python-jose[cryptography]==3.3.0 >> backend\requirements.txt
    echo passlib[bcrypt]==1.7.4 >> backend\requirements.txt
    echo python-dotenv==1.0.0 >> backend\requirements.txt
    echo httpx==0.25.2 >> backend\requirements.txt
    echo aiosqlite==0.19.0 >> backend\requirements.txt
)

echo.
echo ================================================
echo Local Development Setup Complete!
echo ================================================
echo.
echo To start the application:
echo   Windows: start-local-no-docker.bat
echo   Linux/Mac: ./start-local-no-docker.sh
echo.
echo The app will run on:
echo   Frontend: http://localhost:3000
echo   Backend: http://localhost:8000
echo ================================================

pause