@echo off
echo ==========================================
echo  Manual Server Setup Commands
echo ==========================================
echo.
echo The deploy.sh script has file format issues.
echo Let's run the deployment commands manually.
echo.
echo Server: 148.251.195.222 (currently in rescue mode)
echo Password: BrfiDiUwxFEAvu
echo.
echo Copy and paste these commands in the SSH session:
echo.
echo ==========================================
echo # Fix file permissions and format
echo dos2unix deploy.sh
echo chmod +x deploy.sh
echo.
echo # OR run deployment commands manually:
echo apt update
echo apt install -y curl docker.io docker-compose
echo.
echo # Start Docker
echo systemctl start docker
echo systemctl enable docker
echo.
echo # Build and start services
echo docker-compose -f docker-compose.production.yml build
echo docker-compose -f docker-compose.production.yml up -d
echo.
echo # Check status
echo docker-compose -f docker-compose.production.yml ps
echo.
echo ==========================================
echo.
echo Your 9,997 German legal examples are ready in /opt/data/
echo.
pause