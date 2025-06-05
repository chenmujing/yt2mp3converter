#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单格式转换测试脚本
"""

import requests
import time

def test_single_format():
    """测试单格式转换"""
    base_url = "http://localhost:5000"
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("=== 单格式转换测试 ===")
    print(f"测试视频: {test_video_url}")
    
    # 测试MP3格式
    print("\n测试MP3 256kbps格式...")
    try:
        response = requests.post(f"{base_url}/api/convert", 
                               json={
                                   'url': test_video_url,
                                   'formats': ['mp3_256']
                               })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task_id = data['task_id']
                print(f"✓ 任务创建成功: {task_id}")
                
                # 等待完成
                for i in range(30):
                    status_response = requests.get(f"{base_url}/api/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        print(f"状态: {status}, 进度: {progress}%")
                        
                        if status == 'completed':
                            print("✓ 转换完成!")
                            if 'files' in status_data:
                                files = status_data['files']
                                print(f"可用文件: {list(files.keys())}")
                            break
                        elif status == 'error':
                            print(f"✗ 转换失败: {status_data.get('error')}")
                            break
                    
                    time.sleep(3)
                else:
                    print("⚠️ 任务超时")
            else:
                print(f"✗ 任务创建失败: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == "__main__":
    test_single_format() 