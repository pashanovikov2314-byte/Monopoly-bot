"""
Common utilities for the bot
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Менеджер конфигурации"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict:
        """Загрузить JSON файл"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Файл не найден: {file_path}")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения JSON {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return {}
    
    @staticmethod
    def save_json(file_path: str, data: Dict):
        """Сохранить данные в JSON"""
        try:
            # Создаем директорию если нет
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения файла {file_path}: {e}")
    
    @staticmethod
    def get_env_bool(key: str, default: bool = False) -> bool:
        """Получить булево значение из переменных окружения"""
        value = os.environ.get(key, '').lower()
        if value in ['true', '1', 'yes', 'on']:
            return True
        elif value in ['false', '0', 'no', 'off']:
            return False
        return default
    
    @staticmethod
    def get_env_int(key: str, default: int = 0) -> int:
        """Получить целое число из переменных окружения"""
        try:
            return int(os.environ.get(key, default))
        except (ValueError, TypeError):
            return default


class ErrorHandler:
    """Обработчик ошибок"""
    
    @staticmethod
    async def handle_error(error: Exception, context: str = "") -> str:
        """Обработать ошибку и вернуть сообщение для пользователя"""
        error_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Логируем ошибку
        logger.error(f"[{error_id}] Ошибка в {context}: {error}", exc_info=True)
        
        # Сохраняем в файл ошибок
        error_log_path = Path("logs/errors.log")
        error_log_path.parent.mkdir(exist_ok=True)
        
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] ID: {error_id}\n")
            f.write(f"Контекст: {context}\n")
            f.write(f"Ошибка: {error}\n")
            f.write("-" * 50 + "\n")
        
        # Возвращаем сообщение для пользователя
        return (
            f"⚠️ Произошла ошибка (ID: {error_id})\n"
            f"Темный Принц уже получил уведомление и исправляет это! ♥️♥️"
        )


class CacheManager:
    """Простой кэш-менеджер"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Установить значение в кэш"""
        self.cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=ttl or self.ttl)
        }
        self._cleanup()
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        self._cleanup()
        if key in self.cache:
            return self.cache[key]['value']
        return None
    
    def delete(self, key: str):
        """Удалить значение из кэша"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Очистить весь кэш"""
        self.cache.clear()
    
    def _cleanup(self):
        """Очистить просроченные записи"""
        now = datetime.now()
        expired_keys = [
            key for key, data in self.cache.items()
            if data['expires'] < now
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict:
        """Получить статистику кэша"""
        self._cleanup()
        return {
            'size': len(self.cache),
            'ttl': self.ttl
        }


class TextFormatter:
    """Форматирование текста"""
    
    @staticmethod
    def format_money(amount: int) -> str:
        """Форматировать деньги"""
        return f"${amount:,}".replace(',', ' ')
    
    @staticmethod
    def format_property(name: str, price: int, rent: int) -> str:
        """Форматировать информацию о недвижимости"""
        return f"🏠 {name}\n💰 Цена: ${price:,}\n🏦 Рента: ${rent:,}"
    
    @staticmethod
    def format_player_stats(stats: Dict) -> str:
        """Форматировать статистику игрока"""
        if not stats:
            return "📊 Статистика не найдена"
        
        win_rate = 0
        if stats['games_played'] > 0:
            win_rate = (stats['games_won'] / stats['games_played']) * 100
        
        return (
            f"👤 {stats['first_name']} (@{stats.get('username', 'нет')})\n\n"
            f"🎮 Сыграно игр: {stats['games_played']}\n"
            f"🏆 Побед: {stats['games_won']}\n"
            f"📈 Винрейт: {win_rate:.1f}%\n"
            f"💰 Всего денег: ${stats['total_money']:,}\n"
            f"🏠 Построено домов: {stats['total_houses']}\n"
            f"🏨 Построено отелей: {stats['total_hotels']}\n"
            f"🤝 Сделок: {stats['total_trades']}\n"
            f"🏛️ Посещений тюрьмы: {stats['total_jail_visits']}"
        )
    
    @staticmethod
    def format_top_players(players: List[Dict], by: str = "games_won") -> str:
        """Форматировать топ игроков"""
        if not players:
            return "🏆 Рейтинг пуст"
        
        titles = {
            "games_won": "🏆 Топ по победам",
            "total_money": "💰 Топ по деньгам",
            "games_played": "🎮 Топ по активности"
        }
        
        title = titles.get(by, "🏆 Топ игроков")
        result = [f"{title}:\n"]
        
        for i, player in enumerate(players, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            if by == "games_won":
                score = f"🏆 {player['score']} побед"
            elif by == "total_money":
                score = f"💰 ${player['score']:,}"
            else:
                score = f"🎮 {player['score']} игр"
            
            result.append(
                f"{medal} {player['first_name']} (@{player.get('username', 'нет')})\n"
                f"   {score} | Игр: {player['games_played']} | Побед: {player['games_won']}\n"
            )
        
        return "\n".join(result)


# Глобальные экземпляры
config_manager = ConfigManager()
error_handler = ErrorHandler()
cache = CacheManager()
text_formatter = TextFormatter()
