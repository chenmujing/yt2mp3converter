@echo off
echo 正在启动YouTube转换器后端服务...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查pip是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pip，请检查Python安装
    pause
    exit /b 1
)

:: 安装依赖
echo 正在安装Python依赖包...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

:: 检查FFmpeg（yt-dlp需要）
echo 检查FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: 未找到FFmpeg，某些转换功能可能无法使用
    echo 请下载FFmpeg并添加到PATH: https://ffmpeg.org/download.html
    echo.
    echo 按任意键继续启动服务（将使用基础功能）...
    pause >nul
)

:: 启动Flask应用
echo.
echo 正在启动后端服务...
echo 服务地址: http://localhost:5000
echo 按Ctrl+C停止服务
echo.

python app.py 