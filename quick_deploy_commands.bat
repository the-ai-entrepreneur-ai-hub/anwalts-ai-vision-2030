@echo off
echo ==========================================
echo  AnwaltsAI Hetzner Server Deployment
echo ==========================================
echo.
echo Server: 148.251.195.222
echo Owner: Dr. Markus Weigl, AIgenex GmbH
echo Dataset: 9,997 German legal examples
echo.

echo Choose deployment method:
echo 1. Upload ZIP file (Recommended)
echo 2. Upload directory directly
echo 3. Show manual commands
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto upload_zip
if "%choice%"=="2" goto upload_dir
if "%choice%"=="3" goto show_commands
goto invalid

:upload_zip
echo.
echo Uploading ZIP file to server...
echo Command: scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
echo.
scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
if errorlevel 1 (
    echo Upload failed. Try manual method.
    pause
    goto end
)
echo.
echo ZIP uploaded successfully!
echo.
echo Next steps:
echo 1. SSH into server: ssh root@148.251.195.222
echo 2. Password: BrfiDiUwxFEAvu
echo 3. Extract: cd /opt && unzip "anwalts-ai-deployment-Law Firm Vision 2030.zip"
echo 4. Deploy: cd deployment_package && chmod +x deploy.sh && ./deploy.sh
echo.
pause
goto end

:upload_dir
echo.
echo Uploading deployment directory...
echo Command: scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/
echo.
scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/
if errorlevel 1 (
    echo Upload failed. Try manual method.
    pause
    goto end
)
echo.
echo Directory uploaded successfully!
echo.
echo Next steps:
echo 1. SSH into server: ssh root@148.251.195.222
echo 2. Password: BrfiDiUwxFEAvu
echo 3. Deploy: cd /opt/anwalts-ai && chmod +x deploy.sh && ./deploy.sh
echo.
pause
goto end

:show_commands
echo.
echo ==========================================
echo  Manual Deployment Commands
echo ==========================================
echo.
echo 1. Upload ZIP file:
echo    scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
echo.
echo 2. OR Upload directory:
echo    scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/
echo.
echo 3. SSH into server:
echo    ssh root@148.251.195.222
echo    Password: BrfiDiUwxFEAvu
echo.
echo 4. If you uploaded ZIP:
echo    cd /opt
echo    unzip "anwalts-ai-deployment-Law Firm Vision 2030.zip"
echo    cd deployment_package
echo.
echo 5. If you uploaded directory:
echo    cd /opt/anwalts-ai
echo.
echo 6. Deploy:
echo    chmod +x deploy.sh
echo    ./deploy.sh
echo.
echo 7. Verify deployment:
echo    Access: http://148.251.195.222
echo    API: http://148.251.195.222/api/docs
echo    Health: http://148.251.195.222/health
echo.
pause
goto end

:invalid
echo Invalid choice. Please run again and select 1, 2, or 3.
pause
goto end

:end
echo.
echo Deployment package ready with 9,997 German legal examples!
echo Application will be available at: http://148.251.195.222
echo.
pause