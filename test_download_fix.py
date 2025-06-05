#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载链接修复测试脚本
"""

import requests
import time
import json

def test_download_fix():
    """测试下载链接修复"""
    base_url = "http://localhost:5000"
    
    print("=== 下载链接修复测试 ===")
    
    # 使用现有的任务ID进行测试
    test_task_id = "5742c0bfe2215239a2f67cd532f855ff"
    
    print(f"测试任务ID: {test_task_id}")
    
    # 1. 检查任务状态
    print("\n1. 检查任务状态...")
    try:
        response = requests.get(f"{base_url}/api/status/{test_task_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 任务状态: {data.get('status')}")
            print(f"✓ 进度: {data.get('progress')}%")
            
            if 'files' in data:
                print(f"✓ 可用文件: {len(data['files'])} 个")
                for format_type, file_info in data['files'].items():
                    print(f"  - {format_type}: {file_info['filename']} ({file_info['size']} bytes)")
                    
                    # 测试下载链接
                    download_url = file_info['download_url']
                    full_url = f"{base_url}{download_url}"
                    print(f"    下载链接: {full_url}")
                    
                    # 测试链接是否有效（只检查头部）
                    try:
                        head_response = requests.head(full_url)
                        if head_response.status_code == 200:
                            content_length = head_response.headers.get('content-length', 'unknown')
                            print(f"    ✓ 链接有效，文件大小: {content_length} bytes")
                        else:
                            print(f"    ✗ 链接无效，状态码: {head_response.status_code}")
                    except Exception as e:
                        print(f"    ✗ 链接测试失败: {e}")
            else:
                print("✗ 没有找到转换文件")
        else:
            print(f"✗ 获取任务状态失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 状态检查失败: {e}")
    
    # 2. 测试具体下载链接
    print("\n2. 测试具体下载链接...")
    test_formats = ['mp3_128', 'mp4_360']
    
    for format_type in test_formats:
        download_url = f"{base_url}/api/download/{test_task_id}/{format_type}"
        print(f"\n测试 {format_type} 下载:")
        print(f"URL: {download_url}")
        
        try:
            # 只获取前1KB来测试连接
            response = requests.get(download_url, stream=True, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'unknown')
                content_length = response.headers.get('content-length', 'unknown')
                content_disposition = response.headers.get('content-disposition', 'unknown')
                
                print(f"✓ 下载成功!")
                print(f"  Content-Type: {content_type}")
                print(f"  Content-Length: {content_length} bytes")
                print(f"  Content-Disposition: {content_disposition}")
            else:
                print(f"✗ 下载失败，状态码: {response.status_code}")
                if response.text:
                    print(f"  错误信息: {response.text[:200]}")
        except Exception as e:
            print(f"✗ 下载测试失败: {e}")
    
    # 3. 测试新转换
    print("\n3. 测试新转换...")
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        # 创建新的转换任务
        response = requests.post(f"{base_url}/api/convert", 
                               json={
                                   'url': test_video_url,
                                   'formats': ['mp3_128']
                               })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                new_task_id = data['task_id']
                print(f"✓ 新任务创建成功: {new_task_id}")
                
                # 等待任务完成
                print("等待任务完成...")
                for i in range(30):  # 最多等待30次 = 150秒
                    status_response = requests.get(f"{base_url}/api/status/{new_task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        print(f"  状态: {status}, 进度: {progress}%")
                        
                        if status == 'completed':
                            print("✓ 新任务完成!")
                            if 'files' in status_data:
                                for format_type, file_info in status_data['files'].items():
                                    download_url = f"{base_url}{file_info['download_url']}"
                                    print(f"  新下载链接: {download_url}")
                                    
                                    # 测试新链接
                                    try:
                                        head_response = requests.head(download_url)
                                        if head_response.status_code == 200:
                                            print(f"  ✓ 新链接有效!")
                                        else:
                                            print(f"  ✗ 新链接无效: {head_response.status_code}")
                                    except Exception as e:
                                        print(f"  ✗ 新链接测试失败: {e}")
                            break
                        elif status == 'error':
                            print(f"✗ 任务失败: {status_data.get('error')}")
                            break
                        
                        time.sleep(5)
                else:
                    print("⚠️  任务超时")
            else:
                print(f"✗ 任务创建失败: {data}")
        else:
            print(f"✗ 创建转换请求失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 新转换测试失败: {e}")
    
    print("\n=== 测试完成 ===")

def main():
    print("YouTube转MP3 下载链接修复测试")
    print("=" * 50)
    
    test_download_fix()

if __name__ == "__main__":
    main() 