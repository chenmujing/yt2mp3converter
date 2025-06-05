#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载速度优化测试脚本
"""

import requests
import time
import json

def test_speed_optimization():
    """测试优化后的下载速度"""
    base_url = "http://localhost:5000"
    
    print("=== 下载速度优化测试 ===")
    
    # 使用较短的测试视频
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 3分33秒的视频
    
    print(f"测试视频: {test_video_url}")
    
    # 1. 先获取视频信息
    print("\n1. 获取视频信息...")
    try:
        response = requests.post(f"{base_url}/api/video-info", 
                               json={'url': test_video_url})
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                video_info = data['data']
                print(f"✓ 视频标题: {video_info.get('title', 'N/A')}")
                print(f"✓ 时长: {video_info.get('duration_string', 'N/A')}")
            else:
                print(f"✗ 视频信息获取失败: {data}")
                return
        else:
            print(f"✗ 请求失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 视频信息测试错误: {e}")
        return
    
    # 2. 测试快速转换（只转换一种格式）
    print("\n2. 快速转换测试（MP3 128k）...")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/convert", 
                               json={
                                   'url': test_video_url,
                                   'formats': ['mp3_128']  # 只转换一种格式
                               })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task_id = data['task_id']
                print(f"✓ 任务创建成功: {task_id}")
                
                # 监控转换进度
                print("监控转换进度...")
                max_wait_time = 120  # 最多等待2分钟
                last_progress = 0
                stalled_count = 0
                
                while time.time() - start_time < max_wait_time:
                    status_response = requests.get(f"{base_url}/api/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        # 检测进度是否停滞
                        if progress == last_progress:
                            stalled_count += 1
                        else:
                            stalled_count = 0
                        last_progress = progress
                        
                        elapsed_time = time.time() - start_time
                        print(f"  状态: {status}, 进度: {progress}%, 耗时: {elapsed_time:.1f}s")
                        
                        if status == 'completed':
                            total_time = time.time() - start_time
                            print(f"✓ 转换完成! 总耗时: {total_time:.1f}秒")
                            if 'files' in status_data:
                                for format_type, file_info in status_data['files'].items():
                                    file_size_mb = file_info['size'] / (1024 * 1024)
                                    speed_mbps = file_size_mb / total_time if total_time > 0 else 0
                                    print(f"  文件: {file_info['filename']}")
                                    print(f"  大小: {file_size_mb:.2f} MB")
                                    print(f"  平均速度: {speed_mbps:.2f} MB/s")
                            break
                        elif status == 'error':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"✗ 转换失败: {error_msg}")
                            break
                        
                        # 检测停滞（进度10秒没有变化）
                        if stalled_count >= 5:  # 5次检查 = 25秒没有进度
                            print("⚠️  检测到下载停滞，可能存在网络问题")
                        
                        time.sleep(5)  # 等待5秒再检查
                    else:
                        print(f"✗ 状态检查失败: {status_response.status_code}")
                        break
                else:
                    print("✗ 转换超时")
            else:
                print(f"✗ 任务创建失败: {data}")
        else:
            print(f"✗ 转换请求失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 转换测试错误: {e}")
    
    # 3. 测试多格式转换
    print("\n3. 多格式转换测试（MP3 + MP4）...")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/convert", 
                               json={
                                   'url': test_video_url,
                                   'formats': ['mp3_128', 'mp4_360']  # 转换两种格式
                               })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task_id = data['task_id']
                print(f"✓ 多格式任务创建成功: {task_id}")
                
                # 简单监控（最多1分钟）
                max_wait_time = 180  # 3分钟
                while time.time() - start_time < max_wait_time:
                    status_response = requests.get(f"{base_url}/api/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        elapsed_time = time.time() - start_time
                        print(f"  多格式转换 - 状态: {status}, 进度: {progress}%, 耗时: {elapsed_time:.1f}s")
                        
                        if status == 'completed':
                            total_time = time.time() - start_time
                            print(f"✓ 多格式转换完成! 总耗时: {total_time:.1f}秒")
                            if 'files' in status_data:
                                print(f"  成功转换 {len(status_data['files'])} 个格式:")
                                for format_type, file_info in status_data['files'].items():
                                    file_size_mb = file_info['size'] / (1024 * 1024)
                                    print(f"    {format_type}: {file_info['filename']} ({file_size_mb:.2f} MB)")
                            break
                        elif status == 'error':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"✗ 多格式转换失败: {error_msg}")
                            break
                        
                        time.sleep(10)  # 等待10秒再检查
                    else:
                        print(f"✗ 多格式状态检查失败: {status_response.status_code}")
                        break
                else:
                    print("⚠️  多格式转换超时")
    except Exception as e:
        print(f"✗ 多格式转换测试错误: {e}")
    
    print("\n=== 测试完成 ===")

def main():
    print("YouTube转MP3 下载速度优化测试")
    print("=" * 50)
    
    test_speed_optimization()
    
    print("\n性能优化要点:")
    print("1. 串行下载格式（避免网络拥堵）")
    print("2. 减少默认格式数量")
    print("3. 限制下载速度和并发")
    print("4. 优化超时和重试设置")
    print("5. 增强进度追踪")

if __name__ == "__main__":
    main() 