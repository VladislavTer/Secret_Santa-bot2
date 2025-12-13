import os

print("=" * 60)
print("⚙️  ЗАГРУЗКА КОНФИГУРАЦИИ")
print("=" * 60)

# Токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8113476209:AAFD9UKvOSLVVmNSAVrLExcaJhFn28nHlQM')
print(f"✅ BOT_TOKEN загружен: {BOT_TOKEN[:15]}...")

# ========== НАСТРОЙКИ POSTGRESQL ==========
# Railway автоматически устанавливает DATABASE_URL, используем его
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    print(f"✅ DATABASE_URL найден: {DATABASE_URL[:50]}...")
    # Устанавливаем переменные для старого кода
    try:
        # Парсим DATABASE_URL
        import re
        match = re.search(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if match:
            DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = match.groups()
            print(f"📦 Парсинг DATABASE_URL:")
            print(f"   Host: {DB_HOST}")
            print(f"   Database: {DB_NAME}")
            print(f"   User: {DB_USER}")
            print(f"   Port: {DB_PORT}")
    except:
        print("⚠️ Не удалось распарсить DATABASE_URL, использую значения по умолчанию")
        DB_HOST = "postgres.railway.internal"
        DB_NAME = "railway"
        DB_USER = "postgres"
        DB_PASSWORD = "yJCAySOrrhAUQYmohuUcaXPuuQuGoUIC"
        DB_PORT = 5432
else:
    print("⚠️ DATABASE_URL не найден, использую ручные настройки")
    DB_HOST = os.environ.get('DB_HOST', "postgres.railway.internal")
    DB_NAME = os.environ.get('DB_NAME', "railway")
    DB_USER = os.environ.get('DB_USER', "postgres")
    DB_PASSWORD = os.environ.get('DB_PASSWORD', "yJCAySOrrhAUQYmohuUcaXPuuQuGoUIC")
    DB_PORT = os.environ.get('DB_PORT', 5432)

# Если на Railway, принудительно используем PostgreSQL
if os.getenv('RAILWAY_ENVIRONMENT'):
    print("🚂 Обнаружена среда Railway")
    if not DATABASE_URL:
        # Собираем DATABASE_URL из параметров
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        os.environ['DATABASE_URL'] = DATABASE_URL
        print(f"📦 Создан DATABASE_URL: {DATABASE_URL[:50]}...")

# ID администраторов
ADMINS = [1931547001]
print(f"👑 Администраторы: {ADMINS}")

# Даты
DRAW_YEAR = 2025
DRAW_MONTH = 12
DRAW_DAY = 15
GIFT_DEADLINE_MONTH = 12
GIFT_DEADLINE_DAY = 24
GIFT_BUDGET = "~500₽"

# Дата раскрытия
REVEAL_YEAR = 2025
REVEAL_MONTH = 12
REVEAL_DAY = 31

print(f"📅 Даты:")
print(f"   Жеребьёвка: {DRAW_DAY}.{DRAW_MONTH}.{DRAW_YEAR}")
print(f"   Раскрытие: {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}")
print("=" * 60)
