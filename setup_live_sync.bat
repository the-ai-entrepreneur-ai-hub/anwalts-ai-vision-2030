@echo off
echo.
echo =================================================================
echo   🔄 Live Sync Setup for Portal-Anwalts.AI Development
echo   Local Changes → Server 148.251.195.222 (Real-time)
echo =================================================================
echo.

echo Choose your sync method:
echo   1. Auto-sync with file watcher (Recommended)
echo   2. Manual rsync on command
echo   3. VS Code SSH Extension (Real-time editing)
echo   4. Git-based workflow
echo.

choice /c 1234 /m "Select sync method (1-4):"

if %ERRORLEVEL%==1 goto :auto_sync
if %ERRORLEVEL%==2 goto :manual_sync
if %ERRORLEVEL%==3 goto :vscode_ssh
if %ERRORLEVEL%==4 goto :git_workflow

:auto_sync
echo.
echo 🔄 Setting up Auto-Sync with File Watcher...
echo.
echo This will:
echo   ✅ Watch for file changes in Client/ and backend/
echo   ✅ Automatically sync to server when you save
echo   ✅ Real-time updates on portal-anwalts.ai
echo.
echo Installing nodemon for file watching...
npm install -g nodemon

echo Creating auto-sync script...
echo @echo off > auto_sync_to_server.bat
echo echo 🔄 Syncing changes to server... >> auto_sync_to_server.bat
echo rsync -avz --delete Client/ root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> auto_sync_to_server.bat
echo rsync -avz --delete backend/ root@148.251.195.222:/var/www/portal-anwalts.ai/backend/ >> auto_sync_to_server.bat
echo echo ✅ Sync complete! >> auto_sync_to_server.bat

echo Starting file watcher...
echo Run this command to start watching:
echo   nodemon --watch Client/ --watch backend/ --exec auto_sync_to_server.bat
goto :end

:manual_sync
echo.
echo 📤 Setting up Manual Sync Command...
echo.
echo Creating manual sync script...
echo @echo off > sync_to_server.bat
echo echo 🚀 Syncing to portal-anwalts.ai server... >> sync_to_server.bat
echo rsync -avz --progress Client/ root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ >> sync_to_server.bat
echo rsync -avz --progress backend/ root@148.251.195.222:/var/www/portal-anwalts.ai/backend/ >> sync_to_server.bat
echo ssh root@148.251.195.222 "systemctl restart anwalts-api" >> sync_to_server.bat
echo echo ✅ Sync complete! Visit https://portal-anwalts.ai >> sync_to_server.bat

echo ✅ Manual sync ready!
echo Run: sync_to_server.bat whenever you want to sync
goto :end

:vscode_ssh
echo.
echo 📝 VS Code SSH Extension Setup...
echo.
echo 1. Install "Remote - SSH" extension in VS Code
echo 2. Press Ctrl+Shift+P and type "Remote-SSH: Connect to Host"
echo 3. Enter: root@148.251.195.222
echo 4. VS Code will open connected to your server
echo 5. Edit files directly on the server - instant updates!
echo.
echo Server paths:
echo   Frontend: /var/www/portal-anwalts.ai/frontend/
echo   Backend:  /var/www/portal-anwalts.ai/backend/
goto :end

:git_workflow
echo.
echo 🔧 Git-Based Workflow Setup...
echo.
echo This creates a deployment pipeline using Git:
echo 1. Push changes to Git repository
echo 2. Server pulls changes automatically
echo 3. Restarts services
echo.
echo Creating git deployment hook...
echo #!/bin/bash > deploy_via_git.sh
echo cd /var/www/portal-anwalts.ai >> deploy_via_git.sh
echo git pull origin main >> deploy_via_git.sh
echo systemctl restart anwalts-api >> deploy_via_git.sh
echo echo "✅ Deployment complete!" >> deploy_via_git.sh

echo Would you like to set up Git repository? (Y/N)
choice /c YN
if %ERRORLEVEL%==1 (
    git init
    git remote add origin YOUR_REPO_URL
    echo ✅ Git repository initialized
)
goto :end

:end
echo.
echo =================================================================
echo   🎉 Sync Setup Complete!
echo =================================================================
echo.
echo 💡 Pro Tips:
echo   • Use auto-sync for active development
echo   • Use manual sync for controlled deployments
echo   • Use VS Code SSH for direct server editing
echo   • Use Git workflow for team collaboration
echo.
echo Your changes will now sync to: https://portal-anwalts.ai
echo.
pause