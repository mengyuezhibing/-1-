# 使用threading模式替代eventlet以提高稳定性
from flask import Flask, render_template, request, jsonify, redirect, session
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import json
import re
import os
import random
import requests
import hashlib
import datetime

# 尝试导入OpenAI库（用于兼容其他AI API服务）
openai = None
try:
    import openai as openai_lib
    # 保存导入的库到变量
    openai = openai_lib
    # 设置API密钥
    openai.api_key = "sk-cpgqvljyhmugkkdtobnhurrxcenarmrvygfflwqzexgryjkm"
    # 可以选择设置API基础URL（如果使用其他AI服务）
    # openai.api_base = "https://api.example.com/v1"
    print("AI库导入成功并设置了API密钥")
except Exception as e:
    print(f"导入或配置AI库失败: {str(e)}")

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
# 为了安全，设置session密钥
app.config['SESSION_TYPE'] = 'filesystem'
# 会话安全配置
app.config['SESSION_COOKIE_SECURE'] = False  # 在生产环境中应设为True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)  # 会话超时设置为30分钟
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 确保导入所需的装饰器
from functools import wraps

# 用户数据库 - 实际项目中应使用真正的数据库
user_database = {}
# 存储在线用户信息
users = {}
# 存储系统用户（常驻在线）
system_users = {'萝卜子'}
room = 'main_room'
# 存储用户与AI的对话状态，记录哪些用户已经@过萝卜子
user_ai_conversation = {}
# 在线用户存储
online_users = {}

# 会话超时检查函数
def check_session_timeout():
    """检查会话是否已超时"""
    if 'username' in session and 'created_at' in session:
        try:
            created_at = datetime.datetime.fromisoformat(session['created_at'])
            if datetime.datetime.now() - created_at > app.config['PERMANENT_SESSION_LIFETIME']:
                # 会话已超时
                username = session.pop('username', '未知用户')
                session.pop('created_at', None)
                # 更新用户状态
                if username in user_database:
                    user_database[username]['status'] = 'offline'
                    save_users()
                print(f"用户 {username} 会话已超时")
                return True  # 已超时
        except:
            pass
    return False  # 未超时

# 验证用户是否已登录的装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        # 检查会话是否超时
        if check_session_timeout():
            return redirect('/login?error=会话已超时，请重新登录')
        return f(*args, **kwargs)
    return decorated_function

# 哈希密码函数
def hash_password(password):
    """对密码进行MD5哈希处理"""
    return hashlib.md5(password.encode()).hexdigest()

# 检查用户名是否存在
def is_username_exists(username):
    return username in user_database

# 验证用户凭据
def authenticate_user(username, password):
    if username not in user_database:
        return False
    return user_database[username]['password'] == hash_password(password)

# 加载用户数据
def load_users():
    global user_database
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                user_database = json.load(f)
                print(f"成功加载用户数据，共 {len(user_database)} 个用户")
    except json.JSONDecodeError as e:
        print(f"解析用户数据文件失败: {e}")
        user_database = {}
    except FileNotFoundError:
        print("用户数据文件不存在，创建新的数据库")
        user_database = {}
    except Exception as e:
        print(f"加载用户数据失败: {e}")
        user_database = {}

# 保存用户数据
def save_users():
    global user_database
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname('users.json') or '.', exist_ok=True)
        # 保存用户数据
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(user_database, f, ensure_ascii=False, indent=4)
        print(f"成功保存用户数据，共 {len(user_database)} 个用户")
        return True
    except Exception as e:
        print(f"保存用户数据失败: {e}")
        # 尝试创建一个备份
        try:
            backup_path = 'users_backup.json'
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(user_database, f, ensure_ascii=False, indent=4)
            print(f"已创建用户数据备份到 {backup_path}")
        except:
            pass
        return False

# 不使用新的客户端类，而是使用传统的API调用方式
client = None

# 同步网络搜索函数（将被异步调用）
def _sync_search_web(query):
    """使用网络搜索获取相关信息（同步版本）"""
    try:
        # 使用DuckDuckGo搜索API（无需API密钥）
        search_url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1
        }
        response = requests.get(search_url, params=params, timeout=5)  # 保持5秒超时
        response.raise_for_status()
        data = response.json()
        
        # 判断是否是专门查询网站或URL的请求
        is_url_query = any(keyword in query for keyword in ['官网', '网站', '网址', '链接', 'URL', '官网地址'])
        
        # 收集搜索结果
        search_results = []
        urls_collected = []  # 存储收集到的URL
        
        # 添加Abstract内容（如果有）
        if 'AbstractText' in data and data['AbstractText']:
            abstract_info = f"摘要: {data['AbstractText']}"
            # 只有在明确查询URL或摘要内容很重要时才添加URL
            if 'AbstractURL' in data and data['AbstractURL']:
                abstract_url = data['AbstractURL']
                urls_collected.append(abstract_url)
                # 如果是专门查询URL的请求，直接显示URL
                if is_url_query:
                    abstract_info += f"\n直达链接: {abstract_url}"
            search_results.append(abstract_info)
        
        # 添加RelatedTopics（如果有）
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics']:
                # 处理直接的topic项
                if 'Text' in topic and topic['Text']:
                    topic_info = topic['Text']
                    # 收集URL但不自动添加到每个结果中
                    if 'FirstURL' in topic and topic['FirstURL']:
                        first_url = topic['FirstURL']
                        # 确保URL是直达链接，不是中间页
                        if 'duckduckgo.com' not in first_url:
                            urls_collected.append(first_url)
                    search_results.append(topic_info)
                # 处理嵌套的Topics数组
                if 'Topics' in topic:
                    for sub_topic in topic['Topics']:
                        if 'Text' in sub_topic and sub_topic['Text']:
                            sub_topic_info = sub_topic['Text']
                            # 收集URL但不自动添加到每个结果中
                            if 'FirstURL' in sub_topic and sub_topic['FirstURL']:
                                first_url = sub_topic['FirstURL']
                                # 确保URL是直达链接，不是中间页
                                if 'duckduckgo.com' not in first_url:
                                    urls_collected.append(first_url)
                            search_results.append(sub_topic_info)
        
        # 去重URL列表
        unique_urls = list(dict.fromkeys(urls_collected))
        
        # 如果是专门查询URL的请求且收集到了URL，添加URL部分
        if is_url_query and unique_urls:
            # 添加标题提示
            search_results.append("\n找到的相关直达链接:")
            # 添加每个URL
            for url in unique_urls[:3]:  # 最多显示3个直达链接
                search_results.append(f"- {url}")
        
        # 如果没有获取到任何搜索结果
        if not search_results:
            if is_url_query:
                # 对于URL查询，说明未找到直达链接
                return "抱歉，未能找到相关的官方网站或直达链接。请尝试使用其他关键词重新查询。"
            else:
                # 对于普通查询，说明未找到相关信息
                return "抱歉，未能找到与你的问题相关的详细信息。请尝试使用其他关键词重新查询。"
        
        # 限制返回的结果数量
        return "\n\n".join(search_results[:5])  # 保持最多5条结果
    except Exception as e:
        print(f"网络搜索失败: {str(e)}")
        # 出错时提供友好的错误信息，不再直接提供搜索链接
        return "抱歉，在获取信息时遇到了一些技术问题。请稍后再试，或者尝试使用其他关键词重新查询。"

