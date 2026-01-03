# -*- coding: utf-8 -*-
"""Главный файл бота"""

import os
import sys
import logging

# Добавляем пути
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Запуск бота"""
    # Настройка логирования
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # Проверка токена
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в переменных окружения!")
        logger.info("Создайте файл .env на основе config/.env.example")
        logger.info("Или установите переменную в Render Dashboard")
        return
    
    try:
        # Импортируем веб-сервер
        from web.server import start_in_thread
        
        # Запускаем веб-сервер для Render
        logger.info("Запуск веб-сервера для Render...")
        start_in_thread()
        logger.info("Веб-сервер запущен в отдельном потоке")
        
    except ImportError as e:
        logger.error(f"Не удалось импортировать веб-сервер: {e}")
        logger.info("Веб-сервер не запущен, Render может не увидеть порт")
    
    try:
        # Импортируем и запускаем бота
        from bot.core.bot_app import MonopolyBot
        
        logger.info("Запуск Monopoly Bot...")
        bot = MonopolyBot(BOT_TOKEN)
        logger.info("Бот инициализирован")
        bot.run()
        
    except ImportError as e:
        logger.error(f"Ошибка импорта модулей бота: {e}")
        logger.info("Проверьте установлены ли зависимости")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
