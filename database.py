import os
import sys
import logging
import random
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

# Настройка логгера
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """
        Инициализация базы данных.
        Автоматически определяет тип БД на основе доступных переменных окружения.
        """
        self.db_type = self._detect_database_type()
        self._setup_connection()
        self.init_db()
        logger.info(f"✅ База данных инициализирована. Тип: {self.db_type}")

    def _detect_database_type(self) -> str:
        """Определяет тип базы данных."""
        database_url = os.getenv('DATABASE_URL')
        
        if database_url and 'postgres' in database_url.lower():
            logger.info("🔍 Обнаружена переменная DATABASE_URL, использую PostgreSQL")
            return 'postgresql'
        else:
            logger.info("🔍 Переменная DATABASE_URL не найдена, использую SQLite")
            return 'sqlite'

    def _setup_connection(self):
        """Настраивает параметры подключения."""
        if self.db_type == 'postgresql':
            self.conn_string = os.getenv('DATABASE_URL')
            if not self.conn_string:
                raise ValueError("❌ DATABASE_URL не найден для PostgreSQL")
        else:
            # SQLite - определяем путь к файлу
            if os.getenv('RAILWAY_ENVIRONMENT'):
                # На Railway используем /tmp (сохраняется между перезапусками)
                self.db_path = '/tmp/secret_santa.db'
            else:
                # Локальная разработка
                self.db_path = 'secret_santa.db'
            
            logger.info(f"📁 Путь к SQLite базе: {self.db_path}")

    def get_connection(self):
        """Возвращает подключение к базе данных с правильным адаптером."""
        try:
            if self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extras import RealDictCursor
                # Для Railway PostgreSQL важно использовать sslmode=require
                conn = psycopg2.connect(self.conn_string, sslmode='require')
                # Для удобства работы с результатами как со словарями
                conn.cursor_factory = RealDictCursor
            else:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                # Для совместимости с PostgreSQL, используем row_factory
                conn.row_factory = sqlite3.Row
            
            return conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД ({self.db_type}): {e}")
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
                # Преобразуем результат в словарь для единообразия
                if result and self.db_type == 'sqlite':
                    result = dict(result)
            elif fetchall:
                result = cursor.fetchall()
                # Преобразуем результат в список словарей
                if result and self.db_type == 'sqlite':
                    result = [dict(row) for row in result]
            else:
                result = cursor.rowcount
                conn.commit()
            
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка SQL: {e}")
            logger.error(f"📝 Запрос: {query}")
            if params:
                logger.error(f"📌 Параметры: {params}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def init_db(self):
        """Инициализирует таблицы в базе данных."""
        if self.db_type == 'postgresql':
            # PostgreSQL таблицы
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS players (
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
            
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS santa_pairs (
                    id SERIAL PRIMARY KEY,
                    santa_user_id BIGINT NOT NULL,
                    receiver_user_id BIGINT NOT NULL,
                    year INTEGER DEFAULT 2025,
                    is_notified BOOLEAN DEFAULT FALSE,
                    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(santa_user_id, year)
                )
            ''')
            
            self._execute_query('''
                CREATE TABLE IF NOT EXISTS revealed_pairs (
                    id SERIAL PRIMARY KEY,
                    santa_user_id BIGINT NOT NULL,
                    receiver_user_id BIGINT NOT NULL,
                    year INTEGER DEFAULT 2025,
                    revealed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revealed_by_admin BOOLEAN DEFAULT FALSE
                )
            ''')
        else:
            # SQLite таблицы (сохраняем для обратной совместимости)
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
                    assignment_date TIMESTAMP,
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
        
        logger.info("✅ Таблицы базы данных проверены/созданы.")

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ИГРОКАМИ ===

    def add_player(self, user_id, username, full_name, telegram_name=None, wish_list=None):
        """Добавление или обновление игрока."""
        try:
            if self.db_type == 'postgresql':
                query = '''
                    INSERT INTO players (user_id, username, full_name, telegram_name, wish_list, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        full_name = EXCLUDED.full_name,
                        telegram_name = EXCLUDED.telegram_name,
                        wish_list = EXCLUDED.wish_list,
                        is_active = TRUE
                '''
            else:
                query = '''
                    INSERT OR REPLACE INTO players
                    (user_id, username, full_name, telegram_name, wish_list, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                '''
            
            self._execute_query(query, (user_id, username, full_name, telegram_name, wish_list))
            logger.info(f"✅ Игрок добавлен/обновлен: {full_name} (@{username})")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении игрока: {e}")
            return False

    def get_player(self, user_id):
        """Получение информации об игроке по ID."""
        query = 'SELECT * FROM players WHERE user_id = ?'
        result = self._execute_query(query, (user_id,), fetchone=True)
        return result

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
        
        result = self._execute_query(query, fetchall=True)
        # Конвертируем в список кортежей для обратной совместимости
        if result and isinstance(result[0], dict):
            return [(row['user_id'], row['full_name'], row['username']) for row in result]
        return result

    def get_player_by_name(self, full_name):
        """Поиск игрока по полному имени."""
        query = 'SELECT * FROM players WHERE full_name = ?'
        return self._execute_query(query, (full_name,), fetchone=True)

    # === МЕТОДЫ ДЛЯ ЖЕРЕБЬЁВКИ И ПАР ===

    def perform_draw(self, year=2025):
        """Проведение жеребьёвки."""
        # Проверяем, не проводилась ли уже жеребьёвка
        query = 'SELECT COUNT(*) as count FROM santa_pairs WHERE year = ?'
        result = self._execute_query(query, (year,), fetchone=True)
        
        if result and result['count'] > 0:
            logger.warning(f"⚠️ Жеребьёвка уже проводилась в {year} году!")
            return False

        # Получаем активных игроков
        players = self.get_all_active_players()
        player_ids = [player[0] for player in players]

        if len(player_ids) < 2:
            logger.warning("⚠️ Недостаточно игроков для жеребьёвки!")
            return False

        # Алгоритм жеребьёвки
        receivers = player_ids.copy()
        random.shuffle(receivers)

        attempts = 0
        while any(santa == receiver for santa, receiver in zip(player_ids, receivers)) and attempts < 100:
            random.shuffle(receivers)
            attempts += 1

        if attempts >= 100:
            logger.error("❌ Не удалось создать уникальные пары!")
            return False

        # Создаем пары
        for santa_id, receiver_id in zip(player_ids, receivers):
            if self.db_type == 'postgresql':
                self._execute_query('''
                    INSERT INTO santa_pairs (santa_user_id, receiver_user_id, year)
                    VALUES (%s, %s, %s)
                ''', (santa_id, receiver_id, year))
            else:
                self._execute_query('''
                    INSERT INTO santa_pairs (santa_user_id, receiver_user_id, year, assignment_date)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (santa_id, receiver_id, year))

        logger.info(f"🎅 Жеребьёвка проведена! Создано {len(player_ids)} пар.")
        return True

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
            # Проверяем, не раскрыта ли уже пара
            check_query = '''
                SELECT id FROM revealed_pairs 
                WHERE receiver_user_id = ? AND year = ?
            '''
            existing = self._execute_query(check_query, (receiver_user_id, year), fetchone=True)
            
            if existing:
                logger.warning(f"⚠️ Пара для получателя {receiver_user_id} уже раскрыта")
                return self.get_receiver_pair(receiver_user_id, year)

            # Получаем информацию о паре
            pair_query = '''
                SELECT sp.santa_user_id, sp.receiver_user_id
                FROM santa_pairs sp
                WHERE sp.receiver_user_id = ? AND sp.year = ?
            '''
            pair = self._execute_query(pair_query, (receiver_user_id, year), fetchone=True)
            
            if not pair:
                logger.error(f"❌ Пара для получателя {receiver_user_id} не найдена")
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
            return santa['full_name'] if santa else None

        except Exception as e:
            logger.error(f"❌ Ошибка при раскрытии пары: {e}")
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
        # Конвертируем для обратной совместимости
        if result and isinstance(result[0], dict):
            return [(row['santa_user_id'], row['receiver_user_id'], 
                     row['santa_name'], row['receiver_name']) for row in result]
        return result

    def reveal_all_pairs(self, year=2025, by_admin=False):
        """Раскрыть все пары сразу."""
        try:
            pairs = self.get_all_pairs_to_reveal(year)
            
            if not pairs:
                logger.info("ℹ️ Нет пар для раскрытия")
                return 0

            revealed_count = 0
            for santa_id, receiver_id, santa_name, receiver_name in pairs:
                # Проверяем, не раскрыта ли уже эта пара
                check_query = '''
                    SELECT id FROM revealed_pairs 
                    WHERE receiver_user_id = ? AND year = ?
                '''
                existing = self._execute_query(check_query, (receiver_id, year), fetchone=True)
                
                if not existing:
                    insert_query = '''
                        INSERT INTO revealed_pairs 
                        (santa_user_id, receiver_user_id, year, revealed_by_admin)
                        VALUES (?, ?, ?, ?)
                    '''
                    if self.db_type == 'postgresql':
                        insert_query = insert_query.replace('?', '%s')
                    
                    self._execute_query(insert_query, (santa_id, receiver_id, year, by_admin))
                    revealed_count += 1

            logger.info(f"✅ Раскрыто {revealed_count} пар")
            return revealed_count

        except Exception as e:
            logger.error(f"❌ Ошибка при раскрытии всех пар: {e}")
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
            total_players = self._execute_query(
                'SELECT COUNT(*) as count FROM players', 
                fetchone=True
            )['count']
            
            total_pairs = self._execute_query(
                'SELECT COUNT(*) as count FROM santa_pairs WHERE year = 2025', 
                fetchone=True
            )['count']
            
            total_revealed = self._execute_query(
                'SELECT COUNT(*) as count FROM revealed_pairs WHERE year = 2025', 
                fetchone=True
            )['count']

            return {
                'total_players': total_players or 0,
                'total_pairs': total_pairs or 0,
                'total_revealed': total_revealed or 0
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при получении статистики: {e}")
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
        # Конвертируем для обратной совместимости
        if result and isinstance(result[0], dict):
            return [(row['santa_user_id'], row['full_name']) for row in result]
        return result

    def get_all_players_with_wishlists(self):
        """Получить всех игроков с их wishlist."""
        query = '''
            SELECT user_id, full_name, username, wish_list
            FROM players
            WHERE is_active = TRUE AND wish_list IS NOT NULL AND wish_list != ''
            ORDER BY full_name
        '''
        return self._execute_query(query, fetchall=True)
