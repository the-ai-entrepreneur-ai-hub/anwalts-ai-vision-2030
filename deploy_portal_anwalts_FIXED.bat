@echo off
echo.
echo ========================================================
echo    Portal-Anwalts.AI Deployment Package Creator (FIXED)
echo    Using CORRECT frontend files: anwalts-ai-app.html
echo ========================================================
echo.

echo [1/4] Creating deployment directory...
if exist "portal-anwalts-ai-deployment" rmdir /s /q "portal-anwalts-ai-deployment"
mkdir "portal-anwalts-ai-deployment"
mkdir "portal-anwalts-ai-deployment\backend"
mkdir "portal-anwalts-ai-deployment\frontend" 
mkdir "portal-anwalts-ai-deployment\config"
mkdir "portal-anwalts-ai-deployment\scripts"

echo [2/4] Copying backend files...
copy "backend\main.py" "portal-anwalts-ai-deployment\backend\" >nul
copy "backend\models.py" "portal-anwalts-ai-deployment\backend\" >nul
copy "backend\database.py" "portal-anwalts-ai-deployment\backend\" >nul
copy "backend\auth_service.py" "portal-anwalts-ai-deployment\backend\" >nul
copy "backend\ai_service.py" "portal-anwalts-ai-deployment\backend\" >nul
copy "backend\cache_service.py" "portal-anwalts-ai-deployment\backend\" >nul
echo   ✅ Backend files copied

echo [3/4] Copying CORRECT frontend files...
echo   📱 Main app: anwalts-ai-app.html (PRIMARY FRONTEND)
copy "Client\anwalts-ai-app.html" "portal-anwalts-ai-deployment\frontend\" >nul
copy "Client\anwalts-ai-dashboard.html" "portal-anwalts-ai-deployment\frontend\" >nul
copy "Client\enhanced-registration.html" "portal-anwalts-ai-deployment\frontend\" >nul
copy "Client\api-client.js" "portal-anwalts-ai-deployment\frontend\" >nul
copy "Client\anwalts-design-system.css" "portal-anwalts-ai-deployment\frontend\" >nul
copy "Client\form-validation-system.js" "portal-anwalts-ai-deployment\frontend\" >nul

echo   🎨 Favicons and assets...
copy "Client\favicon.ico" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
copy "Client\favicon-16x16.png" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
copy "Client\favicon-32x32.png" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
copy "Client\favicon-48x48.png" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
copy "Client\favicon-64x64.png" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
copy "Client\config.js" "portal-anwalts-ai-deployment\frontend\" >nul 2>nul
echo   ✅ Frontend files copied

echo [4/4] Creating CORRECTED configuration files...

rem Create production environment file
echo # Portal-Anwalts.AI Production Environment > "portal-anwalts-ai-deployment\config\.env.production"
echo ENVIRONMENT=production >> "portal-anwalts-ai-deployment\config\.env.production"
echo DOMAIN=portal-anwalts.ai >> "portal-anwalts-ai-deployment\config\.env.production"
echo DATABASE_URL=postgresql://anwalts_user:secure_password@localhost/anwalts_ai_prod >> "portal-anwalts-ai-deployment\config\.env.production"
echo TOGETHER_API_KEY=your_together_api_key_here >> "portal-anwalts-ai-deployment\config\.env.production"
echo JWT_SECRET_KEY=your_super_secure_jwt_secret_here >> "portal-anwalts-ai-deployment\config\.env.production"
echo CORS_ORIGINS=https://portal-anwalts.ai,https://www.portal-anwalts.ai >> "portal-anwalts-ai-deployment\config\.env.production"

