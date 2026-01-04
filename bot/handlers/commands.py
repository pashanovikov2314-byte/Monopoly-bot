"""
Обработчики команд бота
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет {user.first_name}! 👋\n'
        f'Я бот для игры в Монополию в Telegram.\n\n'
        f'Доступные команды:\n'
        f'/new_game - начать новую игру\n'
        f'/join - присоединиться к игре\n'
        f'/roll - бросить кубики\n'
        f'/buy - купить собственность'
    )

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /new_game"""
    user = update.effective_user
    await update.message.reply_text(
        f'{user.first_name}, новая игра создана! 🎮\n'
        f'ID игры: 12345\n'
        f'Пригласи друзей командой /join'
    )

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /join"""
    user = update.effective_user
    await update.message.reply_text(
        f'{user.first_name} присоединился к игре! 🎉\n'
        f'Ожидаем других игроков...'
    )

async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /roll"""
    import random
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    await update.message.reply_text(
        f'🎲 Бросок кубиков:\n'
        f'Кубик 1: {dice1}\n'
        f'Кубик 2: {dice2}\n'
        f'Сумма: {total}'
    )

async def buy_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy"""
    await update.message.reply_text(
        '🏠 Покупка собственности...\n'
        'Функция в разработке!'
    )
