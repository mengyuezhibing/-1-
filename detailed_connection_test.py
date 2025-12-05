import socket
import time

def test_socket_connection(host, port, timeout=10):
    """使用socket模块测试端口连接"""
    print(f"测试连接到: {host}:{port}")
    print(f"超时设置: {timeout}秒")
    
    try:
        # 创建socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        
        # 尝试连接
        start_time = time.time()
        result = s.connect_ex((host, port))
        end_time = time.time()
        
        if result == 0:
            print(f"✓ 成功连接到 {host}:{port}")
            print(f"请求耗时: {end_time - start_time:.2f}秒")
            
            # 尝试发送一个简单的HTTP请求
            try:
                request = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
                s.sendall(request.encode('utf-8'))
                
                # 接收响应
                response = s.recv(4096)
                print(f"✓ 成功发送HTTP请求并接收响应")
                status_line = response.split(b'\r\n')[0].decode('utf-8')
                print(f"响应状态行: {status_line}")
                print(f"响应长度: {len(response)}字节")
            except Exception as e:
                print(f"✗ 发送/接收HTTP请求失败: {e}")
                
            s.close()
            return True
        else:
            print(f"✗ 连接失败，错误码: {result}")
            print(f"错误描述: {socket.error(result)}")
            s.close()
            return False
            
    except socket.timeout:
        print(f"✗ 连接超时 ({timeout}秒)")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return False

def check_port_listening(host, port):
    """检查端口是否正在监听"""
    print(f"\n检查 {host}:{port} 是否正在监听...")
    
    try:
        # 创建socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        
        # 尝试绑定端口
        try:
            s.bind((host, port))
            print(f"✗ 端口 {port} 未被占用")
            s.close()
            return False
        except socket.error as e:
            if e.errno == 10048:  # Address already in use
                print(f"✓ 端口 {port} 已被占用")
                s.close()
                return True
            else:
                print(f"✗ 检查端口监听失败: {e}")
                s.close()
                return False
                
    except Exception as e:
        print(f"✗ 检查端口监听失败: {e}")
        return False

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5003
    
    # 检查端口是否正在监听
    is_listening = check_port_listening(host, port)
    
    if is_listening:
        # 如果端口正在监听，尝试连接
        print("\n" + "="*50)
        print(f"端口 {port} 正在监听，尝试连接...")
        success = test_socket_connection(host, port)
        
        if success:
            print("\n✓ 服务器连接测试成功！")
        else:
            print("\n✗ 服务器连接测试失败！")
    else:
        print(f"\n✗ 端口 {port} 未在监听，服务器可能未启动")
        print("请先启动服务器，然后再运行此测试脚本")