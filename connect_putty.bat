@echo off
echo Connecting to server using PuTTY...
echo Password is: 8sKHWH5cVu5fb3
echo.
echo Option 1: GUI Connection (PuTTY)
"C:\Program Files\PuTTY\putty.exe" -ssh root@148.251.195.222
echo.
echo Option 2: Command line (plink) - run this separately:
echo plink -ssh -pw 8sKHWH5cVu5fb3 root@148.251.195.222
pause