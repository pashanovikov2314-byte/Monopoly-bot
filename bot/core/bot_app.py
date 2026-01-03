# -*- coding: utf-8 -*-
"""Основной класс бота"""

import logging
from telegram.ext import Application
from bot.handlers.commands import register_commands
from bot.handlers.callbacks import register_callbacks
from bot.handlers.messages import register_messages
from bot.handlers.game_handlers import register_game_handlers

logger = logging.getLogger(__name__)

class MonopolyBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка всех обработчиков"""
        register_commands(self.application)
        register_callbacks(self.application)
        register_messages(self.application)
        register_game_handlers(self.application)
        logger.info("Все обработчики зарегистрированы")
    
    def run(self):
        """Запуск бота"""
        logger.info("Бот запускается...")
        self.application.run_polling()
