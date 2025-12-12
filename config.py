import os

# ВАЖНО: На Railway используем RAILWAY_ENVIRONMENT, но в ваших переменных это "railway"
is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# Загружаем .env только если НЕ на Railway
if not is_railway:
    from dotenv import load_dotenv
    load_dotenv()

# Токен бота - ОБЯЗАТЕЛЬНО используем os.environ.get() для Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # <- ИЗМЕНИТЬ НА environ.get()

# Проверка наличия токена
if not BOT_TOKEN:
    print("=" * 50)
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    print(f"Загружены переменные окружения: {list(os.environ.keys())}")
    print(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
    print("=" * 50)
    # Принудительно останавливаем бота
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
else:
    print(f"✅ BOT_TOKEN загружен успешно ({len(BOT_TOKEN)} символов)")

# ID администраторов
ADMIN_IDS = [1931547001]

# Даты
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24
GIFT_BUDGET = "~500₽"
