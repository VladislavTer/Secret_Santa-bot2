import os
import telebot
from telebot import types
from datetime import date
import config
from database import Database
from flask import Flask, request
import time
import logging

# ================ ИНИЦИАЛИЗАЦИЯ ================
print("=" * 60)
print("🤖 ЗАГРУЗКА ТАЙНОГО САНТЫ")
print("=" * 60)

# 1. Сначала Flask app (для health-check)
app = Flask(__name__)

# 2. Базовые health-check маршруты (ДО ВСЕГО!)
@app.route('/health', methods=['GET'])
def health_check():
    """Моментальный health-check для Railway"""
    return 'OK', 200

@app.route('/')
def home():
    return '🎅 Тайный Санта работает!'

print("✅ Flask app создан")

# 3. Инициализация бота
try:
    bot = telebot.TeleBot(config.BOT_TOKEN)
    print(f"✅ Бот инициализирован: {config.BOT_TOKEN[:15]}...")
except Exception as e:
    print(f"❌ Ошибка инициализации бота: {e}")
    raise

# 4. База данных
try:
    db = Database()
    print(f"✅ База данных: {db.db_path if hasattr(db, 'db_path') else 'secret_santa.db'}")
except Exception as e:
    print(f"❌ Ошибка базы данных: {e}")
    raise

user_states = {}

# НАСТРОЙКИ ДЛЯ РАСКРЫТИЯ
REVEAL_YEAR = 2025
REVEAL_MONTH = 12
REVEAL_DAY = 31

print("=" * 60)
print("✅ ВСЕ КОМПОНЕНТЫ ИНИЦИАЛИЗИРОВАНЫ")
print("=" * 60)

# ================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ DATABASE ================
def get_player_by_name(self, full_name):
    """Найти игрока по полному имени"""
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE full_name = ?', (full_name,))
    player = cursor.fetchone()
    conn.close()
    return player

Database.get_player_by_name = get_player_by_name

