import os

# Используем переменную окружения, если она есть
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8425931021:AAFk0RDxPhzpUH30kJyFAjPEDMBxQnfkgIA")

print(f"✅ BOT_TOKEN загружен: {BOT_TOKEN[:15]}...")

# ID администраторов
ADMIN_IDS = [1931547001]

# Даты
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24
GIFT_BUDGET = "~500₽"
