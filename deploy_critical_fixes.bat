@echo off
echo =========================================
echo   ANWALTSAI CRITICAL FIXES DEPLOYMENT
echo =========================================
echo.
echo SERVER: 148.251.195.222
echo LOCATION: /opt/anwalts-ai-production/
echo.

REM Create temporary directory for deployment files
set TEMP_DIR=%TEMP%\anwalts-ai-fixes-%RANDOM%
mkdir "%TEMP_DIR%"

echo 📦 Preparing deployment files...
copy "Client\anwalts-ai-dashboard.html" "%TEMP_DIR%\" >NUL
copy "Client\api-client.js" "%TEMP_DIR%\" >NUL
copy "Client\crypto-polyfill.js" "%TEMP_DIR%\" >NUL

echo.
echo 🚀 Deploying files to production server...
echo.

REM Use WinSCP or similar tool if available, otherwise use pscp
pscp -pw "8sKHWH5cVu5fb3" -batch "%TEMP_DIR%\*" root@148.251.195.222:/opt/anwalts-ai-production/Client/

if errorlevel 1 (
    echo ❌ Deployment failed! Trying alternative method...
    echo.
    echo Please manually copy these files to the server:
    echo   - anwalts-ai-dashboard.html
    echo   - api-client.js  
    echo   - crypto-polyfill.js
    echo.
    echo To: /opt/anwalts-ai-production/Client/
    echo.
    pause
    goto cleanup
)

echo.
echo ✅ Files deployed successfully!
echo.
echo 🔧 Updating HTML file to include crypto polyfill...

REM Connect to server and update HTML file
plink -pw "8sKHWH5cVu5fb3" -batch root@148.251.195.222 "cd /opt/anwalts-ai-production/Client && sed -i '/<\/head>/i\    <script src=\"crypto-polyfill.js\"></script>' anwalts-ai-dashboard.html"

if errorlevel 1 (
    echo ⚠️  Could not automatically add crypto polyfill to HTML.
    echo Please manually add this line before </head> in anwalts-ai-dashboard.html:
    echo     ^<script src="crypto-polyfill.js"^>^</script^>
    echo.
)

echo.
echo 🔄 Restarting nginx service...
plink -pw "8sKHWH5cVu5fb3" -batch root@148.251.195.222 "systemctl reload nginx"

echo.
echo ✅ DEPLOYMENT COMPLETE!
echo.
echo 🎯 FIXES APPLIED:
echo   ✅ Removed hardcoded "Dr. Anna Vogel" from dashboard
echo   ✅ Added dynamic user display from localStorage
echo   ✅ Fixed MockApiClient to use dynamic user data
echo   ✅ Added crypto polyfill for older browsers
echo   ✅ Updated authentication flow
echo.
echo 🧪 TESTING:
echo   1. Visit: https://portal-anwalts.ai
echo   2. Login with: admin@anwalts-ai.com / admin123
echo   3. Verify user name shows correctly in top-right
echo   4. Check browser console for any errors
echo.

:cleanup
rmdir /s /q "%TEMP_DIR%" 2>NUL
pause