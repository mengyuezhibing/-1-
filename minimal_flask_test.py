# 最小化Flask测试应用
from flask import Flask, render_template_string
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 简单的HTML页面
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>最小化Flask测试</title>
</head>
<body>
    <h1>Flask服务器运行中</h1>
    <p>这是一个纯Flask应用，不使用SocketIO</p>
    <p>服务端口: 5002</p>
</body>
</html>
'''

@app.route('/')
def index():
    logger.info("访问主页")
    return render_template_string(HTML)

if __name__ == '__main__':
    try:
        logger.info("启动最小化Flask测试服务器")
        logger.info("访问地址: http://localhost:5002")
        # 直接使用Flask的run方法
        app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        # 打印异常信息到控制台
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        # 保持进程运行以便查看错误
        input("按Enter键退出...")