# 网络搜索函数（异步版本）
def search_web(query):
    """异步使用网络搜索获取相关信息"""
    try:
        # 使用eventlet.spawn异步执行网络请求
        greenlet = eventlet.spawn(_sync_search_web, query)
        # 等待执行完成并获取结果，设置超时时间
        return greenlet.wait(timeout=8)  # 增加超时时间到8秒，给网络请求足够的完成时间
    except eventlet.timeout.Timeout:
        print("网络搜索超时")
        # 超时也提供DuckDuckGo搜索链接作为备选
        duckduckgo_search_link = f"https://duckduckgo.com/?q={requests.utils.quote(query)}"
        return f"搜索超时，但你可以访问以下链接查看搜索结果：\n{duckduckgo_search_link}"
    except Exception as e:
        print(f"异步搜索处理失败: {str(e)}")
        # 出错时也提供DuckDuckGo搜索链接作为备选
        duckduckgo_search_link = f"https://duckduckgo.com/?q={requests.utils.quote(query)}"
        return f"处理搜索请求时出错，但你可以访问以下链接查看搜索结果：\n{duckduckgo_search_link}"

import socket

# 从配置文件读取服务器列表并添加本机局域网IP
def get_servers(flatten=True):
    # 获取本机局域网IP地址
    def get_local_ip():
        try:
            # 创建一个UDP套接字连接到外部地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return '127.0.0.1'
    
    local_ip = get_local_ip()
    # 创建本机服务器条目
    local_servers_entries = [
        {'name': '本机IP', 'url': f'http://{local_ip}:5000'},
        {'name': '本地主机', 'url': 'http://localhost:5000'}
    ]
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 获取配置文件中的服务器，默认为空对象
            servers = config.get('servers', {})
            
            # 创建完整的分类服务器列表
            categorized_servers = {}
            
            # 确保'本地'分类存在并包含本地服务器
            categorized_servers['本地'] = local_servers_entries.copy()
            
            # 添加配置文件中的所有分类
            for category, server_list in servers.items():
                if category not in categorized_servers:
                    categorized_servers[category] = []
                # 避免重复添加本地服务器
                for server in server_list:
                    # 检查是否是本地服务器（通过URL匹配）
                    is_local = False
                    for local_server in local_servers_entries:
                        if server['url'] == local_server['url']:
                            is_local = True
                            break
                    if not is_local:
                        categorized_servers[category].append(server)
            
            # 如果需要扁平列表（用于兼容旧代码）
            if flatten:
                flat_servers = []
                for category, server_list in categorized_servers.items():
                    for server in server_list:
                        flat_servers.append(server['url'])
                return flat_servers
            
            # 否则返回分类结构
            return categorized_servers
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        # 出错时，根据flatten参数返回适当的结构
        if flatten:
            return [server['url'] for server in local_servers_entries]
        else:
            return {'本地': local_servers_entries}



# 配置管理页面
@app.route('/config')
def config_page():
    return render_template('config_form.html')

# API: 获取配置
@app.route('/api/get_config', methods=['GET'])
def api_get_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        print(f"读取配置失败: {str(e)}")
        return jsonify({'servers': []}), 500

