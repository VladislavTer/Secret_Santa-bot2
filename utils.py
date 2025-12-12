from datetime import date, datetime
import time
import threading
from database import Database
import config

# Добавьте константы для раскрытия
REVEAL_YEAR = 2025
REVEAL_MONTH = 12
REVEAL_DAY = 31


def check_draw_date(bot_instance):
    db = Database()

    while True:
        today = date.today()
        draw_date = date(config.DRAW_YEAR, config.DRAW_MONTH, config.DRAW_DAY)
        reveal_date = date(REVEAL_YEAR, REVEAL_MONTH, REVEAL_DAY)

        if today == draw_date:
            print("🎄 Наступила дата жеребьёвки!")

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
    pairs = db.get_unnotified_pairs(config.DRAW_YEAR)

    for santa_id, receiver_name in pairs:
        try:
            player = db.get_player(santa_id)
            santa_name = player[3] if player and len(player) > 3 else "Тайный Санта"

            # Получаем информацию о получателе (для виш-листа)
            receiver_player = db.get_player_by_name(receiver_name)
            wish_list = ""

            if receiver_player and len(receiver_player) > 5:
                wish_list = receiver_player[5]  # wish_list находится на 5-й позиции (индекс 5)

            message = f"🎅 Дорогой {santa_name}!\n\n"
            message += f"Твой подопечный: *{receiver_name}*\n\n"

            # Добавляем виш-лист, если он есть
            if wish_list:
                message += "🎁 *Пожелания получателя:*\n"
                message += f"{wish_list}\n\n"
            else:
                message += "🎁 У получателя нет списка пожеланий. Прояви креативность!\n\n"

            message += "Теперь твоя задача:\n"
            message += f"1. Придумай креативный подарок ({config.GIFT_BUDGET})\n"
            message += "2. Узнай предпочтения получателя (можешь спросить у друзей)\n"
            message += f"3. Подготовь подарок до {config.GIFT_DEADLINE_DAY}.{config.GIFT_DEADLINE_MONTH}.{config.DRAW_YEAR}\n"
            message += "4. Сохраняй анонимность!\n"
            message += f"5. Раскрытие Сант: {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}\n\n"
            message += "Удачи в подготовке сюрприза! 🎁"

            bot_instance.send_message(santa_id, message, parse_mode='Markdown')

            db.mark_as_notified(santa_id, config.DRAW_YEAR)

            print(f"📨 Уведомлен Санта {santa_id} (дарит {receiver_name})")

            if wish_list:
                print(f"   📝 Виш-лист отправлен: {wish_list[:50]}...")

        except Exception as e:
            print(f"❌ Ошибка при уведомлении пользователя {santa_id}: {e}")


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
                    message = f"🎉 <b>Внимание! Тайна раскрыта!</b>\n\n"
                    message += f"Сегодня {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR} - день раскрытия Тайных Сант!\n\n"
                    message += f"Твоим Тайным Сантой был: <b>{santa_name}</b>\n\n"
                    message += "Надеемся, тебе понравился подарок! Спасибо за участие в игре! 🎁❤️"

                    bot_instance.send_message(user_id, message, parse_mode='HTML')
                    notified_count += 1
                    time.sleep(0.5)  # Пауза между отправками

            except Exception as e:
                print(f"❌ Ошибка при уведомлении игрока {full_name}: {e}")

        print(f"📨 Уведомлено {notified_count} игроков о раскрытии Сант")

    except Exception as e:
        print(f"❌ Ошибка при автоматическом раскрытии Сант: {e}")


def start_background_check(bot_instance):
    thread = threading.Thread(target=check_draw_date, args=(bot_instance,), daemon=True)
    thread.start()
    print("✅ Фоновая проверка даты запущена")
    print(f"📅 Дата раскрытия Сант: {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}")