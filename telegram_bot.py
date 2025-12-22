"""
Monopoly Premium Bot - Telegram бот (ЧИСТАЯ ЛОГИКА)
👑 Создано Темным Принцем (Dark Prince) 👑
ТОЛЬКО команды, кнопки, обработчики
"""

import os
import asyncio
import logging
import random
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove, WebAppInfo

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

# ==================== ОБЩИЕ ДАННЫЕ (симуляция) ====================
# В реальном проекте это импортируется из shared_data.py
WAITING_GAMES = {}
ACTIVE_GAMES = {}
STATS = {
    "active_games": 0,
    "total_players": 0,
    "version": "Premium v2.5 👑",
    "maintenance_mode": False
}

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

# ==================== КЛАВИАТУРЫ ====================
def main_menu_kb():
    """Главное меню (как в вашем начальном коде)"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Начать сбор игроков", callback_data="start_player_gathering")
    kb.button(text="📖 Правила игры", callback_data="show_rules")
    kb.button(text="👨‍💻 О девелопере", callback_data="show_developer")
    
    # WebApp ссылка
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
    web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
    kb.button(text="🌐 Статус системы", web_app=WebAppInfo(url=web_url))
    
    kb.adjust(1)
    return kb.as_markup()

def waiting_room_kb(chat_id, is_creator=False):
    """Лобби ожидания (как в вашем коде)"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    if is_creator:
        kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
    kb.adjust(2, 1)
    return kb.as_markup()

