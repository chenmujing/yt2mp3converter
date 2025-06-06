from flask import Flask, request, jsonify, send_file, abort, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import subprocess
import tempfile
import threading
import time
import hashlib
import json
import requests
import ssl
import socket
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
# CORS配置 - 允许GitHub Pages和本地开发
   CORS(app, origins=['*'])  # 允许所有来源（临时解决方案）

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加根路径路由，返回主页面
@app.route('/')
def index():
    """返回主页面"""
    return send_file('index.html')

# 添加静态文件路由
@app.route('/<path:filename>')
def static_files(filename):
    """提供静态文件服务"""
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        abort(404)

# FFmpeg路径检测和设置
def find_ffmpeg_path():
    """查找FFmpeg安装路径"""
    # 常见的FFmpeg安装路径
    possible_paths = [
        # WinGet安装路径
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-essentials_build\bin"),
        # 其他可能的路径
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "ffmpeg.exe")):
            logger.info(f"Found FFmpeg at: {path}")
            return path
    
    # 检查系统PATH中是否有ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg found in system PATH")
        return None  # 系统PATH中已有
    except:
        logger.warning("FFmpeg not found in any location")
        return None

# 设置FFmpeg路径
FFMPEG_PATH = find_ffmpeg_path()

# 配置
TEMP_DIR = os.path.join(os.getcwd(), 'temp_files')
CLEANUP_INTERVAL = 3600  # 1小时后清理文件
MAX_FILE_AGE = 7200  # 2小时后删除文件

# 确保临时目录存在
os.makedirs(TEMP_DIR, exist_ok=True)

# 存储任务状态
conversion_tasks = {}

class ConversionTask:
    def __init__(self, task_id, url, formats):
        self.task_id = task_id
        self.url = url
        self.formats = formats
        self.status = 'pending'
        self.progress = 0
        self.video_info = None
        self.files = {}
        self.error = None
        self.created_at = datetime.now()

def cleanup_old_files():
    """清理过期文件"""
    current_time = datetime.now()
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            if current_time - file_time > timedelta(seconds=MAX_FILE_AGE):
                try:
                    os.remove(filepath)
                    logger.info(f"Cleaned up old file: {filename}")
                except Exception as e:
                    logger.error(f"Error cleaning up file {filename}: {e}")

