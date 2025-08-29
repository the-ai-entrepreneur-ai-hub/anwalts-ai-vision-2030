@echo off
echo ==========================================
echo  Hetzner Robot API - Server Recovery
echo ==========================================
echo.
echo Server: AX102 #2743403 (148.251.195.222)
echo.
echo You need to create Hetzner Robot API credentials first.
echo.
echo Steps:
echo 1. Go to: https://robot.hetzner.com/
echo 2. Login with Dr. Markus Weigl's account
echo 3. Go to Settings ^> Web service and app settings
echo 4. Create a web service user
echo 5. Note down username and password
echo.
echo Then run these API commands:
echo.
echo ==========================================
echo  API Commands (replace USER:PASS):
echo ==========================================
echo.
echo # Activate Rescue Mode:
echo curl -u "USER:PASS" -X POST https://robot-ws.your-server.de/boot/2743403/rescue -d "os=linux"
echo.
echo # Reboot Server:
echo curl -u "USER:PASS" -X POST https://robot-ws.your-server.de/reset/2743403 -d "type=hw"
echo.
echo # Check Rescue Status:
echo curl -u "USER:PASS" https://robot-ws.your-server.de/boot/2743403/rescue
echo.
echo ==========================================
echo.
echo Alternative: Contact Dr. Markus Weigl (017621137333)
echo to access Robot panel and activate rescue mode.
echo.
pause