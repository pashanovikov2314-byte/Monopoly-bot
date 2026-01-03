"""Обработчики команд бота (/start, /help и т.д.)"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

logger = logging.getLogger(__name__)

# ===== КОМАНДА /START =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота"""
    keyboard = [
        [
            InlineKeyboardButton("🎮 Новая игра", callback_data='new_game'),
            InlineKeyboardButton("📊 Статистика", callback_data='stats')
        ],
        [
            InlineKeyboardButton("📖 Правила", callback_data='rules'),
            InlineKeyboardButton("👥 Пригласить", callback_data='invite')
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data='settings'),
            InlineKeyboardButton("💎 Премиум", callback_data='premium')
        ],
        [
            InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_menu'),
            InlineKeyboardButton("✨ Показать меню", callback_data='show_menu')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
✨ *MONOPOLY PREMIUM BOT* ✨

🏰 Элитная версия классической игры!

🎯 *Доступные режимы:*
• Классическая монополия
• Турнирный режим  
• Быстрая игра (10 мин)
• Мультиплеер до 8 игроков

👇 *Выберите действие:*"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===== КОМАНДА /HELP =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по боту"""
    help_text = """
🎮 *Monopoly Bot - Помощь*

*📋 Основные команды:*
/start - Главное меню
/help - Эта справка  
/stats - Ваша статистика
/newgame - Новая игра
/rules - Правила игры

*🎲 Игровые действия:*
• Бросить кубики
• Купить участок  
• Строить дома/отели
• Торговать с игроками
• Взять ипотеку

*👁️ Управление интерфейсом:*
• Скрыть меню - убрать кнопки
• Показать меню - вернуть кнопки
• Компактный вид - минимальный интерфейс

*❓ Нужна помощь?*
Напишите @support"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ===== КОМАНДА /STATS =====
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика игрока"""
    stats_text = """
📊 *Ваша статистика:*

*🎮 Игры:*
• Всего сыграно: 15
• Побед: 8 (53%)
• Поражений: 7

*💰 Финансы:*
• Максимальный баланс: $2,500,000
• Средний доход: $150,000
• Налоги уплачено: $75,000

*🏆 Достижения:*
• Первый миллионер 🏅
• Владелец 5 участков 🏠
• Торговый магнат 💼

*📈 Рейтинг:*
• Место в топе: #42
• Уровень: Новичок
• Опыт: 450/1000"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# ===== РЕГИСТРАЦИЯ КОМАНД =====
def register_commands(application):
    """Регистрация всех команд"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("newgame", start_command))  # Пока то же самое
    
    logger.info("✅ Команды зарегистрированы")