def game_main_kb():
    """Основная игровая клавиатура (ВСЕ КНОПКИ из ваших пожеланий)"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить")
    kb.button(text="📊 Мои активы")
    kb.button(text="🤝 Торговля")
    kb.button(text="❌ Скрыть меню")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def hide_menu_kb():
    """Скрыть меню"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="📱 Показать меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def build_kb(properties):
    """Клавиатура для строительства (дома/отели)"""
    kb = InlineKeyboardBuilder()
    for prop_id, prop_info in properties:
        prop_name = BOARD[prop_id][0] if prop_id in BOARD else f"Клетка {prop_id}"
        kb.button(text=f"🏠 {prop_name} (+1 дом)", callback_data=f"build_{prop_id}_house")
        kb.button(text=f"🏨 {prop_name} (отель)", callback_data=f"build_{prop_id}_hotel")
    
    if properties:
        kb.button(text="◀️ Назад", callback_data="back_to_game")
    else:
        kb.button(text="❌ Нет доступной недвижимости", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb.as_markup()

def trade_kb(other_players):
    """Клавиатура для торговли"""
    kb = InlineKeyboardBuilder()
    
    # Выбор игрока для торговли
    for player in other_players:
        kb.button(text=f"🤝 Торг с {player['name']}", callback_data=f"trade_with_{player['id']}")
    
    # Предложение денег
    kb.button(text="💰 Предложить деньги", callback_data="trade_money")
    
    # Предложение недвижимости
    kb.button(text="🏠 Предложить недвижимость", callback_data="trade_property")
    
    # Отмена
    kb.button(text="❌ Отменить сделку", callback_data="trade_cancel")
    
    kb.adjust(1, 2, 1)
    return kb.as_markup()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    try:
        await message.answer(
            f"👋 Привет! Я бот для игры в Монополию!\n\n"
            f"Используйте команду /monopoly чтобы начать игру в группе.\n"
            f"Используйте /hide чтобы скрыть меню.\n\n"
            f"Разработчик: {DEV_TAG}\n"
            f"👑 Версия Темного Принца",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("monopoly"))
async def cmd_monopoly(message: types.Message):
    """Главная команда - РОВНО КАК В ВАШЕМ КОДЕ"""
    try:
        if STATS.get("maintenance_mode", False):
            await message.answer(
                f"⚠️ {MAINTENANCE_MSG}\n\n"
                f"👑 Темный Принц уже исправляет это ♥️♥️",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n"
            "👑 Версия Темного Принца\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_monopoly: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("hide"))
async def cmd_hide_menu(message: types.Message):
    """Команда /hide - скрыть меню"""
    try:
        await message.answer(
            "✅ Меню скрыто. Чтобы вернуть меню, нажмите кнопку ниже или используйте /monopoly",
            reply_markup=hide_menu_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_hide: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

# ==================== КНОПКИ МЕНЮ ====================
@dp.message(F.text == "❌ Скрыть меню")
async def hide_menu_button(message: types.Message):
    """Кнопка скрытия меню"""
    try:
        await message.answer(
            "✅ Меню скрыто. Чтобы вернуть меню, нажмите кнопку ниже или используйте /monopoly",
            reply_markup=hide_menu_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в hide_menu_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "📱 Показать меню")
async def show_menu_button(message: types.Message):
    """Кнопка показа меню"""
    try:
        await cmd_monopoly(message)
    except Exception as e:
        logger.error(f"Ошибка в show_menu_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "🎲 Бросить кубик")
async def roll_dice_button(message: types.Message):
    """Кнопка броска кубика - ПОЛНАЯ ЛОГИКА"""
    try:
        chat_id = message.chat.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена в этом чате!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        if not game.get("players"):
            await message.answer("⚠️ В игре нет игроков!")
            return
        
        # Определяем текущего игрока
        current_idx = game.get("current_player", 0)
        player = game["players"][current_idx]
        
        # Бросаем кубик (2 кубика как в настоящей Монополии)
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        # Обновляем позицию
        current_pos = player.get("position", 0)
        new_pos = (current_pos + total) % 40
        
        player["position"] = new_pos
        
        # Определяем клетку
        if new_pos in BOARD:
            cell_name, price, rent, color = BOARD[new_pos]
            cell_type = "property"
            cell_info = f"🏠 <b>{cell_name}</b>\n💰 Цена: {price}$\n🎨 Цвет: {color}"
        elif new_pos == 0:
            cell_name = "СТАРТ"
            cell_type = "start"
            cell_info = "🏁 <b>СТАРТ</b>\n🎉 Получите 200$!"
        elif new_pos == 4:
            cell_name = "ПОДОХОДНЫЙ НАЛОГ"
            cell_type = "tax"
            cell_info = "💸 <b>ПОДОХОДНЫЙ НАЛОГ</b>\n⚠️ Заплатите 200$"
        elif new_pos == 10:
            cell_name = "ТЮРЬМА"
            cell_type = "jail"
            cell_info = "🚓 <b>ТЮРЬМА</b>\n👮 Просто посещение"
        elif new_pos == 20:
            cell_name = "БЕСПЛАТНАЯ ПАРКОВКА"
            cell_type = "parking"
            cell_info = "🅿️ <b>БЕСПЛАТНАЯ ПАРКОВКА</b>\n🎁 Бесплатный отдых"
        elif new_pos == 30:
            cell_name = "ОТПРАВЛЯЙТЕСЬ В ТЮРЬМУ"
            cell_type = "go_to_jail"
            cell_info = "⛓️ <b>ОТПРАВЛЯЙТЕСЬ В ТЮРЬМУ</b>\n🚨 Прямо в тюрьму!"
        else:
            cell_name = f"Клетка {new_pos}"
            cell_type = "other"
            cell_info = f"📍 <b>Клетка {new_pos}</b>"
        
        # Сообщение о результате
        message_text = (
            f"🎲 <b>Ход игрока {player['name']}:</b>\n"
            f"🎯 Кубик 1: <b>{dice1}</b>\n"
            f"🎯 Кубик 2: <b>{dice2}</b>\n"
            f"📊 Сумма: <b>{total}</b>\n"
            f"📍 Позиция: {current_pos} → <b>{new_pos}</b>\n\n"
            f"{cell_info}\n\n"
        )
        
        # Дополнительные действия в зависимости от клетки
        if cell_type == "property":
            # Проверяем, свободна ли недвижимость
            if new_pos not in game.get("properties", {}):
                message_text += f"❓ <b>Свободная недвижимость!</b>\nХотите купить за {price}$?"
            else:
                owner_id = game["properties"][new_pos]["owner"]
                if owner_id != player["id"]:
                    rent_to_pay = rent * (2 if game["properties"][new_pos].get("monopoly", False) else 1)
                    message_text += f"💸 <b>Чужая недвижимость!</b>\nПлатите аренду {rent_to_pay}$ владельцу"
                else:
                    message_text += f"✅ <b>Ваша недвижимость!</b>\nМожете строить дома"
        
        elif cell_type == "start":
            # Начисляем деньги за прохождение старта
            player["balance"] = player.get("balance", 1500) + 200
            message_text += f"💰 <b>+200$</b> за прохождение СТАРТА\n💰 Баланс: {player['balance']}$"
        
        elif cell_type == "tax":
            tax_amount = 200
            player["balance"] = player.get("balance", 1500) - tax_amount
            message_text += f"💸 <b>-{tax_amount}$</b> уплачено в казну\n💰 Баланс: {player['balance']}$"
        
        elif cell_type == "go_to_jail":
            player["position"] = 10  # Тюрьма
            player["in_jail"] = True
            player["jail_turns"] = 0
            message_text += f"⛓️ <b>Отправляетесь в тюрьму!</b>\nСледующие 3 хода в тюрьме"
        
        await message.answer(message_text, parse_mode="HTML")
        
        # Передаем ход следующему игроку
        next_idx = (current_idx + 1) % len(game["players"])
        ACTIVE_GAMES[chat_id]["current_player"] = next_idx
        
        # Уведомляем о следующем ходе
        next_player = game["players"][next_idx]
        await message.answer(
            f"➡️ <b>Следующий ход: {next_player['name']}</b>\n"
            f"Нажмите '🎲 Бросить кубик' для хода",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в roll_dice_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "🏠 Построить")
async def build_button(message: types.Message):
    """Кнопка строительства - логика строительства домов/отелей"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим игрока
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Находим недвижимость игрока
        player_properties = []
        game_properties = game.get("properties", {})
        
        for cell_id, prop_info in game_properties.items():
            if prop_info.get("owner") == user_id:
                # Проверяем, можно ли строить (есть монополия)
                color = BOARD[cell_id][3] if cell_id in BOARD else ""
                same_color_props = [cid for cid, pinfo in game_properties.items() 
                                  if BOARD.get(cid, ["", 0, 0, ""])[3] == color and pinfo.get("owner") == user_id]
                
                # Монополия - если владеет всеми свойствами этого цвета
                all_same_color = [cid for cid in BOARD if BOARD[cid][3] == color]
                has_monopoly = len(same_color_props) == len(all_same_color)
                
                if has_monopoly:
                    current_houses = prop_info.get("houses", 0)
                    player_properties.append((cell_id, {
                        "name": BOARD[cell_id][0],
                        "houses": current_houses,
                        "can_build_house": current_houses < 4,
                        "can_build_hotel": current_houses == 4,
                        "price": BOARD[cell_id][1]
                    }))
        
        if not player_properties:
            await message.answer(
                "❌ <b>Нет доступной недвижимости для строительства</b>\n\n"
                "Чтобы строить дома, вам нужно:\n"
                "1. Купить недвижимость 🏠\n"
                "2. Собрать все свойства одного цвета 🎨\n"
                "3. Иметь достаточный баланс 💰",
                parse_mode="HTML"
            )
            return
        
        # Показываем клавиатуру для строительства
        await message.answer(
            "🏗️ <b>Строительство домов и отелей</b>\n\n"
            "Выберите недвижимость для улучшения:\n"
            "🏠 Дом (+ к аренде)\n"
            "🏨 Отель (требуется 4 дома)\n\n"
            "💰 Стоимость строительства: 50% от цены недвижимости",
            parse_mode="HTML",
            reply_markup=build_kb(player_properties)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в build_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "📊 Мои активы")
async def show_assets_button(message: types.Message):
    """Кнопка показа активов - полная информация"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим игрока
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Собираем информацию об активах
        balance = player.get("balance", 1500)
        position = player.get("position", 0)
        in_jail = player.get("in_jail", False)
        jail_turns = player.get("jail_turns", 0)
        
        # Недвижимость игрока
        properties = []
        total_property_value = 0
        game_properties = game.get("properties", {})
        
        for cell_id, prop_info in game_properties.items():
            if prop_info.get("owner") == user_id:
                if cell_id in BOARD:
                    name, price, rent, color = BOARD[cell_id]
                    houses = prop_info.get("houses", 0)
                    is_hotel = houses == 5
                    
                    properties.append({
                        "name": name,
                        "price": price,
                        "color": color,
                        "houses": houses,
                        "is_hotel": is_hotel,
                        "current_rent": rent * (1 + houses) * (2 if prop_info.get("monopoly", False) else 1)
                    })
                    total_property_value += price
        
        # Формируем сообщение
        assets_text = f"💰 <b>Активы игрока {player['name']}</b>\n\n"
        
        # Основная информация
        assets_text += f"💵 Баланс: <b>{balance}$</b>\n"
        assets_text += f"📍 Позиция: <b>{position}</b> "
        
        if position in BOARD:
            assets_text += f"({BOARD[position][0]})\n"
        elif position == 0:
            assets_text += "(СТАРТ)\n"
        elif position == 10:
            assets_text += "(ТЮРЬМА)\n"
        else:
            assets_text += "\n"
        
        if in_jail:
            assets_text += f"🚓 В тюрьме, осталось ходов: <b>{3 - jail_turns}</b>\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(properties)} объектов</b>\n"
        assets_text += f"💎 Общая стоимость: <b>{total_property_value}$</b>\n\n"
        
        # Детали недвижимости
        if properties:
            assets_text += "📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties:
                house_info = ""
                if prop["is_hotel"]:
                    house_info = "🏨 Отель"
                elif prop["houses"] > 0:
                    house_info = f"🏠 {prop['houses']} дом(а)"
                
                assets_text += (
                    f"• {prop['name']} ({prop['color']})\n"
                    f"  💰 Цена: {prop['price']}$ | "
                    f"🏘️ Аренда: {prop['current_rent']}$\n"
                    f"  {house_info}\n"
                )
        else:
            assets_text += "❌ <i>У вас пока нет недвижимости</i>\n"
        
        # Советы
        assets_text += "\n💡 <b>Советы:</b>\n"
        if balance < 500:
            assets_text += "💰 Низкий баланс! Старайтесь не покупать дорогую недвижимость\n"
        if len(properties) >= 3:
            assets_text += "🏆 Хороший портфель! Подумайте о строительстве домов\n"
        if not properties:
            assets_text += "🎯 Покупайте недвижимость при первой возможности\n"
        
        await message.answer(assets_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в show_assets_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "🤝 Торговля")
async def trade_button(message: types.Message):
    """Кнопка торговли - система обмена"""
    try:
        if STATS.get("maintenance_mode", False):
            await message.answer(f"⚠️ {MAINTENANCE_MSG}")
            return
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, достаточно ли игроков
        if len(game.get("players", [])) < 2:
            await message.answer("❌ <b>Недостаточно игроков для торговли!</b>\n\n"
                               "Нужно минимум 2 игрока в игре",
                               parse_mode="HTML")
            return
        
        # Находим текущего игрока
        current_player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        if not current_player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Другие игроки
        other_players = [p for p in game.get("players", []) if p["id"] != user_id]
        
        if not other_players:
            await message.answer("❌ Нет других игроков для торговли!")
            return
        
        # Создаем клавиатуру для торговли
        kb = InlineKeyboardBuilder()
        
        # Кнопки для предложения денег
        money_options = [50, 100, 200, 500, 1000]
        for amount in money_options:
            if current_player.get("balance", 1500) >= amount:
                kb.button(text=f"💰 Предложить {amount}$", callback_data=f"trade_offer_money_{amount}")
        
        # Кнопки для предложения недвижимости
        player_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id and prop_id in BOARD:
                prop_name = BOARD[prop_id][0]
                player_properties.append((prop_id, prop_name))
        
        for prop_id, prop_name in player_properties[:5]:  # Ограничиваем 5 свойствами
            kb.button(text=f"🏠 {prop_name}", callback_data=f"trade_offer_prop_{prop_id}")
        
        # Кнопка отмены
        kb.button(text="❌ Отменить", callback_data="trade_cancel")
        
        kb.adjust(2, 2, 1)  # Разметка кнопок
        
        await message.answer(
            "🤝 <b>Система торговли</b>\n\n"
            "Выберите, что хотите предложить:\n\n"
            f"💰 Ваш баланс: <b>{current_player.get('balance', 1500)}$</b>\n"
            f"🏠 Ваша недвижимость: <b>{len(player_properties)} объектов</b>\n\n"
            "Или выберите игрока для прямых переговоров:",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в trade_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

# ==================== CALLBACK ОБРАБОТЧИКИ ДЛЯ ТОРГОВЛИ ====================
@dp.callback_query(F.data.startswith("trade_offer_money_"))
async def trade_offer_money(c: types.CallbackQuery):
    """Предложение денег в торговле"""
    try:
        amount = int(c.data.split("_")[3])
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        
        if not player:
            await c.answer("⚠️ Вы не в игре!", show_alert=True)
            return
        
        if player.get("balance", 1500) < amount:
            await c.answer("❌ Недостаточно средств!", show_alert=True)
            return
        
        # Создаем клавиатуру для выбора игрока
        kb = InlineKeyboardBuilder()
        other_players = [p for p in game.get("players", []) if p["id"] != user_id]
        
        for other in other_players:
            kb.button(text=f"🤝 {other['name']}", callback_data=f"trade_to_{other['id']}_money_{amount}")
        
        kb.button(text="❌ Отмена", callback_data="trade_cancel")
        kb.adjust(1)
        
        await c.message.edit_text(
            f"💰 <b>Предложение: {amount}$</b>\n\n"
            "Выберите игрока, которому хотите предложить деньги:",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в trade_offer_money: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("trade_offer_prop_"))
async def trade_offer_property(c: types.CallbackQuery):
    """Предложение недвижимости в торговле"""
    try:
        prop_id = int(c.data.split("_")[3])
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что игрок владеет этой недвижимостью
        if prop_id not in game.get("properties", {}) or game["properties"][prop_id].get("owner") != user_id:
            await c.answer("❌ Вы не владеете этой недвижимостью!", show_alert=True)
            return
        
        prop_name = BOARD[prop_id][0] if prop_id in BOARD else f"Клетка {prop_id}"
        
        # Создаем клавиатуру для выбора игрока
        kb = InlineKeyboardBuilder()
        other_players = [p for p in game.get("players", []) if p["id"] != user_id]
        
        for other in other_players:
            kb.button(text=f"🤝 {other['name']}", callback_data=f"trade_to_{other['id']}_prop_{prop_id}")
        
        kb.button(text="❌ Отмена", callback_data="trade_cancel")
        kb.adjust(1)
        
        await c.message.edit_text(
            f"🏠 <b>Предложение недвижимости: {prop_name}</b>\n\n"
            f"💰 Цена покупки: {BOARD[prop_id][1]}$\n"
            f"💸 Аренда: {BOARD[prop_id][2]}$\n\n"
            "Выберите игрока, которому хотите предложить:",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в trade_offer_property: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("trade_to_"))
async def trade_to_player(c: types.CallbackQuery):
    """Предложение сделки конкретному игроку"""
    try:
        parts = c.data.split("_")
        target_player_id = int(parts[2])
        offer_type = parts[3]  # money или prop
        offer_value = parts[4]  # amount или prop_id
        
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим игроков
        from_player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        to_player = next((p for p in game.get("players", []) if p["id"] == target_player_id), None)
        
        if not from_player or not to_player:
            await c.answer("❌ Игрок не найден!", show_alert=True)
            return
        
        # Формируем предложение
        if offer_type == "money":
            amount = int(offer_value)
            offer_text = f"💰 {amount}$"
            # Проверяем баланс
            if from_player.get("balance", 1500) < amount:
                await c.answer("❌ Недостаточно средств!", show_alert=True)
                return
        else:  # property
            prop_id = int(offer_value)
            prop_name = BOARD[prop_id][0] if prop_id in BOARD else f"Клетка {prop_id}"
            offer_text = f"🏠 {prop_name}"
            # Проверяем владение
            if prop_id not in game.get("properties", {}) or game["properties"][prop_id].get("owner") != user_id:
                await c.answer("❌ Вы не владеете этой недвижимостью!", show_alert=True)
                return
        
        # Сохраняем предложение в игре
        if "trade_offers" not in game:
            game["trade_offers"] = []
        
        game["trade_offers"].append({
            "from_player_id": user_id,
            "from_player_name": from_player.get("name", "Неизвестно"),
            "to_player_id": target_player_id,
            "to_player_name": to_player.get("name", "Неизвестно"),
            "offer_type": offer_type,
            "offer_value": offer_value,
            "created_at": datetime.now().isoformat()
        })
        
        # Уведомляем получателя
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🤝 <b>Предложение сделки от {from_player['name']}</b>\n\n"
                     f"📦 Предложение: {offer_text}\n\n"
                     f"💬 Чтобы принять или отклонить, используйте команду /trade",
                parse_mode="HTML"
            )
        except:
            pass  # Если не удалось отправить сообщение
        
        await c.message.edit_text(
            f"✅ <b>Предложение отправлено {to_player['name']}!</b>\n\n"
            f"📦 Ваше предложение: {offer_text}\n\n"
            f"⏳ Ожидайте ответа...",
            parse_mode="HTML"
        )
        
        await c.answer("✅ Предложение отправлено!")
        
    except Exception as e:
        logger.error(f"Ошибка в trade_to_player: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "trade_cancel")
async def trade_cancel(c: types.CallbackQuery):
    """Отмена торговли"""
    await c.message.edit_text(
        "❌ <b>Торговля отменена</b>\n\n"
        "Возвращаюсь в игровое меню...",
        parse_mode="HTML"
    )
    await c.answer()

@dp.callback_query(F.data == "show_rules")
async def show_rules(c: types.CallbackQuery):
    """Показать правила игры (как в вашем коде)"""
    try:
        if STATS.get("maintenance_mode", False):
            await c.answer(MAINTENANCE_MSG, show_alert=True)
            return
        
        rules_text = (
            "📖 <b>Правила Monopoly Premium:</b>\n\n"
            "1. 🏁 Каждый игрок начинает с <b>1500$</b> на позиции <b>Старт</b>\n"
            "2. 🎲 По очереди бросайте кубик и передвигайтесь по полю\n"
            "3. 🏠 При попадании на свободную клетку можете её купить\n"
            "4. 💰 При попадании на чужую клетку платите аренду владельцу\n"
            "5. 🎨 Собирайте наборы одного цвета для увеличения аренды\n"
            "6. 🏘️ Стройте дома (до 4) и отели для увеличения доходов\n"
            "7. 🏦 Цель - остаться последним непобанкротившимся игроком\n\n"
            "🎯 <b>Особенности Premium версии:</b>\n"
            "• 🌐 Web-статистика в реальном времени\n"
            "• 🏆 Система достижений и наград\n"
            "• 🤝 Поддержка торговли между игроками\n"
            "• 💾 Автосохранение прогресса в БД\n"
            "• 👥 Поддержка до 8 игроков одновременно\n\n"
            "⚠️ <b>Важно:</b>\n"
            "• Минимум 2 игрока для начала\n"
            "• Используйте /hide чтобы скрыть меню\n"
            "• Игра сохраняется автоматически\n\n"
            "👑 <b>Версия Темного Принца включает:</b>\n"
            "• Улучшенную графику\n"
            "• Расширенные возможности\n"
            "• Эксклюзивные функции"
        )
        
        # Создаем клавиатуру для правил
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад в меню", callback_data="back_to_main")
        kb.adjust(1)
        
        await c.message.answer(rules_text, parse_mode="HTML", reply_markup=kb.as_markup())
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_rules: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "show_developer")
async def show_developer(c: types.CallbackQuery):
    """Показать информацию о разработчике (как в вашем коде)"""
    try:
        if STATS.get("maintenance_mode", False):
            await c.answer(MAINTENANCE_MSG, show_alert=True)
            return
        
        dev_text = (
            "👨‍💻 <b>О разработчике:</b>\n\n"
            f"<b>Разработчик:</b> {DEV_TAG}\n"
            "<b>Версия бота:</b> Premium v2.5\n"
            "<b>Титул:</b> Темный Принц (Dark Prince)\n"
            "<b>Дата релиза:</b> 2024.12.18\n"
            "<b>Технологии:</b> Python, aiogram, Flask, SQLite\n\n"
            "✨ <b>Особенности этой версии:</b>\n"
            "• 🎨 Полностью переработанный интерфейс\n"
            "• 🌐 Web-панель управления и мониторинга\n"
            "• 🎮 Улучшенная система игрового процесса\n"
            "• 💾 База данных для сохранения прогресса\n"
            "• 👥 Поддержка групповых игр до 8 человек\n"
            "• 📊 Подробная статистика и аналитика\n\n"
            "💡 <b>Идеи и предложения:</b>\n"
            f"Пишите разработчику: {DEV_TAG}\n\n"
            "⭐ Если вам нравится бот, поделитесь им с друзьями!\n\n"
            "👑 <i>Создано с любовью Темным Принцем</i>"
        )
        
        # Создаем клавиатуру
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад в меню", callback_data="back_to_main")
        
        # WebApp кнопка
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
        web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
        kb.button(text="🌐 Web-статус", web_app=WebAppInfo(url=web_url))
        
        kb.adjust(1)
        
        await c.message.answer(dev_text, parse_mode="HTML", reply_markup=kb.as_markup())
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_developer: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(c: types.CallbackQuery):
    """Вернуться в главное меню"""
    try:
        await c.message.delete()
        await cmd_monopoly(c.message)
        await c.answer()
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== БАЗА ДАННЫХ ====================
async def init_db():
    """Инициализация базы данных"""
    try:
        import aiosqlite
        async with aiosqlite.connect('monopoly_premium.db') as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS players (
                chat_id int, user_id int, name text, 
                balance int DEFAULT 1500, pos int DEFAULT 0, 
                jail int DEFAULT 0, PRIMARY KEY(chat_id, user_id))""")
            await db.execute("""CREATE TABLE IF NOT EXISTS property (
                chat_id int, cell_idx int, owner_id int, houses int DEFAULT 0, 
                PRIMARY KEY(chat_id, cell_idx))""")
            await db.execute("CREATE TABLE IF NOT EXISTS awards (user_id int, title text, chat_id int)")
            await db.commit()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")

# ==================== ЗАПУСК БОТА ====================
async def start_bot():
    """Асинхронный запуск бота"""
    try:
        logger.info("🤖 Инициализация базы данных...")
        await init_db()
        
        logger.info("🚀 Telegram бот запускается...")
        logger.info("👑 Темный Принц активирован")
        
        # Удаляем вебхук (если был)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем поллинг
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise

def main():
    """Основная функция запуска"""
    logger.info("=" * 60)
    logger.info("🎮 MONOPOLY PREMIUM BOT")
    logger.info(f"👑 Версия: {STATS['version']}")
    logger.info(f"🤴 Разработчик: {STATS.get('prince_title', 'Темный Принц')}")
    logger.info(f"🌐 Web-панель: http://localhost:{PORT}")
    logger.info("=" * 60)
    
    if STATS.get("maintenance_mode", False):
        logger.warning(f"⚠️  Режим обслуживания: {STATS['maintenance_msg']}")
    
    # Запускаем бота
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
