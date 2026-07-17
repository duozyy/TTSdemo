@echo off
chcp 65001 >nul 2>&1
title TTS Demo - Offline TTS Engine Comparison
color 0A

echo.
echo  ===================================================
echo   TTS Demo - Offline TTS Engine Comparison
echo  ===================================================
echo.

:: Check models directory
if not exist "models\" (
    echo  [WARNING] models/ directory not found!
    echo.
    echo  Please download models first:
    echo    python download_models.py
    echo.
    pause
    exit /b 1
)

:: Create virtual environment if not exists
if not exist "venv\" (
    echo  [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create venv. Please install Python 3.10+
        pause
        exit /b 1
    )
    echo  [DONE] Virtual environment created
) else (
    echo  [1/3] Virtual environment already exists
)

:: Activate virtual environment
call venv\Scripts\activate.bat >nul 2>&1

:: Install dependencies
echo  [2/3] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies. Check requirements.txt
    pause
    exit /b 1
)
echo  [DONE] Dependencies installed

echo.
echo  ===================================================
echo   Starting server...
echo.
echo   Open in browser:  http://localhost:5000
echo   LAN access:       http://%COMPUTERNAME%:5000
echo  ===================================================
echo   Press Ctrl+C to stop
echo.

:: Start Flask
python app.py