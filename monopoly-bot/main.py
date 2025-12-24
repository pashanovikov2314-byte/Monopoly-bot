"""
Monopoly Premium Bot - Telegram бот
👑 Создано Темным Принцем (Dark Prince) 👑
Полная версия со всеми механиками
"""

import asyncio
import logging
import sys
from datetime import datetime
import os
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.bot import setup_bot
from core.database import Database
from core.security import RateLimiter
from core.web_server import WebServer
from utils.scheduler import GameScheduler
from handlers.commands import setup_commands
from handlers.callback_handlers import setup_callbacks
from handlers.text_handlers import setup_text_handlers
from keyboards.main_keyboards import BANNER

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные (как в вашем коде)
WAITING_GAMES: Dict[int, Any] = {}
ACTIVE_GAMES: Dict[int, Any] = {}
HIDDEN_MENU_USERS: Dict[int, int] = {}  # {user_id: chat_id}
STATS = {
    "maintenance_mode": False,
    "total_games": 0,
    "active_games": 0,
    "total_players": 0
}

class MonopolyBot:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.db = Database()
        self.rate_limiter = RateLimiter()
        self.scheduler = GameScheduler()
        self.web_server = WebServer()
        
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск Monopoly Premium Bot...")
            print(BANNER)
            logger.info(f"👑 Версия Темного Принца - {datetime.now().strftime('%Y.%m.%d')}")
            
            # Инициализация базы данных
            await self.db.init_database()
            
            # Очистка старых игр
            await self.db.cleanup_old_games()
            
            # Настройка бота
            self.bot, self.dp = await setup_bot()
            
            # Регистрация обработчиков
            await self._register_handlers()
            
            # Запуск планировщика
            await self.scheduler.start(self.bot, self.db)
            
            # Запуск веб-сервера
            await self.web_server.start(self.bot)
            
            logger.info("✅ Бот успешно инициализирован")
            logger.info("🤖 Ожидание сообщений...")
            
            # Запуск бота
            await self.dp.start_polling(self.bot, skip_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запуске: {e}")
            raise
        finally:
            await self._shutdown()
    
    async def _register_handlers(self):
        """Регистрация всех обработчиков"""
        setup_commands(self.dp, self.db, HIDDEN_MENU_USERS, STATS)
        setup_callbacks(self.dp, self.db, WAITING_GAMES, ACTIVE_GAMES, HIDDEN_MENU_USERS, STATS)
        setup_text_handlers(self.dp, self.db, ACTIVE_GAMES)
        
        # Регистрация middleware
        self.dp.message.middleware(self.rate_limiter)
    
    async def _shutdown(self):
        """Корректное завершение работы"""
        logger.info("🛑 Остановка бота...")
        await self.scheduler.stop()
        await self.web_server.stop()
        await self.db.close()
        if self.bot:
            await self.bot.session.close()

async def main():
    """Основная функция запуска"""
    # Создание директорий
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("web/static/images", exist_ok=True)
    
    bot = MonopolyBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}")
        sys.exit(1)
