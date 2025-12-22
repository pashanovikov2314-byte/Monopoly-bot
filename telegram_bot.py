"""
Monopoly Premium Bot - Telegram бот (Часть 1)
👑 Создано Темным Принцем (Dark Prince) 👑
Исправленный код: разные меню, скрытие меню
"""

import os
import asyncio
import logging
import random
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

# Глобальные переменные
WAITING_GAMES = {}
ACTIVE_GAMES = {}
HIDDEN_MENU_USERS = {}  # {user_id: chat_id} - кто скрыл меню
STATS = {"maintenance_mode": False}

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
def main_menu_kb(is_group=False):
    """Главное меню - РАЗНЫЕ кнопки для групп и ЛС"""
    kb = InlineKeyboardBuilder()
    
    if is_group:
        # Меню для ГРУППЫ
        kb.button(text="🎮 Начать сбор игроков", callback_data="start_player_gathering")
    else:
        # Меню для ЛИЧНЫХ СООБЩЕНИЙ
        kb.button(text="➕ Добавить в группу", url="https://t.me/MonopolyPremiumBot?startgroup=true")
    
    # Общие кнопки
    kb.button(text="📖 Правила игры", callback_data="show_rules")
    kb.button(text="👨‍💻 О девелопере", callback_data="show_developer")
    
    # WebApp ссылка
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
    web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
    kb.button(text="🌐 Статус системы", web_app=WebAppInfo(url=web_url))
    
    kb.adjust(1)
    return kb.as_markup()

