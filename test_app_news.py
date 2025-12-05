# 测试应用中的新闻功能
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import crawl_news

# 测试crawl_news函数
def test_crawl_news():
    """测试应用中的crawl_news函数"""
    print("正在测试应用中的crawl_news函数...")
    
    try:
        # 测试无分类参数
        news_data = crawl_news()
        
        print("\n测试结果:")
        print(f"新闻数据类型: {type(news_data)}")
        print(f"是否包含list字段: {'list' in news_data}")
        
        if 'list' in news_data and isinstance(news_data['list'], list):
            print(f"新闻列表长度: {len(news_data['list'])}")
            
            # 打印前3条新闻
            print("\n前3条新闻:")
            for i, news in enumerate(news_data['list'][:3], 1):
                print(f"{i}. {news.get('title')}")
                print(f"   图片: {'有' if news.get('image') else '无'}")
                print(f"   链接: {'有' if news.get('url') else '无'}")
                print()
            
            return True
        else:
            print("新闻数据格式不正确")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

# 执行测试
if __name__ == "__main__":
    test_crawl_news()