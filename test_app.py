print("Python环境测试")
print("尝试导入必要的模块...")

try:
    import flask
    print("✓ Flask导入成功")
except ImportError as e:
    print(f"✗ Flask导入失败: {e}")

try:
    import flask_socketio
    print("✓ Flask-SocketIO导入成功")
except ImportError as e:
    print(f"✗ Flask-SocketIO导入失败: {e}")

try:
    import eventlet
    print("✓ Eventlet导入成功")
except ImportError as e:
    print(f"✗ Eventlet导入失败: {e}")

print("测试完成")