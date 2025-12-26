#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monopoly Premium Bot - Основной файл"""

import asyncio
import logging
import sys
import os

# Добавляем текущую папку в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=== ЗАПУСК MONOPOLY BOT ===")
print("Python путь:", sys.path[:2])
print("Текущая папка:", current_dir)

try:
    # Импортируем основные модули
    from core.bot import setup_bot
    from core.database import Database
    print("✅ Основные модули импортированы")
    
    # Импортируем обработчики
    from handlers.commands import setup_commands
    from handlers.callback_handlers import setup_callbacks
    from handlers.text_handlers import setup_text_handlers
    from test_router import setup_test_handlers
    
    print("✅ Обработчики импортированы")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск Monopoly Premium Bot...")
    logger.info("👑 Версия Темного Принца")
    
    try:
        # Получаем токен бота
        BOT_TOKEN = os.environ.get("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не установлен в Environment Variables!")
            logger.info("Добавьте BOT_TOKEN в Render Dashboard -> Environment")
            # Бесконечный цикл чтобы Render не убил процесс
            while True:
                await asyncio.sleep(60)
            return
        
        # Инициализируем бота
        bot, dp = await setup_bot()
        
        # Инициализируем базу данных
        db = Database()
        await db.init_database()
        
        # Настраиваем обработчики
        setup_test_handlers(dp)
        setup_commands(dp, db, {}, {})
        setup_callbacks(dp, db, {}, {}, {}, {})
        setup_text_handlers(dp, db, {})
        
        logger.info("✅ Бот инициализирован и готов к работе")
        logger.info("📱 Тестовые команды: /test, /start")
        
        # Запускаем polling
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        # Бесконечный цикл для Render
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Импорт игровых обработчиков
try:
    from handlers.game_handlers import game_router
    print("✅ Игровые обработчики импортированы")
except ImportError as e:
    print(f"⚠️ Игровые обработчики не импортированы: {e}")

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
            logger.info("👑 Версия Темного Принца")
            
            # Проверяем наличие токена
            BOT_TOKEN = os.environ.get("BOT_TOKEN")
            if not BOT_TOKEN:
                logger.error("❌ BOT_TOKEN не установлен!")
                logger.info("🔧 Режим техработ включен")
                STATS["maintenance_mode"] = True
                # Запускаем веб-сервер для Render
                await self.web_server.start(None)
                return
            
            await self.db.init_database()
            self.bot, self.dp = await setup_bot()
            
            # Регистрация ВСЕХ обработчиков
            setup_test_handlers(self.dp)
            setup_commands(self.dp, self.db, HIDDEN_MENU_USERS, STATS)
            setup_callbacks(self.dp, self.db, WAITING_GAMES, ACTIVE_GAMES, HIDDEN_MENU_USERS, STATS)
            setup_text_handlers(self.dp, self.db, ACTIVE_GAMES)
            
            # Регистрация игровых обработчиков
            try:
                self.dp.include_router(game_router)
                logger.info("✅ Игровые обработчики зарегистрированы")
            except:
                logger.warning("⚠️ Не удалось зарегистрировать игровые обработчики")
            
            logger.info("✅ Бот инициализирован")
            logger.info("🎮 Доступны игровые функции")
            
            await self.dp.start_polling(self.bot, skip_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            STATS["maintenance_mode"] = True
            # Бесконечный цикл для Render
            while True:
                await asyncio.sleep(60)
