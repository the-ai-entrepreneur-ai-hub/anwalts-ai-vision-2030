@echo off
echo Connecting to server to fix navigation and backend issues...

echo Uploading navigation fix...
pscp -pw "8sKHWH5cVu5fb3" "fix_navigation_auth_issue.js" root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/

echo Restarting backend with API key...
echo pkill -f uvicorn > temp_commands.txt
echo export TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720 >> temp_commands.txt
echo cd /var/www/portal-anwalts.ai/backend >> temp_commands.txt
echo nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload ^> server.log 2^>^&1 ^& >> temp_commands.txt

plink -pw "8sKHWH5cVu5fb3" root@148.251.195.222 -m temp_commands.txt

del temp_commands.txt
echo Done!
pause