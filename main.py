import asyncio
import logging
import sys
from datetime import datetime
import os

# === КРИТИЧЕСКИ ВАЖНО ДЛЯ RENDER ===
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# =====================================

print(\"=== ЗАПУСК MONOPOLY BOT ===\")
print(f\"Python путь: {sys.path[:2]}\")
print(f\"Текущая папка: {os.getcwd()}\")

try:
    from core.bot import setup_bot
    from core.database import Database
    from core.security import RateLimiter
    from core.web_server import WebServer
    from utils.scheduler import GameScheduler
    from handlers.commands import setup_commands
    from handlers.callback_handlers import setup_callbacks
    from handlers.text_handlers import setup_text_handlers
    
    print(\"✅ Все модули импортированы успешно!\")
    
except ImportError as e:
    print(f\"❌ Ошибка импорта: {e}\")
    print(\"Содержимое текущей папки:\", os.listdir('.'))
    if os.path.exists('core'):
        print(\"Содержимое папки core:\", os.listdir('core'))
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
WAITING_GAMES = {}
ACTIVE_GAMES = {}
HIDDEN_MENU_USERS = {}
STATS = {
    \"maintenance_mode\": False,  # По умолчанию выключено (True для техработ)
    \"total_games\": 0,
    \"active_games\": 0,
    \"total_players\": 0
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
        \"\"\"Запуск бота\"\"\"
        try:
            logger.info(\"🚀 Запуск Monopoly Premium Bot...\")
            logger.info(\"👑 Версия Темного Принца\")
            
            # Проверяем наличие токена
            BOT_TOKEN = os.environ.get('BOT_TOKEN')
            if not BOT_TOKEN:
                logger.error(\"❌ BOT_TOKEN не установлен! Добавьте его в Environment Variables Render\")
                logger.info(\"🔧 Режим техработ включен из-за отсутствия токена\")
                STATS[\"maintenance_mode\"] = True
                # Запускаем веб-сервер для Render даже без токена
                await self.web_server.start(None)
                return
            
            await self.db.init_database()
            self.bot, self.dp = await setup_bot()
            
            # Регистрация обработчиков
            setup_commands(self.dp, self.db, HIDDEN_MENU_USERS, STATS)
            setup_callbacks(self.dp, self.db, WAITING_GAMES, ACTIVE_GAMES, HIDDEN_MENU_USERS, STATS)
            setup_text_handlers(self.dp, self.db, ACTIVE_GAMES)
            
            # Запуск веб-сервера
            await self.web_server.start(self.bot)
            
            logger.info(\"✅ Бот инициализирован\")
            
            if STATS[\"maintenance_mode\"]:
                logger.warning(\"⚠️ Бот запущен в режиме технических работ!\")
                logger.info(\"👑 Сообщения будут содержать информацию о Темном Принце\")
            
            await self.dp.start_polling(self.bot, skip_updates=True)
            
        except Exception as e:
            logger.error(f\"❌ Ошибка: {e}\")
            STATS[\"maintenance_mode\"] = True
            raise

async def main():
    \"\"\"Основная функция\"\"\"
    os.makedirs(\"logs\", exist_ok=True)
    os.makedirs(\"data\", exist_ok=True)
    
    bot = MonopolyBot()
    await bot.start()

if __name__ == \"__main__\":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(\"👋 Бот остановлен\")
    except Exception as e:
        print(f\"❌ Фатальная ошибка: {e}\")
        sys.exit(1)
