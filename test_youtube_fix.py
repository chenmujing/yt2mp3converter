#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube反机器人检测修复测试
测试新的yt-dlp配置是否能绕过YouTube的身份验证要求
"""

import requests
import json
import time

def test_youtube_download():
    """测试YouTube下载功能"""
    
    # 测试URL - 使用一个常见的视频
    test_url = "https://www.youtube.com/watch?v=xLxTVQxOKOg"
    
    print("🔧 测试YouTube反机器人检测修复")
    print(f"📺 测试视频: {test_url}")
    print("=" * 60)
    
    try:
        # 1. 测试视频信息获取
        print("1️⃣ 测试视频信息获取...")
        
        response = requests.post('http://localhost:5000/api/video-info', 
                               json={'url': test_url}, 
                               timeout=30)
        
        if response.status_code == 200:
            video_info = response.json()
            if video_info.get('success'):
                print(f"✅ 视频信息获取成功!")
                data = video_info['data']
                print(f"   标题: {data.get('title', '未知')}")
                print(f"   时长: {data.get('duration_string', '未知')}")
                print(f"   作者: {data.get('uploader', '未知')}")
            else:
                print(f"❌ 视频信息获取失败: {video_info}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
        # 2. 测试转换启动
        print("\n2️⃣ 测试转换启动...")
        
        response = requests.post('http://localhost:5000/api/convert', 
                               json={'url': test_url}, 
                               timeout=30)
        
        if response.status_code == 200:
            convert_result = response.json()
            if convert_result.get('success'):
                task_id = convert_result['task_id']
                print(f"✅ 转换任务启动成功! 任务ID: {task_id}")
                
                # 3. 监控转换进度
                print("\n3️⃣ 监控转换进度...")
                
                max_wait_time = 300  # 最大等待5分钟
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    try:
                        status_response = requests.get(f'http://localhost:5000/api/status/{task_id}', 
                                                     timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            progress = status_data.get('progress', 0)
                            status = status_data.get('status', 'unknown')
                            error = status_data.get('error')
                            
                            print(f"   进度: {progress}% | 状态: {status}")
                            
                            if error:
                                print(f"❌ 转换错误: {error}")
                                return False
                                
                            if status == 'completed':
                                print("✅ 转换完成!")
                                files = status_data.get('files', {})
                                print(f"   生成文件数: {len(files)}")
                                for format_type, file_info in files.items():
                                    print(f"   - {format_type}: {file_info['filename']} ({file_info['size']} bytes)")
                                return True
                                
                            elif status == 'failed':
                                print(f"❌ 转换失败")
                                return False
                                
                        time.sleep(5)  # 等待5秒再检查
                        
                    except Exception as e:
                        print(f"⚠️ 状态检查错误: {e}")
                        time.sleep(5)
                
                print(f"⏰ 转换超时 (超过{max_wait_time}秒)")
                return False
                
            else:
                print(f"❌ 转换启动失败: {convert_result}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_server_health():
    """测试服务器健康状态"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务器运行正常")
            print(f"   状态: {data.get('status')}")
            print(f"   活跃任务: {data.get('active_tasks')}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 YouTube反机器人检测修复测试")
    print("=" * 60)
    
    # 首先检查服务器状态
    print("📡 检查服务器状态...")
    if not test_server_health():
        print("❌ 服务器未运行，请先启动 python app.py")
        exit(1)
    
    print("\n" + "=" * 60)
    
    # 测试YouTube下载
    success = test_youtube_download()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试通过! YouTube反机器人检测修复成功!")
        print("✅ 新的配置能够成功下载YouTube视频")
    else:
        print("❌ 测试失败! 可能需要进一步调整配置")
        print("💡 建议:")
        print("   1. 确保Chrome浏览器已登录YouTube")
        print("   2. 尝试手动在浏览器中访问测试视频")
        print("   3. 检查网络连接和代理设置")
    
    print("=" * 60) 