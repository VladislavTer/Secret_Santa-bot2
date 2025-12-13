from datetime import date, datetime
import time
import threading
from database import Database
import config

# Добавьте константы для раскрытия
REVEAL_YEAR = 2025
REVEAL_MONTH = 12
REVEAL_DAY = 31

def safe_get_player_field(player, field_name, default_value=''):
    """Безопасное получение поля игрока из dict или tuple"""
    if not player:
        return default_value
    
    if isinstance(player, dict):
        return player.get(field_name, default_value)
    else:
        # Маппинг полей на индексы для tuple (старая SQLite версия)
        field_map = {
            'id': 0,
            'user_id': 1,
            'username': 2,
            'full_name': 3,
            'telegram_name': 4,
            'wish_list': 5,
            'registration_date': 6,
            'is_active': 7
        }
        idx = field_map.get(field_name)
        if idx is not None and len(player) > idx:
            value = player[idx]
            return value if value is not None else default_value
        return default_value


def check_draw_date(bot_instance):
    db = Database()

    while True:
        today = date.today()
        draw_date = date(config.DRAW_YEAR, config.DRAW_MONTH, config.DRAW_DAY)
        reveal_date = date(REVEAL_YEAR, REVEAL_MONTH, REVEAL_DAY)

        if today == draw_date:
            print("🎄 Наступила дата жеребьёвки!")

            # ИСПРАВЛЕНО: убран параметр bot
            if db.perform_draw(config.DRAW_YEAR):
                notify_players_after_draw(bot_instance, db)

            time.sleep(86400)

        elif today == reveal_date:
            print("🎭 Наступила дата раскрытия Сант!")
            reveal_all_santas(bot_instance, db)
            time.sleep(86400)

        elif today > draw_date and today > reveal_date:
            print(f"✅ Все даты прошли: жеребьёвка {draw_date}, раскрытие {reveal_date}")
            break

        else:
            if today < draw_date:
                days_left = (draw_date - today).days
                print(f"⏳ До жеребьёвки: {days_left} дней")
            elif today < reveal_date:
                days_left = (reveal_date - today).days
                print(f"⏳ До раскрытия Сант: {days_left} дней")

            time.sleep(86400)


def notify_players_after_draw(bot_instance, db):
    """Уведомление игроков после жеребьёвки"""
    try:
        print("📨 Уведомление игроков после жеребьёвки...")
        pairs = db.get_unnotified_pairs(config.DRAW_YEAR)
        
        if not pairs:
            print("ℹ️ Нет неуведомленных пар")
            return
        
        notified_count = 0
        
        for santa_id, receiver_name in pairs:
            try:
                player = db.get_player(santa_id)
                # ИСПРАВЛЕНО: используем безопасный метод вместо player[3]
                santa_name = safe_get_player_field(player, 'full_name', "Тайный Санта")
                username = safe_get_player_field(player, 'username', '')
                
                # Получаем информацию о получателе
                receiver_player = db.get_player_by_name(receiver_name)
                wish_list = safe_get_player_field(receiver_player, 'wish_list', "")
                
                # Формируем сообщение
                message = f"""
🎅 *Дорогой {santa_name}!*

Жеребьёвка проведена!

*Твой подопечный:* {receiver_name}

🎁 *Информация о подопечном:*
{f"📝 *Пожелания:* {wish_list}" if wish_list else "📝 *Пожелания не указаны*"}

📅 *Напоминание о датах:*
• Дедлайн для подарков: до {config.GIFT_DEADLINE_DAY}.{config.GIFT_DEADLINE_MONTH}.{config.DRAW_YEAR}
• Раскрытие Сант: {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}

💰 *Бюджет подарка:* {config.GIFT_BUDGET}

*Совет:* Прояви креативность! Узнай предпочтения получателя через друзей.

Удачи в подготовке сюрприза! 🎁
"""
                
                bot_instance.send_message(santa_id, message, parse_mode='Markdown')
                db.mark_as_notified(santa_id, config.DRAW_YEAR)
                notified_count += 1
                
                print(f"📤 Уведомлен {santa_name} → {receiver_name}")
                time.sleep(0.5)  # Пауза между отправками
                
            except Exception as e:
                print(f"❌ Ошибка при уведомлении пользователя {santa_id}: {e}")
        
        print(f"✅ Уведомлено {notified_count} игроков")
        
    except Exception as e:
        print(f"❌ Общая ошибка в notify_players_after_draw: {e}")


