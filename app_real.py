from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp
import os
import hashlib
import threading
import time
import tempfile
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置
TEMP_DIR = os.path.join(os.getcwd(), 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)

# 任务存储
tasks = {}

class Task:
    def __init__(self, task_id, url):
        self.task_id = task_id
        self.url = url
        self.status = 'pending'
        self.progress = 0
        self.video_info = None
        self.files = {}
        self.error = None
        self.created_at = datetime.now()

@app.route('/')
def index():
    """返回主页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>YT2MP3 Converter - Real</title></head>
    <body>
        <h1>YT2MP3 Converter - 真实下载功能</h1>
        <p>真实的YouTube视频下载和转换API</p>
        <p>Test endpoints:</p>
        <ul>
            <li><a href="/api/health">/api/health</a></li>
        </ul>
    </body>
    </html>
    '''

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'YT2MP3 Real API is running',
        'active_tasks': len(tasks)
    })

@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
def get_video_info():
    """获取真实YouTube视频信息"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 真实获取YouTube视频信息
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'no_proxy': True,
            'socket_timeout': 30,
            'retries': 3,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
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
        return jsonify({'error': f'无法获取视频信息: {str(e)}'}), 500

@app.route('/api/convert', methods=['POST', 'OPTIONS'])
def start_conversion():
    """开始真实转换"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 生成任务ID
        task_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # 创建任务
        task = Task(task_id, url)
        tasks[task_id] = task
        
        # 在后台开始转换
        threading.Thread(target=perform_conversion, args=(task_id,), daemon=True).start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def perform_conversion(task_id):
    """执行真实转换"""
    task = tasks[task_id]
    
    try:
        task.status = 'processing'
        task.progress = 10
        
        # 获取视频信息
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'no_proxy': True,
            'socket_timeout': 30,
            'retries': 3,
            'nocheckcertificate': True,
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
        
        task.progress = 30
        
        # 下载MP3
        download_mp3(task)
        
        task.status = 'completed'
        task.progress = 100
        
    except Exception as e:
        task.status = 'error'
        task.error = str(e)

def download_mp3(task):
    """下载MP3格式"""
    try:
        video_id = task.video_info['id']
        safe_title = "".join(c for c in task.video_info['title'][:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{video_id}_{safe_title}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filepath.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '256',
            'socket_timeout': 60,
            'retries': 3,
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([task.url])
        
        # 查找下载的文件
        for file in os.listdir(TEMP_DIR):
            if file.startswith(video_id) and file.endswith('.mp3'):
                actual_filepath = os.path.join(TEMP_DIR, file)
                task.files['mp3_256'] = {
                    'filename': f"{safe_title}.mp3",
                    'path': actual_filepath,
                    'size': os.path.getsize(actual_filepath)
                }
                break
        
        task.progress = 80
        
    except Exception as e:
        raise Exception(f"MP3下载失败: {str(e)}")

@app.route('/api/status/<task_id>', methods=['GET'])
def get_conversion_status(task_id):
    """获取转换状态"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'video_info': task.video_info,
        'error': task.error
    }
    
    if task.status == 'completed' and task.files:
        response['files'] = {}
        for format_type, file_info in task.files.items():
            response['files'][format_type] = {
                'filename': file_info['filename'],
                'size': file_info['size'],
                'download_url': f'/api/download/{task_id}/{format_type}'
            }
    
    return jsonify(response)

@app.route('/api/download/<task_id>/<format_type>', methods=['GET'])
def download_file(task_id, format_type):
    """下载真实转换的文件"""
    if task_id not in tasks:
        abort(404)
    
    task = tasks[task_id]
    
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
        mimetype='audio/mpeg'
    )

# 清理旧文件
def cleanup_old_files():
    """清理2小时前的文件"""
    try:
        current_time = time.time()
        for filename in os.listdir(TEMP_DIR):
            filepath = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getctime(filepath)
                if file_age > 7200:  # 2小时
                    os.remove(filepath)
    except Exception as e:
        print(f"Cleanup error: {e}")

# 启动清理线程
def start_cleanup():
    def cleanup_loop():
        while True:
            time.sleep(3600)  # 每小时清理一次
            cleanup_old_files()
    
    threading.Thread(target=cleanup_loop, daemon=True).start()

start_cleanup()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 