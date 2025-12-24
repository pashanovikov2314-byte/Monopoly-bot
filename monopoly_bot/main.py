"""
Monopoly Premium Bot - Telegram бот (Обновленная версия)
👑 Создано Темным Принцем (Dark Prince) 👑
Включает ВСЕ новые функции и кнопки
"""

import os
import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove

# Импортируем наши модули
from config import *
from database import db
from keyboards import *
from handlers.commands import dp, HIDDEN_MENU_USERS, STATS

# ==================== НАСТРОЙКИ ====================
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    logging.error("❌ BOT_TOKEN не найден!")
    exit(1)

PORT = int(os.environ.get("PORT", 8083))
DEV_TAG = "@Whylovely05"
MAINTENANCE_MSG = "Бот обновляется, Темный принц уже исправляет это ♥️♥️"
BANNER = "┏━━━━━━━━━━━━━━━━━━┓\n┃  Monopoly Premium  ┃\n┗━━━━━━━━━━━━━━━━━━┛"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Глобальные переменные (как в вашем скелете)
WAITING_GAMES = {}
ACTIVE_GAMES = {}
HIDDEN_MENU_USERS = {}  # {user_id: chat_id} - кто скрыл меню (как в скелете)
STATS = {"maintenance_mode": False}

# Игровое поле (как в скелете, можно расширить)
BOARD = {
    1: ["Житная", 60, 4, "BROWN"], 3: ["Нагатинская", 60, 4, "BROWN"],
    5: ["Рижская ж/д", 200, 25, "RAIL"], 6: ["Варшавское ш.", 100, 6, "BLUE"],
    8: ["Огородный пр.", 100, 6, "BLUE"], 9: ["Рижская", 120, 8, "BLUE"],
    11: ["Курская", 140, 10, "PINK"], 12: ["Электросеть", 150, 10, "UTIL"],
    13: ["Абрамцево", 140, 10, "PINK"], 14: ["Пантелеевская", 160, 12, "PINK"],
    15: ["Казанская ж/д", 200, 25, "RAIL"], 16: ["Вавилова", 180, 14, "ORANGE"],
    18: ["Тимирязевская", 180, 14, "ORANGE"], 19: ["Лихоборы", 200, 16, "ORANGE"],
    21: ["Арбат", 220, 18, "RED"], 23: ["Полянка", 220, 18, "RED"],
    24: ["Сретенка", 240, 20, "RED"], 25: ["Курская ж/д", 200, 25, "RAIL"],
    26: ["Ростовская", 260, 22, "YELLOW"], 27: ["Рязанский пр.", 260, 22, "YELLOW"],
    28: ["Водопровод", 150, 10, "UTIL"], 29: ["Новинский б-р", 280, 24, "YELLOW"],
    31: ["Пушкинская", 300, 26, "GREEN"], 32: ["Тверская", 300, 26, "GREEN"],
    34: ["Маяковского", 320, 28, "GREEN"], 35: ["Ленинградская ж/д", 200, 25, "RAIL"],
    37: ["Кутузовский", 350, 35, "DARKBLUE"], 39: ["Бродвей", 400, 50, "DARKBLUE"]
}

# ==================== ОБРАБОТЧИКИ ТЕКСТОВЫХ КНОПОК ====================

@dp.message(F.text.in_([
    "🎲 Бросить кубик", "🏠 Построить", "💰 Банк", 
    "🤝 Торговля", "📊 Мои активы", "🗺️ Карта игры",
    "🏛️ Тюрьма", "📈 Статистика"
]))
async def handle_game_buttons(message: types.Message):
    """Обработка игровых кнопок из ReplyKeyboard"""
    text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Получаем клавиатуру для этой кнопки
    reply_kb = get_reply_keyboard_for_text(text)
    
    if reply_kb:
        if text == "🎲 Бросить кубик":
            await message.answer(
                "🎲 <b>Бросок кубиков</b>\n\n"
                "Выберите тип броска:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "🏠 Построить":
            await message.answer(
                "🏠 <b>Управление недвижимостью</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "💰 Банк":
            await message.answer(
                "💰 <b>Банковские операции</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "🤝 Торговля":
            await message.answer(
                "🤝 <b>Торговля с игроками</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "📊 Мои активы":
            await message.answer(
                "📊 <b>Мои активы</b>\n\n"
                "Выберите что показать:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "🗺️ Карта игры":
            await message.answer(
                "🗺️ <b>Карта игры</b>\n\n"
                "Выберите тип карты:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "🏛️ Тюрьма":
            await message.answer(
                "🏛️ <b>Тюрьма</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
        elif text == "📈 Статистика":
            await message.answer(
                "📈 <b>Статистика</b>\n\n"
                "Выберите что показать:",
                parse_mode="HTML",
                reply_markup=reply_kb
            )
    else:
        # Если нет специальной клавиатуры, возвращаем основную
        await message.answer(
            "Выберите действие:",
            reply_markup=game_main_kb()
        )

@dp.message(F.text == "⬅️ Назад в меню")
async def back_to_main_menu(message: types.Message):
    """Возврат в главное меню игры"""
    await message.answer(
        "Возврат в главное меню:",
        reply_markup=game_main_kb()
    )

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск Monopoly Premium Bot...")
    
    # Инициализация базы данных
    db.init_database()
    
    # Очистка старых игр
    db.cleanup_old_games()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
