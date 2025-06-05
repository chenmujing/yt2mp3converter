@echo off
echo 正在启动YouTube转换器...
echo.

:: 检查并安装FFmpeg
echo 检查FFmpeg安装状态...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg未找到，正在安装...
    winget install "FFmpeg (Essentials Build)" --accept-package-agreements --accept-source-agreements
    
    :: 手动添加FFmpeg到当前会话的PATH
    set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-essentials_build\bin"
    
    echo FFmpeg安装完成！
) else (
    echo FFmpeg已安装。
)

:: 启动Python服务
echo.
echo 正在启动后端服务...
echo 服务地址: http://localhost:5000
echo 按Ctrl+C停止服务
echo.

python app.py

pause 