import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="monopoly.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных (аналогично предыдущей, но проще)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Игроки и статистика
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    total_money INTEGER DEFAULT 0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Ожидающие игры
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS waiting_games (
                    chat_id INTEGER PRIMARY KEY,
                    players TEXT,
                    message_id INTEGER,
                    creator_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_pinned INTEGER DEFAULT 1
                )
            ''')
            
            # Активные игры
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_games (
                    chat_id INTEGER PRIMARY KEY,
                    game_state TEXT,
                    current_player INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Админы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить админа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def get_game(self, chat_id: int) -> Optional[Dict]:
        """Получить игру"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT game_state FROM active_games WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None
    
    def get_waiting_game(self, chat_id: int) -> Optional[Dict]:
        """Получить лобби"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT players, message_id, creator_id FROM waiting_games WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "players": json.loads(row[0]),
                    "message_id": row[1],
                    "creator_id": row[2]
                }
        return None
    
    def get_player_stats(self, user_id: int) -> Optional[Dict]:
        """Получить статистику игрока"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, first_name, games_played, games_won, total_money
                FROM players WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "username": row[0],
                    "first_name": row[1],
                    "games_played": row[2],
                    "games_won": row[3],
                    "total_money": row[4]
                }
        return None
    
    def cleanup_old_games(self, hours: int = 24):
        """Очистить старые игры"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute('DELETE FROM waiting_games WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM active_games WHERE created_at < ?', (cutoff,))
            conn.commit()

db = Database()
