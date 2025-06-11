#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化Flask应用 - 测试yt-dlp在Flask环境中的DPAPI问题
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import threading

app = Flask(__name__)
CORS(app)

# 全局任务存储
current_task = None

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': '最小化测试应用'})

@app.route('/api/test-download', methods=['POST'])
def test_download():
    """测试下载功能"""
    global current_task
    
    try:
        data = request.get_json()
        url = data.get('url', 'https://www.youtube.com/watch?v=xLxTVQxOKOg')
        
        # 启动下载线程
        current_task = {'status': 'processing', 'error': None, 'result': None}
        threading.Thread(target=download_worker, args=(url,), daemon=True).start()
        
        return jsonify({'success': True, 'message': '下载任务已启动'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前任务状态"""
    global current_task
    
    if current_task is None:
        return jsonify({'status': 'no_task'})
    
    return jsonify(current_task)

def download_worker(url):
    """下载工作线程"""
    global current_task
    
    try:
        import yt_dlp
        
        # 使用与test_direct_ydl.py完全相同的配置
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s_%(title).50s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }],
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'ignoreerrors': False,
            'socket_timeout': 60,
            'retries': 3,
            'nocheckcertificate': True,
            'cookiefile': None,
            'no_check_certificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'sleep_interval': 1,
            'max_sleep_interval': 3,
        }
        
        print(f"开始下载: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先获取信息
            info = ydl.extract_info(url, download=False)
            current_task['title'] = info.get('title', 'Unknown')
            print(f"视频标题: {current_task['title']}")
            
            # 开始下载
            ydl.download([url])
            
        current_task['status'] = 'completed'
        current_task['result'] = '下载成功'
        print("✅ 下载完成")
        
    except Exception as e:
        current_task['status'] = 'error'
        current_task['error'] = str(e)
        print(f"❌ 下载失败: {e}")

if __name__ == '__main__':
    print("🚀 启动最小化Flask应用")
    print("📡 测试地址: http://localhost:5001/api/health")
    app.run(host='0.0.0.0', port=5001, debug=False) 