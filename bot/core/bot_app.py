"""Основной класс Monopoly Bot"""

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers.commands import register_commands
from bot.handlers.callbacks import register_callbacks
from bot.handlers.messages import register_messages
from bot.handlers.game_handlers import register_game_handlers

logger = logging.getLogger(__name__)

class MonopolyBot:
    """Главный класс бота"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка всех обработчиков"""
        # Регистрируем команды
        register_commands(self.application)
        
        # Регистрируем обработчики кнопок
        register_callbacks(self.application)
        
        # Регистрируем обработчики сообщений
        register_messages(self.application)
        
        # Регистрируем игровые обработчики
        register_game_handlers(self.application)
        register_messages(self.application)
        
        logger.info("✅ Все обработчики зарегистрированы")
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Monopoly Bot запускается...")
        self.application.run_polling()

