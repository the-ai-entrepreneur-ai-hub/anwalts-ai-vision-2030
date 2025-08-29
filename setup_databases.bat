@echo off
echo.
echo ==========================================
echo    AnwaltsAI Database Setup
echo ==========================================
echo.

echo [1/4] Installing PostgreSQL and Redis with Docker...
echo.

REM Stop and remove existing containers if they exist
docker stop anwalts-postgres 2>nul
docker stop anwalts-redis 2>nul
docker rm anwalts-postgres 2>nul
docker rm anwalts-redis 2>nul

echo Starting PostgreSQL container...
docker run -d ^
  --name anwalts-postgres ^
  -e POSTGRES_DB=anwalts_ai_db ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=postgres ^
  -p 5432:5432 ^
  postgres:15

echo.
echo Starting Redis container...
docker run -d ^
  --name anwalts-redis ^
  -p 6379:6379 ^
  redis:7-alpine

echo.
echo [2/4] Waiting for databases to start...
timeout /t 10 /nobreak >nul

echo.
echo [3/4] Testing database connections...
docker exec anwalts-postgres pg_isready -U postgres -d anwalts_ai_db
docker exec anwalts-redis redis-cli ping

echo.
echo [4/4] Database setup complete!
echo.
echo ==========================================
echo    Database Services Running
echo ==========================================
echo PostgreSQL: localhost:5432
echo   Database: anwalts_ai_db
echo   Username: postgres  
echo   Password: postgres
echo.
echo Redis: localhost:6379
echo.
echo Next step: Run the database initialization
echo   cd backend
echo   python init_db.py
echo ==========================================
echo.
pause