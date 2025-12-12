import os

# ВРЕМЕННО: Жёстко заданный токен для проверки работы
BOT_TOKEN = "8425931021:AAFk0RDxPhzpUH30kJyFAjPEDMBxQnfkgIA"

# Отладочная информация
print("=" * 50)
print("🔧 DEBUG MODE: Используется жёстко заданный токен!")
print(f"Токен из окружения: {os.environ.get('BOT_TOKEN', 'НЕ НАЙДЕН')}")
print(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'НЕ НАЙДЕН')}")
print(f"Используемый токен: {BOT_TOKEN[:10]}...")
print("=" * 50)

# ID администраторов
ADMIN_IDS = [1931547001]

# Даты
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24
GIFT_BUDGET = "~500₽"
