from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    print('测试应用启动，监听端口5003')
    app.run(host='0.0.0.0', port=5003, debug=False)