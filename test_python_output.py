import sys
import os

print("Python版本:", sys.version)
print("Python执行路径:", sys.executable)
print("当前工作目录:", os.getcwd())
print("环境变量PATH:", os.environ.get('PATH', '未设置'))
print("\n所有环境变量:")
for key, value in os.environ.items():
    print(f"{key}: {value}")
    if len(value) > 50:  # 限制输出长度
        break
