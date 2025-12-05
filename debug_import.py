# 诊断app.py导入错误的脚本
print("开始诊断app.py...")

import sys
try:
    # 添加当前目录到路径
    sys.path.append('.')
    
    # 尝试导入app模块
    import app
    print("✅ app.py导入成功！")
    
    # 检查关键对象是否存在
    if hasattr(app, 'app'):
        print("✅ Flask应用实例存在")
    else:
        print("❌ Flask应用实例不存在")
    
    if hasattr(app, 'socketio'):
        print("✅ SocketIO实例存在")
    else:
        print("❌ SocketIO实例不存在")
    
    print("诊断完成")
    
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    print(f"错误位置: 第{e.lineno}行")
    print(f"错误信息: {e.msg}")
    import traceback
    traceback.print_exc()
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print("诊断脚本执行完毕")