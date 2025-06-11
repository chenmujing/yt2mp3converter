#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YT2MP3 Converter - 最终修复版
彻底解决Flask环境中的DPAPI错误
"""

import os
import sys

# 🔥 CRITICAL: 在导入任何模块之前设置环境变量
os.environ['YT_DLP_NO_BROWSER_COOKIES'] = '1'
os.environ['YT_DLP_NO_CACHE'] = '1'
os.environ['YT_DLP_NO_CONFIG'] = '1'

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import hashlib
import threading
import time
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# 任务存储
tasks = {}
TEMP_DIR = os.path.join(os.getcwd(), 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)

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

def get_ultra_safe_ydl_config(output_dir=None):
    """超级安全的yt-dlp配置"""
    if output_dir is None:
        output_dir = TEMP_DIR
    
    return {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s_%(title).50s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        'quiet': False,
        'no_warnings': False,
        'socket_timeout': 60,
        'retries': 3,
        'nocheckcertificate': True,
        
        # 🔥 多层禁用cookies
        'cookiefile': None,
        'cookiesfrombrowser': None,
        'no_check_certificate': True,
        'cachedir': False,
        'no_cache_dir': True,
        
        # 禁用浏览器相关功能
        'writeinfojson': False,
        'writethumbnail': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        'sleep_interval': 1,
        'max_sleep_interval': 3,
    }

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>YT2MP3 Converter - 最终修复版</title></head>
    <body>
        <h1>🔥 YT2MP3 Converter - 最终修复版</h1>
        <p>✅ 彻底解决DPAPI错误</p>
        <p>✅ 支持真实文件下载</p>
        <p>Test: <a href="/api/health">/api/health</a></p>
    </body>
    </html>
    '''

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'YT2MP3 最终修复版运行正常',
        'active_tasks': len(tasks),
        'environment_fixed': True
    })

def perform_conversion(task_id):
    """执行转换任务"""
    task = tasks.get(task_id)
    if not task:
        return
    
    try:
        task.status = 'processing'
        task.progress = 10
        
        # 再次确认环境变量
        os.environ['YT_DLP_NO_BROWSER_COOKIES'] = '1'
        
        import yt_dlp
        
        # 获取视频信息
        ydl_opts = {
            'quiet': True,
            'cookiefile': None,
            'cookiesfrombrowser': None,
            'no_check_certificate': True,
            'cachedir': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(task.url, download=False)
            task.video_info = {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration', 0)
            }
            
        task.progress = 50
        
        # 下载文件
        config = get_ultra_safe_ydl_config()
        with yt_dlp.YoutubeDL(config) as ydl:
            ydl.download([task.url])
        
        # 查找下载的文件
        video_id = task.video_info['id']
        for file in os.listdir(TEMP_DIR):
            if video_id in file and file.endswith('.mp3'):
                filepath = os.path.join(TEMP_DIR, file)
                task.files['mp3_256'] = {
                    'filename': f"{task.video_info['title'][:50]}.mp3",
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'download_url': f'/api/download/{task_id}/mp3_256'
                }
                break
        
        task.status = 'completed'
        task.progress = 100
        
    except Exception as e:
        print(f"转换失败: {e}")
        task.status = 'failed'
        task.error = str(e)

@app.route('/api/convert', methods=['POST'])
def start_conversion():
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        task_id = hashlib.md5((url + str(time.time())).encode()).hexdigest()
        task = Task(task_id, url)
        tasks[task_id] = task
        
        threading.Thread(target=perform_conversion, args=(task_id,), daemon=True).start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<task_id>')
def get_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'status': task.status,
        'progress': task.progress,
        'video_info': task.video_info,
        'files': task.files if task.status == 'completed' else None,
        'error': task.error
    })

@app.route('/api/download/<task_id>/<format_type>')
def download_file(task_id, format_type):
    task = tasks.get(task_id)
    if not task or format_type not in task.files:
        abort(404)
    
    file_info = task.files[format_type]
    return send_file(
        file_info['path'],
        as_attachment=True,
        download_name=file_info['filename']
    )

if __name__ == '__main__':
    print("🔥 启动YT2MP3转换器 - 最终修复版")
    print("✅ 环境变量已设置，彻底禁用cookies")
    app.run(host='0.0.0.0', port=5000, debug=False) 