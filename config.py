# import os
# from dotenv import load_dotenv

# # Загружаем переменные из .env файла
# load_dotenv()

# # Токен бота (берётся из переменных окружения)
# BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# # Проверка наличия токена
# if not BOT_TOKEN:
#     print("⚠️ ВНИМАНИЕ: BOT_TOKEN не найден!")
#     print("Добавьте BOT_TOKEN в файл .env или переменные окружения")

# # ID администраторов (замените на свои)
# ADMIN_IDS = [1931547001]

# # Дата жеребьёвки
# DRAW_YEAR = 2025
# DRAW_MONTH = 12
# DRAW_DAY = 15

# # Дата дедлайна подарков
# GIFT_DEADLINE_MONTH = 12
# GIFT_DEADLINE_DAY = 24

# # Бюджет подарка
# GIFT_BUDGET = "~500₽"

import os
from dotenv import load_dotenv

# Проверяем, локально ли запущен бот или на Railway
is_railway = os.getenv('RAILWAY_ENVIRONMENT') == 'production'

# Загружаем .env только при локальном запуске
if not is_railway:
    load_dotenv()

# Токен бота (берётся из переменных окружения)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Проверка наличия токена
if not BOT_TOKEN:
    print("⚠️ ВНИМАНИЕ: BOT_TOKEN не найден!")
    print("Добавьте BOT_TOKEN в файл .env или переменные окружения")

# ID администраторов (замените на свои)
ADMIN_IDS = [1931547001]

# Дата жеребьёвки
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15

# Дата дедлайна подарков
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24

# Бюджет подарка
GIFT_BUDGET = "~500₽"