def waiting_room_kb(chat_id, is_creator=False):
    """Лобби ожидания"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    if is_creator:
        kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
    kb.adjust(2, 1)
    return kb.as_markup()

def game_main_kb():
    """Основная игровая клавиатура"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить")
    kb.button(text="📊 Мои активы")
    kb.button(text="🤝 Торговля")
    kb.button(text="❌ Скрыть меню")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def inline_menu_kb():
    """Inline меню для тех кто скрыл основное"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик", callback_data="inline_roll_dice")
    kb.button(text="🏠 Построить", callback_data="inline_build")
    kb.button(text="📊 Мои активы", callback_data="inline_assets")
    kb.button(text="🤝 Торговля", callback_data="inline_trade")
    kb.button(text="📱 Вернуть меню", callback_data="restore_menu")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ"""
    try:
        # Проверяем тип чата - отвечаем ТОЛЬКО в ЛС
        if message.chat.type not in ["private"]:
            await message.answer(
                "👋 Для управления игрой используйте команду /monopoly в этой группе",
                parse_mode="HTML"
            )
            return
        
        # Только в личных сообщениях показываем полное меню
        await message.answer(
            f"👋 <b>Добро пожаловать в Monopoly Premium!</b>\n\n"
            f"🎮 <b>Как начать игру:</b>\n"
            f"1. Добавьте меня в группу (кнопка ниже)\n"
            f"2. Дайте мне права администратора\n"
            f"3. Напишите /monopoly в группе\n"
            f"4. Начните сбор игроков\n\n"
            f"👑 <b>Версия Темного Принца</b>\n"
            f"✨ Premium Edition v2.5\n\n"
            f"Разработчик: {DEV_TAG}",
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=False)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("monopoly"))
async def cmd_monopoly(message: types.Message):
    """Главная команда - РАЗНЫЕ меню для групп и ЛС"""
    try:
        if STATS.get("maintenance_mode", False):
            await message.answer(
                f"⚠️ {MAINTENANCE_MSG}\n\n"
                f"👑 Темный Принц уже исправляет это ♥️♥️",
                parse_mode="HTML"
            )
            return
        
        # Определяем тип чата
        is_group = message.chat.type in ["group", "supergroup"]
        
        # Проверяем, скрыл ли пользователь меню
        user_id = message.from_user.id
        if user_id in HIDDEN_MENU_USERS:
            # Пользователь скрыл меню - показываем inline версию
            await show_inline_menu(message)
            return
        
        # Разные приветствия
        if is_group:
            header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
            header += "🎮 <b>Доступные действия:</b>"
        else:
            header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
            header += "👋 <b>Добро пожаловать!</b>\n\n"
            header += "Чтобы начать игру, добавьте бота в группу и используйте /monopoly там"
        
        await message.answer(
            header,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=is_group)
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_monopoly: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("hide"))
async def cmd_hide_menu(message: types.Message):
    """Команда /hide - скрыть меню (ТОЛЬКО для активных игр)"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем, есть ли активная игра
        if chat_id not in ACTIVE_GAMES:
            await message.answer(
                "❌ <b>Нет активной игры для скрытия меню!</b>\n\n"
                "Сначала начните игру с помощью /monopoly",
                parse_mode="HTML"
            )
            return
        
        # Проверяем, участвует ли пользователь в игре
        game = ACTIVE_GAMES[chat_id]
        player_exists = any(p["id"] == user_id for p in game.get("players", []))
        
        if not player_exists:
            await message.answer(
                "❌ <b>Вы не участвуете в этой игре!</b>\n\n"
                "Только игроки могут скрывать меню",
                parse_mode="HTML"
            )
            return
        
        # Скрываем меню
        await message.answer(
            "✅ <b>Меню скрыто!</b>\n\n"
            "Теперь используйте кнопки в сообщении ниже для управления игрой.\n"
            "Эти кнопки видны только вам.\n\n"
            "Чтобы вернуть обычное меню, нажмите '📱 Вернуть меню'",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Сохраняем информацию о скрытии
        HIDDEN_MENU_USERS[user_id] = chat_id
        
        # Показываем inline меню (только этому пользователю)
        await show_inline_menu(message, for_user_only=True)
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_hide: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def show_inline_menu(message: types.Message, for_user_only=False):
    """Показать inline меню (вместо скрытой клавиатуры)"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем, есть ли активная игра
        if chat_id not in ACTIVE_GAMES:
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим игрока
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        if not player:
            return
        
        # Получаем текущего игрока
        current_idx = game.get("current_player", 0)
        is_your_turn = (player["id"] == game["players"][current_idx]["id"]) if game["players"] else False
        
        turn_info = ""
        if is_your_turn:
            turn_info = "🎯 <b>Сейчас ваш ход!</b>\n"
        else:
            current_player = game["players"][current_idx] if game["players"] else None
            if current_player:
                turn_info = f"⏳ <b>Сейчас ходит: {current_player['name']}</b>\n"
        
        menu_text = (
            f"🎮 <b>Monopoly Premium - Inline меню</b>\n\n"
            f"👤 Игрок: {player['name']}\n"
            f"💰 Баланс: {player.get('balance', 1500)}$\n"
            f"{turn_info}\n"
            f"👇 <i>Используйте кнопки ниже для управления:</i>"
        )
        
        # Отправляем inline меню
        if for_user_only:
            # Только для конкретного пользователя
            await message.answer(
                menu_text,
                parse_mode="HTML",
                reply_markup=inline_menu_kb()
            )
        else:
            # В общий чат (но с reply_to, чтобы было видно только отправителю)
            await message.reply(
                menu_text,
                parse_mode="HTML",
                reply_markup=inline_menu_kb()
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_inline_menu: {e}")

# ==================== ОБРАБОТЧИКИ КНОПОК ====================
@dp.message(F.text == "❌ Скрыть меню")
async def hide_menu_button(message: types.Message):
    """Кнопка скрытия меню - работает как команда /hide"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем, есть ли активная игра
        if chat_id not in ACTIVE_GAMES:
            await message.answer(
                "❌ <b>Нет активной игры для скрытия меню!</b>",
                parse_mode="HTML"
            )
            return
        
        # Скрываем меню
        await message.answer(
            "✅ <b>Меню скрыто!</b>\n\n"
            "Теперь используйте кнопки в сообщении ниже для управления игрой.\n"
            "Эти кнопки видны только вам.\n\n"
            "Чтобы вернуть обычное меню, нажмите '📱 Вернуть меню'",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Сохраняем информацию о скрытии
        HIDDEN_MENU_USERS[user_id] = chat_id
        
        # Показываем inline меню
        await show_inline_menu(message, for_user_only=True)
        
    except Exception as e:
        logger.error(f"Ошибка в hide_menu_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.callback_query(F.data == "restore_menu")
async def restore_menu_callback(c: types.CallbackQuery):
    """Вернуть обычное меню"""
    try:
        user_id = c.from_user.id
        
        # Удаляем из списка скрытых
        if user_id in HIDDEN_MENU_USERS:
            del HIDDEN_MENU_USERS[user_id]
        
        # Удаляем inline сообщение
        await c.message.delete()
        
        # Показываем обычное меню
        await c.message.answer(
            "✅ <b>Обычное меню восстановлено!</b>\n\n"
            "Теперь используйте кнопки клавиатуры для управления игрой.\n\n"
            "Чтобы снова скрыть меню, нажмите '❌ Скрыть меню'",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
        await c.answer("✅ Меню восстановлено")
        
    except Exception as e:
        logger.error(f"Ошибка в restore_menu_callback: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== INLINE ОБРАБОТЧИКИ ====================
@dp.callback_query(F.data == "inline_roll_dice")
async def inline_roll_dice(c: types.CallbackQuery):
    """Inline бросок кубика"""
    try:
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем очередь
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if not current_player or current_player["id"] != user_id:
            if current_player:
                await c.answer(f"⏳ Сейчас ходит {current_player['name']}!", show_alert=True)
            else:
                await c.answer("❌ Ошибка определения хода!", show_alert=True)
            return
        
        # Бросаем кубик
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        # Обновляем позицию
        current_pos = current_player.get("position", 0)
        new_pos = (current_pos + total) % 40
        current_player["position"] = new_pos
        
        # Сообщение о результате
        result_text = (
            f"🎲 <b>{current_player['name']} бросает кубики:</b>\n"
            f"🎯 Кубик 1: <b>{dice1}</b>\n"
            f"🎯 Кубик 2: <b>{dice2}</b>\n"
            f"📊 Сумма: <b>{total}</b>\n"
            f"📍 Позиция: {current_pos} → <b>{new_pos}</b>"
        )
        
        # Определяем клетку
        if new_pos in BOARD:
            cell_name, price, rent, color = BOARD[new_pos]
            result_text += f"\n\n🏠 <b>{cell_name}</b>\n💰 Цена: {price}$\n🎨 Цвет: {color}"
        elif new_pos == 0:
            # СТАРТ
            current_player["balance"] = current_player.get("balance", 1500) + 200
            result_text += f"\n\n🏁 <b>СТАРТ</b>\n💰 +200$\n💵 Баланс: {current_player['balance']}$"
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx]
        
        result_text += f"\n\n➡️ <b>Следующий: {next_player['name']}</b>"
        
        # Обновляем сообщение
        await c.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=inline_menu_kb()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_roll_dice: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "inline_assets")
async def inline_assets(c: types.CallbackQuery):
    """Inline просмотр активов"""
    try:
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        
        if not player:
            await c.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        # Собираем информацию
        balance = player.get("balance", 1500)
        position = player.get("position", 0)
        
        # Недвижимость игрока
        properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id and prop_id in BOARD:
                prop_name = BOARD[prop_id][0]
                properties.append(prop_name)
        
        assets_text = (
            f"💰 <b>Активы {player['name']}</b>\n\n"
            f"💵 Баланс: <b>{balance}$</b>\n"
            f"📍 Позиция: <b>{position}</b>\n"
            f"🏠 Недвижимость: <b>{len(properties)} объектов</b>\n"
        )
        
        if properties:
            assets_text += "\n📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties[:5]:  # Ограничиваем 5 свойствами
                assets_text += f"• {prop}\n"
        
        if len(properties) > 5:
            assets_text += f"• ... и еще {len(properties) - 5}\n"
        
        # Обновляем сообщение
        await c.message.edit_text(
            assets_text,
            parse_mode="HTML",
            reply_markup=inline_menu_kb()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_assets: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ЗАПУСК БОТА ====================
async def start_bot():
    """Асинхронный запуск бота"""
    try:
        logger.info("🚀 Telegram бот запускается...")
        logger.info("👑 Темный Принц активирован")
        
        # Удаляем вебхук
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
    logger.info("👑 Версия с исправлениями")
    logger.info("=" * 60)
    
    # Запускаем бота
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()

# ==================== CALLBACK ОБРАБОТЧИКИ ДЛЯ ЛОББИ ====================
@dp.callback_query(F.data == "start_player_gathering")
async def start_gathering(c: types.CallbackQuery):
    """Начать сбор игроков"""
    try:
        if STATS.get("maintenance_mode", False):
            await c.answer(MAINTENANCE_MSG, show_alert=True)
            return
        
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id in WAITING_GAMES:
            await c.answer("⚠️ В этой группе уже идет сбор игроков!", show_alert=True)
            return
        
        WAITING_GAMES[chat_id] = {
            "creator_id": user_id,
            "creator_name": c.from_user.first_name,
            "players": [{
                "id": user_id,
                "name": c.from_user.first_name,
                "username": c.from_user.username,
                "position": 0,
                "balance": 1500
            }],
            "message_id": c.message.message_id,
            "created_at": datetime.now().isoformat()
        }
        
        players_text = "👥 <b>Игроки в ожидании:</b>\n"
        for player in WAITING_GAMES[chat_id]["players"]:
            players_text += f"• {player['name']}"
            if player.get('username'):
                players_text += f" (@{player['username']})"
            players_text += "\n"
        
        await c.message.edit_text(
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"Создатель: {c.from_user.first_name}\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти из игры' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру когда все готовы",
            parse_mode="HTML",
            reply_markup=waiting_room_kb(chat_id, is_creator=True)
        )
        
        await c.answer("🎮 Сбор игроков начат!")
        
    except Exception as e:
        logger.error(f"Ошибка в start_gathering: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("join_game_"))
async def join_game(c: types.CallbackQuery):
    """Присоединиться к игре"""
    try:
        chat_id = int(c.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await c.answer("⚠️ Игра не найдена или уже началась", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        user_id = c.from_user.id
        
        # Проверяем, не в игре ли уже
        for player in game["players"]:
            if player["id"] == user_id:
                await c.answer("✅ Вы уже в игре!")
                return
        
        # Добавляем игрока
        game["players"].append({
            "id": user_id,
            "name": c.from_user.first_name,
            "username": c.from_user.username,
            "position": 0,
            "balance": 1500
        })
        
        # Обновляем сообщение
        players_text = "👥 <b>Игроки в ожидании:</b>\n"
        for player in game["players"]:
            players_text += f"• {player['name']}"
            if player.get('username'):
                players_text += f" (@{player['username']})"
            players_text += "\n"
        
        is_creator = (user_id == game["creator_id"])
        
        await c.message.edit_text(
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"Создатель: {game['creator_name']}\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти из игры' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру когда все готовы",
            parse_mode="HTML",
            reply_markup=waiting_room_kb(chat_id, is_creator=is_creator)
        )
        
        await c.answer(f"🎮 Вы присоединились! Игроков: {len(game['players'])}")
        
    except Exception as e:
        logger.error(f"Ошибка в join_game: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("leave_game_"))
async def leave_game(c: types.CallbackQuery):
    """Выйти из игры"""
    try:
        chat_id = int(c.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await c.answer("⚠️ Игра не найдена", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        user_id = c.from_user.id
        
        # Удаляем игрока
        original_count = len(game["players"])
        game["players"] = [p for p in game["players"] if p["id"] != user_id]
        
        # Если игроков не осталось
        if not game["players"]:
            del WAITING_GAMES[chat_id]
            await c.message.edit_text("❌ Игра отменена - все игроки вышли")
            await c.answer("Игра отменена")
            return
        
        # Если вышел создатель, назначаем нового
        if user_id == game["creator_id"]:
            new_creator = game["players"][0]
            game["creator_id"] = new_creator["id"]
            game["creator_name"] = new_creator["name"]
        
        # Обновляем сообщение
        players_text = "👥 <b>Игроки в ожидании:</b>\n"
        for player in game["players"]:
            players_text += f"• {player['name']}"
            if player.get('username'):
                players_text += f" (@{player['username']})"
            players_text += "\n"
        
        is_creator = (c.from_user.id == game["creator_id"])
        
        await c.message.edit_text(
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"Создатель: {game['creator_name']}\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти из игры' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру когда все готовы",
            parse_mode="HTML",
            reply_markup=waiting_room_kb(chat_id, is_creator=is_creator)
        )
        
        await c.answer(f"🚪 Вы вышли. Игроков: {len(game['players'])}")
        
    except Exception as e:
        logger.error(f"Ошибка в leave_game: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("start_real_game_"))
async def start_real_game(c: types.CallbackQuery):
    """Начать игру"""
    try:
        chat_id = int(c.data.split("_")[3])
        
        if chat_id not in WAITING_GAMES:
            await c.answer("⚠️ Игра не найдена", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        
        # Проверяем права создателя
        if c.from_user.id != game["creator_id"]:
            await c.answer("⚠️ Только создатель игры может её начать!", show_alert=True)
            return
        
        # Проверяем количество игроков
        if len(game["players"]) < 2:
            await c.answer("⚠️ Нужно минимум 2 игрока для начала игры!", show_alert=True)
            return
        
        # Переносим игру в активные
        ACTIVE_GAMES[chat_id] = {
            "players": game["players"],
            "current_player": 0,
            "started_at": datetime.now(),
            "creator_id": game["creator_id"],
            "properties": {},
            "turn": 1
        }
        
        # Инициализируем игроков
        for player in ACTIVE_GAMES[chat_id]["players"]:
            player["balance"] = 1500
            player["position"] = 0
            player["properties"] = []
            player["in_jail"] = False
        
        # Удаляем из ожидающих
        del WAITING_GAMES[chat_id]
        
        # Формируем список игроков
        players_list = "\n".join([f"• {p['name']}" for p in ACTIVE_GAMES[chat_id]["players"]])
        
        # Отправляем сообщение о начале игры
        await c.message.edit_text(
            f"🎉 <b>Игра началась!</b>\n\n"
            f"<b>Участники:</b>\n{players_list}\n\n"
            f"💰 Стартовый баланс: <b>1500$</b>\n"
            f"🎲 Первым ходит: <b>{ACTIVE_GAMES[chat_id]['players'][0]['name']}</b>\n"
            f"🔄 Ход: <b>1</b>\n\n"
            f"<i>Используйте меню ниже для управления игрой</i>",
            parse_mode="HTML"
        )
        
        # Отправляем игровое меню ВСЕМ игрокам
        first_player = ACTIVE_GAMES[chat_id]["players"][0]
        menu_message = await bot.send_message(
            chat_id=chat_id,
            text=f"🎮 <b>Игра началась!</b>\n\n"
                 f"📢 <b>{first_player['name']}</b>, ваш ход первый!\n"
                 f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
        await c.answer("🎮 Игра началась!")
        
    except Exception as e:
        logger.error(f"Ошибка в start_real_game: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ КНОПОК ИГРЫ ====================
@dp.message(F.text == "🎲 Бросить кубик")
async def roll_dice_button(message: types.Message):
    """Кнопка броска кубика в основной клавиатуре"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена в этом чате!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем очередь
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if not current_player or current_player["id"] != user_id:
            if current_player:
                await message.answer(f"⏳ Сейчас ходит {current_player['name']}!")
            return
        
        # Бросаем кубик
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        # Обновляем позицию
        current_pos = current_player.get("position", 0)
        new_pos = (current_pos + total) % 40
        current_player["position"] = new_pos
        
        # Формируем сообщение
        message_text = (
            f"🎲 <b>{current_player['name']} бросает кубики:</b>\n"
            f"🎯 Кубик 1: <b>{dice1}</b>\n"
            f"🎯 Кубик 2: <b>{dice2}</b>\n"
            f"📊 Сумма: <b>{total}</b>\n"
            f"📍 Позиция: {current_pos} → <b>{new_pos}</b>"
        )
        
        # Определяем клетку
        if new_pos in BOARD:
            cell_name, price, rent, color = BOARD[new_pos]
            message_text += f"\n\n🏠 <b>{cell_name}</b>\n💰 Цена: {price}$\n🎨 Цвет: {color}"
            
            # Проверяем, можно ли купить
            if new_pos not in game.get("properties", {}):
                if current_player.get("balance", 1500) >= price:
                    message_text += f"\n\n❓ <b>Свободная недвижимость!</b>\n"
                    message_text += f"Хотите купить за {price}$? (Ответьте 'купить' или 'пропустить')"
        elif new_pos == 0:
            # СТАРТ
            current_player["balance"] = current_player.get("balance", 1500) + 200
            message_text += f"\n\n🏁 <b>СТАРТ</b>\n💰 +200$\n💵 Баланс: {current_player['balance']}$"
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx]
        
        message_text += f"\n\n➡️ <b>Следующий: {next_player['name']}</b>"
        
        await message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в roll_dice_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "🏠 Построить")
