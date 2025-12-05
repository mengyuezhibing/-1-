import requests

# 测试新的百度热点新闻API
def test_news_api():
    """测试百度热点新闻API是否正常工作"""
    print("正在测试百度热点新闻API...")
    
    # 测试API地址
    api_url = 'https://v2.xxapi.cn/api/baiduhot'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应数据: {data}")
            
            if data.get('code') == 200 and data.get('data'):
                news_list = data.get('data')
                print(f"成功获取 {len(news_list)} 条热点新闻")
                
                # 打印前3条新闻
                print("\n前3条热点新闻:")
                for i, news in enumerate(news_list[:3], 1):
                    print(f"{i}. {news.get('title')}")
                    print(f"   热度: {news.get('hot')}")
                    print(f"   图片: {news.get('img')}")
                    print(f"   链接: {news.get('url')}")
                    print()
                
                return True
            else:
                print("API返回数据格式不正确")
                return False
        else:
            print("API请求失败")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

# 执行测试
if __name__ == "__main__":
    test_news_api()