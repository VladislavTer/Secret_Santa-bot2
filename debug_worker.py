import os
import sys
import traceback

print("=" * 60)
print("🔧 DEBUG WORKER: Проверка импортов в воркере")
print("=" * 60)

try:
    print("1. Импорт telebot...")
    import telebot
    print(f"   ✅ telebot версия: {telebot.__version__}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()

try:
    print("2. Импорт Flask...")
    from flask import Flask
    print("   ✅ Flask импортирован")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()

try:
    print("3. Импорт config...")
    import config
    print(f"   ✅ Config загружен, токен: {config.BOT_TOKEN[:15]}...")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()

try:
    print("4. Импорт database...")
    from database import Database
    print("   ✅ Database импортирован")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()

try:
    print("5. Импорт utils...")
    from utils import start_background_check
    print("   ✅ Utils импортирован")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()

print("=" * 60)
print("✅ Все импорты проверены")
print("=" * 60)

# Теперь импортируем основной app
try:
    print("🔄 Импортируем main.app...")
    from main import app
    print("✅ main.app успешно импортирован")
    
    # Держим процесс активным для теста
    import time
    print("⏳ Воркер работает...")
    for i in range(30):  # Работаем 30 секунд
        print(f"   ... {i+1}/30 секунд")
        time.sleep(1)
        
    print("✅ Воркер завершил работу успешно")
    
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при импорте main.py: {e}")
    traceback.print_exc()
    sys.exit(1)
