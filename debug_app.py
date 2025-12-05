import sys
try:
    # 添加当前目录到Python路径
    sys.path.append('.')
    # 尝试导入app模块并捕获所有异常
    import app
    print("模块导入成功！")
    # 尝试打印一些关键信息
    print(f"Flask应用对象: {app.app}")
    print(f"SocketIO对象: {app.socketio}")
    print(f"用户字典长度: {len(app.users)}")
    print("初始化函数测试成功！")
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"导入错误详情: {sys.exc_info()}")
except Exception as e:
    print(f"发生异常: {type(e).__name__}: {e}")
    import traceback
    print("\n详细错误堆栈:")
    traceback.print_exc()