def reveal_all_santas(bot_instance, db):
    """Автоматическое раскрытие всех Сант в указанную дату"""
    try:
        print("🔄 Начинаю автоматическое раскрытие всех Сант...")

        # Раскрываем все пары
        revealed_count = db.reveal_all_pairs(REVEAL_YEAR, by_admin=False)

        if revealed_count == 0:
            print("ℹ️ Нет пар для раскрытия или они уже раскрыты")
            return

        print(f"✅ Раскрыто {revealed_count} пар")

        # Уведомляем всех игроков
        players = db.get_all_active_players()
        notified_count = 0

        for user_id, full_name, username in players:
            try:
                # Получаем имя Санты для этого игрока
                santa_name = db.get_receiver_pair(user_id, REVEAL_YEAR)

                if santa_name:
                    message = f"""
🎉 *Внимание! Тайна раскрыта!*

Сегодня {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR} - день раскрытия Тайных Сант!

Твоим Тайным Сантой был: *{santa_name}*

Надеемся, тебе понравился подарок! Спасибо за участие в игре! 🎁❤️
"""
                    bot_instance.send_message(user_id, message, parse_mode='Markdown')
                    notified_count += 1
                    time.sleep(0.5)  # Пауза между отправками

            except Exception as e:
                print(f"❌ Ошибка при уведомлении игрока {full_name}: {e}")

        print(f"📨 Уведомлено {notified_count} игроков о раскрытии Сант")

    except Exception as e:
        print(f"❌ Ошибка при автоматическом раскрытии Сант: {e}")


def notify_all_players(bot_instance, db, year=2025):
    """Уведомить всех игроков об их подопечных (отдельная функция для ручного вызова)"""
    return notify_players_after_draw(bot_instance, db)


def notify_single_player(bot_instance, user_id, db, year=2025):
    """Отправить уведомление конкретному игроку."""
    try:
        # Проверяем, есть ли пара
        receiver_name = db.get_santa_pair(user_id, year)
        
        if not receiver_name:
            print(f"ℹ️ Для игрока {user_id} нет получателя")
            return False
        
        # Получаем информацию об игроке
        player = db.get_player(user_id)
        santa_name = safe_get_player_field(player, 'full_name', "Тайный Санта")
        
        # Получаем информацию о получателе
        receiver_player = db.get_player_by_name(receiver_name)
        wishlist = safe_get_player_field(receiver_player, 'wish_list', '')
        
        # Формируем сообщение
        message = f"""
🎅 *Дорогой {santa_name}!*

Напоминаю, твой подопечный в игре "Тайный Санта":

*Имя:* {receiver_name}
{f"*Пожелания:* {wishlist}" if wishlist else "*Пожелания:* не указаны"}

📅 *Дедлайн для подарка:* до {config.GIFT_DEADLINE_DAY}.{config.GIFT_DEADLINE_MONTH}.{config.DRAW_YEAR}
🎁 *Бюджет:* {config.GIFT_BUDGET}

Подготовь креативный подарок! 🎄
"""
        
        bot_instance.send_message(user_id, message, parse_mode='Markdown')
        print(f"📤 Персональное уведомление отправлено {santa_name} → {receiver_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки персонального уведомления {user_id}: {e}")
        return False


def start_background_check(bot_instance):
    """Запуск фоновой проверки даты"""
    thread = threading.Thread(target=check_draw_date, args=(bot_instance,), daemon=True)
    thread.start()
    print("✅ Фоновая проверка даты запущена")
    print(f"📅 Дата жеребьёвки: {config.DRAW_DAY}.{config.DRAW_MONTH}.{config.DRAW_YEAR}")
    print(f"📅 Дата раскрытия Сант: {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}")
