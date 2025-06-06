from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import os
import json
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 简化的任务存储
tasks = {}

@app.route('/')
def index():
    """返回简单的HTML页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>YT2MP3 API</title></head>
    <body>
        <h1>YT2MP3 Converter API</h1>
        <p>API is running successfully!</p>
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
        'message': 'YT2MP3 API is running'
    })

@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
def get_video_info():
    """获取视频信息（模拟）"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 模拟视频信息
        video_info = {
            'id': 'test123',
            'title': 'Test Video - ' + url.split('/')[-1][:20],
            'duration': 210,
            'duration_string': '3:30',
            'thumbnail': 'https://img.youtube.com/vi/test123/mqdefault.jpg',
            'uploader': 'Test Channel',
            'view_count': 1000000,
            'upload_date': '20240101'
        }
        
        return jsonify({'success': True, 'data': video_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert', methods=['POST', 'OPTIONS'])
def start_conversion():
    """开始转换（模拟）"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 生成任务ID
        task_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # 存储任务
        tasks[task_id] = {
            'status': 'completed',
            'progress': 100,
            'url': url,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<task_id>', methods=['GET'])
def get_conversion_status(task_id):
    """获取转换状态"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    # 模拟完成的任务
    response = {
        'task_id': task_id,
        'status': 'completed',
        'progress': 100,
        'video_info': {
            'id': 'test123',
            'title': 'Test Video',
            'duration': 210,
            'thumbnail': 'https://img.youtube.com/vi/test123/mqdefault.jpg'
        },
        'files': {
            'mp3_256': {
                'filename': 'test_video.mp3',
                'size': 5242880,
                'download_url': f'/api/download/{task_id}/mp3_256'
            }
        }
    }
    
    return jsonify(response)

@app.route('/api/download/<task_id>/<format_type>', methods=['GET'])
def download_file(task_id, format_type):
    """下载文件（模拟）"""
    if task_id not in tasks:
        abort(404)
    
    # 返回模拟提示
    return jsonify({
        'message': 'This is a demo API. File download is simulated.',
        'task_id': task_id,
        'format': format_type
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 