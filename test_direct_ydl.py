#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试yt-dlp以确定DPAPI错误的来源
"""

import yt_dlp
import tempfile
import os

# 创建一个完全隔离的配置
ydl_opts = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s_%(title).50s.%(ext)s'),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '256',
    }],
    'quiet': False,
    'no_warnings': False,
    'extract_flat': False,
    'ignoreerrors': False,
    'socket_timeout': 60,
    'retries': 3,
    'nocheckcertificate': True,
    'cookiefile': None,
    'no_check_certificate': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    'sleep_interval': 1,
    'max_sleep_interval': 3,
}

print('🧪 开始测试yt-dlp直接调用...')
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print('📡 获取视频信息...')
        info = ydl.extract_info('https://www.youtube.com/watch?v=xLxTVQxOKOg', download=False)
        print(f'✅ 视频信息获取成功: {info.get("title", "Unknown")}')
        
        print('⬇️ 开始下载...')
        ydl.download(['https://www.youtube.com/watch?v=xLxTVQxOKOg'])
        print('✅ 下载完成！')
        
except Exception as e:
    print(f'❌ yt-dlp直接调用失败: {e}') 