#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完全禁用cookies的yt-dlp配置
"""

import yt_dlp
import tempfile
import os

# 尝试更严格的配置以完全避免DPAPI
ydl_opts = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s_%(title).50s.%(ext)s'),
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
    
    # 完全禁用cookies - 多种方式
    'cookiefile': None,
    'no_check_certificate': True,
    'cookiesfrombrowser': None,  # 显式设置为None
    
    # 禁用缓存和其他可能触发DPAPI的功能
    'cachedir': False,  # 禁用缓存
    'no_cache_dir': True,
    
    # 简单HTTP头
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    
    # 降低请求频率
    'sleep_interval': 1,
    'max_sleep_interval': 3,
}

print('🧪 测试严格禁用cookies的yt-dlp配置...')
print('配置:', ydl_opts)

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print('📡 获取视频信息...')
        info = ydl.extract_info('https://www.youtube.com/watch?v=xLxTVQxOKOg', download=False)
        print(f'✅ 视频信息获取成功: {info.get("title", "Unknown")}')
        
        print('⬇️ 开始下载...')
        ydl.download(['https://www.youtube.com/watch?v=xLxTVQxOKOg'])
        print('✅ 下载完成！')
        
except Exception as e:
    print(f'❌ 测试失败: {e}')
    
    # 如果仍然有DPAPI错误，打印更详细的错误信息
    if "DPAPI" in str(e):
        print("\n🔍 DPAPI错误详情:")
        print(f"   错误: {e}")
        print("   这表明yt-dlp仍在尝试从浏览器提取cookies")
        print("   可能的原因:")
        print("   1. yt-dlp默认行为发生了变化")
        print("   2. 环境变量或配置文件影响")
        print("   3. 需要更新的yt-dlp版本") 