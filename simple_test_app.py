# 导入所需的库
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import logging

# 配置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用实例
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# 初始化SocketIO，使用最基本的配置
socketio = SocketIO(app, 
                    cors_allowed_origins="*"  # 只保留CORS设置，其他使用默认值
                    )

# 存储连接的用户
connected_users = []

# 主页路由
@app.route('/')
def index():
    logger.debug('主页访问')
    # 直接渲染chat.html模板来测试背景效果
    return render_template('chat.html', username='test_user')

# 添加基本的socket.io事件处理器
@socketio.on('connect')
def handle_connect():
    logger.debug('客户端已连接')
    # 发送一个确认连接的消息给客户端
    emit('message', {"username": "系统", "message": "连接成功！"})

@socketio.on('disconnect')
def handle_disconnect():
    logger.debug('客户端已断开连接')
    # 从用户列表中移除断开连接的用户
    global connected_users
    # 更新用户列表格式，使用sid跟踪
    connected_users = [user for user in connected_users if user.get('sid') != request.sid]
    # 广播更新后的用户列表
    socketio.emit('update_users', {"users": [user['username'] for user in connected_users]}, namespace='/')

# 处理用户加入事件（前端发送的join事件）
@socketio.on('join')
def handle_join(data):
    logger.debug(f'收到join事件: {data}')
    if data and 'username' in data:
        username = data['username']
        logger.debug(f'{username} 加入了聊天室')
        # 存储用户信息，使用sid标识
        global connected_users
        connected_users.append({
            'sid': request.sid,
            'username': username
        })
        # 广播用户加入消息
        socketio.emit('user_joined', {"username": username}, namespace='/')
        # 更新用户列表
        socketio.emit('update_users', {"users": [user['username'] for user in connected_users]}, namespace='/')
        # 发送确认消息给当前用户
        emit('join_response', {'status': 'success', 'message': f'欢迎 {username}！'})

# 添加消息处理
@socketio.on('message')
def handle_message(msg):
    logger.debug(f'收到消息: {msg}')
    # 简单回显消息
    socketio.emit('message', msg, namespace='/')

# 处理音乐播放事件
@socketio.on('music_play')
def handle_music_play(data):
    logger.debug(f'收到音乐播放事件: {data}')
    # 广播音乐播放状态给其他用户，跳过发送者
    socketio.emit('music_sync', data, namespace='/', skip_sid=request.sid)

# 添加@指令处理功能
@socketio.on('at_command')
def handle_at_command(data):
    import random
    logger.debug(f"收到@指令: {data}")
    command = data.get('command', '').lower()
    result = {}
    
    # 处理天气查询
    if command.startswith('天气'):
        city = command.replace('天气', '').strip() or '北京'
        result = {
            'type': 'weather',
            'city': city,
            'temperature': random.randint(10, 35),
            'condition': random.choice(['晴', '多云', '阴', '小雨', '大雨'])
        }
    # 处理电影推荐
    elif command.startswith('电影'):
        result = {
            'type': 'movie',
            'movies': [
                '肖申克的救赎',
                '阿甘正传',
                '泰坦尼克号',
                '盗梦空间',
                '星际穿越'
            ]
        }
    # 处理音乐播放
    elif command.startswith('音乐'):
        music_name = command.replace('音乐', '').strip() or '默认音乐'
        result = {
            'type': 'music',
            'name': music_name,
            'artist': '测试艺术家',
            'url': '#',
            'duration': random.randint(120, 300)
        }
    # 处理新闻查询
    elif command.startswith('新闻'):
        result = {
            'type': 'news',
            'articles': [
                {'title': '测试新闻1', 'content': '这是一条测试新闻内容'}, 
                {'title': '测试新闻2', 'content': '这是另一条测试新闻内容'}
            ]
        }
    # 未知命令
    else:
        result = {
            'type': 'error',
            'message': '未知命令，请尝试 @天气、@电影、@音乐 或 @新闻'
        }
    
    # 发送命令执行结果给客户端
    logger.debug(f'发送@指令结果: {result}')
    emit('at_command_result', result)

if __name__ == '__main__':
      logger.info('服务器启动中...')
      # 使用SocketIO运行应用，使用不同的端口避免冲突
      socketio.run(app, host='0.0.0.0', port=5005, debug=True, use_reloader=False)