# ================ ОСНОВНЫЕ HANDLERS ================
@bot.message_handler(commands=['start'])
def main(message):
    user = message.from_user
    user_id = message.from_user.id

    player = db.get_player(user_id)

    if player:
        full_name = player[3]
        username = player[2] if player[2] else 'не указан'
        reg_date = player[6] if len(player) > 6 else 'неизвестно'
        wish_list = player[5] if len(player) > 5 and player[5] else 'еще не добавлен'

        welcome_text = f"""
        🎅 *С возвращением, {user.first_name}!* 🎄

        Ты уже зарегистрирован в игре "Тайный Санта IT TOP"!

        📋 *Твои данные:*
        • Имя: *{full_name}*
        • Username: @{username}
        • ID: `{user_id}`
        • Дата регистрации: {reg_date}
        • Список пожеланий: {wish_list}

        Используй команды:
        /status - проверить свой статус
        /reveal - узнать своего Тайного Санту (после 31.12.2025)
        /mywish - посмотреть/обновить список пожеланий
        /help - получить помощь
        /myid - узнать свой ID
        """

        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
        return

    user_name = user.first_name

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Ознакомиться с правилами игры📋', callback_data='rules'))

    bot.send_message(message.chat.id,
                     f'Привет, {user_name}. Мы рады приветствовать тебя в игре "Тайный Санта🎅🎄". Перед началом, рекомендуем ознакомиться с правилами игры!',
                     reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Панель администратора"""
    # Проверка прав администратора (добавь свою логику)
    if message.from_user.id not in [123456789]:  # Замени на свои ID
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton('🔮 Провести жеребьёвку', callback_data='admin_draw'),
        types.InlineKeyboardButton('📊 Статистика', callback_data='admin_stats'),
        types.InlineKeyboardButton('📨 Уведомить всех', callback_data='admin_notify'),
        types.InlineKeyboardButton('👁️ Раскрыть всех', callback_data='admin_reveal_all'),
        types.InlineKeyboardButton('👤 Раскрыть одного', callback_data='admin_reveal_one'),
        types.InlineKeyboardButton('🗃️ Просмотр БД', callback_data='admin_view_db'),
        types.InlineKeyboardButton('🧪 Тестовые игроки', callback_data='admin_add_test'),
        types.InlineKeyboardButton('🗑️ Очистить пары', callback_data='admin_clear_pairs'),
        types.InlineKeyboardButton('🎅 Созданные пары', callback_data='admin_view_pairs'),
    ]
    
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, 
                    "🛠️ *Панель администратора*\n\nВыберите действие:",
                    reply_markup=markup,
                    parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == 'rules':
        markup = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton('Да✅', callback_data='yes')
        btn_no = types.InlineKeyboardButton('Нет❌', callback_data='no')
        markup.row(btn_yes, btn_no)

        bot.send_message(call.message.chat.id,
                         '🎄 Волшебство Тайного Санты начинается! 🎄\nДорогие друзья! Пришло время окутаться атмосферой чудес и радости. Чтобы наш обмен подарками принёс только улыбки, давайте вспомним правила:\n✨ Основной принцип:\nВы становитесь Тайным Сантой для одного человека и получателем подарка от другого. Ваша миссия — сделать приятный сюрприз своему подопечному, оставаясь в тени до самого момента вручения!\n📅 Ключевые даты:\nЖеребьёвка: 15.12.2025\nРаскрытие Сант: 31.12.2025\nДедлайн для подарков: до 25.12.2025.\n🎁 Правила дарения:\nБюджет: ~500₽💵. \nЦенность — в креативности и внимании!\n🤫Анонимность: Ваша главная магия — секретность. Не раскрывайте, кому вы готовите сюрприз!\nНаблюдательность: Проявите внимание! Узнайте у друзей о предпочтениях вашего подопечного.\n❌Запрещённое: Подарки «на скорую руку», обидные или слишком личные шутки, а также живые существа.\n🎅 Как всё пройдёт:\nВ день встречи подарки будут собраны анонимно (с пометкой «Для [Имя получателя]»). Мы по очереди будем вручать их, а потом попробуем угадать, кто же был нашим Тайного Сантой! Пусть дух праздника согреет ваши сердца! ❤️\n\n Ты готов начать?',
                         reply_markup=markup)

    elif call.data == 'yes':
        msg = bot.send_message(call.message.chat.id,
                               'Отлично! Давайте начнем! 🎅🎄\nУважаемые участники, очень просим вводить вас свои реальные данные, чтобы не нарушать правила игры и не доставлять неудобства другим игрокам🤗😉\nВведите своё имя и фамилию:')
        bot.register_next_step_handler(msg, get_name)

    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Жаль, что вы не готовы. Возвращайтесь! 🎅')

    elif call.data == 'add_wish':
        msg = bot.send_message(call.message.chat.id,
                               '🎁 *Напиши свои пожелания для подарка:*\n\n'
                               '• Любимые цвета, хобби\n'
                               '• Размер одежды (если нужно)\n'
                               '• Что не нравится\n'
                               '• Идеи для подарков\n\n'
                               'Чем больше деталей - тем лучше!',
                               parse_mode='Markdown')
        bot.register_next_step_handler(msg, save_wishlist)

    elif call.data == 'skip_wish':
        bot.send_message(call.message.chat.id,
                         'Хорошо! Твой Санта проявит креативность! 🎅\n\n'
                         f'*Жеребьёвка:* {config.DRAW_DAY}.{config.DRAW_MONTH}.{config.DRAW_YEAR}\n'
                         f'*Раскрытие Сант:* {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}\n\n'
                         'Можешь добавить список пожеланий позже командой /addwish',
                         parse_mode='Markdown')

    elif call.data == 'later_wish':
        bot.send_message(call.message.chat.id,
                         'Хорошо! Можешь добавить список пожеланий позже командой /addwish\n\n'
                         f'*Жеребьёвка:* {config.DRAW_DAY}.{config.DRAW_MONTH}.{config.DRAW_YEAR}\n'
                         f'*Раскрытие Сант:* {REVEAL_DAY}.{REVEAL_MONTH}.{REVEAL_YEAR}\n\n'
                         'В этот день ты узнаешь, кому будешь дарить!',
                         parse_mode='Markdown')

    elif call.data == 'update_wish':
        msg = bot.send_message(call.message.chat.id,
                               '🎁 *Обнови список пожеланий:*\n\n'
                               '• Любимые цвета, хобби\n'
                               '• Размер одежды (если нужно)\n'
                               '• Что не нравится\n'
                               '• Идеи для подарков\n\n'
                               'Чем больше деталей - тем лучше!',
                               parse_mode='Markdown')
        bot.register_next_step_handler(msg, save_wishlist_command)

    elif call.data == 'cancel_wish':
        bot.send_message(call.message.chat.id, "❌ Обновление отменено.")

    elif call.data.startswith('admin_'):
        handle_admin_callback(call)

    bot.answer_callback_query(call.id)


def get_name(message):
    name = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    telegram_name = message.from_user.first_name

    if db.add_player(user_id, username, name, telegram_name):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Да, добавить пожелания', callback_data='add_wish'))
        markup.add(types.InlineKeyboardButton('Нет, пропустить', callback_data='skip_wish'))
        markup.add(types.InlineKeyboardButton('Позже, из команд', callback_data='later_wish'))

        bot.send_message(message.chat.id,
                         f'✅ *Отлично, {name}! Ты зарегистрирован в игре!*\n\n'
                         f'Хочешь добавить список пожеланий для своего Тайного Санты?\n'
                         f'Это поможет выбрать тебе идеальный подарок! 🎁\n\n'
                         f'*Можешь добавить позже командой /addwish*',
                         reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id,
                         f'Спасибо, {name}! Но произошла ошибка при регистрации.')


def save_wishlist(message):
    user_id = message.from_user.id
    wishlist = message.text

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE players SET wish_list = ? WHERE user_id = ?', (wishlist, user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id,
                     '✅ *Список пожеланий сохранен!*\n\n'
                     'Твой Санта будет благодарен за подсказки! 🎁\n\n'
                     f'Теперь жди жеребьёвки {config.DRAW_DAY}.{config.DRAW_MONTH}.{config.DRAW_YEAR}!',
                     parse_mode='Markdown')


# ================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ================
def save_wishlist_command(message):
    user_id = message.from_user.id
    wishlist = message.text

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE players SET wish_list = ? WHERE user_id = ?', (wishlist, user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id,
                     '✅ *Список пожеланий сохранен!*\n\n'
                     'Твой Санта будет благодарен за подсказки! 🎁\n\n'
                     'Посмотреть свой список можно командой /mywish',
                     parse_mode='Markdown')

# ================ ADMIN HANDLERS ================
def handle_admin_callback(call):
    try:
        if call.data == 'admin_draw':
            if db.perform_draw(config.DRAW_YEAR):
                bot.send_message(call.message.chat.id, "✅ Жеребьёвка проведена успешно!")
                from utils import notify_players_after_draw
                notify_players_after_draw(bot, db)
                bot.send_message(call.message.chat.id, "📨 Уведомления отправлены!")
            else:
                bot.send_message(call.message.chat.id, "❌ Ошибка при проведении жеребьёвки!")

        elif call.data == 'admin_stats':
            stats = db.get_player_stats()
            players = db.get_all_active_players()
            message = "<b>📊 Статистика игры:</b>\n\n"
            message += f"• <b>Всего игроков:</b> {stats['total_players']}\n"
            message += f"• <b>Создано пар:</b> {stats['total_pairs']}\n"
            message += f"• <b>Раскрыто пар:</b> {stats['total_revealed']}\n\n"

            if players:
                message += "<b>Список игроков:</b>\n"
                for i, (user_id, full_name, username) in enumerate(players, 1):
                    safe_name = full_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    username_display = f"@{username}" if username else "без username"
                    player_info = db.get_player(user_id)
                    has_wishlist = "✅" if player_info and len(player_info) > 5 and player_info[5] else "❌"
                    message += f"{i}. {safe_name} ({username_display}) {has_wishlist}\n"
            else:
                message += "Нет зарегистрированных игроков"
            bot.send_message(call.message.chat.id, message, parse_mode='HTML')

        elif call.data == 'admin_notify':
            from utils import notify_players_after_draw
            notify_players_after_draw(bot, db)
            bot.send_message(call.message.chat.id, "✅ Уведомления отправлены всем игрокам!")

        elif call.data == 'admin_reveal_all':
            confirmed_markup = types.InlineKeyboardMarkup()
            confirmed_markup.add(
                types.InlineKeyboardButton('✅ Да, раскрыть всех', callback_data='admin_confirm_reveal_all'),
                types.InlineKeyboardButton('❌ Нет, отмена', callback_data='admin_cancel')
            )
            bot.send_message(call.message.chat.id,
                             "⚠️ <b>Внимание!</b>\n\nВы собираетесь раскрыть ВСЕХ Тайных Сант принудительно.\nПосле этого игроки узнают, кто им дарил подарки.\n\nПодтвердите действие:",
                             parse_mode='HTML', reply_markup=confirmed_markup)

        elif call.data == 'admin_confirm_reveal_all':
            revealed_count = db.reveal_all_pairs(REVEAL_YEAR, by_admin=True)
            if revealed_count > 0:
                players = db.get_all_active_players()
                notified_count = 0
                for user_id, full_name, username in players:
                    try:
                        santa_name = db.get_receiver_pair(user_id, REVEAL_YEAR)
                        if santa_name:
                            message = f"🎉 <b>Срочное объявление!</b>\n\nОрганизатор раскрыл всех Тайных Сант!\n\nТвоим Сантой был: <b>{santa_name}</b>\n\nСпасибо за участие в игре! 🎁"
                            bot.send_message(user_id, message, parse_mode='HTML')
                            notified_count += 1
                    except Exception as e:
                        print(f"Ошибка при уведомлении {full_name}: {e}")
                bot.send_message(call.message.chat.id,
                                 f"✅ Раскрыто {revealed_count} пар!\nУведомлено {notified_count} игроков.")
            else:
                bot.send_message(call.message.chat.id, "❌ Нет пар для раскрытия или они уже раскрыты.")

        elif call.data == 'admin_reveal_one':
            msg = bot.send_message(call.message.chat.id,
                                   "🔍 <b>Раскрыть Санту для конкретного игрока</b>\n\nВведите ID пользователя, которому хотите раскрыть Санту:",
                                   parse_mode='HTML')
            bot.register_next_step_handler(msg, process_reveal_one)

        elif call.data == 'admin_view_db':
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            message = "<b>📊 База данных:</b>\n\n"
            for table_name, in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                message += f"• <b>{table_name}:</b> {count} записей\n"
                if count > 0 and table_name == 'players':
                    cursor.execute("SELECT full_name, username, wish_list FROM players LIMIT 5;")
                    players_data = cursor.fetchall()
                    message += "  <i>Последние игроки:</i>\n"
                    for name, username, wish_list in players_data:
                        safe_name = name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        username_display = f"@{username}" if username else "нет"
                        has_wishlist = "🎁" if wish_list else "❌"
                        message += f"  - {safe_name} ({username_display}) {has_wishlist}\n"
            conn.close()
            bot.send_message(call.message.chat.id, message, parse_mode='HTML')

        elif call.data == 'admin_add_test':
            test_players = [
                {"user_id": 1001, "username": "test_user1", "full_name": "Иван Иванов", "telegram_name": "Иван"},
                {"user_id": 1002, "username": "test_user2", "full_name": "Мария Петрова", "telegram_name": "Мария"},
                {"user_id": 1003, "username": "test_user3", "full_name": "Алексей Сидоров", "telegram_name": "Алексей"},
                {"user_id": 1004, "username": "test_user4", "full_name": "Екатерина Волкова", "telegram_name": "Екатерина"},
                {"user_id": 1005, "username": "test_user5", "full_name": "Дмитрий Козлов", "telegram_name": "Дмитрий"},
            ]
            added_count = 0
            for player in test_players:
                if db.add_player(
                        user_id=player["user_id"],
                        username=player["username"],
                        full_name=player["full_name"],
                        telegram_name=player["telegram_name"]
                ):
                    added_count += 1
            bot.send_message(
                call.message.chat.id,
                f"✅ Добавлено {added_count} тестовых игроков!\n\nТеперь используйте '🔮 Провести жеребьёвку'"
            )

        elif call.data == 'admin_clear_pairs':
            confirmed_markup = types.InlineKeyboardMarkup()
            confirmed_markup.add(
                types.InlineKeyboardButton('✅ Да, очистить', callback_data='admin_confirm_clear_pairs'),
                types.InlineKeyboardButton('❌ Нет, отмена', callback_data='admin_cancel')
            )
            bot.send_message(call.message.chat.id,
                             "⚠️ <b>Внимание!</b>\n\nВы собираетесь очистить ВСЕ пары Санта-получатель.\nЭто действие нельзя отменить!\n\nПодтвердите:",
                             parse_mode='HTML', reply_markup=confirmed_markup)

        elif call.data == 'admin_confirm_clear_pairs':
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM santa_pairs WHERE year = ?", (config.DRAW_YEAR,))
            cursor.execute("DELETE FROM revealed_pairs WHERE year = ?", (config.DRAW_YEAR,))
            conn.commit()
            conn.close()
            bot.send_message(call.message.chat.id, "🗑️ Пары очищены. Можно провести жеребьёвку заново.")

        elif call.data == 'admin_view_pairs':
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    santa.full_name as santa,
                    receiver.full_name as receiver,
                    santa.user_id as santa_id,
                    receiver.user_id as receiver_id,
                    receiver.wish_list as wish_list,
                    CASE WHEN rp.id IS NOT NULL THEN '✅' ELSE '❌' END as revealed
                FROM santa_pairs sp
                JOIN players santa ON sp.santa_user_id = santa.user_id
                JOIN players receiver ON sp.receiver_user_id = receiver.user_id
                LEFT JOIN revealed_pairs rp ON sp.receiver_user_id = rp.receiver_user_id AND sp.year = rp.year
                WHERE sp.year = ?
            ''', (config.DRAW_YEAR,))
            pairs = cursor.fetchall()
            conn.close()
            if not pairs:
                bot.send_message(call.message.chat.id, "⚠️ Пары еще не созданы")
                return
            message = "<b>🎅 Созданные пары:</b>\n\n"
            for santa_name, receiver_name, santa_id, receiver_id, wish_list, revealed in pairs:
                safe_santa = santa_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                safe_receiver = receiver_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                has_wishlist = "🎁" if wish_list else "❌"
                message += f"• <b>{safe_santa}</b> → <b>{safe_receiver}</b> {revealed} {has_wishlist}\n"
                message += f"  (ID: {santa_id} → {receiver_id})\n\n"
            message += f"\n<b>Всего пар:</b> {len(pairs)}"
            bot.send_message(call.message.chat.id, message, parse_mode='HTML')

        elif call.data == 'admin_cancel':
            bot.send_message(call.message.chat.id, "❌ Действие отменено.")

    except Exception as e:
        error_message = f"❌ Ошибка при обработке команды:\n{str(e)}"
        print(f"ERROR in handle_admin_callback: {e}")
        bot.send_message(call.message.chat.id, error_message)


def process_reveal_one(message):
    try:
        user_id = int(message.text)
        player = db.get_player(user_id)
        if not player:
            bot.send_message(message.chat.id, f"❌ Игрок с ID {user_id} не найден.")
            return
        full_name = player[3]
        if db.is_pair_revealed(user_id, REVEAL_YEAR):
            santa_name = db.get_receiver_pair(user_id, REVEAL_YEAR)
            bot.send_message(message.chat.id,
                             f"ℹ️ Пара для <b>{full_name}</b> уже раскрыта.\nСанта: <b>{santa_name}</b>",
                             parse_mode='HTML')
            return
        santa_name = db.reveal_pair(user_id, REVEAL_YEAR, by_admin=True)
        if santa_name:
            try:
                receiver_msg = f"🎉 <b>Срочное объявление от организатора!</b>\n\nТайна раскрыта досрочно!\n\nТвоим Тайным Сантой был: <b>{santa_name}</b>\n\nНадеемся, тебе понравился подарок! 🎁"
                bot.send_message(user_id, receiver_msg, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка при уведомлении получателя: {e}")
            try:
                santa_player = db.get_player_by_name(santa_name)
                if santa_player:
                    santa_id = santa_player[1]
                    santa_msg = f"🎅 <b>Внимание!</b>\n\nОрганизатор раскрыл твою тайну досрочно!\n\nТвой подопечный <b>{full_name}</b> теперь знает, что его Сантой был ты!\n\nСпасибо за участие! 🎁"
                    bot.send_message(santa_id, santa_msg, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка при уведомлении Санты: {e}")
            bot.send_message(message.chat.id,
                             f"✅ Санта для <b>{full_name}</b> раскрыт!\nСанта: <b>{santa_name}</b>\n\nОба игрока уведомлены.",
                             parse_mode='HTML')
        else:
            bot.send_message(message.chat.id,
                             f"❌ Не удалось раскрыть Санту для <b>{full_name}</b>.\nВозможно, пара не найдена.",
                             parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID. Введите числовой ID.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# ================ ЗАПУСК ПРИЛОЖЕНИЯ ================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ЗАПУСК ТЕЛЕГРАМ БОТА (основной процесс)")
    print("=" * 60)
    
    # Удаляем вебхук, чтобы не мешал polling
    bot.remove_webhook()
    time.sleep(2)
    
    # Запускаем бота в режиме polling.
    # Эта команда БЛОКИРУЕТ выполнение, пока бот работает.
    # Именно это нужно Railway, чтобы контейнер продолжал работать.
    bot.infinity_polling(
        timeout=60, 
        long_polling_timeout=60,
        logger_level=logging.INFO  # <-- ИСПРАВЛЕНО
    )
