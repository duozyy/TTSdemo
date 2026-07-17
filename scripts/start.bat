@echo off
chcp 65001 >nul
title TTS Demo - 离线语音合成引擎对比
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║       TTS Demo - 离线语音合成引擎对比            ║
echo  ║       Offline TTS Engine Comparison              ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 检查模型目录
if not exist "models\" (
    echo  [警告] models/ 目录不存在！请先运行模型下载脚本。
    echo.
    echo  运行: python download_models.py
    echo.
    pause
    exit /b 1
)

:: 创建虚拟环境（如果不存在）
if not exist "venv\" (
    echo  [1/3] 正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo  [错误] 创建虚拟环境失败！请确保已安装 Python 3.10+
        pause
        exit /b 1
    )
    echo  [完成] 虚拟环境已创建
) else (
    echo  [1/3] 虚拟环境已存在
)

:: 激活虚拟环境
call venv\Scripts\activate.bat >nul 2>&1

:: 安装依赖
echo  [2/3] 正在安装依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [错误] 依赖安装失败，请检查 requirements.txt
    pause
    exit /b 1
)
echo  [完成] 依赖已安装

:: 预加载 ChatTTS（后台）
echo  [3/3] 正在预热 ChatTTS（首次启动需等待 5-10 秒）...
python -c "import requests; requests.get('http://localhost:5000/api/warmup')" >nul 2>&1

echo.
echo  ══════════════════════════════════════════════════
echo  ✓ 服务器已启动！请在浏览器中打开：
echo.
echo    http://localhost:5000
echo.
echo  ✓ 局域网访问地址：
echo.
echo    http://%COMPUTERNAME%:5000
echo.
echo  ══════════════════════════════════════════════════
echo  按 Ctrl+C 停止服务器
echo.

:: 启动 Flask
python app.py