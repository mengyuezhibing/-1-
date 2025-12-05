# 简化版测试应用
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'

# 使用threading模式初始化SocketIO
logger.info("初始化SocketIO，使用threading模式")
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 简单的HTML页面
HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试服务器</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            background-color: #f0f0f0;
        }
        .status {
            font-size: 24px;
            margin: 20px;
        }
        .connected {
            color: green;
        }
        .disconnected {
            color: red;
        }
    </style>
</head>
<body>
    <h1>测试服务器</h1>
    <div id="status" class="status disconnected">正在连接...</div>
    <script>
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('status').textContent = '已连接';
            document.getElementById('status').className = 'status connected';
            console.log('Socket连接成功');
        });
        
        socket.on('connect_error', function(error) {
            console.error('连接错误:', error);
            document.getElementById('status').textContent = '连接失败: ' + error.message;
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logger.info("访问主页")
    return render_template_string(HTML)

@socketio.on('connect')
def handle_connect():
    logger.info("客户端连接成功")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("客户端断开连接")

if __name__ == '__main__':
    try:
        logger.info("启动测试服务器")
        logger.info("访问地址: http://localhost:5001")
        # 使用threading模式运行，禁用调试器和重载器
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        # 打印异常信息到控制台
        import traceback
        traceback.print_exc()
