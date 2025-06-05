#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL连接修复测试脚本
"""

import yt_dlp
import requests
import ssl
import sys

def test_ssl_configuration():
    """测试SSL配置"""
    print("=== SSL配置测试 ===")
    
    # 基本网络连接测试
    test_urls = [
        'https://www.youtube.com',
        'https://www.google.com'
    ]
    
    print("\n1. 基本网络连接测试:")
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10, verify=False)
            print(f"✓ {url}: {response.status_code}")
        except Exception as e:
            print(f"✗ {url}: {e}")
    
    # yt-dlp配置测试
    print("\n2. yt-dlp配置测试:")
    
    # 使用增强的SSL配置
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'no_proxy': True,
        'socket_timeout': 60,
        'retries': 10,
        'fragment_retries': 10,
        'retry_sleep_functions': {
            'http': lambda n: min(2 ** n, 30),
            'fragment': lambda n: min(2 ** n, 30)
        },
        # SSL相关配置
        'nocheckcertificate': True,
        'prefer_insecure': False,
        # 添加用户代理和头部信息
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Connection': 'close'
        },
        # 网络错误处理
        'ignoreerrors': False,
        'abort_on_error': False,
        'continue_dl': True,
    }
    
    # 测试视频URL (请将此URL替换为您想测试的视频)
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 示例URL
    
    try:
        print(f"正在测试视频信息提取: {test_video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_video_url, download=False)
            print(f"✓ 视频标题: {info.get('title', 'N/A')}")
            print(f"✓ 时长: {info.get('duration_string', 'N/A')}")
            print(f"✓ 上传者: {info.get('uploader', 'N/A')}")
            
    except Exception as e:
        print(f"✗ yt-dlp测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        
        # 如果仍然是SSL错误，提供更多诊断信息
        if "SSL" in str(e) or "ssl" in str(e).lower():
            print("\n=== SSL诊断信息 ===")
            print(f"OpenSSL版本: {ssl.OPENSSL_VERSION}")
            print(f"SSL库版本: {ssl.ssl_version}")
            print(f"默认证书位置: {ssl.get_default_verify_paths()}")

def main():
    print("YouTube转MP3 SSL修复测试")
    print("=" * 40)
    
    test_ssl_configuration()
    
    print("\n=== 测试完成 ===")
    print("如果仍有SSL错误，请尝试:")
    print("1. 检查网络连接和防火墙设置")
    print("2. 更新yt-dlp: pip install --upgrade yt-dlp")
    print("3. 使用VPN或更换网络环境")

if __name__ == "__main__":
    main() 