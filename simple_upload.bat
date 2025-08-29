@echo off
echo ==========================================
echo  Simple AnwaltsAI Deployment
echo ==========================================
echo.
echo Server: 148.251.195.222
echo Dataset: 9,997 German legal examples  
echo.

REM Check if PowerShell is available
powershell -Command "exit" >nul 2>&1
if errorlevel 1 (
    echo PowerShell not found!
    pause
    exit /b 1
)

echo Checking for OpenSSH...
powershell -Command "Get-Command ssh -ErrorAction SilentlyContinue" >nul 2>&1
if errorlevel 1 (
    echo.
    echo OpenSSH not found. Installing...
    echo This requires Administrator privileges.
    echo.
    powershell -Command "Start-Process PowerShell -ArgumentList 'Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0; Write-Host Install completed; pause' -Verb RunAs"
    echo.
    echo After installation, run this script again.
    pause
    exit /b 0
)

echo OpenSSH found!
echo.

REM Check if ZIP file exists
if not exist "anwalts-ai-deployment-Law Firm Vision 2030.zip" (
    echo ZIP file not found!
    echo Please run: python create_deployment_package.py
    pause
    exit /b 1
)

echo Found deployment package.
echo.
echo Uploading to server...
echo.

REM Upload ZIP file
scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/

if errorlevel 1 (
    echo.
    echo Upload failed. Try manual method:
    echo 1. Download WinSCP: https://winscp.net/eng/download.php
    echo 2. Connect to 148.251.195.222 with user 'root' and password 'BrfiDiUwxFEAvu'
    echo 3. Upload ZIP file to /opt/ directory
    pause
    exit /b 1
)

echo.
echo Upload successful!
echo.
echo Now deploying on server...
echo.

REM Deploy on server
ssh root@148.251.195.222 "cd /opt && unzip -o 'anwalts-ai-deployment-Law Firm Vision 2030.zip' && cd deployment_package && chmod +x deploy.sh && ./deploy.sh"

if errorlevel 1 (
    echo.
    echo Deployment may have failed. 
    echo SSH manually to check: ssh root@148.251.195.222
    echo Password: BrfiDiUwxFEAvu
    pause
    exit /b 1
)

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
pause