@echo off
title YatraPlan Server
color 0A
echo.
echo  ==========================================
echo    YatraPlan - Starting Backend Server
echo  ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please install Python from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  [1/3] Python found OK
echo.

REM Install required packages
echo  [2/3] Installing required packages...
python -m pip install flask flask-cors --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install packages.
    echo  Try running: python -m pip install flask flask-cors
    pause
    exit /b 1
)
echo  Packages installed OK
echo.

REM Start the server
echo  [3/3] Starting server...
echo.
echo  ==========================================
echo    Server running at http://localhost:5000
echo    Open index.html in your browser
echo    Press Ctrl+C to stop
echo  ==========================================
echo.

python server.py

pause
