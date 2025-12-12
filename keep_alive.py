import requests
import time
import os

def keep_alive():
    """Отправляет периодические запросы для поддержания активности"""
    url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'secretsanta-bot2-production.up.railway.app')
    
    print(f"🔄 Keep-alive запущен для {url}")
    
    # Ждём дополнительно на всякий случай
    time.sleep(5)
    
    while True:
        try:
            # Пробуем разные эндпоинты
            endpoints = ['/health', '/', '/setup_webhook']
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"https://{url}{endpoint}", timeout=10)
                    print(f"✅ Keep-alive {endpoint}: {response.status_code}")
                    break  # Если один сработал, остальные не проверяем
                except:
                    continue
            
        except Exception as e:
            print(f"⚠️ Keep-alive ошибка: {e}")
        
        # Ждём 4 минуты
        time.sleep(240)
