from flask import Flask, render_template_string
from flask_socketio import SocketIO

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key'

# 初始化SocketIO，使用基本配置
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML模板 - 简化版用于测试socket.io连接
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO 连接测试</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        // 连接到Socket.IO服务器
        const socket = io();
        
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
            msgElement.textContent = data;
            messages.appendChild(msgElement);
        });
        
        // 连接错误事件
        socket.on('connect_error', function(error) {
            console.error('连接错误:', error);
            document.getElementById('status').textContent = '连接失败: ' + error.message;
            document.getElementById('status').style.color = 'red';
        });
        
        // 断开连接事件
        socket.on('disconnect', function() {
            console.log('连接已断开');
            document.getElementById('status').textContent = '连接已断开';
            document.getElementById('status').style.color = 'orange';
        });
        
        // 发送消息函数
        function sendMessage() {
            const message = document.getElementById('messageInput').value;
            if (message) {
                socket.emit('message', message);
                document.getElementById('messageInput').value = '';
            }
        }
    </script>
</head>
<body>
    <h1>Socket.IO 连接测试</h1>
    <p>状态: <span id="status" style="color: orange;">正在连接...</span></p>
    
    <div id="messages" style="margin: 20px 0; padding: 10px; border: 1px solid #ddd;">
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

if __name__ == '__main__':
    # 在端口5002上运行应用，避免端口冲突
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
