@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  TTS Demo - Self-Healing Startup Script
::  Double-click to run. Auto-detects and fixes common issues.
:: ============================================================

:: Force UTF-8 to avoid encoding issues on Chinese Windows
set "PYTHONUTF8=1"

:: Lock working directory to script location
cd /d "%~dp0"

title TTS Demo - Self-Healing Startup

echo.
echo ============================================
echo    TTS Demo - Self-Healing Startup
echo ============================================
echo.

:: ============================================================
:: STEP 1: Detect Python 3.10+
:: ============================================================
echo [Step 1/4] Checking Python...

set "PYTHON_EXE="
set "PY_VERSION="

:: Try python, python3, py
for %%c in (python python3 py) do (
    for /f "tokens=2 delims= " %%v in ('%%c --version 2^>nul') do (
        for /f "tokens=1,2 delims=." %%a in ("%%v") do (
            set "MAJ=%%a"
            set "MIN=%%b"
            if !MAJ! GEQ 3 (
                if !MIN! GEQ 10 (
                    set "PYTHON_EXE=%%c"
                    set "PY_VERSION=%%v"
                )
            )
        )
    )
)

if not defined PYTHON_EXE (
    echo [MISSING] Python 3.10+ not found.
    echo.
    echo This demo requires Python 3.10 or newer.
    echo.
    set /p "INSTALL_PYTHON=Download and install Python 3.12 now? (Y/N): "
    if /i not "!INSTALL_PYTHON!"=="Y" (
        echo.
        echo [CANCELLED] Python is required. Download from:
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    call :install_python
    if !ERRORLEVEL! NEQ 0 exit /b 1
) else (
    echo [OK] Found Python !PY_VERSION! ^(!PYTHON_EXE!^)
)

:: ============================================================
:: STEP 2: Create / Verify Virtual Environment
:: ============================================================
echo.
echo [Step 2/4] Checking virtual environment...

if not exist venv\Scripts\python.exe (
    echo [MISSING] Virtual environment not found. Creating...
    python -m venv venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment exists.
)

:: ============================================================
:: STEP 3: Verify Dependencies (Self-Healing)
:: ============================================================
echo.
echo [Step 3/4] Checking dependencies...

:: Activate venv
call venv\Scripts\activate.bat >nul 2>&1

:: Check each package individually and build install list
set "MISSING_PKGS="

python -c "import flask" 2>nul
if !ERRORLEVEL! NEQ 0 set "MISSING_PKGS=!MISSING_PKGS! flask"

python -c "import sherpa_onnx" 2>nul
if !ERRORLEVEL! NEQ 0 set "MISSING_PKGS=!MISSING_PKGS! sherpa-onnx"

python -c "import numpy" 2>nul
if !ERRORLEVEL! NEQ 0 set "MISSING_PKGS=!MISSING_PKGS! numpy"

python -c "import scipy" 2>nul
if !ERRORLEVEL! NEQ 0 set "MISSING_PKGS=!MISSING_PKGS! scipy"

if not "!MISSING_PKGS!"=="" (
    echo [REPAIR] Missing packages:!MISSING_PKGS!
    echo.
    echo This may take 3-10 minutes depending on your network...
    echo.
    
    :: Ensure pip is up to date
    python -m pip install --upgrade pip >nul 2>&1
    
    :: Try batch install from requirements
    pip install -r requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [WARN] Batch install failed. Installing individually...
        echo.
        for %%p in (flask numpy scipy sherpa-onnx edge-tts pyttsx3) do (
            pip install %%p 2>nul
        )
    )
    
    :: Final check - test the critical import
    python -c "import flask; import sherpa_onnx; import numpy; import scipy; print('OK')" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [ERROR] Dependency installation failed.
        echo Please check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed.
) else (
    echo [OK] All dependencies verified.
)

:: ============================================================
:: STEP 4: Verify Model Files
:: ============================================================
echo.
echo [Step 4/4] Checking model files...

set "MODEL_ISSUES=0"
if not exist "models\vits_zh" (
    echo [WARN] Missing VITS model: models\vits_zh
    set /a MODEL_ISSUES+=1
)
if not exist "models\kokoro" (
    echo [WARN] Missing Kokoro model: models\kokoro
    set /a MODEL_ISSUES+=1
)
if not exist "models\ChatTTS" (
    echo [WARN] Missing ChatTTS model: models\ChatTTS
    set /a MODEL_ISSUES+=1
)
if %MODEL_ISSUES%==0 (
    echo [OK] All model files present.
)

:: ============================================================
:: START SERVER
:: ============================================================
echo.
echo ============================================
echo   Starting Web Server...
echo.
echo   Open in browser:  http://localhost:5000
echo   LAN access:       http://%COMPUTERNAME%:5000
echo ============================================
echo   Press Ctrl+C to stop
echo.

:: Auto-open browser
start "" http://localhost:5000

:: Start Flask
python app.py

pause
goto :eof

:: ============================================================
:: SUBROUTINES
:: ============================================================

:install_python
echo.
echo [1/3] Downloading Python 3.12.4...
echo     (About 25MB, may take 1-3 minutes...)
echo.

set "PYTHON_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
set "PYTHON_INSTALLER=%CD%\python-3.12.4-amd64.exe"

powershell -Command "(New-Object Net.WebClient).DownloadFile('!PYTHON_URL!', '!PYTHON_INSTALLER!')"
if not exist "!PYTHON_INSTALLER!" (
    echo [ERROR] Download failed! Please install manually:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Download complete.

echo.
echo [2/3] Installing Python 3.12...
echo     (Silent install, may take 1-2 minutes...)
echo.

"!PYTHON_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 TargetDir="%LOCALAPPDATA%\Programs\Python\Python312"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Python installation failed!
    pause
    exit /b 1
)
echo [OK] Python installed.

echo.
echo [3/3] Refreshing environment...
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%PATH%"

:: Re-check Python
for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do (
    set "PY_VERSION=%%v"
    set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
    echo [ERROR] Python still not detected. Please restart the computer.
    pause
    exit /b 1
)
echo [OK] Python !PY_VERSION! is now available.
exit /b 0
