@echo off
echo ================================================
echo   AnwaltsAI Landing Page Deployment Script
echo ================================================
echo.

REM Set deployment directory
set DEPLOY_DIR=/opt/anwalts-ai-production/Client

echo [1/5] Checking required files...
if not exist "Client\index.html" (
    echo ERROR: Landing page not found!
    pause
    exit /b 1
)

if not exist "Client\api-client.js" (
    echo ERROR: API client not found!
    pause
    exit /b 1
)

echo [2/5] Copying landing page files...
copy "Client\index.html" "Client\index_backup.html" > nul
copy "Client\performance-optimizer.js" "Client\performance-optimizer.js" > nul

echo [3/5] Testing local functionality...
echo Starting local test server...
cd Client
start /min python -m http.server 8080

echo [4/5] Waiting for server startup...
timeout /t 3 /nobreak > nul

echo [5/5] Testing landing page...
echo Opening landing page in browser for testing...
start http://localhost:8080/index.html

echo.
echo ================================================
echo   Deployment Steps Completed Successfully!
echo ================================================
echo.
echo Local test server is running at: http://localhost:8080
echo.
echo Next steps for production deployment:
echo 1. Upload files to server: %DEPLOY_DIR%
echo 2. Configure Nginx to serve index.html as default
echo 3. Setup SSL certificates
echo 4. Test login functionality
echo.
echo Press any key to continue...
pause > nul