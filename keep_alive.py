import requests
import time
import os

def keep_alive():
    """Отправляет однократный запрос для проверки работоспособности"""
    url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'secretsanta-bot2-production.up.railway.app')
    
    print(f"🔄 Keep-alive: проверяем {url}")
    
    # Ждём 5 секунд чтобы веб-сервер успел запуститься
    time.sleep(5)
    
    try:
        # Пробуем разные эндпоинты
        endpoints = ['/health', '/', '/setup_webhook']
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"https://{url}{endpoint}", timeout=10)
                print(f"✅ Keep-alive {endpoint}: {response.status_code} - {response.text[:50]}")
                return True  # Успешно проверили
            except Exception as e:
                print(f"⚠️ Keep-alive {endpoint} ошибка: {e}")
                continue
        
        print("❌ Keep-alive: не удалось подключиться ни к одному эндпоинту")
        return False
        
    except Exception as e:
        print(f"❌ Keep-alive общая ошибка: {e}")
        return False


# Если файл запускается напрямую (для теста)
if __name__ == '__main__':
    print("🔧 Тестируем keep-alive...")
    keep_alive()
    print("🔧 Тест завершен")
