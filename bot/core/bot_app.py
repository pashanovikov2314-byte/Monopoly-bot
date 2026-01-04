"""
Модуль для настройки приложения Telegram бота
"""
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers.commands import start, new_game, join_game, roll_dice, buy_property
from bot.handlers.callbacks import button_callback
from bot.handlers.messages import handle_message

logger = logging.getLogger(__name__)

def setup_application():
    """Настройка и конфигурация приложения Telegram бота"""
    
    # Получаем токен из переменных окружения
    import os
    TOKEN = os.getenv('TOKEN')
    
    if not TOKEN:
        logger.error("❌ Токен бота не найден! Установите переменную окружения TOKEN")
        raise ValueError("TOKEN не установлен")
    
    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("new_game", new_game))
    application.add_handler(CommandHandler("join", join_game))
    application.add_handler(CommandHandler("roll", roll_dice))
    application.add_handler(CommandHandler("buy", buy_property))
    
    # Регистрируем обработчики callback-кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Регистрируем обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Приложение Telegram настроено")
    return application
