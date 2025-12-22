"""
Запуск и веб-сервера, и бота одновременно
"""

import os
import sys
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_flask():
    """Запуск Flask сервера"""
    from web_server import app, PORT
    logger.info(f"🌐 Запуск Flask на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def run_bot():
    """Запуск Telegram бота"""
    from telegram_bot import main
    logger.info("🤖 Запуск Telegram бота")
    main()

def main():
    """Основной запуск"""
    logger.info("🚀 Запуск Monopoly Premium Bot...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота в основном потоке
    run_bot()

if __name__ == "__main__":
    main()
