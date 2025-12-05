import os
import sys

# 设置端口为5001
os.environ['FLASK_RUN_PORT'] = '5001'

# 导入并运行app.py
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()
    exec(code)
