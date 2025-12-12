# import sqlite3
# import random
# from datetime import datetime
#
#
# class Database:
#     def __init__(self, db_name='secret_santa.db'):
#         self.db_name = db_name
#         self.init_db()
#
#     def get_connection(self):
#         return sqlite3.connect(self.db_name)
#
#     def init_db(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS players (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER UNIQUE,
#             username TEXT,
#             full_name TEXT NOT NULL,
#             telegram_name TEXT,
#             wish_list TEXT,
#             registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             is_active BOOLEAN DEFAULT 1
#         )
#         ''')
#
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS santa_pairs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             santa_user_id INTEGER,
#             receiver_user_id INTEGER,
#             year INTEGER DEFAULT 2025,
#             is_notified BOOLEAN DEFAULT 0,
#             assignment_date TIMESTAMP,
#             UNIQUE(santa_user_id, year)
#         )
#         ''')
#
#         # Новая таблица для хранения раскрытых пар
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS revealed_pairs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             santa_user_id INTEGER,
#             receiver_user_id INTEGER,
#             year INTEGER DEFAULT 2025,
#             revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             revealed_by_admin BOOLEAN DEFAULT 0
#         )
#         ''')
#
#         conn.commit()
#         conn.close()
#         print("✅ База данных инициализирована")
#
#     def add_player(self, user_id, username, full_name, telegram_name=None, wish_list=None):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         try:
#             cursor.execute('''
#             INSERT OR REPLACE INTO players
#             (user_id, username, full_name, telegram_name, wish_list, is_active)
#             VALUES (?, ?, ?, ?, ?, 1)
#             ''', (user_id, username, full_name, telegram_name, wish_list))
#
#             conn.commit()
#             print(f"✅ Игрок добавлен в БД: {full_name} (@{username})")
#             return True
#         except Exception as e:
#             print(f"❌ Ошибка при добавлении игрока: {e}")
#             return False
#         finally:
#             conn.close()
#
#     def get_all_active_players(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT user_id, full_name, username
#         FROM players
#         WHERE is_active = 1
#         ''')
#
#         players = cursor.fetchall()
#         conn.close()
#         return players
#
#     def get_player(self, user_id):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
#         player = cursor.fetchone()
#         conn.close()
#
#         return player
#
#     def perform_draw(self, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = ?', (year,))
#         if cursor.fetchone()[0] > 0:
#             print("⚠️ Жеребьёвка уже проводилась в этом году!")
#             conn.close()
#             return False
#
#         players = self.get_all_active_players()
#         player_ids = [player[0] for player in players]
#
#         if len(player_ids) < 2:
#             print("⚠️ Недостаточно игроков для жеребьёвки!")
#             conn.close()
#             return False
#
#         receivers = player_ids.copy()
#         random.shuffle(receivers)
#
#         attempts = 0
#         while any(santa == receiver for santa, receiver in zip(player_ids, receivers)) and attempts < 100:
#             random.shuffle(receivers)
#             attempts += 1
#
#         for santa_id, receiver_id in zip(player_ids, receivers):
#             cursor.execute('''
#             INSERT INTO santa_pairs
#             (santa_user_id, receiver_user_id, year, assignment_date)
#             VALUES (?, ?, ?, datetime('now'))
#             ''', (santa_id, receiver_id, year))
#
#         conn.commit()
#         conn.close()
#         print(f"🎅 Жеребьёвка проведена! Создано {len(player_ids)} пар.")
#         return True
#
#     def get_santa_pair(self, user_id, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT p.full_name
#         FROM santa_pairs sp
#         JOIN players p ON sp.receiver_user_id = p.user_id
#         WHERE sp.santa_user_id = ? AND sp.year = ?
#         ''', (user_id, year))
#
#         pair = cursor.fetchone()
#         conn.close()
#
#         return pair[0] if pair else None
#
#     def get_receiver_pair(self, user_id, year=2025):
#         """Узнать, кто был Сантой для данного пользователя"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT p.full_name
#         FROM santa_pairs sp
#         JOIN players p ON sp.santa_user_id = p.user_id
#         WHERE sp.receiver_user_id = ? AND sp.year = ?
#         ''', (user_id, year))
#
#         pair = cursor.fetchone()
#         conn.close()
#
#         return pair[0] if pair else None
#
#     def reveal_pair(self, receiver_user_id, year=2025, by_admin=False):
#         """Раскрыть пару: кто был Сантой для получателя"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         try:
#             # Получаем пару
#             cursor.execute('''
#             SELECT sp.santa_user_id, sp.receiver_user_id
#             FROM santa_pairs sp
#             WHERE sp.receiver_user_id = ? AND sp.year = ?
#             ''', (receiver_user_id, year))
#
#             pair = cursor.fetchone()
#
#             if not pair:
#                 return None
#
#             santa_user_id, receiver_user_id = pair
#
#             # Проверяем, не раскрыта ли уже эта пара
#             cursor.execute('''
#             SELECT id FROM revealed_pairs
#             WHERE receiver_user_id = ? AND year = ?
#             ''', (receiver_user_id, year))
#
#             if cursor.fetchone():
#                 print(f"⚠️ Пара для получателя {receiver_user_id} уже раскрыта")
#                 conn.close()
#                 return self.get_receiver_pair(receiver_user_id, year)
#
#             # Сохраняем в таблицу раскрытых пар
#             cursor.execute('''
#             INSERT INTO revealed_pairs
#             (santa_user_id, receiver_user_id, year, revealed_by_admin)
#             VALUES (?, ?, ?, ?)
#             ''', (santa_user_id, receiver_user_id, year, 1 if by_admin else 0))
#
#             conn.commit()
#             conn.close()
#
#             # Возвращаем имя Санты
#             player = self.get_player(santa_user_id)
#             return player[3] if player else None
#
#         except Exception as e:
#             print(f"❌ Ошибка при раскрытии пары: {e}")
#             if conn:
#                 conn.close()
#             return None
#
#     def get_all_pairs_to_reveal(self, year=2025):
#         """Получить все пары, которые еще не раскрыты"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT sp.santa_user_id, sp.receiver_user_id,
#                santa.full_name as santa_name, receiver.full_name as receiver_name
#         FROM santa_pairs sp
#         JOIN players santa ON sp.santa_user_id = santa.user_id
#         JOIN players receiver ON sp.receiver_user_id = receiver.user_id
#         WHERE sp.year = ?
#           AND NOT EXISTS (
#               SELECT 1 FROM revealed_pairs rp
#               WHERE rp.receiver_user_id = sp.receiver_user_id AND rp.year = sp.year
#           )
#         ''', (year,))
#
#         pairs = cursor.fetchall()
#         conn.close()
#         return pairs
#
#     def reveal_all_pairs(self, year=2025, by_admin=False):
#         """Раскрыть все пары сразу"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         try:
#             # Получаем все нераскрытые пары
#             pairs = self.get_all_pairs_to_reveal(year)
#
#             if not pairs:
#                 return 0
#
#             revealed_count = 0
#             for santa_id, receiver_id, santa_name, receiver_name in pairs:
#                 cursor.execute('''
#                 INSERT OR IGNORE INTO revealed_pairs
#                 (santa_user_id, receiver_user_id, year, revealed_by_admin)
#                 VALUES (?, ?, ?, ?)
#                 ''', (santa_id, receiver_id, year, 1 if by_admin else 0))
#
#                 if cursor.rowcount > 0:
#                     revealed_count += 1
#
#             conn.commit()
#             conn.close()
#             print(f"✅ Раскрыто {revealed_count} пар")
#             return revealed_count
#
#         except Exception as e:
#             print(f"❌ Ошибка при раскрытии всех пар: {e}")
#             if conn:
#                 conn.close()
#             return 0
#
#     def is_pair_revealed(self, receiver_user_id, year=2025):
#         """Проверить, раскрыта ли пара для получателя"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT id FROM revealed_pairs
#         WHERE receiver_user_id = ? AND year = ?
#         ''', (receiver_user_id, year))
#
#         result = cursor.fetchone() is not None
#         conn.close()
#         return result
#
#     def get_player_by_name(self, full_name):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT * FROM players WHERE full_name = ?', (full_name,))
#         player = cursor.fetchone()
#
#         conn.close()
#         return player
#
#     def get_player_stats(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT COUNT(*) FROM players')
#         total_players = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = 2025')
#         total_pairs = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM revealed_pairs WHERE year = 2025')
#         total_revealed = cursor.fetchone()[0]
#
#         conn.close()
#
#         return {
#             'total_players': total_players,
#             'total_pairs': total_pairs,
#             'total_revealed': total_revealed
#         }
#
#     def mark_as_notified(self, user_id, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         UPDATE santa_pairs
#         SET is_notified = 1
#         WHERE santa_user_id = ? AND year = ?
#         ''', (user_id, year))
#
#         conn.commit()
#         conn.close()
#
#     def get_unnotified_pairs(self, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT sp.santa_user_id, p.full_name
#         FROM santa_pairs sp
#         JOIN players p ON sp.receiver_user_id = p.user_id
#         WHERE sp.year = ? AND sp.is_notified = 0
#         ''', (year,))
#
#         pairs = cursor.fetchall()
#         conn.close()
#
#         return pairs

