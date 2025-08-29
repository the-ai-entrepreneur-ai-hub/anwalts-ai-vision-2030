@echo off
echo =================================
echo AnwaltsAI Server Diagnostic Script
echo =================================
echo.

echo Testing server connectivity...
echo.

echo 1. Testing basic connectivity...
ping -n 4 148.251.195.222

echo.
echo 2. Testing HTTP port...
powershell -Command "Test-NetConnection -ComputerName 148.251.195.222 -Port 80 -InformationLevel Detailed"

echo.
echo 3. Testing HTTPS port...
powershell -Command "Test-NetConnection -ComputerName 148.251.195.222 -Port 443 -InformationLevel Detailed"

echo.
echo 4. Testing SSH port...
powershell -Command "Test-NetConnection -ComputerName 148.251.195.222 -Port 22 -InformationLevel Detailed"

echo.
echo 5. Testing with curl...
curl -I --connect-timeout 10 http://148.251.195.222
curl -I --connect-timeout 10 https://148.251.195.222

echo.
echo Diagnostic complete.
pause