async def build_button(message: types.Message):
    """Кнопка строительства"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Находим недвижимость игрока
        player_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id and prop_id in BOARD:
                player_properties.append(prop_id)
        
        if not player_properties:
            await message.answer(
                "❌ <b>У вас нет недвижимости для строительства!</b>\n\n"
                "Сначала купите недвижимость, бросая кубик.",
                parse_mode="HTML"
            )
            return
        
        # Создаем клавиатуру для строительства
        kb = InlineKeyboardBuilder()
        for prop_id in player_properties[:5]:  # Ограничиваем 5
            prop_name = BOARD[prop_id][0]
            houses = game["properties"][prop_id].get("houses", 0)
            
            if houses < 4:
                kb.button(text=f"🏠 {prop_name} (+1 дом)", callback_data=f"build_{prop_id}_house")
            elif houses == 4:
                kb.button(text=f"🏨 {prop_name} (отель)", callback_data=f"build_{prop_id}_hotel")
        
        kb.button(text="❌ Отмена", callback_data="build_cancel")
        kb.adjust(1)
        
        await message.answer(
            "🏗️ <b>Строительство домов и отелей</b>\n\n"
            "Выберите недвижимость для улучшения:\n"
            "🏠 Дом (+50% к аренде за каждый)\n"
            "🏨 Отель (требуется 4 дома)\n\n"
            "💰 Стоимость строительства: 50% от цены недвижимости",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в build_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(F.text == "🤝 Торговля")
async def trade_button(message: types.Message):
    """Кнопка торговли"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        if len(game.get("players", [])) < 2:
            await message.answer(
                "❌ <b>Недостаточно игроков для торговли!</b>\n\n"
                "Нужно минимум 2 игрока в игре",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            "🤝 <b>Система торговли временно отключена</b>\n\n"
            "👑 <i>Темный Принц работает над улучшением этой функции...</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в trade_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.callback_query(F.data == "show_rules")
async def show_rules(c: types.CallbackQuery):
    """Показать правила"""
    try:
        rules_text = (
            "📖 <b>Правила Monopoly Premium:</b>\n\n"
            "1. 🏁 Каждый игрок начинает с <b>1500$</b>\n"
            "2. 🎲 По очереди бросайте кубик (2 кубика)\n"
            "3. 🏠 При попадании на свободную клетку можете её купить\n"
            "4. 💰 При попадании на чужую клетку платите аренду\n"
            "5. 🎨 Собирайте наборы одного цвета\n"
            "6. 🏘️ Стройте дома (до 4) и отели\n"
            "7. 🏦 Цель - остаться последним непобанкротившимся\n\n"
            "👑 <b>Версия Темного Принца</b>\n"
            "• Улучшенный интерфейс\n"
            "• Inline меню при скрытии\n"
            "• Web-статистика\n"
            "• Premium качество"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад", callback_data="back_to_main")
        kb.adjust(1)
        
        await c.message.answer(rules_text, parse_mode="HTML", reply_markup=kb.as_markup())
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_rules: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "show_developer")
async def show_developer(c: types.CallbackQuery):
    """Показать информацию о разработчике"""
    try:
        dev_text = (
            "👨‍💻 <b>О разработчике:</b>\n\n"
            f"<b>Разработчик:</b> {DEV_TAG}\n"
            "<b>Титул:</b> Темный Принц (Dark Prince)\n"
            "<b>Версия:</b> Premium v2.5\n\n"
            "👑 <b>Особенности версии:</b>\n"
            "• Разные меню для ЛС и групп\n"
            "• Inline меню при скрытии\n"
            "• Защищенная веб-панель\n"
            "• Полная игровая логика\n\n"
            f"⭐ Отзывы и предложения: {DEV_TAG}"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад", callback_data="back_to_main")
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
        
        # Определяем тип чата
        is_group = c.message.chat.type in ["group", "supergroup"]
        
        header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
        header += "🎮 <b>Выберите действие:</b>" if is_group else "👋 <b>Добро пожаловать!</b>"
        
        await c.message.answer(
            header,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=is_group)
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ЗАВЕРШЕНИЕ ====================
if __name__ == "__main__":
    main()