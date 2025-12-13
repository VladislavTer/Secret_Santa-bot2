import os
import sys
import logging
import random
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """
        Инициализация базы данных.
        Автоматически определяет тип БД на основе доступных переменных окружения.
        """
        print("=" * 60)
        print("🔧 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        # ВЫВОД ВСЕХ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ДЛЯ ДЕБАГА
        print("🔍 DEBUG: Переменные окружения:")
        for key, value in os.environ.items():
            if any(db_key in key.lower() for db_key in ['database', 'postgres', 'pg', 'railway']):
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
        print("-" * 40)
        
        self.db_type = self._detect_database_type()
        self._setup_connection()
        self.init_db()
        
        print(f"✅ База данных инициализирована. Тип: {self.db_type}")
        if self.db_type == 'postgresql':
            print(f"📦 Connection: {self.conn_string[:50]}..." if self.conn_string else "📦 Connection: установлено")
        else:
            print(f"📁 SQLite путь: {self.db_path}")
        print("=" * 60)

    def _detect_database_type(self) -> str:
        """Определяет тип базы данных."""
        # ПРОВЕРКА ВСЕХ ВОЗМОЖНЫХ ПЕРЕМЕННЫХ
        possible_vars = [
            'DATABASE_URL',
            'RAILWAY_DATABASE_URL',
            'POSTGRESQL_URL',
            'PG_CONNECTION_STRING',
            'NEON_DATABASE_URL',
        ]
        
        for var in possible_vars:
            value = os.getenv(var)
            if value and ('postgres' in value.lower() or 'postgresql' in value.lower()):
                print(f"✅ Обнаружена переменная {var}, использую PostgreSQL")
                return 'postgresql'
        
        # ПРОВЕРКА ПО ОТДЕЛЬНЫМ ПАРАМЕТРАМ (для старого config.py)
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if all([db_host, db_name, db_user, db_password]):
            print("✅ Обнаружены параметры БД в config, использую PostgreSQL")
            return 'postgresql'
        
        print("⚠️ PostgreSQL переменные не найдены, использую SQLite")
        return 'sqlite'

    def _setup_connection(self):
        """Настраивает параметры подключения."""
        if self.db_type == 'postgresql':
            # Пытаемся получить DATABASE_URL из окружения
            self.conn_string = os.getenv('DATABASE_URL')
            
            # Если нет DATABASE_URL, собираем из отдельных параметров
            if not self.conn_string:
                db_host = os.getenv('DB_HOST', 'postgres.railway.internal')
                db_name = os.getenv('DB_NAME', 'railway')
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD', '')
                db_port = os.getenv('DB_PORT', '5432')
                
                self.conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                print(f"🔗 Собран DATABASE_URL из параметров")
            
            if not self.conn_string:
                raise ValueError("❌ Не удалось определить строку подключения PostgreSQL")
                
        else:
            # SQLite
            if os.getenv('RAILWAY_ENVIRONMENT'):
                self.db_path = '/tmp/secret_santa.db'
            else:
                self.db_path = 'secret_santa.db'
            
            logger.info(f"📁 Путь к SQLite базе: {self.db_path}")

    def get_connection(self):
        """Возвращает подключение к базе данных с правильным адаптером."""
        try:
            if self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extras import RealDictCursor
                
                # Для Railway PostgreSQL важно использовать sslmode=require
                try:
                    conn = psycopg2.connect(self.conn_string, sslmode='require')
                except:
                    # Пробуем без sslmode для совместимости
                    conn = psycopg2.connect(self.conn_string)
                
                conn.autocommit = True
                conn.cursor_factory = RealDictCursor
                return conn
                
            else:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                return conn
                
        except Exception as e:
            error_msg = f"❌ Ошибка подключения к БД ({self.db_type}): {e}"
            if self.db_type == 'postgresql':
                error_msg += f"\n📦 Connection string: {self.conn_string[:50]}..."
            print(error_msg)
            raise

    def _execute_query(self, query: str, params: tuple = None, 
                       fetchone: bool = False, fetchall: bool = False):
        """
        Универсальный метод выполнения SQL запросов.
        Автоматически адаптирует запросы под тип БД.
        """
        # Заменяем SQLite-специфичные конструкции на PostgreSQL-совместимые
        if self.db_type == 'postgresql':
            query = query.replace('?', '%s')
            query = query.replace('datetime(\'now\')', 'CURRENT_TIMESTAMP')
            query = query.replace('INSERT OR REPLACE', 'INSERT')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = None
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка SQL: {e}")
            logger.error(f"📝 Запрос: {query[:100]}...")
            if params:
                logger.error(f"📌 Параметры: {params}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def init_db(self):
        """Инициализирует таблицы в базе данных."""
        print("🗃️  Создание/проверка таблиц...")
        
        if self.db_type == 'postgresql':
            # Сначала удаляем старые таблицы если они есть (для чистого старта)
            print("🧹 Очистка старых таблиц...")
            try:
                self._execute_query('DROP TABLE IF EXISTS revealed_pairs CASCADE')
                self._execute_query('DROP TABLE IF EXISTS santa_pairs CASCADE')
                self._execute_query('DROP TABLE IF EXISTS players CASCADE')
                print("✅ Старые таблицы удалены")
            except Exception as e:
                print(f"⚠️  Не удалось удалить таблицы: {e}")
            
            # Создаем таблицы с правильными constraints
            print("🔄 Создание новых таблиц...")
            
            # Таблица players С UNIQUE constraint
            self._execute_query('''
                CREATE TABLE players (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    telegram_name TEXT,
                    wish_list TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            print("✅ Таблица 'players' создана с UNIQUE constraint на user_id")
            
            # Таблица santa_pairs
            self._execute_query('''
                CREATE TABLE santa_pairs (
                    id SERIAL PRIMARY KEY,
                    santa_user_id BIGINT NOT NULL REFERENCES players(user_id),
                    receiver_user_id BIGINT NOT NULL REFERENCES players(user_id),
                    year INTEGER DEFAULT 2025,
                    is_notified BOOLEAN DEFAULT FALSE,
                    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(santa_user_id, year)
                )
            ''')
            print("✅ Таблица 'santa_pairs' создана")
            
            # Таблица revealed_pairs
            self._execute_query('''
                CREATE TABLE revealed_pairs (
                    id SERIAL PRIMARY KEY,
                    santa_user_id BIGINT NOT NULL REFERENCES players(user_id),
                    receiver_user_id BIGINT NOT NULL REFERENCES players(user_id),
                    year INTEGER DEFAULT 2025,
                    revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revealed_by_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            print("✅ Таблица 'revealed_pairs' создана")
            
            print("✅ Все PostgreSQL таблицы созданы с правильными constraints")
            
        else:
            # SQLite таблицы (оставляем для локальной разработки)
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    telegram_name TEXT,
                    wish_list TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS santa_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    santa_user_id INTEGER NOT NULL,
                    receiver_user_id INTEGER NOT NULL,
                    year INTEGER DEFAULT 2025,
                    is_notified BOOLEAN DEFAULT 0,
                    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(santa_user_id, year)
                )
            ''')
            
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS revealed_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    santa_user_id INTEGER NOT NULL,
                    receiver_user_id INTEGER NOT NULL,
                    year INTEGER DEFAULT 2025,
                    revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revealed_by_admin BOOLEAN DEFAULT 0
                )
            ''')
            
            print("✅ SQLite таблицы проверены/созданы")

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ИГРОКАМИ ===
    # 🔍 МЕТОД add_player НАХОДИТСЯ ЗДЕСЬ (строка ~175)

    def add_player(self, user_id, username, full_name, telegram_name=None, wish_list=None):
        """Добавление или обновление игрока."""
        try:
            print(f"📝 Добавление игрока: {full_name} (ID: {user_id})")
            
            # Обработка None значений
            username = username if username else ''
            telegram_name = telegram_name if telegram_name else ''
            wish_list = wish_list if wish_list else ''
            
            if self.db_type == 'postgresql':
                # УНИВЕРСАЛЬНЫЙ МЕТОД ДЛЯ POSTGRESQL
                query = '''
                    INSERT INTO players 
                    (user_id, username, full_name, telegram_name, wish_list, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        full_name = EXCLUDED.full_name,
                        telegram_name = EXCLUDED.telegram_name,
                        wish_list = EXCLUDED.wish_list,
                        is_active = TRUE
                '''
                self._execute_query(query, (user_id, username, full_name, telegram_name, wish_list))
                print(f"✅ Игрок добавлен/обновлен: {full_name}")
                
            else:
                # SQLite версия
                query = '''
                    INSERT OR REPLACE INTO players
                    (user_id, username, full_name, telegram_name, wish_list, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                '''
                self._execute_query(query, (user_id, username, full_name, telegram_name, wish_list))
                print(f"✅ Игрок добавлен/обновлен: {full_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении игрока: {e}")
            print(f"   Параметры: user_id={user_id}, username={username}, full_name={full_name}")
            return False

    def get_player(self, user_id):
        """Получение информации об игроке по ID."""
        query = 'SELECT * FROM players WHERE user_id = ?'
        try:
            result = self._execute_query(query, (user_id,), fetchone=True)
            return result
        except Exception as e:
            print(f"❌ Ошибка получения игрока {user_id}: {e}")
            return None

    def get_all_active_players(self):
        """Получение списка всех активных игроков."""
        if self.db_type == 'postgresql':
            query = '''
                SELECT user_id, full_name, username
                FROM players
                WHERE is_active = TRUE
                ORDER BY full_name
            '''
        else:
            query = '''
                SELECT user_id, full_name, username
                FROM players
                WHERE is_active = 1
                ORDER BY full_name
            '''
        
        try:
            result = self._execute_query(query, fetchall=True)
            if result and isinstance(result[0], dict):
                return [(row['user_id'], row['full_name'], row['username']) for row in result]
            return result or []
        except Exception as e:
            print(f"❌ Ошибка получения игроков: {e}")
            return []

    def get_player_by_name(self, full_name):
        """Поиск игрока по полному имени."""
        query = 'SELECT * FROM players WHERE full_name = ?'
        return self._execute_query(query, (full_name,), fetchone=True)

    # === МЕТОДЫ ДЛЯ ЖЕРЕБЬЁВКИ И ПАР ===

    def perform_draw(self, year=2025, bot=None):
    """Проведение жеребьёвки и отправка уведомлений."""
    try:
        print(f"🎅 Проведение жеребьёвки для {year} года...")
        
        # Проверяем, не проводилась ли уже жеребьёвка
        query = 'SELECT COUNT(*) as count FROM santa_pairs WHERE year = ?'
        result = self._execute_query(query, (year,), fetchone=True)
        
        if result and result['count'] > 0:
            print(f"⚠️ Жеребьёвка уже проводилась в {year} году!")
            return False

        # Получаем активных игроков
        players = self.get_all_active_players()
        player_ids = [player[0] for player in players]

        if len(player_ids) < 2:
            print("⚠️ Недостаточно игроков для жеребьёвки!")
            return False

        # Алгоритм жеребьёвки
        receivers = player_ids.copy()
        random.shuffle(receivers)

        attempts = 0
        while any(santa == receiver for santa, receiver in zip(player_ids, receivers)) and attempts < 100:
            random.shuffle(receivers)
            attempts += 1

        if attempts >= 100:
            print("❌ Не удалось создать уникальные пары!")
            return False

        # Создаем пары
        pairs_count = 0
        pairs_info = []  # Сохраняем информацию о парах для уведомлений
        
        for santa_id, receiver_id in zip(player_ids, receivers):
            if self.db_type == 'postgresql':
                self._execute_query('''
                    INSERT INTO santa_pairs (santa_user_id, receiver_user_id, year)
                    VALUES (%s, %s, %s)
                ''', (santa_id, receiver_id, year))
            else:
                self._execute_query('''
                    INSERT INTO santa_pairs (santa_user_id, receiver_user_id, year)
                    VALUES (?, ?, ?)
                ''', (santa_id, receiver_id, year))
            
            # Сохраняем информацию о паре
            santa_info = self.get_player(santa_id)
            receiver_info = self.get_player(receiver_id)
            
            if santa_info and receiver_info:
                pairs_info.append({
                    'santa_id': santa_id,
                    'santa_name': santa_info.get('full_name', f'Игрок {santa_id}'),
                    'receiver_id': receiver_id,
                    'receiver_name': receiver_info.get('full_name', f'Игрок {receiver_id}'),
                    'receiver_wishlist': receiver_info.get('wish_list', '')
                })
            
            pairs_count += 1

        print(f"✅ Жеребьёвка проведена! Создано {pairs_count} пар.")
        
        # ОТПРАВКА УВЕДОМЛЕНИЙ ИГРОКАМ
        if bot and pairs_info:
            print(f"📨 Отправка уведомлений {len(pairs_info)} игрокам...")
            notified_count = self._send_notifications(bot, pairs_info)
            print(f"✅ Отправлено {notified_count} уведомлений")
        
        return True
            
    except Exception as e:
        print(f"❌ Ошибка при проведении жеребьёвки: {e}")
        return False

    def _send_notifications(self, bot, pairs_info):
    """Отправка уведомлений игрокам об их подопечных."""
    notified_count = 0
    
    for pair in pairs_info:
        try:
            santa_id = pair['santa_id']
            receiver_name = pair['receiver_name']
            receiver_wishlist = pair['receiver_wishlist']
            
            # Формируем сообщение
            message = f"""
                            🎅 *Жеребьёвка проведена!*
                            
                            Твоим подопечным в игре "Тайный Санта" назначен: 
                            *{receiver_name}*
                            
                            🎁 *Информация о подопечном:*
                            {f"📝 *Пожелания:* {receiver_wishlist}" if receiver_wishlist else "📝 *Пожелания не указаны*"}
                            
                            📅 *Напоминание о датах:*
                            • Дедлайн для подарков: до 25.12.2025
                            • Раскрытие Сант: 31.12.2025
                            
                            *Совет:* Прояви креативность! Бюджет подарка: ~500₽
                            
                            Удачи в подготовке подарка! 🎄
                            """
            
            # Отправляем сообщение
            bot.send_message(santa_id, message, parse_mode='Markdown')
            print(f"   📤 Уведомление отправлено {pair['santa_name']} → {receiver_name}")
            
            # Помечаем как уведомленного
            self.mark_as_notified(santa_id, 2025)
            notified_count += 1
            
            # Небольшая задержка между сообщениями
            import time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Ошибка отправки уведомления {pair['santa_name']}: {e}")
    
    return notified_count


    def get_santa_pair(self, user_id, year=2025):
        """Получить получателя для данного Санты."""
        query = '''
            SELECT p.full_name
            FROM santa_pairs sp
            JOIN players p ON sp.receiver_user_id = p.user_id
            WHERE sp.santa_user_id = ? AND sp.year = ?
        '''
        result = self._execute_query(query, (user_id, year), fetchone=True)
        return result['full_name'] if result else None

    def get_receiver_pair(self, user_id, year=2025):
        """Узнать, кто был Сантой для данного пользователя."""
        query = '''
            SELECT p.full_name
            FROM santa_pairs sp
            JOIN players p ON sp.santa_user_id = p.user_id
            WHERE sp.receiver_user_id = ? AND sp.year = ?
        '''
        result = self._execute_query(query, (user_id, year), fetchone=True)
        return result['full_name'] if result else None

    # === МЕТОДЫ ДЛЯ РАСКРЫТИЯ ПАР ===

    def reveal_pair(self, receiver_user_id, year=2025, by_admin=False):
        """Раскрыть пару: кто был Сантой для получателя."""
        try:
            print(f"🔓 Раскрытие пары для пользователя {receiver_user_id}...")
            
            # Проверяем, не раскрыта ли уже пара
            if self.is_pair_revealed(receiver_user_id, year):
                print(f"⚠️ Пара для получателя {receiver_user_id} уже раскрыта")
                return self.get_receiver_pair(receiver_user_id, year)

            # Получаем информацию о паре
            pair_query = '''
                SELECT sp.santa_user_id, sp.receiver_user_id
                FROM santa_pairs sp
                WHERE sp.receiver_user_id = ? AND sp.year = ?
            '''
            pair = self._execute_query(pair_query, (receiver_user_id, year), fetchone=True)
            
            if not pair:
                print(f"❌ Пара для получателя {receiver_user_id} не найдена")
                return None

            # Сохраняем в таблицу раскрытых пар
            insert_query = '''
                INSERT INTO revealed_pairs 
                (santa_user_id, receiver_user_id, year, revealed_by_admin)
                VALUES (?, ?, ?, ?)
            '''
            self._execute_query(insert_query, 
                               (pair['santa_user_id'], pair['receiver_user_id'], 
                                year, by_admin))

            # Возвращаем имя Санты
            santa = self.get_player(pair['santa_user_id'])
            santa_name = santa['full_name'] if santa else 'Неизвестно'
            
            print(f"✅ Пара раскрыта: Санта {santa_name} → Получатель {receiver_user_id}")
            return santa_name
            
        except Exception as e:
            print(f"❌ Ошибка при раскрытии пары: {e}")
            return None

    def get_all_pairs_to_reveal(self, year=2025):
        """Получить все пары, которые еще не раскрыты."""
        query = '''
            SELECT sp.santa_user_id, sp.receiver_user_id,
                   santa.full_name as santa_name, receiver.full_name as receiver_name
            FROM santa_pairs sp
            JOIN players santa ON sp.santa_user_id = santa.user_id
            JOIN players receiver ON sp.receiver_user_id = receiver.user_id
            WHERE sp.year = ?
              AND NOT EXISTS (
                  SELECT 1 FROM revealed_pairs rp
                  WHERE rp.receiver_user_id = sp.receiver_user_id 
                    AND rp.year = sp.year
              )
            ORDER BY santa.full_name
        '''
        result = self._execute_query(query, (year,), fetchall=True)
        
        if result and isinstance(result[0], dict):
            return [(row['santa_user_id'], row['receiver_user_id'], 
                     row['santa_name'], row['receiver_name']) for row in result]
        return result or []

    def reveal_all_pairs(self, year=2025, by_admin=False):
        """Раскрыть все пары сразу."""
        try:
            print(f"🔓 Раскрытие всех пар для {year} года...")
            pairs = self.get_all_pairs_to_reveal(year)
            
            if not pairs:
                print("ℹ️ Нет пар для раскрытия")
                return 0

            revealed_count = 0
            for santa_id, receiver_id, santa_name, receiver_name in pairs:
                if not self.is_pair_revealed(receiver_id, year):
                    insert_query = '''
                        INSERT INTO revealed_pairs 
                        (santa_user_id, receiver_user_id, year, revealed_by_admin)
                        VALUES (?, ?, ?, ?)
                    '''
                    if self.db_type == 'postgresql':
                        insert_query = insert_query.replace('?', '%s')
                    
                    self._execute_query(insert_query, (santa_id, receiver_id, year, by_admin))
                    revealed_count += 1

            print(f"✅ Раскрыто {revealed_count} пар")
            return revealed_count

        except Exception as e:
            print(f"❌ Ошибка при раскрытии всех пар: {e}")
            return 0

    def is_pair_revealed(self, receiver_user_id, year=2025):
        """Проверить, раскрыта ли пара для получателя."""
        query = '''
            SELECT id FROM revealed_pairs
            WHERE receiver_user_id = ? AND year = ?
        '''
        result = self._execute_query(query, (receiver_user_id, year), fetchone=True)
        return result is not None

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def get_player_stats(self):
        """Получить статистику по игрокам."""
        try:
            total_players_result = self._execute_query(
                'SELECT COUNT(*) as count FROM players', 
                fetchone=True
            )
            total_players = total_players_result['count'] if total_players_result else 0
            
            total_pairs_result = self._execute_query(
                'SELECT COUNT(*) as count FROM santa_pairs WHERE year = 2025', 
                fetchone=True
            )
            total_pairs = total_pairs_result['count'] if total_pairs_result else 0
            
            total_revealed_result = self._execute_query(
                'SELECT COUNT(*) as count FROM revealed_pairs WHERE year = 2025', 
                fetchone=True
            )
            total_revealed = total_revealed_result['count'] if total_revealed_result else 0

            return {
                'total_players': total_players,
                'total_pairs': total_pairs,
                'total_revealed': total_revealed
            }
        except Exception as e:
            print(f"❌ Ошибка при получении статистики: {e}")
            return {'total_players': 0, 'total_pairs': 0, 'total_revealed': 0}

    def mark_as_notified(self, user_id, year=2025):
        """Пометить пару как уведомленную."""
        if self.db_type == 'postgresql':
            query = '''
                UPDATE santa_pairs
                SET is_notified = TRUE
                WHERE santa_user_id = %s AND year = %s
            '''
        else:
            query = '''
                UPDATE santa_pairs
                SET is_notified = 1
                WHERE santa_user_id = ? AND year = ?
            '''
        
        self._execute_query(query, (user_id, year))

    def get_unnotified_pairs(self, year=2025):
        """Получить все неуведомленные пары."""
        if self.db_type == 'postgresql':
            query = '''
                SELECT sp.santa_user_id, p.full_name
                FROM santa_pairs sp
                JOIN players p ON sp.receiver_user_id = p.user_id
                WHERE sp.year = %s AND sp.is_notified = FALSE
                ORDER BY p.full_name
            '''
        else:
            query = '''
                SELECT sp.santa_user_id, p.full_name
                FROM santa_pairs sp
                JOIN players p ON sp.receiver_user_id = p.user_id
                WHERE sp.year = ? AND sp.is_notified = 0
                ORDER BY p.full_name
            '''
        
        result = self._execute_query(query, (year,), fetchall=True)
        if result and isinstance(result[0], dict):
            return [(row['santa_user_id'], row['full_name']) for row in result]
        return result or []

    def get_all_players_with_wishlists(self):
        """Получить всех игроков с их wishlist."""
        query = '''
            SELECT user_id, full_name, username, wish_list
            FROM players
            WHERE is_active = TRUE AND wish_list IS NOT NULL AND wish_list != ''
            ORDER BY full_name
        '''
        return self._execute_query(query, fetchall=True) or []

    def test_connection(self):
        """Тест подключения к базе данных."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("SELECT version();")
                version = cursor.fetchone()['version']
                print(f"✅ PostgreSQL подключена. Версия: {version}")
            else:
                cursor.execute("SELECT sqlite_version();")
                version = cursor.fetchone()[0]
                print(f"✅ SQLite подключена. Версия: {version}")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка тестирования подключения: {e}")
            return False

    def check_table_constraints(self):
        """Проверить constraints таблиц."""
        if self.db_type != 'postgresql':
            print("⚠️ Эта функция только для PostgreSQL")
            return
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Проверяем constraints таблицы players
            cursor.execute('''
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_name = 'players'
                ORDER BY tc.constraint_type, kcu.column_name;
            ''')
            
            constraints = cursor.fetchall()
            print("🔍 Constraints таблицы 'players':")
            for const in constraints:
                print(f"   - {const['constraint_name']}: {const['constraint_type']} на {const['column_name']}")
            
            cursor.close()
            conn.close()
            return constraints
        except Exception as e:
            print(f"❌ Ошибка проверки constraints: {e}")
            return None
