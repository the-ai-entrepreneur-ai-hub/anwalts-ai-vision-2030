@echo off
REM AnwaltsAI Production Upload Script
REM Uploads deployment package to Hetzner AX102 server
REM Server: 148.251.195.222 (Dr. Markus Weigl, AIgenex GmbH)

echo =====================================================
echo 🚀 AnwaltsAI Production Upload to Hetzner Server
echo =====================================================
echo Server: 148.251.195.222 (AX102 #2743403)
echo Owner: Dr. Markus Weigl, AIgenex GmbH
echo =====================================================
echo.

REM Check if SCP is available
where scp >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: SCP not found!
    echo Please install OpenSSH client or use WinSCP
    echo.
    echo Options:
    echo 1. Install OpenSSH: Settings ^> Apps ^> Optional Features ^> OpenSSH Client
    echo 2. Download WinSCP: https://winscp.net/
    pause
    exit /b 1
)

REM Find the latest deployment package
echo 📦 Looking for deployment package...
for /f "delims=" %%i in ('dir /b /o-d anwalts-ai-production-*.tar.gz 2^>nul') do (
    set "LATEST_PACKAGE=%%i"
    goto :found
)

echo ❌ No deployment package found!
echo Please run create_production_deployment.py first
pause
exit /b 1

:found
echo ✅ Found package: %LATEST_PACKAGE%
echo.

REM Get file size
for %%A in (%LATEST_PACKAGE%) do set "FILESIZE=%%~zA"
set /a FILESIZE_MB=%FILESIZE% / 1024 / 1024

echo 📊 Package size: %FILESIZE_MB% MB
echo.

REM Confirm upload
echo 🔄 Ready to upload to server...
echo Destination: root@148.251.195.222:/opt/
echo Package: %LATEST_PACKAGE%
echo.
set /p CONFIRM="Continue with upload? (Y/N): "
if /i not "%CONFIRM%"=="Y" if /i not "%CONFIRM%"=="YES" (
    echo ❌ Upload cancelled
    pause
    exit /b 0
)

echo.
echo 🚀 Starting upload...
echo ⏳ This may take several minutes depending on connection speed...
echo.

REM Upload the package
scp -o StrictHostKeyChecking=no "%LATEST_PACKAGE%" root@148.251.195.222:/opt/

if %errorlevel% equ 0 (
    echo.
    echo ✅ Upload successful!
    echo.
    echo 📋 NEXT STEPS:
    echo =====================================================
    echo 1. SSH into the server:
    echo    ssh root@148.251.195.222
    echo    Password: BrfiDiUwxFEAvu
    echo.
    echo 2. Extract and deploy:
    echo    cd /opt
    echo    tar -xzf %LATEST_PACKAGE%
    echo    cd anwalts-ai-production
    echo    chmod +x deploy.sh
    echo    ./deploy.sh
    echo.
    echo 3. Verify deployment:
    echo    curl http://148.251.195.222/health
    echo.
    echo 📊 Your AnwaltsAI with 9,997 German legal examples
    echo    will be available at: http://148.251.195.222
    echo =====================================================
    echo.
    
    REM Ask if user wants to SSH now
    set /p SSH_NOW="🔗 SSH into server now? (Y/N): "
    if /i "%SSH_NOW%"=="Y" (
        echo.
        echo 🔐 Connecting to server...
        echo Password: BrfiDiUwxFEAvu
        echo.
        ssh root@148.251.195.222
    )
) else (
    echo.
    echo ❌ Upload failed!
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo - Check internet connection
    echo - Verify server is accessible: ping 148.251.195.222
    echo - Try manual upload with WinSCP
    echo - Check SSH key authentication
    echo.
    echo 📞 Support:
    echo - Hetzner Support: +49 [0] 9831 505-0
    echo - Project Owner: Dr. Markus Weigl (017621137333)
)

echo.
pause