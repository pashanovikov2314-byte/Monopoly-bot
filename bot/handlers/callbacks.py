"""Обработчики нажатий кнопок"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)

# ===== ОБРАБОТЧИКИ КНОПОК =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    # Определяем какая кнопка нажата
    data = query.data
    
    if data == 'new_game':
        await handle_new_game(query)
    elif data == 'stats':
        await handle_stats(query)
    elif data == 'rules':
        await handle_rules(query)
    elif data == 'hide_menu':
        await handle_hide_menu(query)
    elif data == 'show_menu':
        await handle_show_menu(query)
    elif data == 'settings':
        await handle_settings(query)
    elif data == 'premium':
        await handle_premium(query)
    elif data == 'invite':
        await handle_invite(query)
    else:
        await query.edit_message_text(f"Кнопка: {data}")

# ===== КОНКРЕТНЫЕ ОБРАБОТЧИКИ =====
async def handle_new_game(query):
    """Новая игра"""
    keyboard = [
        [InlineKeyboardButton("👤 Одиночная", callback_data='single')],
        [InlineKeyboardButton("👥 Мультиплеер", callback_data='multi')],
        [InlineKeyboardButton("⚡ Быстрая", callback_data='fast')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎲 *Выберите режим игры:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_stats(query):
    """Статистика"""
    await query.edit_message_text(
        "📊 *Статистика загружается...*\nИспользуйте команду /stats",
        parse_mode='Markdown'
    )

async def handle_rules(query):
    """Правила игры"""
    rules = """
📖 *ПРАВИЛА МОНОПОЛИИ*

*🎯 Цель игры:*
Стать единственным необанкротившимся игроком.

*🎲 Как играть:*
1. Бросьте кубики для перемещения
2. Покупайте свободные участки
3. Собирайте комплекты одного цвета
4. Стройте дома и отели
5. Взимайте арендную плату

*💰 Экономика:*
• Стартовый капитал: $1,500
• Прохождение старта: +$200
• Налоги: 10% от дохода"""
    
    await query.edit_message_text(rules, parse_mode='Markdown')

async def handle_hide_menu(query):
    """Скрыть меню"""
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(
        query.message.text + "\n\n✅ *Меню скрыто* 👁️",
        parse_mode='Markdown'
    )

async def handle_show_menu(query):
    """Показать меню"""
    keyboard = [
        [InlineKeyboardButton("🎮 Новая игра", callback_data='new_game')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🔙 Главное меню", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✨ *Меню восстановлено!*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_settings(query):
    """Настройки"""
    await query.edit_message_text(
        "⚙️ *Настройки*\n\nДоступно в следующем обновлении!",
        parse_mode='Markdown'
    )

async def handle_premium(query):
    """Премиум функции"""
    await query.edit_message_text(
        "💎 *Премиум функции*\n\n• Без рекламы\n• Эксклюзивные фишки\n• Приоритетная поддержка",
        parse_mode='Markdown'
    )

async def handle_invite(query):
    """Пригласить друзей"""
    await query.edit_message_text(
        "👥 *Пригласить друзей*\n\nПоделитесь ссылкой:\n`https://t.me/your_bot`",
        parse_mode='Markdown'
    )

# ===== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ =====
def register_callbacks(application):
    """Регистрация обработчиков кнопок"""
    application.add_handler(CallbackQueryHandler(button_handler))
    logger.info("✅ Обработчики кнопок зарегистрированы")
