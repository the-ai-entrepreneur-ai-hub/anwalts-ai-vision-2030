@echo off
echo ==========================================
echo  AnwaltsAI Windows Deployment Fix
echo ==========================================
echo.
echo The original quick_deploy_commands.bat failed because
echo Windows doesn't have 'scp' command by default.
echo.
echo Here are your options:
echo.
echo 1. Install OpenSSH on Windows (Recommended)
echo 2. Use WinSCP (GUI File Transfer)
echo 3. Use PuTTY + PSCP
echo 4. Use PowerShell script
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto install_openssh
if "%choice%"=="2" goto use_winscp
if "%choice%"=="3" goto use_putty
if "%choice%"=="4" goto use_powershell
goto invalid

:install_openssh
echo.
echo Installing OpenSSH Client...
echo This requires Administrator privileges.
echo.
powershell -Command "Start-Process PowerShell -ArgumentList 'Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0; pause' -Verb RunAs"
echo.
echo After installation completes, run this command:
echo scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
echo.
pause
goto end

:use_winscp
echo.
echo Download WinSCP from: https://winscp.net/eng/download.php
echo.
echo Connection details:
echo Protocol: SFTP
echo Host: 148.251.195.222
echo Username: root
echo Password: BrfiDiUwxFEAvu
echo.
echo Upload "anwalts-ai-deployment-Law Firm Vision 2030.zip" to /opt/ directory
echo Then SSH and run: cd /opt && unzip "anwalts-ai-deployment-Law Firm Vision 2030.zip" && cd deployment_package && chmod +x deploy.sh && ./deploy.sh
echo.
pause
goto end

:use_putty
echo.
echo Download PuTTY from: https://www.putty.org/
echo.
echo Upload with PSCP:
echo pscp -pw BrfiDiUwxFEAvu "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
echo.
echo Then SSH with PuTTY:
echo Host: 148.251.195.222
echo Username: root
echo Password: BrfiDiUwxFEAvu
echo.
pause
goto end

:use_powershell
echo.
echo Running PowerShell deployment script...
echo.
powershell -ExecutionPolicy Bypass -File "deploy_windows.ps1"
goto end

:invalid
echo Invalid choice. Please run again and select 1-4.
pause
goto end

:end
echo.
echo Deployment package contains 9,997 German legal examples!
echo Target server: 148.251.195.222
echo.
pause