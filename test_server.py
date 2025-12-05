import socket
import threading
import time

def test_socket():
    """测试套接字是否可以正常绑定和监听"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', 5003))
        s.listen(1)
        print("套接字测试成功：可以绑定到端口5003")
        # 等待1秒后关闭
        time.sleep(1)
        s.close()
        return True
    except Exception as e:
        print(f"套接字测试失败：{e}")
        s.close()
        return False

if __name__ == "__main__":
    print("测试端口5003是否可用...")
    if test_socket():
        print("端口5003可用，尝试启动简单HTTP服务器...")
        import http.server
        import socketserver
        
        PORT = 5003
        Handler = http.server.SimpleHTTPRequestHandler
        
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"简单HTTP服务器已启动，地址：http://localhost:{PORT}")
                print("按Ctrl+C停止服务器")
                # 运行5秒后自动停止
                threading.Timer(5.0, httpd.shutdown).start()
                httpd.serve_forever()
        except Exception as e:
            print(f"启动简单HTTP服务器失败：{e}")
    else:
        print("端口5003不可用")