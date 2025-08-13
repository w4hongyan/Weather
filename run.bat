@echo off
cd /d "%~dp0"
echo 正在启动天气数据建模与分析系统...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装或未添加到系统PATH
    echo 请安装Python 3.7或更高版本
    pause
    exit /b 1
)

:: 检查虚拟环境
if exist "venv" (
    echo 激活虚拟环境...
    call venv\Scripts\activate
) else (
    echo 创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate
    
    echo 安装依赖包...
    pip install -r requirements.txt
)

:: 启动应用程序
echo.
echo 启动主程序...
cd src
python main.py

pause