from flask import Flask, render_template_string
from flask_socketio import SocketIO
import time

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key'

# 初始化SocketIO，使用threading模式，避免eventlet兼容性问题
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# HTML模板 - 简化版用于测试socket.io连接
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO 连接测试 (Threading模式)</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        // 连接到Socket.IO服务器
        const socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });
        
        // 连接成功事件
        socket.on('connect', function() {
            console.log('连接成功！');
            document.getElementById('status').textContent = '连接成功';
            document.getElementById('status').style.color = 'green';
        });
        
        // 接收消息事件
        socket.on('message', function(data) {
            console.log('收到消息:', data);
            const messages = document.getElementById('messages');
            const msgElement = document.createElement('div');
            msgElement.textContent = new Date().toLocaleTimeString() + ': ' + data;
            messages.appendChild(msgElement);
            // 自动滚动到底部
            messages.scrollTop = messages.scrollHeight;
        });
        
        // 连接错误事件
        socket.on('connect_error', function(error) {
            console.error('连接错误:', error);
            document.getElementById('status').textContent = '连接失败: ' + error.message;
            document.getElementById('status').style.color = 'red';
        });
        
        // 断开连接事件
        socket.on('disconnect', function(reason) {
            console.log('连接已断开，原因:', reason);
            document.getElementById('status').textContent = '连接已断开: ' + reason;
            document.getElementById('status').style.color = 'orange';
        });
        
        // 重新连接尝试事件
        socket.on('reconnect_attempt', function(attemptNumber) {
            console.log('尝试重新连接，次数:', attemptNumber);
            document.getElementById('status').textContent = '正在重新连接... (' + attemptNumber + ')';
        });
        
        // 发送消息函数
        function sendMessage() {
            const message = document.getElementById('messageInput').value;
            if (message) {
                socket.emit('message', message);
                document.getElementById('messageInput').value = '';
            }
        }
        
        // 页面加载完成后自动连接
        window.onload = function() {
            console.log('页面已加载，准备连接到Socket.IO服务器');
        };
    </script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        #messages {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            margin: 20px 0;
        }
        input {
            width: 80%;
            padding: 8px;
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
    <h1>Socket.IO 连接测试 (Threading模式)</h1>
    <p>状态: <span id="status" style="color: orange;">正在连接...</span></p>
    
    <div id="messages">
        <!-- 消息会显示在这里 -->
    </div>
    
    <div>
        <input type="text" id="messageInput" placeholder="输入消息...">
        <button onclick="sendMessage()">发送</button>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    # 渲染简化的HTML模板
    return render_template_string(HTML_TEMPLATE)

# 处理socket.io消息事件
@socketio.on('message')
def handle_message(message):
    print(f'收到消息: {message}')
    # 回显消息给客户端
    socketio.emit('message', f'服务器收到: {message}')

# 处理连接事件
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    # 发送欢迎消息
    socketio.emit('message', '欢迎连接到Socket.IO服务器！')

# 处理断开连接事件
@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')

# 处理连接错误事件
@socketio.on_error()
def handle_error(e):
    print(f'发生错误: {e}')

if __name__ == '__main__':
    print('正在启动Socket.IO服务器，使用threading模式...')
    print('服务器将在 http://localhost:5003 上运行')
    # 在端口5003上运行应用，使用threading模式
    socketio.run(app, host='0.0.0.0', port=5003, debug=True, use_reloader=False)
