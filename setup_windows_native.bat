@echo off
echo.
echo ==========================================
echo    AnwaltsAI Setup (Windows Native)
echo ==========================================
echo.

echo This script will help you install PostgreSQL and Redis natively on Windows.
echo.

echo [1/4] Checking if PostgreSQL is installed...
pg_ctl --version >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL not found. Please download and install:
    echo https://www.postgresql.org/download/windows/
    echo.
    echo During installation:
    echo - Set password: postgres
    echo - Port: 5432
    echo - Remember the superuser password!
    echo.
    echo After installation, restart this script.
    pause
    exit /b 1
) else (
    echo ✅ PostgreSQL is installed
)

echo.
echo [2/4] Checking if Redis is available...
REM Redis for Windows is available through Microsoft's port or using WSL
echo For Redis on Windows, you have options:
echo 1. Use WSL2 and install Redis there
echo 2. Use Redis Docker container
echo 3. Use Memurai (Redis-compatible for Windows)
echo.
echo For now, we'll continue without Redis (optional for basic functionality)

echo.
echo [3/4] Creating database...
echo Creating AnwaltsAI database...
createdb -U postgres anwalts_ai_db
if errorlevel 1 (
    echo Failed to create database. Make sure PostgreSQL is running:
    echo net start postgresql-x64-15
    pause
)

echo.
echo [4/4] Initializing database schema...
cd /d "%~dp0\backend"
python init_db.py

echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo Database: PostgreSQL (anwalts_ai_db)
echo Cache: Disabled (Redis not required)
echo AI: Ready (DeepSeek-V3)
echo.
echo Start the app:
echo 1. python start_backend.py
echo 2. python start_frontend.py (new terminal)
echo ==========================================
pause