# 测试环境的简单脚本
print("Python环境测试")

# 尝试导入基本模块
try:
    import sys
    print(f"Python版本: {sys.version}")
except ImportError:
    print("sys模块导入失败")
    import sys
    print(f"Python版本: {sys.version}")
    
# 尝试导入Flask和其他库
try:
    import flask
    print(f"Flask版本: {flask.__version__}")
except ImportError:
    print("Flask未安装")

try:
    import flask_socketio
    print(f"Flask-SocketIO版本: {flask_socketio.__version__}")
except ImportError:
    print("Flask-SocketIO未安装")

try:
    import eventlet
    print(f"Eventlet版本: {eventlet.__version__}")
except ImportError:
    print("Eventlet未安装")

try:
    import openai
    print(f"OpenAI版本: {openai.__version__}")
except ImportError:
    print("OpenAI未安装")

print("测试完成")