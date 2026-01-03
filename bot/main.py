#!/usr/bin/env python3
"""Главный файл бота - точка входа (исправленная версия)"""

import os
import sys
import logging
import threading

# Добавляем пути
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== НАСТРОЙКА ЛОГГИРОВАНИЯ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота и веб-сервера"""
    
    # ===== ПРОВЕРКА ТОКЕНА =====
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
        logger.info("ℹ️  Создайте файл .env на основе config/.env.example")
        logger.info("ℹ️  Или установите переменную в Render Dashboard")
        return
    
    # ===== ЗАПУСК ВЕБ-СЕРВЕРА ДЛЯ RENDER =====
    logger.info("🌐 Запуск веб-сервера для Render...")
    
    try:
        from web.server import start_in_thread
        web_thread = start_in_thread()
        logger.info("✅ Веб-сервер запущен в отдельном потоке")
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать веб-сервер: {e}")
        logger.info("⚠️  Веб-сервер не запущен, но бот будет работать")
    
    # ===== ЗАПУСК TELEGRAM БОТА =====
    logger.info("🤖 Запуск Monopoly Bot...")
    
    try:
        from bot.core.bot_app import MonopolyBot
        
        # Создаем и запускаем бота
        bot = MonopolyBot(BOT_TOKEN)
        logger.info("✅ Бот инициализирован, начинаю опрос...")
        bot.run()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта модулей бота: {e}")
        logger.info("📋 Проверьте установлены ли зависимости:")
        logger.info("   pip install -r config/requirements.txt")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.info("🔄 Проверьте структуру проекта и зависимости")

if __name__ == "__main__":
    main()
