@echo off 
echo 🔄 Syncing backend... 
rsync -avz backend/ root@148.251.195.222:/var/www/portal-anwalts.ai/backend/ 
ssh root@148.251.195.222 "systemctl restart anwalts-api" 
echo ✅ Backend synced! 