rem Create CORRECTED nginx configuration with anwalts-ai-app.html as index
echo server { > "portal-anwalts-ai-deployment\config\nginx.conf"
echo     listen 80; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     server_name portal-anwalts.ai www.portal-anwalts.ai; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     return 301 https://$server_name$request_uri; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo } >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo. >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo server { >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     listen 443 ssl http2; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     server_name portal-anwalts.ai www.portal-anwalts.ai; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo. >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     # SSL Configuration >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     ssl_certificate /etc/ssl/certs/portal-anwalts.ai.crt; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     ssl_certificate_key /etc/ssl/private/portal-anwalts.ai.key; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo. >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     # Frontend static files with CORRECT index >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     location / { >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         root /var/www/portal-anwalts.ai/frontend; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         index anwalts-ai-app.html; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         try_files $uri $uri/ /anwalts-ai-app.html; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     } >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo. >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     # API backend >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     location /api/ { >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         proxy_pass http://127.0.0.1:8000/; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         proxy_set_header Host $host; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         proxy_set_header X-Real-IP $remote_addr; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo         add_header Access-Control-Allow-Origin "https://portal-anwalts.ai" always; >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo     } >> "portal-anwalts-ai-deployment\config\nginx.conf"
echo } >> "portal-anwalts-ai-deployment\config\nginx.conf"

rem Create deployment script
echo #!/bin/bash > "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo # Portal-Anwalts.AI Deployment Script >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo echo "Deploying AnwaltsAI to portal-anwalts.ai..." >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo apt update ^&^& sudo apt upgrade -y >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo apt install -y python3-pip nginx postgresql certbot python3-certbot-nginx >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo mkdir -p /var/www/portal-anwalts.ai >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo cp -r backend /var/www/portal-anwalts.ai/ >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo cp -r frontend /var/www/portal-anwalts.ai/ >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo cd /var/www/portal-anwalts.ai/backend >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo pip3 install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-jose passlib >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo cp ../config/nginx.conf /etc/nginx/sites-available/portal-anwalts.ai >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/ >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo sudo systemctl restart nginx >> "portal-anwalts-ai-deployment\scripts\deploy.sh"
echo echo "✅ Main frontend will be served from anwalts-ai-app.html" >> "portal-anwalts-ai-deployment\scripts\deploy.sh"

rem Create requirements.txt
echo fastapi==0.104.1 > "portal-anwalts-ai-deployment\backend\requirements.txt"
echo uvicorn[standard]==0.24.0 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo pydantic==2.5.0 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo sqlalchemy==2.0.23 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo psycopg2-binary==2.9.9 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo python-jose[cryptography]==3.3.0 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo passlib[bcrypt]==1.7.4 >> "portal-anwalts-ai-deployment\backend\requirements.txt"
echo python-multipart==0.0.6 >> "portal-anwalts-ai-deployment\backend\requirements.txt"

rem Create deployment package
powershell -command "Compress-Archive -Path 'portal-anwalts-ai-deployment' -DestinationPath 'portal-anwalts-ai-production-deployment.zip' -Force"

echo.
echo ========================================================
echo  🎉 CORRECTED Portal-Anwalts.AI deployment package!
echo ========================================================
echo.
echo 📦 Files created:
echo   - portal-anwalts-ai-deployment\ (folder)
echo   - portal-anwalts-ai-production-deployment.zip
echo.
echo ✅ CORRECTED Features:
echo   📱 Main frontend: anwalts-ai-app.html (CORRECT!)
echo   📊 Dashboard: anwalts-ai-dashboard.html
echo   📝 Registration: enhanced-registration.html
echo   🎨 Favicons and assets included
echo   🔧 Nginx configured for anwalts-ai-app.html as index
echo.
echo 🚀 To deploy on server 148.251.195.222:
echo   1. Upload: scp portal-anwalts-ai-production-deployment.zip root@148.251.195.222:/tmp/
echo   2. SSH: ssh root@148.251.195.222
echo   3. Deploy: cd /tmp ^&^& unzip -o portal-anwalts-ai-production-deployment.zip
echo   4. Install: cd portal-anwalts-ai-deployment ^&^& sudo bash scripts/deploy.sh
echo.
echo 🔗 Your CORRECT frontend will be available at:
echo   https://portal-anwalts.ai/ (serves anwalts-ai-app.html)
echo   https://portal-anwalts.ai/anwalts-ai-dashboard.html
echo   https://portal-anwalts.ai/enhanced-registration.html
echo.
pause