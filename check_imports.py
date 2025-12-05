import sys
try:
    # 尝试导入所需的模块
    import eventlet
    eventlet.monkey_patch()
    from flask import Flask
    from flask_socketio import SocketIO
    import json
    import re
    import os
    import random
    import requests
    import hashlib
    import datetime
    import socket
    print("所有模块导入成功")
except Exception as e:
    print(f"导入错误: {str(e)}", file=sys.stderr)
    sys.exit(1)

print("检查完成，没有发现语法或导入错误")