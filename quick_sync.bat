@echo off 
echo 🔄 Quick sync to portal-anwalts.ai... 
rsync -avz Client/anwalts-ai-app.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ 
rsync -avz Client/anwalts-ai-dashboard.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ 
rsync -avz Client/enhanced-registration.html root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ 
rsync -avz Client/api-client.js root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ 
rsync -avz Client/*.css root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/ 
echo ✅ Frontend synced! 
