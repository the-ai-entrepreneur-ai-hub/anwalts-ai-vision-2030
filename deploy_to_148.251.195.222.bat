@echo off
echo.
echo =================================================================
echo   🚀 Portal-Anwalts.AI Deploy to 148.251.195.222
echo =================================================================
echo.

echo Server: 148.251.195.222
echo Domain: portal-anwalts.ai
echo Features: Enhanced Registration + German Legal Specializations
echo.

echo [1/3] Creating CORRECTED deployment package...
echo 📱 Using anwalts-ai-app.html as main frontend (FIXED!)
echo.

if not exist "deploy_portal_anwalts_FIXED.bat" (
    echo ❌ Fixed deployment script not found!
    pause
    exit /b 1
)

call deploy_portal_anwalts_FIXED.bat

echo.
echo [2/3] Uploading to server...
echo 💡 Enter your server password when prompted
echo.

scp portal-anwalts-ai-production-deployment.zip root@148.251.195.222:/tmp/

echo.
echo [3/3] SSH and deploy instructions:
echo.
echo Run these commands:
echo   ssh root@148.251.195.222
echo   cd /tmp ^&^& unzip -o portal-anwalts-ai-production-deployment.zip
echo   cd portal-anwalts-ai-deployment ^&^& sudo bash scripts/deploy.sh
echo.
echo After deployment, visit: https://portal-anwalts.ai/enhanced-registration.html
echo.
pause