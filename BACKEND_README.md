# YouTube到MP3/MP4转换器 - 后端服务

## 🚀 功能特性

- **真实视频下载**: 使用yt-dlp解析YouTube视频链接
- **多格式转换**: 支持MP3(128k/256k/320k) 和 MP4(360p/720p/1080p)
- **实时进度追踪**: WebSocket式的进度监控
- **自动文件清理**: 防止服务器存储空间耗尽
- **RESTful API**: 标准化的API接口

## 📋 系统要求

### 必需软件
- Python 3.7+
- pip (Python包管理器)

### 推荐软件
- FFmpeg (用于高质量音视频处理)

## 🛠️ 安装步骤

### 方法一：使用启动脚本 (推荐)
1. 双击运行 `start_backend.bat`
2. 脚本会自动检查环境并安装依赖
3. 服务启动后在 http://localhost:5000 可用

### 方法二：手动安装
```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py
```

## 🔧 FFmpeg安装 (可选但推荐)

### Windows
1. 访问 https://ffmpeg.org/download.html
2. 下载Windows静态构建版本
3. 解压到目录（如 C:\ffmpeg）
4. 添加 C:\ffmpeg\bin 到系统PATH环境变量

### 验证安装
```bash
ffmpeg -version
```

## 📡 API接口文档

### 1. 获取视频信息
```http
POST /api/video-info
Content-Type: application/json

{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "id": "VIDEO_ID",
        "title": "视频标题",
        "duration": 225,
        "duration_string": "3:45",
        "thumbnail": "https://img.youtube.com/vi/VIDEO_ID/mqdefault.jpg",
        "uploader": "频道名称",
        "view_count": 1000000
    }
}
```

### 2. 开始转换
```http
POST /api/convert
Content-Type: application/json

{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "formats": ["mp3_128", "mp3_256", "mp3_320", "mp4_360", "mp4_720", "mp4_1080"]
}
```

**响应示例:**
```json
{
    "success": true,
    "task_id": "abc123def456"
}
```

### 3. 查询转换状态
```http
GET /api/status/{task_id}
```

**响应示例:**
```json
{
    "task_id": "abc123def456",
    "status": "completed",
    "progress": 100,
    "video_info": { ... },
    "files": {
        "mp3_128": {
            "filename": "视频标题_128kbps.mp3",
            "size": 3145728,
            "download_url": "/api/download/abc123def456/mp3_128"
        }
    }
}
```

### 4. 下载文件
```http
GET /api/download/{task_id}/{format_type}
```

### 5. 健康检查
```http
GET /api/health
```

## 🏗️ 技术架构

### 核心组件
- **Flask**: Web框架
- **yt-dlp**: YouTube视频下载工具
- **FFmpeg**: 音视频处理 (可选)
- **Threading**: 异步任务处理

### 工作流程
1. **视频信息提取**: 使用yt-dlp解析YouTube URL
2. **后台转换**: 多线程处理不同格式转换
3. **进度追踪**: 实时更新转换进度
4. **文件管理**: 临时存储转换结果
5. **自动清理**: 定期删除过期文件

### 文件存储
- 临时目录: `./temp_files/`
- 文件生命周期: 2小时后自动删除
- 清理间隔: 每小时检查一次

## ⚙️ 配置选项

在 `app.py` 中可以修改以下配置:

```python
TEMP_DIR = os.path.join(os.getcwd(), 'temp_files')  # 临时文件目录
CLEANUP_INTERVAL = 3600    # 清理检查间隔 (秒)
MAX_FILE_AGE = 7200       # 文件最大保存时间 (秒)
```

## 🐛 故障排除

### 常见问题

**1. yt-dlp下载失败**
- 检查网络连接
- 确认YouTube链接有效
- 某些视频可能有地区限制

**2. FFmpeg相关错误**
- 安装FFmpeg并添加到PATH
- 或者使用基础音频提取功能

**3. 端口占用**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# 或修改app.py中的端口
app.run(debug=True, host='0.0.0.0', port=5001)
```

**4. 权限错误**
- 确保temp_files目录有写入权限
- Windows用户可能需要以管理员身份运行

## 📈 性能优化

### 建议配置
- **内存**: 最少2GB可用内存
- **存储**: 至少5GB临时存储空间
- **网络**: 稳定的互联网连接

### 扩展部署
- 使用Gunicorn + Nginx进行生产部署
- 配置Redis进行任务队列管理
- 使用云存储服务(S3/OSS)存储转换文件

## 🔒 安全注意事项

- 仅在受信任的网络环境中运行
- 定期更新yt-dlp版本
- 监控磁盘使用情况
- 考虑添加访问限制和速率限制

## 📞 支持

如果遇到问题，请检查:
1. Python和pip版本
2. 依赖包是否正确安装
3. FFmpeg是否可用
4. 网络连接是否正常
5. 临时目录权限设置 