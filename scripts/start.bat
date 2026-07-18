@echo off
setlocal EnableDelayedExpansion

:: Force UTF-8 mode to avoid encoding issues with Chinese Windows
set "PYTHONUTF8=1"

:: Set working directory to the folder containing this script
cd /d "%~dp0"

title TTS Demo - Offline TTS Engine Comparison

echo ============================================
echo    TTS Offline Engine Comparison Web Demo
echo ============================================
echo.
echo Working directory: %CD%
echo.

:: ==================== Python Check ====================
:: Check Python version (require 3.10+)
set "PYTHON_OK=0"
set "PY_VERSION=not found"

for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do (
    set "PY_VERSION=%%v"
    for /f "tokens=1,2 delims=." %%a in ("%%v") do (
        if %%a GEQ 3 (
            if %%b GEQ 10 (
                set "PYTHON_OK=1"
            )
        )
    )
)

if "!PYTHON_OK!"=="1" (
    echo [OK] Found Python !PY_VERSION!
    goto :python_found
)

:: Python not found or version too low
echo [MISSING] Python 3.10+ not found (current: !PY_VERSION!)
echo.
echo This demo requires Python 3.10 or newer.
echo.
set /p "INSTALL_PYTHON=Download and install Python 3.12 now? (Y/N): "
if /i not "!INSTALL_PYTHON!"=="Y" (
    echo.
    echo [ERROR] Python is required to run TTS Demo.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Download Python 3.12 to local folder (same as run.bat)
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
set "PYTHON_INSTALLER=%CD%\python-3.12.4-amd64.exe"

echo.
echo [1/4] Downloading Python 3.12.4...
echo     Source: !PYTHON_URL!
echo     Target: !PYTHON_INSTALLER!
echo     (About 25MB, may take 1-3 minutes depending on your network...)
echo.

:: Download using PowerShell (save to local folder)
powershell -Command "(New-Object Net.WebClient).DownloadFile('!PYTHON_URL!', '!PYTHON_INSTALLER!')"
if not exist "!PYTHON_INSTALLER!" (
    echo.
    echo [ERROR] Download failed! Please install manually:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Download complete

:: Silent install Python (install to LOCALAPPDATA to avoid admin rights)
echo.
echo [2/4] Installing Python 3.12...
echo     (Silent install, may take 1-2 minutes...)
echo.
"!PYTHON_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 TargetDir="%LOCALAPPDATA%\Programs\Python\Python312"
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Python installation failed! Please install manually.
    echo.
    pause
    exit /b 1
)
echo [OK] Python installed

:: Refresh PATH
echo.
echo [3/4] Refreshing environment...
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%PATH%"

:: Verify Python now works
python --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Python still not detected. Please restart the computer.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do (
    echo [OK] Python %%v is now available
)

:python_found

:: ==================== Virtual Environment ====================
echo.
if not exist venv (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [ERROR] Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [1/3] Virtual environment already exists
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: ==================== Dependencies =====================
echo.
echo [2/3] Installing dependencies (this may take 3-10 minutes)...
echo.

:: Use local folder for pip cache and downloads (avoids permission issues)
set "PIP_CACHE_DIR=%CD%\.pip_cache"
set "PIP_TARGET=%CD%\.pip_packages"

pip install --cache-dir="%PIP_CACHE_DIR%" -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] Some dependencies failed, trying individual install...
    pip install --cache-dir="%PIP_CACHE_DIR%" flask numpy scipy sherpa-onnx edge-tts pyttsx3 ChatTTS
)

:: ==================== Model Check =======================
echo.
echo [3/3] Checking model files...
if not exist "models\vits_zh" (
    echo [WARN] Missing VITS model: models\vits_zh
)
if not exist "models\kokoro" (
    echo [WARN] Missing Kokoro model: models\kokoro
)
if not exist "models\ChatTTS" (
    echo [WARN] Missing ChatTTS model: models\ChatTTS
)
if not exist "models\matcha_zh" (
    echo [WARN] Missing Matcha model: models\matcha_zh
)

:: ==================== Start Server =====================
echo.
echo =============================================
echo   Starting Web Server...
echo.
echo   Open in browser:  http://localhost:5000
echo   LAN access:       http://%COMPUTERNAME%:5000
echo =============================================
echo   Press Ctrl+C to stop
echo.

python app.py

pause
goto :eof
