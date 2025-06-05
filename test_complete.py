import requests
import time
import json

def test_complete_conversion():
    print("🧪 测试完整的YouTube转换功能...")
    
    # 1. 测试视频信息获取
    print("\n1️⃣ 测试视频信息获取...")
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    response = requests.post('http://localhost:5000/api/video-info', 
                           json={'url': video_url})
    
    if response.status_code == 200:
        video_info = response.json()['data']
        print(f"✅ 视频信息获取成功: {video_info['title']}")
    else:
        print(f"❌ 视频信息获取失败: {response.text}")
        return False
    
    # 2. 测试转换启动
    print("\n2️⃣ 测试转换启动...")
    response = requests.post('http://localhost:5000/api/convert',
                           json={'url': video_url, 'formats': ['mp3_128']})
    
    if response.status_code == 200:
        task_id = response.json()['task_id']
        print(f"✅ 转换任务创建成功: {task_id}")
    else:
        print(f"❌ 转换启动失败: {response.text}")
        return False
    
    # 3. 监控转换进度
    print("\n3️⃣ 监控转换进度...")
    for i in range(30):  # 最多等待60秒
        response = requests.get(f'http://localhost:5000/api/status/{task_id}')
        if response.status_code == 200:
            status = response.json()
            print(f"进度: {status['progress']}% - {status['status']}")
            
            if status['status'] == 'completed':
                print("✅ 转换完成！")
                print(f"可用文件: {list(status['files'].keys())}")
                return True
            elif status['status'] == 'error':
                print(f"❌ 转换失败: {status.get('error', '未知错误')}")
                return False
        
        time.sleep(2)
    
    print("❌ 转换超时")
    return False

if __name__ == "__main__":
    success = test_complete_conversion()
    if success:
        print("\n🎉 所有测试通过！YouTube转换器工作正常。")
    else:
        print("\n💥 测试失败，请检查服务配置。")
    
    input("\n按Enter键退出...") 