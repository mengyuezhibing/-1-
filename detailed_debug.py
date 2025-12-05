import sys
import traceback
import os

# 确保文件编码设置
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("=== 开始调试应用程序 ===")
print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

# 尝试逐步导入并检查可能的问题
print("\n=== 检查基本模块导入 ===")
try:
    import flask
    print(f"Flask版本: {flask.__version__}")
except ImportError as e:
    print(f"Flask导入失败: {e}")

try:
    import flask_socketio
    print(f"Flask-SocketIO版本: {flask_socketio.__version__}")
except ImportError as e:
    print(f"Flask-SocketIO导入失败: {e}")

try:
    import eventlet
    print(f"Eventlet版本: {eventlet.__version__}")
except ImportError as e:
    print(f"Eventlet导入失败: {e}")

# 现在尝试导入app模块，但设置更详细的错误处理
print("\n=== 尝试导入app模块 ===")
try:
    # 使用__import__函数并设置fromlist参数
    module = __import__('app', fromlist=['app', 'socketio'])
    print("app模块导入成功!")
    
    # 尝试访问关键对象
    print(f"Flask应用对象: {hasattr(module, 'app')}")
    print(f"SocketIO对象: {hasattr(module, 'socketio')}")
    print(f"users字典: {hasattr(module, 'users')}")
    
except ImportError as e:
    print(f"导入错误: {type(e).__name__}: {e}")
    print("导入错误堆栈:")
    traceback.print_exc(file=sys.stdout)
    
except SyntaxError as e:
    print(f"语法错误: {type(e).__name__}: {e}")
    print(f"错误位置: 第{e.lineno}行, 第{e.offset}列")
    print(f"错误信息: {e.msg}")
    print(f"文件名: {e.filename}")
    print("\n语法错误堆栈:")
    traceback.print_exc(file=sys.stdout)
    
except Exception as e:
    print(f"运行时错误: {type(e).__name__}: {e}")
    print("\n详细错误堆栈:")
    traceback.print_exc(file=sys.stdout)

print("\n=== 调试完成 ===")
