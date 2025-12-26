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