def progress_hook(d):
    """yt-dlp进度钩子"""
    task_id = d.get('info_dict', {}).get('task_id')
    if task_id and task_id in conversion_tasks:
        task = conversion_tasks[task_id]
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                task.progress = int((d['downloaded_bytes'] / d['total_bytes']) * 50)  # 下载占50%
            elif '_percent_str' in d:
                percent = float(d['_percent_str'].replace('%', ''))
                task.progress = int(percent * 0.5)  # 下载占50%
        elif d['status'] == 'finished':
            task.progress = 50  # 下载完成

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """获取YouTube视频信息"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'no_proxy': True,  # 禁用代理
            'socket_timeout': 60,  # 增加超时时间
            'retries': 10,  # 增加重试次数
            'fragment_retries': 10,  # 片段重试
            'retry_sleep_functions': {
                'http': lambda n: min(2 ** n, 30),  # HTTP重试间隔，最大30秒
                'fragment': lambda n: min(2 ** n, 30)  # 片段重试间隔，最大30秒
            },
            # SSL相关配置
            'nocheckcertificate': True,  # 跳过SSL证书验证
            'prefer_insecure': False,  # 但仍优先使用安全连接
            # 添加用户代理和头部信息
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Connection': 'close'  # 避免保持连接
            },
            # 网络错误处理
            'ignoreerrors': False,  # 不忽略错误，但会重试
            'abort_on_error': False,  # 遇到错误时不立即终止
            'continue_dl': True,  # 断点续传
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_info = {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration'),
                'duration_string': info.get('duration_string'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'upload_date': info.get('upload_date')
            }
            
            return jsonify({'success': True, 'data': video_info})
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def start_conversion():
    """开始转换任务"""
    try:
        data = request.get_json()
        url = data.get('url')
        # 修改默认格式，只转换单个格式以提高速度
        formats = data.get('formats', ['mp3_256'])  # 默认只转换MP3 256kbps
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 生成任务ID
        task_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # 创建转换任务
        task = ConversionTask(task_id, url, formats)
        conversion_tasks[task_id] = task
        
        # 在后台开始转换
        threading.Thread(target=perform_conversion, args=(task_id,)).start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        logger.error(f"Error starting conversion: {e}")
        return jsonify({'error': str(e)}), 500

def perform_conversion(task_id):
    """执行转换任务"""
    task = conversion_tasks[task_id]
    
    try:
        task.status = 'processing'
        
        # 获取视频信息 - 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'no_proxy': True,  # 禁用代理
                    'socket_timeout': 60,  # 增加超时时间
                    'retries': 10,  # 增加重试次数
                    'fragment_retries': 10,  # 片段重试
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 30),  # HTTP重试间隔，最大30秒
                        'fragment': lambda n: min(2 ** n, 30)  # 片段重试间隔，最大30秒
                    },
                    # SSL相关配置
                    'nocheckcertificate': True,  # 跳过SSL证书验证
                    'prefer_insecure': False,  # 但仍优先使用安全连接
                    # 添加用户代理和头部信息
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Accept-Encoding': 'gzip,deflate',
                        'Connection': 'close'  # 避免保持连接
                    },
                    # 网络错误处理
                    'ignoreerrors': False,  # 不忽略错误，但会重试
                    'abort_on_error': False,  # 遇到错误时不立即终止
                    'continue_dl': True,  # 断点续传
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(task.url, download=False)
                    task.video_info = {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'duration_string': info.get('duration_string'),
                        'thumbnail': info.get('thumbnail'),
                        'uploader': info.get('uploader')
                    }
                break  # 成功则跳出重试循环
                
            except Exception as e:
                logger.warning(f"视频信息获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e  # 最后一次尝试失败则抛出异常
                time.sleep(2 ** attempt)  # 指数退避
        
        task.progress = 10
        
        # 处理每种格式 - 改为串行处理，避免网络拥堵
        successful_formats = []
        failed_formats = []
        
        total_formats = len(task.formats)
        for i, format_type in enumerate(task.formats):
            try:
                # 更新当前格式处理进度
                base_progress = 10 + int((i / total_formats) * 80)  # 10-90%的进度分配给格式转换
                task.progress = base_progress
                
                logger.info(f"开始处理格式 {format_type} ({i+1}/{total_formats})")
                convert_format(task, format_type)
                successful_formats.append(format_type)
                logger.info(f"成功转换格式: {format_type}")
                
                # 完成当前格式后更新进度
                task.progress = 10 + int(((i + 1) / total_formats) * 80)
                
            except Exception as e:
                logger.error(f"格式转换失败 {format_type}: {e}")
                failed_formats.append((format_type, str(e)))
                # 继续处理其他格式，不让单个格式失败影响整体
                continue
        
        # 如果至少有一个格式成功，标记为完成
        if successful_formats:
            task.status = 'completed'
            task.progress = 100
            if failed_formats:
                task.error = f"部分格式失败: {failed_formats}"
        else:
            # 所有格式都失败
            task.status = 'error'
            task.error = f"所有格式转换失败: {failed_formats}"
        
    except Exception as e:
        logger.error(f"Conversion error for task {task_id}: {e}")
        task.status = 'error'
        task.error = str(e)

def convert_format(task, format_type):
    """转换特定格式"""
    max_retries = 2  # 减少重试次数，加快处理速度
    
    for attempt in range(max_retries):
        try:
            video_id = task.video_info['id']
            title = task.video_info['title']
            
            # 清理文件名
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            
            if format_type.startswith('mp3'):
                # 音频转换 - 转换为MP3格式
                quality = format_type.split('_')[1]  # mp3_128 -> 128
                output_filename = f"{safe_title}_{quality}kbps.mp3"
                output_path = os.path.join(TEMP_DIR, f"{task.task_id}_{output_filename}")
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(TEMP_DIR, f"{task.task_id}_temp_audio.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'no_proxy': True,  # 禁用代理
                    'socket_timeout': 30,  # 减少超时时间，加快失败检测
                    'retries': 5,  # 减少重试次数
                    'fragment_retries': 5,  # 片段重试
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 10),  # 减少重试间隔
                        'fragment': lambda n: min(2 ** n, 10)
                    },
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'audioquality': quality,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
                    }],
                    # SSL相关配置
                    'nocheckcertificate': True,  # 跳过SSL证书验证
                    'prefer_insecure': False,  # 但仍优先使用安全连接
                    # 添加用户代理和头部信息
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Accept-Encoding': 'gzip,deflate',
                        'Connection': 'close'  # 避免保持连接
                    },
                    # 网络错误处理
                    'ignoreerrors': False,  # 不忽略错误，但会重试
                    'abort_on_error': False,  # 遇到错误时不立即终止
                    'continue_dl': True,  # 断点续传
                    # 限制下载速度和并发
                    'concurrent_fragment_downloads': 1,  # 单线程下载
                    'ratelimit': 5000000,  # 限制下载速度为5MB/s，避免网络拥堵
                }
                
                # 如果找到了FFmpeg路径，添加到配置中
                if FFMPEG_PATH:
                    ydl_opts['ffmpeg_location'] = FFMPEG_PATH
                
                logger.info(f"开始下载音频格式: {format_type}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([task.url])
                
                # 查找下载的文件并重命名
                temp_files = [f for f in os.listdir(TEMP_DIR) if f.startswith(f"{task.task_id}_temp_audio") and f.endswith('.mp3')]
                if temp_files:
                    os.rename(os.path.join(TEMP_DIR, temp_files[0]), output_path)
                    task.files[format_type] = {
                        'filename': output_filename,
                        'path': output_path,
                        'size': os.path.getsize(output_path)
                    }
                    logger.info(f"音频文件保存完成: {output_filename}")
                    break  # 成功则跳出重试循环
                else:
                    raise Exception("未找到下载的音频文件")
            
            elif format_type.startswith('mp4'):
                # 视频转换
                quality = format_type.split('_')[1]  # mp4_720 -> 720
                output_filename = f"{safe_title}_{quality}p.mp4"
                output_path = os.path.join(TEMP_DIR, f"{task.task_id}_{output_filename}")
                
                # 根据质量选择格式
                if quality == '360':
                    format_selector = 'best[height<=360]/worst'
                elif quality == '720':
                    format_selector = 'best[height<=720]/best[height<=480]/worst'
                elif quality == '1080':
                    format_selector = 'best[height<=1080]/best[height<=720]/worst'
                else:
                    format_selector = 'worst'  # 默认选择最小质量以加快下载
                
                ydl_opts = {
                    'format': format_selector,
                    'outtmpl': output_path,
                    'quiet': True,
                    'no_warnings': True,
                    'no_proxy': True,  # 禁用代理
                    'socket_timeout': 30,  # 减少超时时间
                    'retries': 5,  # 减少重试次数
                    'fragment_retries': 5,  # 片段重试
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 10),  # 减少重试间隔
                        'fragment': lambda n: min(2 ** n, 10)
                    },
                    # SSL相关配置
                    'nocheckcertificate': True,  # 跳过SSL证书验证
                    'prefer_insecure': False,  # 但仍优先使用安全连接
                    # 添加用户代理和头部信息
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Accept-Encoding': 'gzip,deflate',
                        'Connection': 'close'  # 避免保持连接
                    },
                    # 网络错误处理
                    'ignoreerrors': False,  # 不忽略错误，但会重试
                    'abort_on_error': False,  # 遇到错误时不立即终止
                    'continue_dl': True,  # 断点续传
                    # 限制下载速度和并发
                    'concurrent_fragment_downloads': 1,  # 单线程下载
                    'ratelimit': 5000000,  # 限制下载速度为5MB/s
                }
                
                logger.info(f"开始下载视频格式: {format_type}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([task.url])
                
                if os.path.exists(output_path):
                    task.files[format_type] = {
                        'filename': output_filename,
                        'path': output_path,
                        'size': os.path.getsize(output_path)
                    }
                    logger.info(f"视频文件保存完成: {output_filename}")
                    break  # 成功则跳出重试循环
                else:
                    raise Exception("未找到下载的视频文件")
            
        except Exception as e:
            error_msg = str(e).lower()
            if ("ssl" in error_msg or "unexpected_eof" in error_msg or "timeout" in error_msg) and attempt < max_retries - 1:
                logger.warning(f"网络错误，重试格式转换 {format_type} (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(3 * (attempt + 1))  # 网络错误时等待
                continue
            else:
                logger.error(f"Error converting format {format_type}: {e}")
                raise

@app.route('/api/status/<task_id>', methods=['GET'])
def get_conversion_status(task_id):
    """获取转换状态"""
    if task_id not in conversion_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = conversion_tasks[task_id]
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'video_info': task.video_info,
        'error': task.error
    }
    
    if task.status == 'completed':
        # 添加下载链接
        response['files'] = {}
        for format_type, file_info in task.files.items():
            response['files'][format_type] = {
                'filename': file_info['filename'],
                'size': file_info['size'],
                'download_url': f"/api/download/{task_id}/{format_type}"
            }
    
    return jsonify(response)

@app.route('/api/download/<task_id>/<format_type>', methods=['GET'])
def download_file(task_id, format_type):
    """下载转换后的文件"""
    if task_id not in conversion_tasks:
        abort(404)
    
    task = conversion_tasks[task_id]
    
    if format_type not in task.files:
        abort(404)
    
    file_info = task.files[format_type]
    file_path = file_info['path']
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_info['filename'],
        mimetype='application/octet-stream'
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len([t for t in conversion_tasks.values() if t.status in ['pending', 'processing']])
    })

def test_network_connectivity():
    """测试网络连接和SSL配置"""
    test_urls = [
        'https://www.youtube.com',
        'https://www.google.com',
        'https://httpbin.org/get'
    ]
    
    results = {}
    
    for url in test_urls:
        try:
            # 测试基本HTTP连接
            response = requests.get(url, timeout=10, verify=False)
            results[url] = {
                'status': 'success',
                'status_code': response.status_code,
                'ssl_version': 'N/A'
            }
        except requests.exceptions.SSLError as e:
            results[url] = {
                'status': 'ssl_error',
                'error': str(e)
            }
        except Exception as e:
            results[url] = {
                'status': 'error',
                'error': str(e)
            }
    
    return results

@app.route('/api/network-test', methods=['GET'])
def network_test():
    """网络连接测试接口"""
    try:
        results = test_network_connectivity()
        return jsonify({
            'success': True,
            'network_tests': results,
            'ssl_context': {
                'ssl_version': ssl.OPENSSL_VERSION,
                'default_ciphers': ssl._DEFAULT_CIPHERS if hasattr(ssl, '_DEFAULT_CIPHERS') else 'N/A'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 定期清理文件
def start_cleanup_thread():
    def cleanup_loop():
        while True:
            time.sleep(CLEANUP_INTERVAL)
            cleanup_old_files()
            
            # 清理过期任务
            current_time = datetime.now()
            expired_tasks = [
                task_id for task_id, task in conversion_tasks.items()
                if current_time - task.created_at > timedelta(seconds=MAX_FILE_AGE)
            ]
            for task_id in expired_tasks:
                del conversion_tasks[task_id]
    
    threading.Thread(target=cleanup_loop, daemon=True).start()

if __name__ == '__main__':
    # 启动清理线程
    start_cleanup_thread()
    
    # 从环境变量获取端口，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 判断是否为生产环境
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # 启动Flask应用
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 
