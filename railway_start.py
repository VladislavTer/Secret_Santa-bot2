import os
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Запуск на порту: {port}")
    app.run(host='0.0.0.0', port=port)
