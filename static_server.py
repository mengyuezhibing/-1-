import http.server
import socketserver
import os

# 设置端口
PORT = 8000

# 获取当前目录作为文档根目录
handler = http.server.SimpleHTTPRequestHandler

# 创建服务器
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"服务器运行在 http://localhost:{PORT}")
    print(f"可以访问预览页面: http://localhost:{PORT}/preview.html")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")