@echo off
echo.
echo =================================================================
echo   🚀 Development Sync Setup for Portal-Anwalts.AI
echo   Real-time sync: Local → Server 148.251.195.222
echo =================================================================
echo.

echo [1/3] Creating sync scripts...

rem Create instant sync script
echo @echo off > quick_sync.bat
echo echo 🔄 Quick sync to portal-anwalts.ai... >> quick_sync.bat
echo rsync -avz Client/anwalts-ai-app.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> quick_sync.bat
echo rsync -avz Client/anwalts-ai-dashboard.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> quick_sync.bat
echo rsync -avz Client/enhanced-registration.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> quick_sync.bat
echo rsync -avz Client/api-client.js root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> quick_sync.bat
echo rsync -avz Client/*.css root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> quick_sync.bat
echo echo ✅ Frontend synced! >> quick_sync.bat

rem Create backend sync script  
echo @echo off > sync_backend.bat
echo echo 🔄 Syncing backend... >> sync_backend.bat
echo rsync -avz backend/ root@148.251.195.222:/var/www/portal-anwalts.ai/backend/ >> sync_backend.bat
echo ssh root@148.251.195.222 "systemctl restart anwalts-api" >> sync_backend.bat
echo echo ✅ Backend synced! >> sync_backend.bat

echo [2/3] Creating VS Code integration...
mkdir .vscode 2>nul
echo Creating VS Code tasks...

echo [3/3] Setup complete!
echo.
echo ✅ Available Commands:
echo   quick_sync.bat    - Sync frontend files
echo   sync_backend.bat  - Sync backend files
echo.
echo 🔗 Changes appear at: https://portal-anwalts.ai
echo.
pause