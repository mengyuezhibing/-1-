import sys
import traceback
import os

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("开始启动服务...")
print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")

# 尝试导入关键模块
print("\n尝试导入必要的模块...")
try:
    from flask import Flask
    print("✓ Flask导入成功")
except Exception as e:
    print(f"✗ Flask导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from flask_socketio import SocketIO
    print("✓ Flask-SocketIO导入成功")
except Exception as e:
    print(f"✗ Flask-SocketIO导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

# 尝试启动应用
print("\n尝试启动应用...")
try:
    # 导入app模块
    import app
    print("✓ app模块导入成功")
    
    # 启动服务
    print("\n启动服务器...")
    app.socketio.run(app.app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"\n✗ 服务启动失败: {type(e).__name__}: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)
