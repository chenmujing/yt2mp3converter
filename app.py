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
            'id': 'demo123',
            'title': '演示视频 - ' + url.split('/')[-1][:20] + ' [演示模式]',
            'duration': 210,
            'duration_string': '3:30',
            'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg',
            'uploader': '演示频道',
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
            'id': 'demo123',
            'title': '演示视频 [演示模式]',
            'duration': 210,
            'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg'
        },
        'files': {
            'mp3_256': {
                'filename': '演示音频.mp3',
                'size': 5242880,
                'download_url': f'/api/download/{task_id}/mp3_256'
            },
            'mp4_720': {
                'filename': '演示视频.mp4',
                'size': 15728640,
                'download_url': f'/api/download/{task_id}/mp4_720'
            }
        }
    }
    
    return jsonify(response)

@app.route('/api/download/<task_id>/<format_type>', methods=['GET'])
def download_file(task_id, format_type):
    """下载文件（重定向到真实文件）"""
    if task_id not in tasks:
        abort(404)
    
    # 根据不同格式重定向到示例文件
    if 'mp3' in format_type:
        # 重定向到一个公开的MP3示例文件
        from flask import redirect
        return redirect('https://www.soundjay.com/misc/sounds/beep-07a.mp3', code=302)
    elif 'mp4' in format_type:
        # 重定向到一个公开的MP4示例文件
        from flask import redirect  
        return redirect('https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4', code=302)
    else:
        # 返回HTML页面说明
        return '''
        <html>
        <head><title>Demo Download</title></head>
        <body>
            <h1>这是演示模式</h1>
            <p>当前API处于演示模式，实际的文件转换功能正在开发中。</p>
            <p>任务ID: {}</p>
            <p>格式: {}</p>
            <p><a href="javascript:window.close()">关闭窗口</a></p>
        </body>
        </html>
        '''.format(task_id, format_type)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 