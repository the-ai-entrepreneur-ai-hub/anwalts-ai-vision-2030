@echo off
echo.
echo ======================================================
echo    AnwaltsAI Enhanced Registration Demo
echo ======================================================
echo.

echo [1/3] Starting Enhanced Registration Backend...
cd /d "%~dp0\backend"
start "Backend Server" cmd /k "python test_enhanced_registration.py"
echo Backend starting at: http://localhost:8000

echo.
echo [2/3] Starting Frontend Server...
cd /d "%~dp0\Client"
start "Frontend Server" cmd /k "python -m http.server 3000"
echo Frontend starting at: http://localhost:3000

echo.
echo [3/3] Waiting for servers to start...
timeout /t 5 /nobreak >nul

echo.
echo ======================================================
echo    Servers Started Successfully!
echo ======================================================
echo.
echo Backend API:     http://localhost:8000
echo Frontend:        http://localhost:3000
echo.
echo Test Pages:
echo 1. Enhanced Registration Form:
echo    http://localhost:3000/test-enhanced-registration.html
echo.
echo 2. API Test Endpoints:
echo    GET  http://localhost:8000/health
echo    GET  http://localhost:8000/test/validate-fields
echo    POST http://localhost:8000/auth/register
echo    GET  http://localhost:8000/test/users
echo.
echo ======================================================
echo    How to Test Enhanced Registration:
echo ======================================================
echo.
echo Option 1 - Web Interface:
echo 1. Open: http://localhost:3000/test-enhanced-registration.html
echo 2. Click "Test Enhanced Registration" 
echo 3. Fill the enhanced form with legal professional details
echo 4. Submit and see the comprehensive profile created
echo.
echo Option 2 - API Testing:
echo 1. Use the test buttons on the web page
echo 2. Check results in the browser console
echo 3. View registered users at: http://localhost:8000/test/users
echo.
echo Option 3 - Manual API Test:
echo Run: python test_registration_api.py
echo.
echo Press any key when done testing to stop servers...
pause >nul

echo.
echo Stopping servers...
taskkill /F /IM python.exe /T >nul 2>&1
echo Servers stopped.
echo.
pause