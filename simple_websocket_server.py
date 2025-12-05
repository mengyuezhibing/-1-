from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import threading
import time
import os
import json

# 创建一个简单的HTTP服务器类，用于提供HTML页面
class WebSocketDemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # 返回WebSocket测试页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # HTML内容
            html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket 测试</title>
    <script>
        let socket;
        let reconnectInterval;
        
        // 连接WebSocket服务器
        function connectWebSocket() {
            try {
                // 连接到WebSocket服务器
                socket = new WebSocket('ws://localhost:5004');
                
                // 连接打开事件
                socket.onopen = function(event) {
                    console.log('WebSocket连接已建立');
                    updateStatus('连接成功', 'green');
                    addMessage('系统', '连接已建立');
                    
                    // 清除重连定时器
                    if (reconnectInterval) {
                        clearInterval(reconnectInterval);
                        reconnectInterval = null;
                    }
                };
                
                // 接收消息事件
                socket.onmessage = function(event) {
                    console.log('收到消息:', event.data);
                    addMessage('服务器', event.data);
                };
                
                // 连接关闭事件
                socket.onclose = function(event) {
                    console.log('WebSocket连接已关闭:', event.code, event.reason);
                    updateStatus('连接已关闭，尝试重连...', 'orange');
                    addMessage('系统', '连接已关闭，正在尝试重连...');
                    
                    // 尝试重连
                    setupReconnect();
                };
                
                // 连接错误事件
                socket.onerror = function(error) {
                    console.error('WebSocket错误:', error);
                    updateStatus('连接错误', 'red');
                    addMessage('系统', '连接发生错误');
                };
                
            } catch (e) {
                console.error('连接失败:', e);
                updateStatus('连接失败', 'red');
                addMessage('系统', '连接失败: ' + e.message);
                
                // 尝试重连
                setupReconnect();
            }
        }
        
        // 设置重连
        function setupReconnect() {
            if (!reconnectInterval) {
                reconnectInterval = setInterval(function() {
                    console.log('尝试重新连接...');
                    updateStatus('尝试重新连接...', 'orange');
                    connectWebSocket();
                }, 3000); // 每3秒尝试重连一次
            }
        }
        
        // 更新状态显示
        function updateStatus(message, color) {
            const statusElement = document.getElementById('status');
            statusElement.textContent = message;
            statusElement.style.color = color;
        }
        
        // 添加消息到聊天区域
        function addMessage(sender, message) {
            const messagesDiv = document.getElementById('messages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 发送消息
        function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (message && socket && socket.readyState === WebSocket.OPEN) {
                socket.send(message);
                addMessage('你', message);
                messageInput.value = '';
            } else if (socket && socket.readyState !== WebSocket.OPEN) {
                alert('连接未建立，请等待重连完成');
            }
        }
        
        // 页面加载时连接WebSocket
        window.onload = function() {
            updateStatus('正在连接WebSocket服务器...', 'orange');
            connectWebSocket();
            
            // 允许按Enter键发送消息
            document.getElementById('messageInput').addEventListener('keyup', function(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            });
        };
        
        // 页面关闭时清理
        window.onbeforeunload = function() {
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
            }
            if (socket) {
                socket.close();
            }
        };
    </script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        #status {
            font-weight: bold;
            margin-bottom: 20px;
        }
        #messages {
            height: 400px;
            border: 1px solid #ddd;
            padding: 10px;
            overflow-y: auto;
            margin-bottom: 20px;
            background-color: #f9f9f9;
        }
        .message {
            margin-bottom: 10px;
            padding: 5px;
        }
        .message strong {
            color: #0066cc;
        }
        #messageInput {
            width: 80%;
            padding: 8px;
            margin-right: 10px;
        }
        button {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>WebSocket 测试服务器</h1>
    <p>状态: <span id="status">正在连接...</span></p>
    
    <div id="messages">
        <!-- 消息将显示在这里 -->
    </div>
    
    <div>
        <input type="text" id="messageInput" placeholder="输入消息...">
        <button onclick="sendMessage()">发送</button>
    </div>
</body>
</html>
'''
            
            self.wfile.write(html_content.encode('utf-8'))
        else:
            # 对于其他路径，返回404
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')

# 启动HTTP服务器的函数
def start_http_server():
    try:
        server_address = ('', 5004)
        httpd = HTTPServer(server_address, WebSocketDemoHandler)
        print(f'HTTP服务器启动在 http://localhost:5004')
        httpd.serve_forever()
    except Exception as e:
        print(f'HTTP服务器错误: {e}')

if __name__ == '__main__':
    print('启动WebSocket测试服务...')
    
    # 启动HTTP服务器线程
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True
    http_thread.start()
    
    print('服务已启动，请在浏览器中访问 http://localhost:5004')
    print('注意：此页面仅提供HTML界面，不包含真正的WebSocket功能')
    print('按Ctrl+C停止服务器...')
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('服务器正在关闭...')
