"""
DATABASE.PY - Работа с базой данных и статистикой
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pickle

from modules.config import (
    logger, DATA_DIR, USER_STATS, 
    save_user_stats, load_user_stats,
    ADMINS, BOARD
)

# ==================== БАЗА ДАННЫХ SQLITE ====================

class SQLiteDatabase:
    """Работа с SQLite базой данных"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(DATA_DIR, "monopoly.db")
        self._init_database()
    
    def _init_database(self):
        """Инициализировать базу данных"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    total_money INTEGER DEFAULT 0,
                    last_played TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица игр
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    players_count INTEGER,
                    winner_id INTEGER,
                    duration_minutes INTEGER,
                    total_turns INTEGER,
                    finished_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица игроков в играх
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    user_id INTEGER,
                    final_balance INTEGER,
                    position INTEGER,
                    properties_count INTEGER,
                    FOREIGN KEY (game_id) REFERENCES games(game_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица активных игр (для восстановления)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_games (
                    chat_id INTEGER PRIMARY KEY,
                    game_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индексы для ускорения запросов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_games ON users(games_played)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_wins ON users(games_won)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_finished ON games(finished_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_game_players_user ON game_players(user_id)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ База данных инициализирована: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавить пользователя в БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    def update_user_stats(self, user_id: int, win: bool = False, money: int = 0):
        """Обновить статистику пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Обновляем игры сыгранные
            cursor.execute('''
                UPDATE users 
                SET games_played = games_played + 1,
                    last_played = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            # Если победа - обновляем победы
            if win:
                cursor.execute('''
                    UPDATE users 
                    SET games_won = games_won + 1
                    WHERE user_id = ?
                ''', (user_id,))
            
            # Обновляем общие деньги
            if money > 0:
                cursor.execute('''
                    UPDATE users 
                    SET total_money = total_money + ?
                    WHERE user_id = ?
                ''', (money, user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False
    
    def save_game_result(self, chat_id: int, players: List[Dict], 
                        winner_id: int, duration_minutes: int, total_turns: int):
        """Сохранить результат игры"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Сохраняем игру
            cursor.execute('''
                INSERT INTO games (chat_id, players_count, winner_id, 
                                 duration_minutes, total_turns, finished_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (chat_id, len(players), winner_id, duration_minutes, total_turns))
            
            game_id = cursor.lastrowid
            
            # Сохраняем игроков
            for player in players:
                cursor.execute('''
                    INSERT INTO game_players (game_id, user_id, final_balance, 
                                            position, properties_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (game_id, player["id"], player.get("balance", 0),
                     player.get("position", 0), len(player.get("properties", []))))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Результат игры сохранен: ID {game_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения игры: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, first_name, games_played, games_won, 
                       total_money, last_played, created_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                username, first_name, games_played, games_won, \
                total_money, last_played, created_at = row
                
                win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "games_played": games_played,
                    "games_won": games_won,
                    "total_money": total_money,
                    "win_rate": round(win_rate, 2),
                    "last_played": last_played,
                    "created_at": created_at
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def get_top_players(self, limit: int = 10, period_days: int = None) -> List[Dict]:
        """Получить топ игроков"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            where_clause = ""
            params = []
            
            if period_days:
                where_clause = "WHERE last_played >= datetime('now', ?)"
                params.append(f"-{period_days} days")
            
            query = f'''
                SELECT user_id, username, first_name, games_played, games_won, total_money
                FROM users 
                {where_clause}
                ORDER BY 
                    CASE WHEN games_played >= 5 THEN (games_won * 1.0 / games_played) ELSE 0 END DESC,
                    games_won DESC,
                    total_money DESC
                LIMIT ?
            '''
            
            params.append(limit)
            cursor.execute(query, params)
            
            top_players = []
            for row in cursor.fetchall():
                user_id, username, first_name, games_played, games_won, total_money = row
                
                win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                
                top_players.append({
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "games": games_played,
                    "wins": games_won,
                    "total_money": total_money,
                    "win_rate": round(win_rate, 2)
                })
            
            conn.close()
            return top_players
            
        except Exception as e:
            logger.error(f"Ошибка получения топа: {e}")
            return []
    
    def get_recent_games(self, limit: int = 10) -> List[Dict]:
        """Получить последние игры"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT g.game_id, g.chat_id, g.players_count, g.winner_id,
                       g.duration_minutes, g.total_turns, g.finished_at,
                       u.first_name as winner_name
                FROM games g
                LEFT JOIN users u ON g.winner_id = u.user_id
                ORDER BY g.finished_at DESC
                LIMIT ?
            ''', (limit,))
            
            games = []
            for row in cursor.fetchall():
                game_id, chat_id, players_count, winner_id, \
                duration_minutes, total_turns, finished_at, winner_name = row
                
                games.append({
                    "game_id": game_id,
                    "chat_id": chat_id,
                    "players_count": players_count,
                    "winner_id": winner_id,
                    "winner_name": winner_name,
                    "duration_minutes": duration_minutes,
                    "total_turns": total_turns,
                    "finished_at": finished_at
                })
            
            conn.close()
            return games
            
        except Exception as e:
            logger.error(f"Ошибка получения игр: {e}")
            return []
    
    def get_user_games(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получить игры пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT g.game_id, g.chat_id, g.players_count, g.winner_id,
                       g.duration_minutes, g.total_turns, g.finished_at,
                       gp.final_balance, gp.position, gp.properties_count,
                       u.first_name as winner_name
                FROM game_players gp
                JOIN games g ON gp.game_id = g.game_id
                LEFT JOIN users u ON g.winner_id = u.user_id
                WHERE gp.user_id = ?
                ORDER BY g.finished_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            games = []
            for row in cursor.fetchall():
                game_id, chat_id, players_count, winner_id, \
                duration_minutes, total_turns, finished_at, \
                final_balance, position, properties_count, winner_name = row
                
                is_winner = (winner_id == user_id)
                
                games.append({
                    "game_id": game_id,
                    "chat_id": chat_id,
                    "players_count": players_count,
                    "is_winner": is_winner,
                    "winner_name": winner_name,
                    "duration_minutes": duration_minutes,
                    "total_turns": total_turns,
                    "finished_at": finished_at,
                    "final_balance": final_balance,
                    "position": position,
                    "properties_count": properties_count
                })
            
            conn.close()
            return games
            
        except Exception as e:
            logger.error(f"Ошибка получения игр пользователя: {e}")
            return []
    
    def save_active_game(self, chat_id: int, game_data: Dict):
        """Сохранить активную игру"""
        try:
            # Сериализуем данные игры
            serialized_data = pickle.dumps(game_data)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO active_games (chat_id, game_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (chat_id, serialized_data))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Активная игра сохранена: чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения активной игры: {e}")
            return False
    
    def load_active_game(self, chat_id: int) -> Optional[Dict]:
        """Загрузить активную игру"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT game_data FROM active_games WHERE chat_id = ?
            ''', (chat_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                game_data = pickle.loads(row[0])
                return game_data
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка загрузки активной игры: {e}")
            return None
    
    def delete_active_game(self, chat_id: int):
        """Удалить активную игру"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM active_games WHERE chat_id = ?', (chat_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Активная игра удалена: чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления активной игры: {e}")
            return False
    
    def cleanup_old_games(self, days_old: int = 30):
        """Очистить старые игры"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Удаляем старые игры
            cursor.execute('''
                DELETE FROM games 
                WHERE finished_at < datetime('now', ?)
            ''', (f"-{days_old} days",))
            
            deleted_games = cursor.rowcount
            
            # Удаляем связанных игроков
            cursor.execute('''
                DELETE FROM game_players 
                WHERE game_id NOT IN (SELECT game_id FROM games)
            ''')
            
            # Удаляем старые активные игры (старше 7 дней)
            cursor.execute('''
                DELETE FROM active_games 
                WHERE updated_at < datetime('now', ?)
            ''', ("-7 days",))
            
            deleted_active = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Очистка БД: удалено {deleted_games} игр, {deleted_active} активных")
            
            return {
                "deleted_games": deleted_games,
                "deleted_active": deleted_active
            }
            
        except Exception as e:
            logger.error(f"Ошибка очистки БД: {e}")
            return {"error": str(e)}
    
    def get_database_stats(self) -> Dict:
        """Получить статистику базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM games')
            total_games = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM active_games')
            total_active = cursor.fetchone()[0]
            
            # Размер базы данных
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn.close()
            
            return {
                "total_users": total_users,
                "total_games": total_games,
                "total_active_games": total_active,
                "db_size_mb": round(db_size / (1024 * 1024), 2),
                "last_cleanup": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {"error": str(e)}

# ==================== МЕНЕДЖЕР СТАТИСТИКИ ====================

class StatisticsManager:
    """Менеджер статистики игроков"""
    
    def __init__(self):
        self.db = SQLiteDatabase()
        self.cache = {}
        self.cache_timeout = 300  # 5 минут
        
    def update_player_stats(self, user_id: int, username: str, 
                           first_name: str, win: bool = False, money: int = 0):
        """Обновить статистику игрока"""
        try:
            # Обновляем в SQLite
            self.db.add_user(user_id, username, first_name)
            self.db.update_user_stats(user_id, win, money)
            
            # Обновляем в памяти (для обратной совместимости)
            from modules.config import update_user_stats
            update_user_stats(user_id, username, first_name, win, money)
            
            # Очищаем кэш
            if user_id in self.cache:
                del self.cache[user_id]
            
            logger.info(f"📊 Статистика обновлена: {first_name}, win={win}, money={money}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False
    
        def get_player_stats(self, user_id: int, use_cache: bool = True) -> Dict:
        """Получить статистику игрока"""
        try:
            # Проверяем кэш
            if use_cache and user_id in self.cache:
                cached_data, timestamp = self.cache[user_id]
                if (datetime.now().timestamp() - timestamp) < self.cache_timeout:
                    return cached_data
            
            # Получаем из базы
            stats = self.db.get_user_stats(user_id)
            
            if not stats:
                # Если нет в базе, проверяем старую JSON базу
                from modules.config import USER_STATS
                if user_id in USER_STATS:
                    old_stats = USER_STATS[user_id]
                    stats = {
                        "user_id": user_id,
                        "username": old_stats.get("username", ""),
                        "first_name": old_stats.get("first_name", ""),
                        "games_played": old_stats.get("games", 0),
                        "games_won": old_stats.get("wins", 0),
                        "total_money": old_stats.get("total_money", 0),
                        "win_rate": (old_stats.get("wins", 0) / old_stats.get("games", 1) * 100) 
                                    if old_stats.get("games", 0) > 0 else 0,
                        "last_played": old_stats.get("last_played", ""),
                        "created_at": datetime.now().isoformat()
                    }
            
            # Сохраняем в кэш
            self.cache[user_id] = (stats, datetime.now().timestamp())
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики игрока: {e}")
            return {}
    
    def get_top_players(self, limit: int = 10, period: str = "all") -> List[Dict]:
        """Получить топ игроков"""
        try:
            cache_key = f"top_{limit}_{period}"
            
            # Проверяем кэш
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self.cache_timeout:
                    return cached_data
            
            # Определяем период
            period_days = None
            if period == "week":
                period_days = 7
            elif period == "month":
                period_days = 30
            elif period == "today":
                period_days = 1
            
            # Получаем из базы
            top_players = self.db.get_top_players(limit, period_days)
            
            # Сохраняем в кэш
            self.cache[cache_key] = (top_players, datetime.now().timestamp())
            
            return top_players
            
        except Exception as e:
            logger.error(f"Ошибка получения топа: {e}")
            return []
    
    def get_player_rank(self, user_id: int) -> Dict:
        """Получить ранг игрока"""
        try:
            stats = self.get_player_stats(user_id)
            
            if not stats or stats.get("games_played", 0) == 0:
                return {
                    "rank": "Новичок",
                    "emoji": "🎮",
                    "level": 0,
                    "progress": 0
                }
            
            games = stats["games_played"]
            wins = stats["games_won"]
            win_rate = stats["win_rate"]
            total_money = stats["total_money"]
            
            # Определяем ранг
            if games < 5:
                rank = "Новичок"
                emoji = "🎮"
                level = 0
                progress = (games / 5) * 100  # Прогресс до 5 игр
                
            elif win_rate < 20:
                rank = "Игрок"
                emoji = "⭐"
                level = 1
                progress = (win_rate / 20) * 100
                
            elif win_rate < 40:
                rank = "Опытный"
                emoji = "🏆"
                level = 2
                progress = ((win_rate - 20) / 20) * 100
                
            elif win_rate < 60:
                rank = "Эксперт"
                emoji = "👑"
                level = 3
                progress = ((win_rate - 40) / 20) * 100
                
            else:
                rank = "Легенда"
                emoji = "🌟"
                level = 4
                progress = min(100, ((win_rate - 60) / 20) * 100)
            
            # Бонус за деньги
            money_bonus = min(20, total_money // 5000)  # +1% за каждые 5000$
            
            return {
                "rank": rank,
                "emoji": emoji,
                "level": level,
                "progress": min(100, progress + money_bonus),
                "games_played": games,
                "wins": wins,
                "win_rate": win_rate,
                "total_money": total_money,
                "next_rank": self._get_next_rank_info(level, progress)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения ранга: {e}")
            return {"rank": "Новичок", "emoji": "🎮", "level": 0}
    
    def _get_next_rank_info(self, current_level: int, current_progress: int) -> Dict:
        """Получить информацию о следующем ранге"""
        ranks = [
            {"name": "Игрок", "emoji": "⭐", "min_games": 5, "min_win_rate": 0},
            {"name": "Опытный", "emoji": "🏆", "min_games": 10, "min_win_rate": 20},
            {"name": "Эксперт", "emoji": "👑", "min_games": 20, "min_win_rate": 40},
            {"name": "Легенда", "emoji": "🌟", "min_games": 30, "min_win_rate": 60}
        ]
        
        if current_level >= len(ranks):
            return {"name": "МАКСИМУМ", "emoji": "🏅", "progress": 100}
        
        next_rank = ranks[current_level]
        return {
            "name": next_rank["name"],
            "emoji": next_rank["emoji"],
            "progress": current_progress,
            "requirements": f"{next_rank['min_games']}+ игр, {next_rank['min_win_rate']}%+ винрейт"
        }
    
    def save_game_history(self, chat_id: int, players: List[Dict], 
                         winner_id: int, duration_minutes: int, total_turns: int):
        """Сохранить историю игры"""
        try:
            success = self.db.save_game_result(
                chat_id, players, winner_id, 
                duration_minutes, total_turns
            )
            
            if success:
                logger.info(f"✅ История игры сохранена: чат {chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {e}")
            return False
    
    def get_player_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю игр игрока"""
        try:
            games = self.db.get_user_games(user_id, limit)
            
            # Форматируем для отображения
            formatted_games = []
            for game in games:
                result = "🏆 ПОБЕДА" if game["is_winner"] else "💔 ПОРАЖЕНИЕ"
                
                formatted_games.append({
                    "game_id": game["game_id"],
                    "result": result,
                    "players_count": game["players_count"],
                    "duration": f"{game['duration_minutes']} мин",
                    "turns": game["total_turns"],
                    "balance": game["final_balance"],
                    "position": game["position"],
                    "properties": game["properties_count"],
                    "date": game["finished_at"][:10] if game["finished_at"] else "?"
                })
            
            return formatted_games
            
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def get_global_stats(self) -> Dict:
        """Получить глобальную статистику"""
        try:
            # Статистика из базы
            db_stats = self.db.get_database_stats()
            
            # Топ игроков
            top_players = self.get_top_players(5)
            
            # Последние игры
            recent_games = self.db.get_recent_games(5)
            
            # Считаем общий винрейт
            total_games = db_stats.get("total_games", 0)
            if total_games > 0:
                # Для простоты берем средний винрейт топ игроков
                avg_win_rate = sum(p["win_rate"] for p in top_players) / len(top_players) if top_players else 0
            else:
                avg_win_rate = 0
            
            return {
                "total_players": db_stats.get("total_users", 0),
                "total_games": total_games,
                "active_games": db_stats.get("total_active_games", 0),
                "avg_win_rate": round(avg_win_rate, 1),
                "db_size": db_stats.get("db_size_mb", 0),
                "top_players": top_players,
                "recent_games": recent_games,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения глобальной статистики: {e}")
            return {}

# ==================== МИГРАЦИЯ ДАННЫХ ====================

class DataMigrator:
    """Миграция данных из старого формата в новый"""
    
    @staticmethod
    def migrate_json_to_sqlite():
        """Мигрировать данные из JSON в SQLite"""
        try:
            from modules.config import USER_STATS, load_user_stats
            
            logger.info("🔄 Начало миграции данных из JSON в SQLite...")
            
            # Загружаем текущие данные
            load_user_stats()
            
            stats_manager = StatisticsManager()
            migrated = 0
            errors = 0
            
            for user_id, user_data in USER_STATS.items():
                try:
                    # Мигрируем пользователя
                    username = user_data.get("username", "")
                    first_name = user_data.get("first_name", "")
                    games = user_data.get("games", 0)
                    wins = user_data.get("wins", 0)
                    total_money = user_data.get("total_money", 0)
                    
                    # Добавляем в SQLite
                    stats_manager.db.add_user(user_id, username, first_name)
                    
                    # Имитируем обновление статистики для каждой игры
                    for i in range(games):
                        win = (i < wins)
                        money = total_money // games if games > 0 else 0
                        stats_manager.db.update_user_stats(user_id, win, money)
                    
                    migrated += 1
                    
                    if migrated % 100 == 0:
                        logger.info(f"🔄 Мигрировано {migrated} пользователей...")
                        
                except Exception as e:
                    logger.error(f"Ошибка миграции пользователя {user_id}: {e}")
                    errors += 1
            
            logger.info(f"✅ Миграция завершена: {migrated} успешно, {errors} ошибок")
            
            return {
                "success": True,
                "migrated": migrated,
                "errors": errors,
                "total": len(USER_STATS)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def backup_database():
        """Создать резервную копию базы данных"""
        try:
            import shutil
            import sqlite3
            
            db_path = os.path.join(DATA_DIR, "monopoly.db")
            if not os.path.exists(db_path):
                return {"success": False, "error": "База данных не найдена"}
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(DATA_DIR, f"backup_{timestamp}.db")
            
            # Копируем файл базы данных
            shutil.copy2(db_path, backup_path)
            
            # Проверяем целостность
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            conn.close()
            
            if integrity == "ok":
                logger.info(f"✅ Резервная копия создана: {backup_path}")
                return {
                    "success": True,
                    "backup_path": backup_path,
                    "size_mb": round(os.path.getsize(backup_path) / (1024 * 1024), 2),
                    "integrity": integrity
                }
            else:
                os.remove(backup_path)
                return {"success": False, "error": f"Ошибка целостности: {integrity}"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа: {e}")
            return {"success": False, "error": str(e)}

# ==================== АВТОСЕЙВ И ВОССТАНОВЛЕНИЕ ====================

class GameAutoSave:
    """Автоматическое сохранение и восстановление игр"""
    
    def __init__(self):
        self.db = SQLiteDatabase()
        self.autosave_interval = 300  # 5 минут
        self.last_save_time = {}
    
    def should_autosave(self, chat_id: int) -> bool:
        """Проверить, нужно ли сохранять игру"""
        current_time = datetime.now().timestamp()
        
        if chat_id not in self.last_save_time:
            self.last_save_time[chat_id] = current_time
            return True
        
        time_since_last = current_time - self.last_save_time[chat_id]
        return time_since_last >= self.autosave_interval
    
    def autosave_game(self, chat_id: int, game_data: Dict) -> bool:
        """Автоматически сохранить игру"""
        try:
            if not self.should_autosave(chat_id):
                return False
            
            from modules.handlers import export_game_state
            export_data = export_game_state(chat_id)
            
            if "error" in export_data:
                return False
            
            success = self.db.save_active_game(chat_id, export_data)
            
            if success:
                self.last_save_time[chat_id] = datetime.now().timestamp()
                logger.debug(f"✅ Автосохранение игры: чат {chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка автосохранения: {e}")
            return False
    
    def restore_game(self, chat_id: int) -> Optional[Dict]:
        """Восстановить игру"""
        try:
            from modules.handlers import import_game_state
            
            saved_data = self.db.load_active_game(chat_id)
            if not saved_data:
                return None
            
            success = import_game_state(saved_data)
            
            if success:
                logger.info(f"✅ Игра восстановлена: чат {chat_id}")
                return saved_data
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка восстановления игры: {e}")
            return None
    
    def cleanup_old_saves(self, days_old: int = 7):
        """Очистить старые сохранения"""
        try:
            result = self.db.cleanup_old_games(days_old)
            
            # Также очищаем старые записи из памяти
            current_time = datetime.now().timestamp()
            old_chats = []
            
            for chat_id, last_save in self.last_save_time.items():
                if current_time - last_save > (days_old * 86400):  # дней в секундах
                    old_chats.append(chat_id)
            
            for chat_id in old_chats:
                del self.last_save_time[chat_id]
            
            logger.info(f"🧹 Очистка автосейвов: удалено {len(old_chats)} старых записей")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка очистки автосейвов: {e}")
            return {"error": str(e)}
    
    def get_autosave_stats(self) -> Dict:
        """Получить статистику автосейва"""
        try:
            db_stats = self.db.get_database_stats()
            
            return {
                "total_saved_games": db_stats.get("total_active_games", 0),
                "active_in_memory": len(self.last_save_time),
                "autosave_interval": self.autosave_interval,
                "last_cleanup": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики автосейва: {e}")
            return {"error": str(e)}

# ==================== ЭКСПОРТ И ИМПОРТ ДАННЫХ ====================

class DataExporter:
    """Экспорт и импорт данных"""
    
    @staticmethod
    def export_all_data(format: str = "json") -> Dict:
        """Экспортировать все данные"""
        try:
            stats_manager = StatisticsManager()
            
            if format == "json":
                # Экспорт в JSON
                all_data = {
                    "export_date": datetime.now().isoformat(),
                    "version": "3.0",
                    "global_stats": stats_manager.get_global_stats(),
                    "top_players": stats_manager.get_top_players(100),
                    "recent_games": stats_manager.db.get_recent_games(50)
                }
                
                return {
                    "success": True,
                    "format": "json",
                    "data": all_data,
                    "size": len(str(all_data))
                }
            
            elif format == "csv":
                # Экспорт в CSV (упрощенный)
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Заголовки
                writer.writerow(["user_id", "username", "first_name", 
                               "games_played", "games_won", "total_money", 
                               "win_rate", "last_played"])
                
                # Данные
                top_players = stats_manager.get_top_players(1000)
                for player in top_players:
                    writer.writerow([
                        player["user_id"],
                        player["username"] or "",
                        player["first_name"],
                        player["games"],
                        player["wins"],
                        player["total_money"],
                        f"{player['win_rate']:.2f}",
                        datetime.now().isoformat()[:10]
                    ])
                
                csv_data = output.getvalue()
                output.close()
                
                return {
                    "success": True,
                    "format": "csv",
                    "data": csv_data,
                    "size": len(csv_data)
                }
            
            else:
                return {"success": False, "error": f"Неизвестный формат: {format}"}
                
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def import_from_json(json_data: Dict) -> Dict:
        """Импортировать данные из JSON"""
        try:
            stats_manager = StatisticsManager()
            imported = 0
            errors = 0
            
            if "players" in json_data:
                # Импорт игроков
                for player_data in json_data["players"]:
                    try:
                        user_id = player_data.get("user_id")
           