# import os
# import psycopg2
# import random
# from datetime import datetime
# from urllib.parse import urlparse
#
#
# class Database:
#     def __init__(self):
#         # Получаем строку подключения из переменной окружения
#         database_url = os.environ.get('DATABASE_URL')
#
#         if not database_url:
#             print("⚠️ DATABASE_URL не найден! Используем SQLite для локальной разработки")
#             # Для локального тестирования используем SQLite
#             import sqlite3
#             self.db_type = 'sqlite'
#             self.db_name = 'secret_santa.db'
#             self.init_db()
#             return
#
#         # Парсим URL для PostgreSQL
#         self.db_type = 'postgresql'
#         self.conn_params = self.parse_db_url(database_url)
#         self.init_db()
#
#     def parse_db_url(self, url):
#         """Парсим DATABASE_URL в параметры для psycopg2"""
#         parsed = urlparse(url)
#         return {
#             'database': parsed.path[1:],
#             'user': parsed.username,
#             'password': parsed.password,
#             'host': parsed.hostname,
#             'port': parsed.port
#         }
#
#     def get_connection(self):
#         if self.db_type == 'sqlite':
#             import sqlite3
#             return sqlite3.connect(self.db_name)
#         else:
#             # Для PostgreSQL
#             return psycopg2.connect(**self.conn_params)
#
#     def init_db(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         # Адаптируем SQL под PostgreSQL
#         if self.db_type == 'postgresql':
#             # Таблица игроков
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS players (
#                 id SERIAL PRIMARY KEY,
#                 user_id INTEGER UNIQUE,
#                 username TEXT,
#                 full_name TEXT NOT NULL,
#                 telegram_name TEXT,
#                 wish_list TEXT,
#                 registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 is_active BOOLEAN DEFAULT TRUE
#             )
#             ''')
#
#             # Таблица пар
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS santa_pairs (
#                 id SERIAL PRIMARY KEY,
#                 santa_user_id INTEGER,
#                 receiver_user_id INTEGER,
#                 year INTEGER DEFAULT 2025,
#                 is_notified BOOLEAN DEFAULT FALSE,
#                 assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(santa_user_id, year)
#             )
#             ''')
#
#             # Таблица раскрытых пар
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS revealed_pairs (
#                 id SERIAL PRIMARY KEY,
#                 santa_user_id INTEGER,
#                 receiver_user_id INTEGER,
#                 year INTEGER DEFAULT 2025,
#                 revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 revealed_by_admin BOOLEAN DEFAULT FALSE
#             )
#             ''')
#         else:
#             # SQLite версия (для локальной разработки)
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS players (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER UNIQUE,
#                 username TEXT,
#                 full_name TEXT NOT NULL,
#                 telegram_name TEXT,
#                 wish_list TEXT,
#                 registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 is_active BOOLEAN DEFAULT 1
#             )
#             ''')
#
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS santa_pairs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 santa_user_id INTEGER,
#                 receiver_user_id INTEGER,
#                 year INTEGER DEFAULT 2025,
#                 is_notified BOOLEAN DEFAULT 0,
#                 assignment_date TIMESTAMP,
#                 UNIQUE(santa_user_id, year)
#             )
#             ''')
#
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS revealed_pairs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 santa_user_id INTEGER,
#                 receiver_user_id INTEGER,
#                 year INTEGER DEFAULT 2025,
#                 revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 revealed_by_admin BOOLEAN DEFAULT 0
#             )
#             ''')
#
#         conn.commit()
#         conn.close()
#         print(f"✅ База данных инициализирована ({self.db_type})")
#
#     def add_player(self, user_id, username, full_name, telegram_name=None, wish_list=None):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         try:
#             if self.db_type == 'postgresql':
#                 cursor.execute('''
#                 INSERT INTO players (user_id, username, full_name, telegram_name, wish_list, is_active)
#                 VALUES (%s, %s, %s, %s, %s, TRUE)
#                 ON CONFLICT (user_id) DO UPDATE SET
#                     username = EXCLUDED.username,
#                     full_name = EXCLUDED.full_name,
#                     telegram_name = EXCLUDED.telegram_name,
#                     wish_list = EXCLUDED.wish_list,
#                     is_active = TRUE
#                 ''', (user_id, username, full_name, telegram_name, wish_list))
#             else:
#                 cursor.execute('''
#                 INSERT OR REPLACE INTO players
#                 (user_id, username, full_name, telegram_name, wish_list, is_active)
#                 VALUES (?, ?, ?, ?, ?, 1)
#                 ''', (user_id, username, full_name, telegram_name, wish_list))
#
#             conn.commit()
#             print(f"✅ Игрок добавлен в БД: {full_name} (@{username})")
#             return True
#         except Exception as e:
#             print(f"❌ Ошибка при добавлении игрока: {e}")
#             return False
#         finally:
#             conn.close()
#
#     # ВСЕ остальные методы остаются почти без изменений,
#     # только заменяем ? на %s для PostgreSQL
#
#     def get_all_active_players(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('''
#         SELECT user_id, full_name, username
#         FROM players
#         WHERE is_active = TRUE
#         ''' if self.db_type == 'postgresql' else '''
#         SELECT user_id, full_name, username
#         FROM players
#         WHERE is_active = 1
#         ''')
#
#         players = cursor.fetchall()
#         conn.close()
#         return players
#
#     def get_player(self, user_id):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         param = (user_id,)
#         cursor.execute('SELECT * FROM players WHERE user_id = %s' if self.db_type == 'postgresql'
#                        else 'SELECT * FROM players WHERE user_id = ?', param)
#
#         player = cursor.fetchone()
#         conn.close()
#         return player
#
#     def perform_draw(self, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = %s' if self.db_type == 'postgresql'
#                        else 'SELECT COUNT(*) FROM santa_pairs WHERE year = ?', (year,))
#
#         if cursor.fetchone()[0] > 0:
#             print("⚠️ Жеребьёвка уже проводилась в этом году!")
#             conn.close()
#             return False
#
#         players = self.get_all_active_players()
#         player_ids = [player[0] for player in players]
#
#         if len(player_ids) < 2:
#             print("⚠️ Недостаточно игроков для жеребьёвки!")
#             conn.close()
#             return False
#
#         receivers = player_ids.copy()
#         random.shuffle(receivers)
#
#         attempts = 0
#         while any(santa == receiver for santa, receiver in zip(player_ids, receivers)) and attempts < 100:
#             random.shuffle(receivers)
#             attempts += 1
#
#         for santa_id, receiver_id in zip(player_ids, receivers):
#             if self.db_type == 'postgresql':
#                 cursor.execute('''
#                 INSERT INTO santa_pairs
#                 (santa_user_id, receiver_user_id, year, assignment_date)
#                 VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
#                 ''', (santa_id, receiver_id, year))
#             else:
#                 cursor.execute('''
#                 INSERT INTO santa_pairs
#                 (santa_user_id, receiver_user_id, year, assignment_date)
#                 VALUES (?, ?, ?, datetime('now'))
#                 ''', (santa_id, receiver_id, year))
#
#         conn.commit()
#         conn.close()
#         print(f"🎅 Жеребьёвка проведена! Создано {len(player_ids)} пар.")
#         return True
#
#     def get_santa_pair(self, user_id, year=2025):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         param = (user_id, year)
#         cursor.execute('''
#         SELECT p.full_name
#         FROM santa_pairs sp
#         JOIN players p ON sp.receiver_user_id = p.user_id
#         WHERE sp.santa_user_id = %s AND sp.year = %s
#         ''' if self.db_type == 'postgresql' else '''
#         SELECT p.full_name
#         FROM santa_pairs sp
#         JOIN players p ON sp.receiver_user_id = p.user_id
#         WHERE sp.santa_user_id = ? AND sp.year = ?
#         ''', param)
#
#         pair = cursor.fetchone()
#         conn.close()
#         return pair[0] if pair else None
#
#     # Остальные методы аналогично - заменяем ? на %s где нужно
#
#     def get_player_by_name(self, full_name):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         param = (full_name,)
#         cursor.execute('SELECT * FROM players WHERE full_name = %s' if self.db_type == 'postgresql'
#                        else 'SELECT * FROM players WHERE full_name = ?', param)
#
#         player = cursor.fetchone()
#         conn.close()
#         return player
#
#     def get_player_stats(self):
#         conn = self.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute('SELECT COUNT(*) FROM players')
#         total_players = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = 2025')
#         total_pairs = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM revealed_pairs WHERE year = 2025')
#         total_revealed = cursor.fetchone()[0]
#
#         conn.close()
#
#         return {
#             'total_players': total_players,
#             'total_pairs': total_pairs,
#             'total_revealed': total_revealed
#         }

import os
import sqlite3
import random
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self):
        # Определяем путь к базе данных
        if os.getenv("RAILWAY_ENVIRONMENT"):
            # На Railway используем /tmp для записи
            self.db_path = "/tmp/secret_santa.db"
        else:
            # Локально используем текущую директорию
            self.db_path = "secret_santa.db"

        self.init_db()
        print(f"✅ База данных инициализирована по пути: {self.db_path}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT NOT NULL,
            telegram_name TEXT,
            wish_list TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS santa_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            santa_user_id INTEGER,
            receiver_user_id INTEGER,
            year INTEGER DEFAULT 2025,
            is_notified BOOLEAN DEFAULT 0,
            assignment_date TIMESTAMP,
            UNIQUE(santa_user_id, year)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS revealed_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            santa_user_id INTEGER,
            receiver_user_id INTEGER,
            year INTEGER DEFAULT 2025,
            revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revealed_by_admin BOOLEAN DEFAULT 0
        )
        ''')

        conn.commit()
        conn.close()

    def add_player(self, user_id, username, full_name, telegram_name=None, wish_list=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
            INSERT OR REPLACE INTO players
            (user_id, username, full_name, telegram_name, wish_list, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            ''', (user_id, username, full_name, telegram_name, wish_list))

            conn.commit()
            print(f"✅ Игрок добавлен в БД: {full_name} (@{username})")
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении игрока: {e}")
            return False
        finally:
            conn.close()

    def get_all_active_players(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT user_id, full_name, username
        FROM players
        WHERE is_active = 1
        ''')

        players = cursor.fetchall()
        conn.close()
        return players

    def get_player(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()
        conn.close()

        return player

    def perform_draw(self, year=2025):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = ?', (year,))
        if cursor.fetchone()[0] > 0:
            print("⚠️ Жеребьёвка уже проводилась в этом году!")
            conn.close()
            return False

        players = self.get_all_active_players()
        player_ids = [player[0] for player in players]

        if len(player_ids) < 2:
            print("⚠️ Недостаточно игроков для жеребьёвки!")
            conn.close()
            return False

        receivers = player_ids.copy()
        random.shuffle(receivers)

        attempts = 0
        while any(santa == receiver for santa, receiver in zip(player_ids, receivers)) and attempts < 100:
            random.shuffle(receivers)
            attempts += 1

        for santa_id, receiver_id in zip(player_ids, receivers):
            cursor.execute('''
            INSERT INTO santa_pairs
            (santa_user_id, receiver_user_id, year, assignment_date)
            VALUES (?, ?, ?, datetime('now'))
            ''', (santa_id, receiver_id, year))

        conn.commit()
        conn.close()
        print(f"🎅 Жеребьёвка проведена! Создано {len(player_ids)} пар.")
        return True

    def get_santa_pair(self, user_id, year=2025):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT p.full_name
        FROM santa_pairs sp
        JOIN players p ON sp.receiver_user_id = p.user_id
        WHERE sp.santa_user_id = ? AND sp.year = ?
        ''', (user_id, year))

        pair = cursor.fetchone()
        conn.close()

        return pair[0] if pair else None

    def get_receiver_pair(self, user_id, year=2025):
        """Узнать, кто был Сантой для данного пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT p.full_name
        FROM santa_pairs sp
        JOIN players p ON sp.santa_user_id = p.user_id
        WHERE sp.receiver_user_id = ? AND sp.year = ?
        ''', (user_id, year))

        pair = cursor.fetchone()
        conn.close()

        return pair[0] if pair else None

    def reveal_pair(self, receiver_user_id, year=2025, by_admin=False):
        """Раскрыть пару: кто был Сантой для получателя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
            SELECT sp.santa_user_id, sp.receiver_user_id
            FROM santa_pairs sp
            WHERE sp.receiver_user_id = ? AND sp.year = ?
            ''', (receiver_user_id, year))

            pair = cursor.fetchone()

            if not pair:
                return None

            santa_user_id, receiver_user_id = pair

            cursor.execute('''
            SELECT id FROM revealed_pairs
            WHERE receiver_user_id = ? AND year = ?
            ''', (receiver_user_id, year))

            if cursor.fetchone():
                print(f"⚠️ Пара для получателя {receiver_user_id} уже раскрыта")
                conn.close()
                return self.get_receiver_pair(receiver_user_id, year)

            cursor.execute('''
            INSERT INTO revealed_pairs
            (santa_user_id, receiver_user_id, year, revealed_by_admin)
            VALUES (?, ?, ?, ?)
            ''', (santa_user_id, receiver_user_id, year, 1 if by_admin else 0))

            conn.commit()
            conn.close()

            player = self.get_player(santa_user_id)
            return player[3] if player else None

        except Exception as e:
            print(f"❌ Ошибка при раскрытии пары: {e}")
            if conn:
                conn.close()
            return None

    def get_all_pairs_to_reveal(self, year=2025):
        """Получить все пары, которые еще не раскрыты"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT sp.santa_user_id, sp.receiver_user_id,
               santa.full_name as santa_name, receiver.full_name as receiver_name
        FROM santa_pairs sp
        JOIN players santa ON sp.santa_user_id = santa.user_id
        JOIN players receiver ON sp.receiver_user_id = receiver.user_id
        WHERE sp.year = ?
          AND NOT EXISTS (
              SELECT 1 FROM revealed_pairs rp
              WHERE rp.receiver_user_id = sp.receiver_user_id AND rp.year = sp.year
          )
        ''', (year,))

        pairs = cursor.fetchall()
        conn.close()
        return pairs

    def reveal_all_pairs(self, year=2025, by_admin=False):
        """Раскрыть все пары сразу"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            pairs = self.get_all_pairs_to_reveal(year)

            if not pairs:
                return 0

            revealed_count = 0
            for santa_id, receiver_id, santa_name, receiver_name in pairs:
                cursor.execute('''
                INSERT OR IGNORE INTO revealed_pairs
                (santa_user_id, receiver_user_id, year, revealed_by_admin)
                VALUES (?, ?, ?, ?)
                ''', (santa_id, receiver_id, year, 1 if by_admin else 0))

                if cursor.rowcount > 0:
                    revealed_count += 1

            conn.commit()
            conn.close()
            print(f"✅ Раскрыто {revealed_count} пар")
            return revealed_count

        except Exception as e:
            print(f"❌ Ошибка при раскрытии всех пар: {e}")
            if conn:
                conn.close()
            return 0

    def is_pair_revealed(self, receiver_user_id, year=2025):
        """Проверить, раскрыта ли пара для получателя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id FROM revealed_pairs
        WHERE receiver_user_id = ? AND year = ?
        ''', (receiver_user_id, year))

        result = cursor.fetchone() is not None
        conn.close()
        return result

    def get_player_by_name(self, full_name):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM players WHERE full_name = ?', (full_name,))
        player = cursor.fetchone()

        conn.close()
        return player

    def get_player_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM players')
        total_players = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM santa_pairs WHERE year = 2025')
        total_pairs = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM revealed_pairs WHERE year = 2025')
        total_revealed = cursor.fetchone()[0]

        conn.close()

        return {
            'total_players': total_players,
            'total_pairs': total_pairs,
            'total_revealed': total_revealed
        }

    def mark_as_notified(self, user_id, year=2025):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE santa_pairs
        SET is_notified = 1
        WHERE santa_user_id = ? AND year = ?
        ''', (user_id, year))

        conn.commit()
        conn.close()

    def get_unnotified_pairs(self, year=2025):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT sp.santa_user_id, p.full_name
        FROM santa_pairs sp
        JOIN players p ON sp.receiver_user_id = p.user_id
        WHERE sp.year = ? AND sp.is_notified = 0
        ''', (year,))

        pairs = cursor.fetchall()
        conn.close()

        return pairs