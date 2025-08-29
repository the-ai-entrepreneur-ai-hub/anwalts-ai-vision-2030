#!/bin/bash 
# Portal-Anwalts.AI Deployment Script 
echo "Deploying AnwaltsAI to portal-anwalts.ai..." 
sudo apt update && sudo apt upgrade -y 
sudo apt install -y python3-pip nginx postgresql certbot python3-certbot-nginx 
sudo mkdir -p /var/www/portal-anwalts.ai 
cp -r backend /var/www/portal-anwalts.ai/ 
cp -r frontend /var/www/portal-anwalts.ai/ 
cd /var/www/portal-anwalts.ai/backend 
pip3 install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-jose passlib 
sudo cp ../config/nginx.conf /etc/nginx/sites-available/portal-anwalts.ai 
sudo ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/ 
sudo systemctl restart nginx 
echo "✅ Main frontend will be served from anwalts-ai-app.html" 