# API: 保存配置
@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    try:
        data = request.json
        if not data or 'servers' not in data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
        
        # 验证所有URL格式（支持分类结构）
        servers = data['servers']
        if isinstance(servers, dict):
            # 验证分类结构的配置
            for category, server_list in servers.items():
                for server in server_list:
                    if not isinstance(server, dict) or 'url' not in server:
                        return jsonify({'success': False, 'message': f'无效的服务器配置格式: {server}'})
                    # 支持http、https、tcp协议
                    if not re.match(r'^(https?|tcp):\/\/', server['url'], re.IGNORECASE):
                        return jsonify({'success': False, 'message': f'无效的URL格式: {server["url"]}'})
        
        # 保存配置到文件
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return jsonify({'success': True, 'message': '配置已保存'})
    except Exception as e:
        print(f"保存配置失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            # 增强验证
            if not username or not password or not confirm_password:
                return render_template('register.html', error='所有字段都不能为空')
            
            if len(username) < 3 or len(username) > 20:
                return render_template('register.html', error='用户名长度应为3-20个字符')
            
            if len(password) < 6:
                return render_template('register.html', error='密码长度至少为6个字符')
            
            if password != confirm_password:
                return render_template('register.html', error='两次输入的密码不一致')
            
            # 检查特殊字符
            if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
                return render_template('register.html', error='用户名只能包含字母、数字、下划线和中文字符')
            
            if is_username_exists(username):
                return render_template('register.html', error='用户名已存在')
            
            # 创建用户
            user_database[username] = {
                'password': hash_password(password),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None,
                'status': 'active'
            }
            
            # 保存用户数据到文件
            if save_users():
                print(f"新用户 {username} 注册成功并已保存")
                return redirect('/login?registered=True')
            else:
                # 保存失败，从内存中移除用户
                if username in user_database:
                    del user_database[username]
                return render_template('register.html', error='注册失败，数据保存出错，请稍后重试')
        except Exception as e:
            print(f"注册过程中发生错误: {str(e)}")
            return render_template('register.html', error='注册过程中发生错误，请稍后重试')
    
    # 处理GET请求，检查是否有初始错误信息
    error = request.args.get('error')
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # 处理登录表单提交
            username = request.form.get('username')
            password = request.form.get('password')
            
            # 验证输入
            if not username or not password:
                return jsonify({'success': False, 'message': '用户名和密码不能为空'})
            
            # 验证用户凭据
            if authenticate_user(username, password):
                # 登录成功，更新用户信息
                if username in user_database:
                    user_database[username]['last_login'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    user_database[username]['status'] = 'online'  # 更新用户状态为在线
                    # 保存更新后的用户数据
                    save_users()
                
                # 设置会话
                session.permanent = True  # 设置为永久会话（受lifetime限制）
                session['username'] = username
                session['created_at'] = datetime.datetime.now().isoformat()  # 记录会话创建时间
                print(f"用户 {username} 登录成功")
                return jsonify({'success': True})
            else:
                # 登录失败
                print(f"用户 {username} 登录失败：用户名或密码错误")
                return jsonify({'success': False, 'message': '用户名或密码错误'})
        except Exception as e:
            print(f"登录过程中发生错误: {str(e)}")
            return jsonify({'success': False, 'message': '登录过程中发生错误，请稍后重试'})
    
    # GET请求，显示登录页面
    registered = request.args.get('registered', False)
    error = request.args.get('error')
    info = request.args.get('info')
    # 获取分类的服务器列表，用于登录页面的分组显示
    servers = get_servers(flatten=False)
    return render_template('login.html', servers=servers, registered=registered, error=error, info=info)

@app.route('/logout')
def logout():
    """处理用户注销"""
    username = session.pop('username', None)
    session.pop('created_at', None)
    
    # 更新用户状态为离线
    if username and username in user_database:
        user_database[username]['status'] = 'offline'
        save_users()
        print(f"用户 {username} 已注销")
    
    # 重定向到登录页面
    return redirect('/login?info=您已成功注销')

@app.route('/chat')
@login_required
def chat():
    # 从会话中获取用户名
    username = session.get('username')
    
    # 更新会话最后活动时间
    session['last_activity'] = datetime.datetime.now().isoformat()
    
    # 获取可用的服务器列表
    servers = get_servers()
    
    # 确保用户状态为在线
    if username in user_database:
        user_database[username]['status'] = 'online'
        save_users()
    
    # 渲染聊天页面
    return render_template('chat.html', username=username, servers=servers)

# 全局错误处理
@app.errorhandler(404)
def page_not_found(e):
    """处理404页面未找到错误"""
    return render_template('error.html', error_code=404, error_message='抱歉，您请求的页面不存在'), 404

@app.errorhandler(403)
def forbidden(e):
    """处理403权限错误"""
    return render_template('error.html', error_code=403, error_message='您没有权限访问此页面'), 403

@app.errorhandler(500)
def internal_server_error(e):
    """处理500服务器内部错误"""
    print(f"服务器内部错误: {str(e)}")
    return render_template('error.html', error_code=500, error_message='服务器内部错误，请稍后重试'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """捕获所有其他未处理的异常"""
    print(f"未处理的异常: {str(e)}")
    if request.is_json:
        return jsonify({'success': False, 'message': '服务器错误，请稍后重试'}), 500
    return render_template('error.html', error_code=500, error_message='服务器错误，请稍后重试'), 500

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if is_username_exists(username):
        return jsonify({'valid': False})
    return jsonify({'valid': True})

@socketio.on('connect')
def handle_connect():
    """处理客户端连接，添加会话检查和错误处理"""
    sid = request.sid
    print(f'客户端连接: {sid}')
    
    try:
        # 检查会话是否已登录
        username = session.get('username')
        if username:
            # 验证用户是否存在于数据库中
            if username in user_database:
                users[sid] = username
                user_database[username]['status'] = 'online'
                save_users()
                print(f'用户 {username} 已连接')
                # 通知所有用户有人上线
                socketio.emit('user_status_change', {'username': username, 'status': 'online'})
                update_user_list()
            else:
                print(f'警告: 连接的用户 {username} 不存在于数据库中')
                emit('error', {'message': '用户信息无效，请重新登录'})
        else:
            print('未登录的客户端连接')
    except Exception as e:
        print(f'处理连接时发生错误: {str(e)}')
        emit('error', {'message': '连接建立失败，请稍后重试'})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接，更新用户状态"""
    sid = request.sid
    try:
        if sid in users:
            username = users[sid]
            # 移除用户关联
            del users[sid]
            print(f'用户 {username} 断开连接')
            
            # 更新用户状态为离线
            if username in user_database:
                user_database[username]['status'] = 'offline'
                save_users()
                # 通知所有用户有人下线
                socketio.emit('user_status_change', {'username': username, 'status': 'offline'})
                update_user_list()
    except Exception as e:
        print(f'处理断开连接时发生错误: {str(e)}')

@socketio.on('join')
def handle_join(data):
    """处理用户加入房间，添加错误处理和用户验证"""
    try:
        sid = request.sid
        username = data.get('username')
        
        if not username:
            emit('error', {'message': '用户名不能为空'})
            return
        
        # 验证用户名是否存在
        if not is_username_exists(username):
            emit('error', {'message': '用户不存在，请先注册'})
            return
        
        # 验证会话中的用户名是否与请求的用户名一致
        session_username = session.get('username')
        if session_username and session_username != username:
            emit('error', {'message': '用户名不匹配，请重新登录'})
            return
        
        # 记录用户信息
        users[sid] = username
        if username not in online_users:
            online_users[username] = sid
            
        # 为用户分配头像（如果还没有的话）
        if username not in user_avatars:
            user_avatars[username] = get_user_avatar()
        
        # 加入主房间
        join_room(room)
        
        # 更新用户状态为在线
        if username in user_database:
            user_database[username]['status'] = 'online'
            save_users()
        
        # 广播用户加入消息
        join_message = {
            'username': username,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'{username} 加入了聊天室'
        }
        socketio.emit('user_joined', join_message, room=room)
        
        # 通知用户自己加入成功
        emit('join_success', {'username': username})
        
        # 更新用户列表
        update_user_list()
        
        # 发送欢迎消息给新加入的用户
        welcome_message = {
            'username': '萝卜子',
            'message': f'欢迎 {username} 加入聊天室！',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        emit('welcome_message', welcome_message)
        
        print(f"用户 {username} 上线")
    except Exception as e:
        print(f'处理加入房间时发生错误: {str(e)}')
        emit('error', {'message': '加入房间失败，请稍后重试'})

def update_user_list():
    """更新并广播房间中的用户列表"""
    # 获取普通用户列表

def update_user_list():
    """更新并广播房间中的用户列表"""
    # 获取普通用户列表
    normal_users = list(online_users.keys())
    # 获取系统用户列表
    all_users = normal_users + list(system_users)
    
    # 构建用户列表数据
    user_list_data = {
        'users': all_users,
        'online_count': len(normal_users),
        'total_count': len(all_users),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_avatars': user_avatars,  # 发送所有用户的头像信息
        'wallpaper': get_wallpaper()  # 发送随机壁纸
    }
    
    # 广播用户列表更新
    socketio.emit('update_users', user_list_data, room=room)
    print(f"更新用户列表: {all_users}")

@socketio.on('music_play')
def handle_music_play(data):
    """处理音乐播放同步事件"""
    try:
        # 获取当前用户
        username = users.get(request.sid, '未知用户')
        
        # 验证数据
        if not data or 'music' not in data or 'status' not in data:
            print("音乐播放事件数据不完整")
            return
        
        # 准备广播数据
        broadcast_data = {
            'music': data['music'],
            'status': data['status'],
            'played_by': username,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 广播给房间内除当前用户外的所有用户
        emit('music_sync', broadcast_data, room=room, skip_sid=request.sid)
        
        print(f"用户 {username} 触发音乐 {data['status']} 同步: {data['music'].get('title', '未知歌曲')}")
        
    except Exception as e:
        # 处理异常
        print(f"处理音乐播放同步时发生错误: {str(e)}")
        # 向当前用户发送错误消息
        emit('error', {'message': f'音乐同步失败: {str(e)}'})

@socketio.on('message')
def handle_message(data):
    # 调试日志
    debug_log(f"收到消息: {data}")
    
    username = data['username']
    message = data['message']
    
    debug_log(f"用户: {username}, 消息内容: {message}")
    
    # 检查用户是否在线
    if username not in online_users:
        debug_log(f"用户 {username} 未在线")
        emit('error', {'message': '用户未上线'})
        return
    
    # 检查是否包含@指令，优先处理具体功能指令
    if '@天气' in message or '@新闻' in message or '@音乐' in message or '@img' in message or '@新闻60s' in message:
        # 提取指令和参数
        at_match = re.match(r'@([\u4e00-\u9fa5a-zA-Z0-9]+)\s*(.*)', message.strip())
        if at_match:
            command = at_match.group(1)
            params = at_match.group(2).strip()
            
            debug_log(f"检测到功能@指令: {command}, 参数: {params}")
            
            # 广播原始消息
            debug_log("广播原始消息到房间")
            emit('message', {
                'username': username,
                'message': message
            }, room=room)
            
            # 处理指令
            debug_log("处理@指令")
            result = None
            
            # 根据命令类型处理
            if command == '天气':
                debug_log(f"处理天气命令，参数: {params}")
                result = get_weather(params)
                debug_log(f"天气数据返回: {result}")
            elif command == '新闻':
                debug_log(f"处理新闻命令，参数: {params}")
                result = get_news(params)
                debug_log(f"新闻数据返回: {result}")
            elif command == '音乐':
                debug_log(f"处理音乐命令，参数: {params}")
                result = get_music(params)
                debug_log(f"音乐数据返回: {result}")
                # 广播音乐开始播放的事件给所有人，实现同步播放
                debug_log(f"广播音乐播放事件给房间: {room}")
                socketio.emit('music_playing', {
                    'music': result,
                    'played_by': username
                }, room=room)
            elif command == '新闻60s':
                debug_log(f"处理新闻60s命令")
                result = get_hot60s()
                debug_log(f"新闻60s数据返回: {result}")
            elif command == 'img':
                debug_log(f"处理图片命令，参数: {params}")
                result = get_image(params)
                debug_log(f"图片数据返回: {result}")
            
            # 确保只发送一次命令结果给客户端
            if result is not None:
                # 音乐命令已经通过music_playing事件处理，不需要再发送at_command_result事件
                if command != '音乐':
                    debug_log(f"发送命令结果给客户端: {command} - {result}")
                    # 使用emit而不是socketio.emit来避免全局广播导致的重复
                    emit('at_command_result', {
                        'command': command,
                        'result': result
                    })
                else:
                    debug_log("音乐命令已通过music_playing事件处理，跳过at_command_result事件")
            
            # 直接返回，避免继续处理
            return
    
    # 特殊处理@萝卜子命令，AI对话功能
    if '@萝卜子' in message or username in user_ai_conversation:
        # 首先广播用户的原始消息
        debug_log("广播用户消息到房间")
        emit('message', {
            'username': username,
            'message': message
        }, room=room)
        
        debug_log("用户处于AI对话状态或消息包含@萝卜子")
        # 提取用户的问题（如果包含@萝卜子，则去掉标记）
        question = message.replace('@萝卜子', '').strip()
        
        # 如果是第一次@萝卜子，记录用户到对话状态中
        if '@萝卜子' in message:
            user_ai_conversation[username] = True
            debug_log(f"启动AI对话，问题: {question}")
        else:
            debug_log(f"继续AI对话，问题: {question}")
        
        try:
            # 生成更详细的AI回复
            debug_log("调用generate_ai_response生成AI回复")
            ai_reply = generate_ai_response(question)
            debug_log(f"AI回复生成成功: {ai_reply}")
            
            # 以"萝卜子"的身份发送回复
            debug_log("发送AI回复到聊天室")
            emit('message', {
                'username': '萝卜子',
                'message': ai_reply,
                'avatar': '/static/images/luobzi.svg'  # 使用萝卜子的固定头像
            }, room=room)
        except Exception as e:
            error_msg = f"处理AI回复时出错: {str(e)}"
            debug_log(error_msg)
            # 出错时也发送一个基本回复，确保用户收到响应
            emit('message', {
                'username': '萝卜子',
                'message': '抱歉，我刚才处理你的请求时遇到了一些问题。请再试一次。'
            }, room=room)
        
        # 直接返回，避免重复处理
        return
    
    # 检查是否是@电影命令（前端会处理，单独优先检查）
    if '@电影' in message:
        debug_log("检测到@电影命令，交由前端处理")
        # 广播原始消息
        emit('message', {
            'username': username,
            'message': message
        }, room=room)
        # 对于@电影命令，前端会处理，后端不需要额外操作
        return
    
    # 广播普通消息给房间内所有人
    debug_log("广播普通消息到房间")
    emit('message', {
        'username': username,
        'message': message,
        'avatar': user_avatars.get(username, '')
    }, room=room)

def generate_ai_response(question):
    """尝试使用AI API生成回复，如果失败则使用增强的模拟回复，同时集成网络搜索功能"""
    # 判断是否需要进行网络搜索的关键词
    search_keywords = [
        '什么', '哪个', '哪里', '如何', '怎样', '为什么', '何时', '是多少', 
        '最新', '现在', '今天', '最近', '2024', '2025',
        '是什么', '什么是', '有哪些', '包括哪些',
        '为什么', '原因', '介绍', '解释', '定义', '含义',
        '2023', '2024', '2025', '时间', '日期', '地点',
        '哪里', '哪里有', '怎么去', '路线', '地址',
        '价格', '多少钱', '费用', '成本', '花费',
        '历史', '由来', '起源', '发展', '演变',
        '区别', '比较', '对比', '不同', '差异',
        '功能', '特点', '特性', '优势', '劣势',
        '方法', '步骤', '教程', '攻略', '指南',
        '推荐', '建议', '意见', '评价', '看法',
        '问题', '解决', '修复', '处理', '应对',
        '新闻', '资讯', '动态', '消息', '报道'
        # URL相关关键词不再包含在这里，单独处理
    ]
    
    # 检查问题是否包含搜索关键词，需要实时信息的问题优先进行网络搜索
    should_search = any(keyword in question for keyword in search_keywords)
    
    # 获取网络搜索结果（如果需要）
    search_info = ""
    if should_search:
        print(f"正在搜索网络信息: {question}")
        search_info = search_web(question)
        print(f"搜索结果: {search_info}")
    
    # 首先尝试使用OpenAI API
    try:
        # 检查OpenAI库是否已成功导入
        if openai is not None:
            # 构建消息，包含网络搜索结果（如果有）
            messages = [
                {
                    "role": "system",
                    "content": "你是萝卜子，一个友好可爱的AI助手。请用详细、友好的语言回答用户问题，提供丰富的信息和有用的建议。如果有网络搜索结果，请基于这些信息来回答。回答内容要充实，不要太简短，确保用户能够获得有价值的回应。如果问题中包含URL或需要提供链接，请直接在回答中包含相关网址。"
                }
            ]
            
            # 如果有搜索结果，添加到用户消息中
            if search_info and search_info != "无法获取网络信息":
                user_content = f"问题: {question}\n\n网络搜索结果:\n{search_info}\n\n请基于以上信息回答问题。"
            else:
                user_content = question
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # 使用兼容的AI API调用方式，并添加超时控制
            with eventlet.timeout.Timeout(8):  # 设置8秒超时
                # 尝试使用ChatCompletion接口（兼容多种AI服务）
                response = openai.ChatCompletion.create(
                    # 使用通用模型名称，大多数兼容服务都支持
                    model="gpt-3.5-turbo",  # 或根据实际服务要求修改为其他模型
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500  # 增加最大token数，允许更长的回复
                )
            
            # 提取生成的回复内容
            ai_response = response.choices[0].message.content.strip()
            
            # 如果进行了网络搜索，可以在回复中提及
            if should_search and search_info != "无法获取网络信息":
                return f"我刚刚查询了相关信息，为你整理如下：\n\n{ai_response}"
            return ai_response
    except Exception as e:
        print(f"AI API调用失败: {str(e)}")
    
    # 如果API调用失败，使用增强的模拟回复作为备用，同时利用网络搜索结果（如果有）
    
    # 如果有网络搜索结果，将其整合到模拟回复中
    if should_search and search_info and search_info != "无法获取网络信息":
        search_responses = [
            f"根据我查到的信息：\n{search_info}\n\n希望这些信息对你有帮助！如果你需要更详细的解释，随时告诉我。",
            f"我刚刚搜索了相关内容，发现：\n{search_info}\n\n这些是目前的最新信息，希望能解答你的问题。",
            f"通过查询，我找到了以下信息：\n{search_info}\n\n这应该能帮助你了解相关情况。还有其他问题吗？"
        ]
        return random.choice(search_responses)
    
    # 检查是否包含URL或需要网址的问题
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    contains_url = bool(url_pattern.search(question))
    
    # 尝试识别是否是询问网站或URL的请求
    url_keywords = ['官网', '网站', '网址', '链接', 'URL', '官网地址']
    is_url_query = any(keyword in question for keyword in url_keywords)
    website_name = None
    
    if contains_url:
        # 提取URL
        urls = url_pattern.findall(question)
        return f"我注意到你分享了链接。以下是你提到的网址：\n\n{chr(10).join(urls)}\n\n这些链接看起来很有趣！你想了解关于这些网站的什么信息呢？或者你想让我搜索这些网站的相关内容？"
    
    if is_url_query:
        # 关于网址的问题，增强网站名称识别能力
        # 模式1: 直接匹配 "XX官网" 或 "XX网站" 格式
        direct_pattern = re.compile(r'([一-龥\w]+)(官网|网站|网址|链接)', re.IGNORECASE)
        direct_match = direct_pattern.search(question)
        
        # 模式2: 匹配 "XX的官网" 或 "XX的网站" 格式
        with_de_pattern = re.compile(r'([一-龥\w]+)(?:的|是)(官网|网站|网址|链接)', re.IGNORECASE)
        de_match = with_de_pattern.search(question)
        
        # 模式3: 匹配 "查找XX"、"搜索XX" 等格式
        search_pattern = re.compile(r'(?:查找|搜索|查询|了解|获取)([一-龥\w]+)', re.IGNORECASE)
        search_match = search_pattern.search(question)
        
        # 确定网站名称
        if direct_match:
            website_name = direct_match.group(1)
        elif de_match:
            website_name = de_match.group(1)
        elif search_match:
            website_name = search_match.group(1)
        
        # 如果识别出网站名称且是URL查询，专门搜索其官网
        if website_name:
            print(f"正在搜索网站信息: {website_name}")
            # 增强搜索查询，使用更精确的关键词组合
            search_query = f"{website_name} 官方网站 官网 网址 链接 官网地址"
            search_info = search_web(search_query)
            # 不再额外添加链接提示，因为_sync_search_web函数会根据查询类型自动处理
            return f"我为您搜索到了关于{website_name}的官网信息：\n\n{search_info}"
        
        # 通用的网址回答
        return "关于网址的问题，我可以帮你查找各种网站的链接！\n1. 你可以直接告诉我网站名称，比如'百度官网'或'淘宝官网'\n2. 也可以询问特定类型的网站，比如'新闻网站推荐'或'学习编程的网站'\n3. 我会为你搜索最新的官方网址和相关信息\n\n请告诉我你想查找什么网站的链接？"
    
    # 返回随机回复
    return random.choice(responses)

# @功能指令处理函数（保留作为socket事件处理器，以防前端直接发送at_command事件）
@socketio.on('at_command')
def handle_at_command(data):
    """处理@指令socket事件，作为备用处理器"""
    # 调试日志
    debug_log(f"收到at_command socket事件: {data}")
    
    # 提取必要的参数
    command = data.get('command')
    params = data.get('params', '')
    username = data.get('username', 'system')
    
    debug_log(f"命令: {command}, 参数: {params}, 用户名: {username}")
    
    # 初始化结果变量
    result = None
    
    # 根据命令类型处理
    if command == '天气':
        debug_log(f"处理天气命令，参数: {params}")
        result = get_weather(params)
        debug_log(f"天气数据返回: {result}")
    elif command == '新闻':
        debug_log(f"处理新闻命令，参数: {params}")
        result = get_news(params)
        debug_log(f"新闻数据返回: {result}")
    elif command == '音乐':
        debug_log(f"处理音乐命令，参数: {params}")
        result = get_music(params)
        debug_log(f"音乐数据返回: {result}")
        # 注意：音乐播放事件已经在handle_message中处理，这里不再重复发送
    else:
        debug_log(f"未知命令: {command}")
        result = f"未知的@命令: @{command}"
    
    # 只发送一次命令结果给客户端
    debug_log(f"发送命令结果给客户端: {command} - {result}")
    socketio.emit('at_command_result', {
        'command': command,
        'result': result
    }, room=room)

def get_weather(city):
    """
    获取天气信息
    使用真实的天气API并处理Key参数
    """
    if not city:
        city = '北京'
    
    try:
        # 调用真实的天气API
        url = 'https://v2.xxapi.cn/api/weatherDetails'
        # 根据API要求添加key参数
        params = {
            'key': 'free_api_key',  # 使用免费API密钥
            'city': city
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        # 检查响应状态
        if response.status_code == 200:
            data = response.json()
            debug_log(f"天气API返回: {data}")
            
            # 检查API返回结果
            if data.get('code') == -8 and '请携带Key' in data.get('msg', ''):
                print(f"天气API需要有效的key: {data.get('msg')}")
                # 即使没有key，也返回模拟数据而不是错误消息
                return get_mock_weather(city)
            elif data.get('code') == 200:
                # 处理API返回的数据
                api_data = data.get('data', {})
                # 转换为前端期望的格式
                weather_data = {
                    'city': city,
                    'main': api_data.get('weather', '未知'),
                    'temp': api_data.get('temperature', 25),
                    'description': api_data.get('desc', '天气状况良好'),
                    'humidity': api_data.get('humidity', 60),
                    'wind_speed': api_data.get('wind_speed', 3.5)
                }
                return weather_data
            else:
                # API返回错误
                error_msg = data.get('msg', 'API返回错误')
                print(f"天气API错误: {error_msg}")
                # 返回模拟数据作为备选
                return get_mock_weather(city)
        else:
            # HTTP错误
            print(f"天气API HTTP错误: {response.status_code}")
            # 返回模拟数据作为备选
            return get_mock_weather(city)
    except Exception as e:
        # 捕获所有异常
        print(f"天气API调用异常: {str(e)}")
        # 返回模拟数据作为备选
        return get_mock_weather(city)

def get_mock_weather(city):
    """
    获取模拟天气数据作为备选
    """
    # 模拟天气数据
    weather_data = {
        'city': city,
        'main': '晴',
        'temp': 25,
        'description': '晴朗的一天，非常适合户外活动',
        'humidity': 60,
        'wind_speed': 3.5
    }
    
    # 模拟不同城市的天气
    city_weather = {
        '北京': {'main': '晴', 'temp': 25, 'humidity': 60},
        '上海': {'main': '多云', 'temp': 28, 'humidity': 75},
        '广州': {'main': '雨', 'temp': 30, 'humidity': 85},
        '深圳': {'main': '多云', 'temp': 29, 'humidity': 80},
        '成都': {'main': '阴', 'temp': 23, 'humidity': 70},
        '杭州': {'main': '晴', 'temp': 26, 'humidity': 65}
    }
    
    if city in city_weather:
        weather_data.update(city_weather[city])
        if weather_data['main'] == '雨':
            weather_data['description'] = '有雨，请记得带伞'
        elif weather_data['main'] == '多云':
            weather_data['description'] = '多云转晴，天气不错'
        elif weather_data['main'] == '阴':
            weather_data['description'] = '阴天，可能会下雨'
    else:
        # 对于未知城市，返回标准信息
        weather_data['description'] = '根据最新数据，当前天气状况良好'
    
    return weather_data

def get_image(keyword=''):
    """
    获取图片信息
    根据关键词返回相关图片
    """
    try:
        # 使用picsum.photos作为图片源
        # 可以根据需要添加更多图片API支持
        image_data = {
            'list': [
                {
                    'title': f'{keyword}相关图片' if keyword else '随机图片',
                    'image': f'https://picsum.photos/800/600?random={random.randint(1, 10000)}',
                    'url': ''
                }
            ]
        }
        return image_data
    except Exception as e:
        print(f"获取图片失败: {str(e)}")
        # 返回默认图片
        return {
            'list': [
                {
                    'title': '图片获取失败',
                    'image': 'https://picsum.photos/800/600',
                    'url': ''
                }
            ]
        }

def get_news(category=''):
    """
    获取新闻信息
    优先调用真实新闻API，如果失败则使用模拟数据
    确保只返回一个新闻项（包含一个图片）
    """
    try:
        # 优先调用真实新闻API获取新闻
        news_data = crawl_news(category)
        if news_data and news_data.get('list'):
            print(f"成功获取新闻API数据: {news_data['list'][0]['title']}")
            return news_data
        
        # 如果API调用失败或没有获取到有效数据，使用模拟数据
        print(f"API获取失败，使用模拟新闻数据")
        news_data = {
            'list': [
                {
                    'title': f'最新{category}新闻头条 - ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'image': 'https://picsum.photos/400/300?' + str(random.randint(1, 1000)),  # 使用picsum随机图片服务
                    'url': ''
                }
            ]
        }
        print(f"返回模拟新闻: {news_data['list'][0]['title']}")
        return news_data
    except Exception as e:
        print(f"获取新闻失败: {str(e)}")
        # 返回默认的单条新闻数据作为备份
        return {
            'list': [
                {
                    'title': f'新闻获取失败 - {category}',
                    'image': 'https://picsum.photos/400/300?' + str(random.randint(1, 1000)),
                    'url': ''
                }
            ]
        }

def crawl_news(category=''):
    """
    简单的新闻爬虫功能
    使用百度热点新闻API获取最新新闻
    """
    debug_log(f"开始爬虫获取新闻，分类: {category}")
    
    # 创建返回数据结构
    news_data = {
        'list': []
    }
    
    # 使用新的百度热点新闻API
    news_api_url = 'https://v2.xxapi.cn/api/baiduhot'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(news_api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # 处理百度热点新闻API响应
            if data.get('code') == 200 and data.get('data') and isinstance(data.get('data'), list):
                baidu_news_list = data.get('data')
                
                # 转换百度新闻数据格式为原有格式
                for news_item in baidu_news_list:
                    news = {
                        'title': news_item.get('title', '').strip() or '无标题新闻',
                        'image': news_item.get('img', '') if news_item.get('img') else '',
                        'url': news_item.get('url', '') if news_item.get('url') else ''
                    }
                    news_data['list'].append(news)
                
                # 如果有分类参数，可以在这里添加分类过滤逻辑
                # 目前百度热点API没有分类参数，所以直接返回所有热点新闻
                
                debug_log(f"爬虫成功获取百度热点新闻，共 {len(news_data['list'])} 条")
                return news_data
                
    except Exception as e:
        debug_log(f"爬取百度热点新闻失败: {str(e)}")
    
    # 如果API调用失败，返回默认新闻
    default_news = {
        'title': '最新热点新闻 - ' + category if category else '最新热点新闻',
        'image': 'https://picsum.photos/400/300',  # 使用picsum随机图片服务
        'url': ''
    }
    news_data['list'] = [default_news]
    debug_log(f"使用默认新闻: {default_news['title']}")
    
    return news_data

def get_mock_news(category=''):
    """
    获取模拟新闻数据作为备选
    确保不使用静态资源路径
    """
    # 模拟新闻数据，不使用本地静态资源路径
    news_data = {
        'list': [
            {
                'title': 'AI技术持续突破，改变各行各业发展格局',
                'image': ''  # 留空或使用在线图片服务
            },
            {
                'title': '全球气候变化加剧，各国加强环保合作',
                'image': ''
            },
            {
                'title': '科技创新推动数字经济快速发展',
                'image': ''
            },
            {
                'title': '医疗健康领域取得重大研究成果',
                'image': ''
            },
            {
                'title': '教育改革深入推进，培养创新型人才',
                'image': ''
            }
        ]
    }
    
    # 根据分类筛选新闻
    if category:
        category = category.lower()
        if category == '科技':
            news_data['list'] = [news for news in news_data['list'] if '科技' in news['title'] or 'AI' in news['title']]
        elif category == '环保':
            news_data['list'] = [news for news in news_data['list'] if '环保' in news['title'] or '气候' in news['title']]
        elif category == '医疗':
            news_data['list'] = [news for news in news_data['list'] if '医疗' in news['title'] or '健康' in news['title']]
    
    return news_data

# 当前正在播放的音乐信息
current_music = None

# 用户头像映射
user_avatars = {}

def get_user_avatar():
    """
    获取随机用户头像
    使用 https://v2.xxapi.cn/api/head API
    """
    try:
        url = 'https://v2.xxapi.cn/api/head'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', '')
    except Exception as e:
        print(f"获取用户头像失败: {str(e)}")
    return ''

def get_wallpaper():
    """
    获取随机壁纸
    使用 https://v2.xxapi.cn/api/wallpaper API
    """
    try:
        url = 'https://v2.xxapi.cn/api/wallpaper'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', '')
    except Exception as e:
        print(f"获取壁纸失败: {str(e)}")
    return ''

def get_hot60s():
    """
    获取新闻60s
    使用 https://v2.xxapi.cn/api/hot60s API
    """
    try:
        url = 'https://v2.xxapi.cn/api/hot60s'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', '')
    except Exception as e:
        print(f"获取新闻60s失败: {str(e)}")
    return ''

def get_music(song_name=''):
    """
    获取音乐信息
    优先使用模拟数据，确保音乐功能稳定
    """
    print(f"获取音乐信息: {song_name}")
    
    # 直接使用模拟数据，确保音乐功能稳定
    result = get_mock_music(song_name)
    print(f"使用模拟音乐数据: {result['title']} - {result['artist']}")
    return result

def get_random_color():
    """
    生成随机颜色，用于背景颜色变化
    """
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2",
        "#F8B739", "#52B788", "#FF8C42", "#74C0FC", "#FF69B4",
        "#A8E6CF", "#DCEDC1", "#FFD3B6", "#FFAAA5", "#FF8C94"
    ]
    return random.choice(colors)

def get_mock_music(song_name=''):
    """
    获取模拟音乐数据作为备选
    """
    # 模拟音乐数据 - 使用公开的示例音频URL
    music_list = [
        {
            'title': '春天里',
            'artist': '汪峰',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'
        },
        {
            'title': '夜曲',
            'artist': '周杰伦',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3'
        },
        {
            'title': '起风了',
            'artist': '买辣椒也用券',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3'
        },
        {
            'title': '成都',
            'artist': '赵雷',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3'
        }
    ]
    
    # 如果指定了歌曲名，则查找匹配的歌曲
    if song_name:
        for music in music_list:
            if song_name in music['title'] or song_name in music['artist']:
                music['color'] = get_random_color()
                return music
    
    # 如果没有指定歌曲名或未找到匹配的歌曲，随机返回一首
    # 使用时间戳作为随机数种子，确保每次调用都能得到不同的随机结果
    random.seed(datetime.datetime.now().timestamp())
    random_music = random.choice(music_list)
    random_music['color'] = get_random_color()
    return random_music

# 增强的回复库
enhanced_responses = {
    # 问候语
    'greetings': [
        "你好！很高兴见到你！",
        "嗨！有什么我可以帮助你的吗？",
        "你好啊！今天过得怎么样？",
        "嗨，很高兴为你服务！",
        "你好！有什么我能为你做的？"
    ],
    # 身份相关
    'identity': [
        "我是亚托莉，一个智能聊天助手。",
        "我是你的AI助手亚托莉，很高兴认识你！",
        "我是亚托莉，设计用来帮助你解决各种问题。",
        "我叫亚托莉，是一个基于AI技术的聊天机器人。"
    ],
    # 帮助相关
    'help': [
        "我可以回答问题、提供信息，还可以陪你聊天！",
        "你可以问我任何问题，或者只是想找人聊聊天，我都很乐意！",
        "我可以帮助你解答疑问，分享知识，或者进行简单的对话交流。",
        "有什么问题尽管问我，我会尽力为你提供帮助！",
        "你也可以使用@功能，比如：@天气 北京、@新闻、@音乐"
    ],
    # 数学相关
    'math': [
        "我可以帮你计算简单的数学问题，比如加减乘除等。",
        "数学计算是我的强项之一，你可以试试问我数学题！",
        "我支持基本的数学运算，包括加减乘除、幂运算等。"
    ],
    # 其他
    'other': [
            "这个问题很有趣！",
            "我理解你的意思。",
            "嗯，这是个好问题。",
            "让我思考一下...",
            "你说得对！",
            "我明白你的感受。"
        ]
}

# 函数内部已处理返回值


# 调试日志函数
def debug_log(message):
    print(f"[DEBUG] {message}")
    # 可以在这里添加更多日志处理，如写入文件等


# 为了向后兼容，保留responses列表
responses = []
for category in enhanced_responses.values():
    responses.extend(category)

# 以下是原始的OpenAI API调用函数（保留但注释掉，供将来配置API密钥后使用）
# def generate_ai_response_with_openai(question):
#     # 使用OpenAI API生成AI回复
#     # 检查client是否已初始化
#     # if client is None:
#     #     return "AI服务暂未初始化，请检查配置。"
#     
#     # 获取API密钥
#     # api_key = os.environ.get("OPENAI_API_KEY")
#     
#     # 如果没有设置有效的API密钥
#     # if not api_key or api_key == "你的OpenAI API密钥":
#     #     return "AI服务需要配置有效的API密钥。"
#     
#     # try:
#     #     # 使用OpenAI的chat completions API
#     #     response = client.chat.completions.create(
#     #         model="gpt-3.5-turbo",
#     #         messages=[
#     #             {
#     #                 "role": "system",
#     #                 "content": "你是萝卜子，一个友好可爱的AI助手。请用简洁、友好的语言回答用户问题。"
#     #             },
#     #             {
#     #                 "role": "user",
#     #                 "content": question
#     #             }
#     #         ],
#     #         temperature=0.7,
#     #         max_tokens=150
#     #     )
#     #     
#     #     # 提取生成的回复内容
#     #     return response.choices[0].message.content.strip()
#     # except Exception as e:
#     #     print(f"OpenAI API调用失败: {str(e)}")
#     #     return "抱歉，我现在无法连接到AI服务。请稍后再试或检查API密钥配置。"

if __name__ == '__main__':
    # 加载用户数据
    load_users()
    # 启动应用
    print("服务器已启动！")
    print("访问地址: http://localhost:5004")
    print("聊天页面: http://localhost:5004/chat")
    # 使用threading模式运行，禁用调试器以提高稳定性
    socketio.run(app, host='0.0.0.0', port=5004, debug=False, use_reloader=False)