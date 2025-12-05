from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Flask服务器正常运行！"

@app.route('/login')
def login():
    return "登录页面"

if __name__ == '__main__':
    print("测试服务器启动在 http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)