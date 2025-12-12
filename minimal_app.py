from flask import Flask
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return '🎅 Тайный Санта работает!'

@app.route('/test')
def test():
    return 'Тестовая страница'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Запуск на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
