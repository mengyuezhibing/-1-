from flask import Flask
from flask_socketio import SocketIO
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 定义基本的load_users函数
users = {}

def load_users():
    global users
    print("用户数据加载成功")

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

@socketio.on('message')
def handle_message(data):
    print(f'收到消息: {data}')

if __name__ == '__main__':
    load_users()
    print('服务器启动中...')
    print('访问地址: http://localhost:9999')
    socketio.run(app, host='0.0.0.0', port=9999, debug=True)
