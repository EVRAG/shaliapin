"""Работа с базой данных"""
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import settings


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем существование таблицы и её структуру
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='messages'
            """)
            table_exists = await cursor.fetchone()
            
            if table_exists:
                # Таблица существует - проверяем структуру и мигрируем
                cursor = await db.execute("PRAGMA table_info(messages)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Если есть старые колонки, создаем новую таблицу и мигрируем данные
                if 'user_id' in column_names and 'name' not in column_names:
                    # Создаем временную таблицу с новой структурой
                    await db.execute("""
                        CREATE TABLE IF NOT EXISTS messages_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            age INTEGER,
                            gender TEXT,
                            mood TEXT,
                            message_text TEXT NOT NULL,
                            openai_response TEXT,
                            status TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_fetched BOOLEAN DEFAULT 0,
                            fetched_at TIMESTAMP
                        )
                    """)
                    
                    # Мигрируем данные (используем username как name, если есть)
                    await db.execute("""
                        INSERT INTO messages_new 
                        (id, name, age, gender, mood, message_text, openai_response, status, created_at, is_fetched, fetched_at)
                        SELECT 
                            id,
                            COALESCE(username, 'Пользователь ' || user_id) as name,
                            NULL as age,
                            NULL as gender,
                            NULL as mood,
                            message_text,
                            openai_response,
                            status,
                            created_at,
                            is_fetched,
                            fetched_at
                        FROM messages
                    """)
                    
                    # Удаляем старую таблицу и переименовываем новую
                    await db.execute("DROP TABLE messages")
                    await db.execute("ALTER TABLE messages_new RENAME TO messages")
                elif 'name' not in column_names:
                    # Добавляем новые колонки если их нет
                    await db.execute("ALTER TABLE messages ADD COLUMN name TEXT")
                    await db.execute("ALTER TABLE messages ADD COLUMN age INTEGER")
                    await db.execute("ALTER TABLE messages ADD COLUMN gender TEXT")
                    await db.execute("ALTER TABLE messages ADD COLUMN mood TEXT")
                    
                    # Заполняем name для существующих записей
                    await db.execute("""
                        UPDATE messages 
                        SET name = COALESCE(username, 'Пользователь ' || user_id)
                        WHERE name IS NULL
                    """)
                    
                    # Удаляем старые колонки если они есть
                    if 'user_id' in column_names:
                        # SQLite не поддерживает DROP COLUMN напрямую, нужно пересоздать таблицу
                        await db.execute("""
                            CREATE TABLE IF NOT EXISTS messages_temp (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                age INTEGER,
                                gender TEXT,
                                mood TEXT,
                                message_text TEXT NOT NULL,
                                openai_response TEXT,
                                status TEXT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                is_fetched BOOLEAN DEFAULT 0,
                                fetched_at TIMESTAMP
                            )
                        """)
                        await db.execute("""
                            INSERT INTO messages_temp 
                            (id, name, age, gender, mood, message_text, openai_response, status, created_at, is_fetched, fetched_at)
                            SELECT 
                                id,
                                COALESCE(name, username, 'Пользователь ' || COALESCE(user_id, 0)) as name,
                                NULL as age,
                                gender,
                                mood,
                                message_text,
                                openai_response,
                                status,
                                created_at,
                                is_fetched,
                                fetched_at
                            FROM messages
                        """)
                        await db.execute("DROP TABLE messages")
                        await db.execute("ALTER TABLE messages_temp RENAME TO messages")
                else:
                    if 'age' not in column_names:
                        await db.execute("ALTER TABLE messages ADD COLUMN age INTEGER")
            else:
                # Таблица не существует - создаем новую
                await db.execute("""
                    CREATE TABLE messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        age INTEGER,
                        gender TEXT,
                        mood TEXT,
                        message_text TEXT NOT NULL,
                        openai_response TEXT,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_fetched BOOLEAN DEFAULT 0,
                        fetched_at TIMESTAMP
                    )
                """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_fetched 
                ON messages(is_fetched, created_at)
            """)
            await db.commit()
    
    async def add_message(
        self,
        name: str,
        age: Optional[int],
        gender: Optional[str],
        mood: Optional[str],
        message_text: str,
        openai_response: str,
        status: str
    ) -> int:
        """Добавить сообщение в базу данных"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO messages 
                (name, age, gender, mood, message_text, openai_response, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, age, gender, mood, message_text, openai_response, status))
            await db.commit()
            return cursor.lastrowid
    
    async def get_next_unfetched_message(self) -> Optional[Dict[str, Any]]:
        """Получить следующее незабранное сообщение (с блокировкой)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Используем BEGIN IMMEDIATE для блокировки записи
            await db.execute("BEGIN IMMEDIATE")
            try:
                # Выбираем сообщение
                cursor = await db.execute("""
                    SELECT id, name, age, gender, mood, message_text, openai_response, 
                           status, created_at
                    FROM messages
                    WHERE is_fetched = 0 AND status = 'ok'
                    ORDER BY created_at ASC
                    LIMIT 1
                """)
                row = await cursor.fetchone()
                
                if not row:
                    await db.rollback()
                    return None
                
                message = {
                    'id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'mood': row[4],
                    'message_text': row[5],
                    'openai_response': row[6],
                    'status': row[7],
                    'created_at': row[8]
                }
                
                # Помечаем как забранное в той же транзакции
                await db.execute("""
                    UPDATE messages
                    SET is_fetched = 1, fetched_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), message['id']))
                
                await db.commit()
                return message
            except Exception as e:
                await db.rollback()
                raise
    
    async def get_latest_messages(self, limit: int = 5) -> list[Dict[str, Any]]:
        """Получить последние N сообщений со статусом 'ok' (без пометки как забранные)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, age, gender, mood, message_text, openai_response, 
                       status, created_at, is_fetched, fetched_at
                FROM messages
                WHERE status = 'ok'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append({
                    'id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'mood': row[4],
                    'message_text': row[5],
                    'openai_response': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'is_fetched': bool(row[9]),
                    'fetched_at': row[10]
                })
            
            return messages
    
    async def reset_queue(self) -> int:
        """Сбросить очередь - пометить все сообщения как незабранные"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE messages
                SET is_fetched = 0, fetched_at = NULL
                WHERE is_fetched = 1
            """)
            await db.commit()
            return cursor.rowcount
    
    async def get_last_approved_message(self) -> Optional[str]:
        """Получить текст последнего одобренного сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT message_text
                FROM messages
                WHERE status = 'ok'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = await cursor.fetchone()
            if row:
                return row[0]
            return None
    
    async def get_last_approved_messages(self, limit: int = 3) -> List[str]:
        """Получить тексты последних N одобренных сообщений"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT message_text
                FROM messages
                WHERE status = 'ok'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row and row[0]]
    
    
    async def get_all_messages(self) -> list[Dict[str, Any]]:
        """Получить все сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, age, gender, mood, message_text, openai_response, 
                       status, created_at, is_fetched, fetched_at
                FROM messages
                ORDER BY created_at DESC
            """)
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append({
                    'id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'mood': row[4],
                    'message_text': row[5],
                    'openai_response': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'is_fetched': bool(row[9]),
                    'fetched_at': row[10]
                })
            
            return messages
    
    async def update_message_status(self, message_id: int, status: str) -> bool:
        """Обновить статус сообщения"""
        if status not in ['ok', 'restricted']:
            raise ValueError(f"Invalid status: {status}")
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE messages
                SET status = ?
                WHERE id = ?
            """, (status, message_id))
            await db.commit()
            return cursor.rowcount > 0


# Глобальный экземпляр базы данных
db = Database(settings.database_path)

