import requests
import time
import threading
import os

def keep_alive():
    """Отправляет периодические запросы для поддержания активности"""
    url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'secretsanta-bot2-production.up.railway.app')
    
    print(f"🔄 Keep-alive запущен для {url}")
    
    while True:
        try:
            # Запрос к health endpoint
            response = requests.get(f"https://{url}/health", timeout=10)
            print(f"✅ Keep-alive: {response.status_code} - {time.ctime()}")
        except Exception as e:
            print(f"⚠️ Keep-alive ошибка: {e}")
        
        # Ждём 4 минуты (240 секунд) - меньше времени ожидания Railway
        time.sleep(240)

# Запускаем в отдельном потоке
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()
