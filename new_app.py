import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import json
import re
import os
import random
import requests

# 初始化应用
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
users = {}
system_users = {'萝卜子'}
room = 'main_room'
user_ai_conversation = {}

# 用户数据管理
def load_users():
    global users
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                users = json.load(f)
        print("用户数据加载成功")
    except Exception as e:
        print(f"加载用户数据失败: {e}")
        users = {}

def save_users():
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存用户数据失败: {e}")

# 生成AI回复的函数
def generate_ai_response(question):
    # 简单的关键词匹配系统
    keywords = {
        'hello': ['你好！', '嗨！', '你好，有什么可以帮助你的吗？'],
        'hi': ['你好！', '嗨！', '你好，有什么可以帮助你的吗？'],
        '你好': ['你好！', '嗨！', '你好，有什么可以帮助你的吗？'],
        '谢谢': ['不客气！', '很高兴能帮到你！', '随时为你服务！'],
        '帮助': ['我可以帮你回答问题、提供信息，或者只是聊天。请告诉我你需要什么帮助？']
    }
    
    # 搜索关键词
    question_lower = question.lower()
    for key, responses in keywords.items():
        if key in question_lower:
            return random.choice(responses)
    
    # 根据问题长度选择更合适的回复
    if len(question) > 20:
        detailed_responses = [
            "这是一个很详细的问题，让我仔细思考一下...",
            "感谢你的详细提问，我来为你解答。",
            "你提出了一个很好的问题，我会尽力回答。"
        ]
        return random.choice(detailed_responses)
    
    # 默认回复
    responses = [
        "我理解你的意思。",
        "这个问题很有趣！",
        "让我思考一下...",
        "你说得对！",
        "我明白你的感受。"
    ]
    
    # 返回随机回复
    return random.choice(responses)

# @功能指令处理函数
@socketio.on('at_command')
def handle_at_command(data):
    # 这里可以处理特殊的@指令
    pass

# SocketIO事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')
    # 从用户列表中移除断开连接的用户
    for username, sid in users.items():
        if sid == request.sid:
            del users[username]
            save_users()
            update_user_list()
            break

@socketio.on('join')
def handle_join(data):
    username = data['username']
    if username not in users:
        users[username] = request.sid
        save_users()
        join_room(room)
        update_user_list()
        # 发送欢迎消息
        emit('message', {
            'username': '系统',
            'message': f'欢迎 {username} 加入聊天室！',
            'type': 'system'
        }, room=room)

@socketio.on('message')
def handle_message(data):
    username = data['username']
    message = data['message']
    
    # 如果是AI用户（萝卜子）发送的消息
    if username in system_users:
        emit('message', {
            'username': username,
            'message': message,
            'type': 'system'
        }, room=room)
    else:
        # 普通用户消息
        emit('message', {
            'username': username,
            'message': message,
            'type': 'user'
        }, room=room)
        
        # 如果消息中提到了萝卜子或使用了@功能，生成AI回复
        if '萝卜子' in message or '@萝卜子' in message:
            # 提取真正的问题（去掉@萝卜子部分）
            question = re.sub(r'@?萝卜子', '', message).strip()
            if not question:
                question = "你好"
            
            # 生成AI回复
            ai_response = generate_ai_response(question)
            
            # 发送AI回复
            emit('message', {
                'username': '萝卜子',
                'message': ai_response,
                'type': 'system'
            }, room=room)

def update_user_list():
    # 更新用户列表
    emit('user_list', {'users': list(users.keys())}, room=room)

# Flask路由
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if username in users:
        return jsonify({'available': False})
    return jsonify({'available': True})

# 主函数
if __name__ == '__main__':
    # 加载用户数据
    load_users()
    # 启动应用
    print("服务器启动中...")
    print("访问 http://localhost:9999 开始聊天")
    socketio.run(app, host='0.0.0.0', port=9999, debug=True, use_reloader=False)
