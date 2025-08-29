@echo off
echo Uploading AnwaltsAI landing page images to server...

REM Upload image 1
pscp -pw 8sKHWH5cVu5fb3 "images/anwalts-ai-landing-page-1.png" root@148.251.195.222:/var/www/anwalts-ai/images/

REM Upload image 2  
pscp -pw 8sKHWH5cVu5fb3 "images/anwalts-ai-landing-page-2.png" root@148.251.195.222:/var/www/anwalts-ai/images/

echo Images uploaded successfully!
pause