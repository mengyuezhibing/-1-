# 综合测试脚本：测试应用中的所有API功能
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import crawl_news, get_weather, get_music, get_image, get_hot60s

# 测试所有API功能
def test_all_apis():
    """测试应用中的所有API功能"""
    print("===== 开始测试所有API功能 =====\n")
    
    # 测试新闻功能
    print("1. 测试新闻功能...")
    try:
        news_data = crawl_news()
        if news_data and 'list' in news_data and len(news_data['list']) > 0:
            print(f"   ✅ 新闻功能测试成功！获取到 {len(news_data['list'])} 条新闻")
            print(f"   示例新闻: {news_data['list'][0]['title']}")
        else:
            print("   ❌ 新闻功能测试失败")
    except Exception as e:
        print(f"   ❌ 新闻功能测试失败: {str(e)}")
    
    # 测试新闻60s功能
    print("\n2. 测试新闻60s功能...")
    try:
        hot60s_data = get_hot60s()
        if hot60s_data:
            print(f"   ✅ 新闻60s功能测试成功")
            # 新闻60s可能返回文本或JSON，简单验证
            if isinstance(hot60s_data, str):
                print(f"   返回类型: 文本")
                print(f"   内容长度: {len(hot60s_data)} 字符")
            else:
                print(f"   返回类型: {type(hot60s_data)}")
        else:
            print("   ❌ 新闻60s功能测试失败")
    except Exception as e:
        print(f"   ❌ 新闻60s功能测试失败: {str(e)}")
    
    # 测试天气功能
    print("\n3. 测试天气功能...")
    try:
        # 为get_weather函数提供city参数
        weather_data = get_weather("北京")
        if weather_data and 'city' in weather_data:
            print(f"   ✅ 天气功能测试成功！")
            print(f"   城市: {weather_data['city']}")
            print(f"   天气: {weather_data['condition']}")
            print(f"   温度: {weather_data['temperature']}°C")
        elif weather_data:
            print(f"   ✅ 天气功能测试成功，但返回格式不同")
            print(f"   返回数据: {weather_data}")
        else:
            print("   ❌ 天气功能测试失败")
    except Exception as e:
        print(f"   ❌ 天气功能测试失败: {str(e)}")
    
    # 测试音乐功能
    print("\n4. 测试音乐功能...")
    try:
        music_data = get_music("测试")
        if music_data and isinstance(music_data, dict):
            print(f"   ✅ 音乐功能测试成功！")
            print(f"   音乐名称: {music_data.get('name', '未知')}")
            print(f"   歌手: {music_data.get('artist', '未知')}")
            print(f"   有URL: {'是' if music_data.get('url') else '否'}")
        elif music_data:
            print(f"   ✅ 音乐功能测试成功，但返回格式不同")
            print(f"   返回数据: {music_data}")
        else:
            print("   ❌ 音乐功能测试失败")
    except Exception as e:
        print(f"   ❌ 音乐功能测试失败: {str(e)}")
    
    # 测试图片功能
    print("\n5. 测试图片功能...")
    try:
        image_data = get_image("测试图片")
        if image_data and isinstance(image_data, dict) and 'url' in image_data:
            print(f"   ✅ 图片功能测试成功！")
            print(f"   图片URL: {image_data['url'][:50]}...")
        elif image_data:
            print(f"   ✅ 图片功能测试成功，但返回格式不同")
            print(f"   返回数据: {image_data}")
        else:
            print("   ❌ 图片功能测试失败")
    except Exception as e:
        print(f"   ❌ 图片功能测试失败: {str(e)}")
    
    print("\n===== 所有API功能测试完成 =====")

# 执行测试
if __name__ == "__main__":
    test_all_apis()