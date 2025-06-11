#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的YouTube下载器
避免DPAPI和cookies问题
"""

import yt_dlp
import os
import tempfile

def simple_download(url, output_dir):
    """
    简单的YouTube下载函数
    完全避免cookies和复杂配置
    """
    
    # 最基本的配置，避免所有可能导致DPAPI错误的选项
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s_%(title).50s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        # 基本设置
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'ignoreerrors': False,
        'socket_timeout': 60,
        'retries': 3,
        'nocheckcertificate': True,
        
        # 明确禁用cookies相关功能
        'cookiefile': None,
        'no_check_certificate': True,
        
        # 简单的HTTP头
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        
        # 降低请求频率避免被检测
        'sleep_interval': 1,
        'max_sleep_interval': 3,
    }
    
    try:
        print(f"开始下载: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先获取信息
            info = ydl.extract_info(url, download=False)
            print(f"视频标题: {info.get('title', 'Unknown')}")
            print(f"视频时长: {info.get('duration_string', 'Unknown')}")
            
            # 开始下载
            ydl.download([url])
            
        print("下载完成!")
        return True
        
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def test_simple_download():
    """测试简化下载"""
    test_url = "https://www.youtube.com/watch?v=xLxTVQxOKOg"
    temp_dir = tempfile.mkdtemp()
    
    print("🧪 测试简化YouTube下载器")
    print(f"📁 输出目录: {temp_dir}")
    print(f"🎥 测试URL: {test_url}")
    print("=" * 60)
    
    success = simple_download(test_url, temp_dir)
    
    if success:
        print("\n✅ 下载成功!")
        print("📂 生成的文件:")
        for file in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, file)
            size = os.path.getsize(filepath)
            print(f"   {file} ({size} bytes)")
    else:
        print("\n❌ 下载失败!")
    
    return success

if __name__ == "__main__":
    test_simple_download() 