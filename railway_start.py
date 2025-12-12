import os
import time
import threading

print("🚀 Railway Startup Script")
print("=" * 60)

# СНАЧАЛА запускаем Flask через gunicorn
print("1. Запускаем gunicorn...")
os.system(f"gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --access-logfile - --error-logfile - &")

# Ждём пока Flask запустится
print("2. Ждём запуска Flask (10 секунд)...")
time.sleep(10)

# ПОТОМ импортируем и запускаем keep-alive
print("3. Запускаем keep-alive...")
try:
    from keep_alive import keep_alive
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("✅ Keep-alive запущен")
except Exception as e:
    print(f"⚠️ Keep-alive не запущен: {e}")

# Держим скрипт активным
print("✅ Все компоненты запущены")
print("=" * 60)
while True:
    time.sleep(3600)  # Спим 1 час
