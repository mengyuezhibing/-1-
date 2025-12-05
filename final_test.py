from flask import Flask, render_template_string
from flask_socketio import SocketIO

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key'

# 初始化SocketIO，使用threading模式
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 简单的HTML页面，使用与GovInfoToFileSystem-main类似的深色主题样式
HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Socket.IO 最小测试</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #e2e8f0;
            --accent-color: #0ea5e9;
            --secondary-color: #94a3b8;
            --border-color: #334155;
            --success-color: #10b981;
            --error-color: #ef4444;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            padding: 2rem;
            background-color: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }
        
        h1 {
            color: var(--accent-color);
            text-align: center;
            margin-bottom: 2rem;
        }
        
        #status {
            font-size: 1.25rem;
            margin: 1.5rem 0;
            text-align: center;
            padding: 1rem;
            background-color: rgba(15, 23, 42, 0.5);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        #messages {
            margin: 1.5rem 0;
            height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            background-color: rgba(15, 23, 42, 0.3);
        }
        
        #messages > div {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(51, 65, 85, 0.3);
        }
        
        #messages > div:last-child {
            border-bottom: none;
        }
        
        .status-connected {
            color: var(--success-color);
        }
        
        .status-error {
            color: #fca5a5;
        }
    </style>
    <script>
        // 连接socket.io
        const socket = io();
        
        socket.on('connect', function() {
            console.log('连接成功！');
            const statusElement = document.getElementById('status');
            statusElement.innerHTML = '连接成功！<br>Socket ID: ' + socket.id;
            statusElement.className = 'status-connected';
        });
        
        socket.on('message', function(data) {
            console.log('收到消息:', data);
            const messagesDiv = document.getElementById('messages');
            const messageElement = document.createElement('div');
            messageElement.textContent = data;
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        });
        
        socket.on('connect_error', function(error) {
            console.error('连接错误:', error);
            const statusElement = document.getElementById('status');
            statusElement.innerHTML = '连接错误: ' + error.message;
            statusElement.className = 'status-error';
        });
        
        socket.on('disconnect', function(reason) {
            console.log('连接断开:', reason);
            const statusElement = document.getElementById('status');
            statusElement.innerHTML = '连接已断开: ' + reason;
            statusElement.className = 'status-error';
        });
    </script>
</head>
<body>
    <div class="container">
        <h1>Socket.IO 连接测试</h1>
        <div id="status">正在连接...</div>
        <div id="messages">
            <!-- 消息将显示在这里 -->
        </div>
    </div>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('connect')
def connect():
    print('客户端连接')
    socketio.emit('message', '欢迎连接到服务器！')

if __name__ == '__main__':
    print('启动最小测试服务器在 http://localhost:5006')
    print('使用threading模式运行，端口5006，禁用调试器')
    # 使用更稳定的配置运行服务器
    socketio.run(app, host='0.0.0.0', port=5006, debug=False, use_reloader=False, log_output=False)
