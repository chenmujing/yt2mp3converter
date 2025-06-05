import yt_dlp

def test_network_fix():
    print("测试网络修复...")
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'no_proxy': True,  # 禁用代理
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            print(f"✅ 成功！视频标题: {info.get('title')}")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

if __name__ == "__main__":
    test_network_fix() 