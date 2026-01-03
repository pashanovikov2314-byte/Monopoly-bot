#!/usr/bin/env python3
"""Главный файл бота - точка входа"""

import os
import sys
import logging

# Добавляем пути
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.core.bot_app import MonopolyBot
from web.server import run_web_server

def main():
    """Запуск бота и веб-сервера"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # Проверяем токен
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
        logger.info("ℹ️  Создайте файл .env на основе config/.env.example")
        return
    
    # Запускаем веб-сервер для Render
    logger.info("🌐 Запуск веб-сервера для Render...")
    run_web_server()
    
    # Запускаем бота
    logger.info("🤖 Запуск Monopoly Bot...")
    bot = MonopolyBot(BOT_TOKEN)
    bot.run()

if __name__ == "__main__":
    main()
