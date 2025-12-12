import os
import time
import threading
import subprocess
import sys

print("=" * 60)
print("🚀 RAILWAY STARTUP SCRIPT")
print("=" * 60)

# 1. Запускаем gunicorn в фоне
print("1. Запускаем gunicorn...")
port = os.environ.get('PORT', '8080')

gunicorn_cmd = [
    'gunicorn',
    'main:app',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1',
    '--timeout', '120',
    '--access-logfile', '-',
    '--error-logfile', '-',
    '--preload'
]

# Запускаем в отдельном процессе
gunicorn_process = subprocess.Popen(gunicorn_cmd)

# 2. Ждём пока Flask запустится
print("2. Ждём запуска Flask (15 секунд)...")
time.sleep(15)

# 3. Импортируем и настраиваем бота
print("3. Настраиваем бота...")
try:
    from main import bot, setup_webhook_route
    print("✅ Бот импортирован")
    
    # Устанавливаем вебхук
    print("🌐 Устанавливаю вебхук...")
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'secretsanta-bot2-production.up.railway.app')
    webhook_url = f"https://{domain}/webhook"
    
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=webhook_url)
    print(f"✅ Вебхук установлен: {webhook_url}")
    
except Exception as e:
    print(f"⚠️ Ошибка настройки бота: {e}")

# 4. Запускаем фоновую проверку
print("4. Запускаем фоновую проверку...")
try:
    from utils import start_background_check
    from main import bot
    start_background_check(bot)
    print("✅ Фоновая проверка запущена")
except Exception as e:
    print(f"⚠️ Не удалось запустить фоновую проверку: {e}")

# 5. Запускаем keep-alive
print("5. Запускаем keep-alive...")
try:
    from keep_alive import keep_alive
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("✅ Keep-alive запущен")
except Exception as e:
    print(f"⚠️ Keep-alive не запущен: {e}")

print("=" * 60)
print("🎅 ВСЕ СИСТЕМЫ ЗАПУЩЕНЫ!")
print("=" * 60)

# Держим процесс активным
try:
    gunicorn_process.wait()
except KeyboardInterrupt:
    print("\n🛑 Получен сигнал остановки")
    gunicorn_process.terminate()
    sys.exit(0)
