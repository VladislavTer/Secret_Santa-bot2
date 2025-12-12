import os
import sys
import traceback

print("=" * 60)
print("🚀 PRODUCTION START: Запуск Тайного Санты")
print("=" * 60)

try:
    # Импортируем всё
    print("1. Импортируем основные модули...")
    from main import app
    
    print("✅ Все импорты успешны!")
    print(f"📡 App: {app}")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Запускаем сервер на порту {port}")
    
    # НИКОГДА не используйте debug=True в production!
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        use_reloader=False  # Важно: без reloader в production!
    )
    
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    traceback.print_exc()
    sys.exit(1)
