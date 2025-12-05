import os
import sys
import time

# 尝试不同的端口
ports = [5003, 5004, 5005]

for port in ports:
    try:
        print(f"尝试在端口 {port} 启动服务...")
        # 使用当前脚本目录作为工作目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # 启动服务
        os.system(f"py -u app.py {port}")
        break
    except Exception as e:
        print(f"端口 {port} 启动失败: {e}")
        time.sleep(1)
else:
    print("所有端口都无法启动服务")