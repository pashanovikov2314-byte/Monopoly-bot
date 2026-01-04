"""
Обработчики текстовых сообщений
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    user = update.effective_user
    
    # Простой ответ на сообщение
    response = f"Привет {user.first_name}! Вы сказали: '{text}'\n\n"
    response += "Я бот для Монополии. Используйте команды:\n"
    response += "/start - начать\n"
    response += "/new_game - создать игру\n"
    response += "/join - присоединиться\n"
    response += "/roll - бросить кубики"
    
    await update.message.reply_text(response)
