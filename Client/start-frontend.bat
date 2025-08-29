@echo off
echo Starting AnwaltsAI Frontend...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found, trying python3...
    python3 -m http.server 3000
) else (
    echo Starting HTTP server on http://localhost:3000
    python -m http.server 3000
)

pause