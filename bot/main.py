import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, request
from telegram.ext import Application
from bot.core.bot_app import setup_application
from bot.core.database import init_database
from web.server import app as flask_app

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение конфигурации из переменных окружения
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').rstrip('/')
MONGODB_URI = os.getenv('MONGODB_URI', '')  # ДОБАВЛЕНО: URI для MongoDB
PORT = int(os.getenv('PORT', 8080))

# Проверка обязательных переменных
if not TOKEN:
    logger.error("❌ Токен бота не найден! Установите переменную окружения TOKEN")
    sys.exit(1)

if not MONGODB_URI:
    logger.error("❌ MONGODB_URI не найден! Установите строку подключения к MongoDB")
    sys.exit(1)
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').rstrip('/')
PORT = int(os.getenv('PORT', 8080))

# Создание приложения Telegram
application = setup_application()

# ДОБАВЛЕНО: Интеграция Flask с Telegram для обработки веб-хуков
@flask_app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обработка входящих обновлений от Telegram"""
    if request.is_json:
        update_data = request.get_json()
        from telegram import Update
        update = Update.de_json(update_data, application.bot)
        application.process_update(update)
    return 'OK'

@flask_app.route('/')
def health_check():
    """Health check endpoint для Render"""
    return '✅ Monopoly Bot is running!'

@flask_app.route('/ping')
def ping():
    """Проверка работоспособности"""
    return 'pong'

async def setup_webhook():
    """Настройка веб-хука для Telegram"""
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL не установлен!")
        return
    
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    logger.info(f"Устанавливаю веб-хук: {webhook_url}")
    
    # Устанавливаем веб-хук
    await application.bot.set_webhook(
        url=webhook_url,
        max_connections=50
    )
    
    # Проверяем установку
    webhook_info = await application.bot.get_webhook_info()
    logger.info(f"Информация о веб-хуке: {webhook_info}")

async def run_polling():
    """Запуск в режиме polling (для разработки)"""
    logger.info("Запуск в режиме polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Блокируем выполнение
    await application.updater.idle()

async def run_webhook():
    """Запуск в режиме веб-хука (для production)"""
    logger.info("Запуск в режиме веб-хука...")
    
    # Настраиваем веб-хук
    await setup_webhook()
    
    # Запускаем Flask сервер
    import threading
    from web.server import run_server
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(
        target=run_server,
        args=(PORT,),
        daemon=True
    )
    flask_thread.start()
    
    logger.info(f"Flask сервер запущен на порту {PORT}")
    
    # Бесконечный цикл для поддержания работы
    import asyncio
    while True:
        await asyncio.sleep(3600)  # Спим 1 час

async def main():
    # Инициализация базы данных
    if not init_database():
        logger.error("Не удалось инициализировать базу данных. Завершение работы.")
        sys.exit(1)
    """Главная функция запуска"""
    try:
        if WEBHOOK_URL and TOKEN:
            # Production режим с веб-хуком
            await run_webhook()
        else:
            # Development режим с polling
            await run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}", exc_info=True)
        raise

# Точка входа
if __name__ == '__main__':
    import asyncio
    
    # Проверяем наличие обязательных переменных
    if not TOKEN:
        logger.error("Токен бота не найден! Установите переменную окружения TOKEN")
        sys.exit(1)
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


