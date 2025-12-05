import requests

try:
    response = requests.get('https://v2.xxapi.cn/api/wallpaper')
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.text}")
except Exception as e:
    print(f"Error: {e}")
