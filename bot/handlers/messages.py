"""Обработчики текстовых сообщений"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()
    user = update.effective_user
    
    responses = {
        "привет": f"👋 Привет, {user.first_name}! Используй /start для начала игры!",
        "hello": f"👋 Hello, {user.first_name}! Use /start to begin!",
        "монополия": "🎮 Да, это бот для игры в Монополию! Используй /newgame чтобы начать.",
        "правила": "📖 Правила игры: /help",
        "статистика": "📊 Твоя статистика: /stats",
        "игра": "🎲 Начать игру: /start",
        "помощь": "❓ Помощь: /help"
    }
    
    # Ищем подходящий ответ
    response = None
    for key in responses:
        if key in text:
            response = responses[key]
            break
    
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"🤔 Не понял, {user.first_name}. Используй /help для списка команд."
        )

def register_messages(application):
    """Регистрация обработчиков сообщений"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("✅ Обработчики сообщений зарегистрированы")
