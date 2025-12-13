import os

# Простой и надёжный config
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8113476209:AAFD9UKvOSLVVmNSAVrLExcaJhFn28nHlQM')

print(f"✅ BOT_TOKEN загружен: {BOT_TOKEN[:15]}...")

# ID администраторов
ADMINS = [1931547001]

# Даты
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24
GIFT_BUDGET = "~500₽"

# Дата раскрытия (ДОБАВЬТЕ!)
REVEAL_YEAR = 2025
REVEAL_MONTH = 12
REVEAL_DAY = 31
