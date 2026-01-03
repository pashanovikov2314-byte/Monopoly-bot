# -*- coding: utf-8 -*-
"""Игровые обработчики"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)

async def handle_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик игровых callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("buy_"):
        property_id = query.data.replace("buy_", "")
        await query.edit_message_text(f"🏠 Куплена собственность #{property_id}")
    elif query.data == "roll_dice":
        await query.edit_message_text("🎲 Бросаем кубики...")
    elif query.data == "game_status":
        await query.edit_message_text("📊 Статус игры...")

def register_game_handlers(application):
    """Регистрация игровых обработчиков"""
    # Без проблемных регулярных выражений
    application.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^roll_dice$"))
    application.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^game_status$"))
    
    logger.info("✅ Игровые обработчики зарегистрированы")