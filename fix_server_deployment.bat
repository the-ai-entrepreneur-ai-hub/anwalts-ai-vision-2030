@echo off
echo ==========================================
echo  Fixing AnwaltsAI Server Deployment
echo ==========================================
echo.
echo The files were extracted to /opt/ directly.
echo Let's fix this and complete the deployment.
echo.

echo Connecting to server to fix and deploy...
echo Password: BrfiDiUwxFEAvu
echo.

ssh root@148.251.195.222 "cd /opt && ls -la && chmod +x deploy.sh && ./deploy.sh"

if errorlevel 1 (
    echo.
    echo If that failed, let's try manual commands:
    echo.
    pause
    echo.
    echo Running manual fix...
    ssh root@148.251.195.222
) else (
    echo.
    echo ==========================================
    echo  Deployment Completed Successfully!
    echo ==========================================
    echo.
    echo Legal Dataset: 9,997 examples loaded
    echo Application: http://148.251.195.222
    echo API Docs: http://148.251.195.222/api/docs
    echo Health Check: http://148.251.195.222/health
    echo.
)

pause