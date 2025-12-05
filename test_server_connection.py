import urllib.request
import time

def test_server_connection(url, timeout=10):
    """使用urllib测试服务器连接"""
    print(f"测试连接到: {url}")
    print(f"超时设置: {timeout}秒")
    
    try:
        # 创建请求对象
        req = urllib.request.Request(url)
        
        # 发送请求
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            end_time = time.time()
            
            # 获取响应状态码
            status_code = response.getcode()
            print(f"响应状态码: {status_code}")
            
            # 获取响应头
            print("响应头:")
            for header, value in response.getheaders():
                print(f"  {header}: {value}")
            
            # 获取响应内容
            content_length = int(response.getheader('Content-Length', 0))
            print(f"响应内容长度: {content_length}字节")
            
            if content_length > 0:
                content = response.read(1000)  # 只读取前1000字节
                print(f"响应内容前1000字节:\n{content.decode('utf-8', errors='ignore')}")
            
            print(f"请求耗时: {end_time - start_time:.2f}秒")
            return True
            
    except urllib.error.URLError as e:
        print(f"URL错误: {e}")
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    
    return False

if __name__ == "__main__":
    # 测试服务器连接
    url = "http://127.0.0.1:5003"
    success = test_server_connection(url)
    
    if success:
        print("\n服务器连接测试成功！")
    else:
        print("\n服务器连接测试失败！")
        
    # 也测试一下/login路径
    print("\n" + "="*50)
    print("测试/login路径")
    login_url = "http://127.0.0.1:5003/login"
    success_login = test_server_connection(login_url)