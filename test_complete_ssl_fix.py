#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整系统SSL修复测试脚本
"""

import requests
import time
import json

def test_complete_system():
    """测试完整的YouTube转换系统"""
    base_url = "http://localhost:5000"
    
    print("=== 完整系统测试 ===")
    
    # 1. 健康检查
    print("\n1. 系统健康检查:")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✓ 系统健康状态良好")
        else:
            print(f"✗ 系统健康检查失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 无法连接到服务器: {e}")
        return
    
    # 2. 网络测试
    print("\n2. 网络连接测试:")
    try:
        response = requests.get(f"{base_url}/api/network-test")
        if response.status_code == 200:
            data = response.json()
            print("✓ 网络连接测试完成")
            for url, result in data['network_tests'].items():
                status = "✓" if result['status'] == 'success' else "✗"
                print(f"  {status} {url}: {result['status']}")
        else:
            print(f"✗ 网络测试失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 网络测试错误: {e}")
    
    # 3. 视频信息测试
    print("\n3. 视频信息获取测试:")
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 测试视频
    
    try:
        response = requests.post(f"{base_url}/api/video-info", 
                               json={'url': test_video_url})
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                video_info = data['data']
                print(f"✓ 视频标题: {video_info.get('title', 'N/A')}")
                print(f"✓ 时长: {video_info.get('duration_string', 'N/A')}")
                print(f"✓ 上传者: {video_info.get('uploader', 'N/A')}")
            else:
                print(f"✗ 视频信息获取失败: {data}")
                return
        else:
            print(f"✗ 请求失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 视频信息测试错误: {e}")
        return
    
    # 4. 转换任务测试（只测试一种格式以节省时间）
    print("\n4. 转换任务测试:")
    try:
        response = requests.post(f"{base_url}/api/convert", 
                               json={
                                   'url': test_video_url,
                                   'formats': ['mp3_128']  # 只测试一种格式
                               })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task_id = data['task_id']
                print(f"✓ 转换任务创建成功: {task_id}")
                
                # 监控任务状态
                print("监控转换进度...")
                max_wait_time = 300  # 最多等待5分钟
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    status_response = requests.get(f"{base_url}/api/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        print(f"  状态: {status}, 进度: {progress}%")
                        
                        if status == 'completed':
                            print("✓ 转换任务完成!")
                            if 'files' in status_data:
                                for format_type, file_info in status_data['files'].items():
                                    print(f"  文件: {file_info['filename']} ({file_info['size']} bytes)")
                            break
                        elif status == 'error':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"✗ 转换失败: {error_msg}")
                            break
                        
                        time.sleep(5)  # 等待5秒再检查
                    else:
                        print(f"✗ 状态检查失败: {status_response.status_code}")
                        break
                else:
                    print("✗ 转换超时")
            else:
                print(f"✗ 转换任务创建失败: {data}")
        else:
            print(f"✗ 转换请求失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 转换任务测试错误: {e}")
    
    print("\n=== 测试完成 ===")

def main():
    print("YouTube转MP3 完整系统测试")
    print("=" * 50)
    
    test_complete_system()
    
    print("\n如果测试失败，请检查:")
    print("1. 服务器是否正在运行 (python app.py)")
    print("2. 网络连接是否正常")
    print("3. 防火墙设置")
    print("4. 尝试不同的视频URL")

if __name__ == "__main__":
    main() 