"""
Monopoly Premium Bot - Telegram бот (Часть 1)
👑 Создано Темным Принцем (Dark Prince) 👑
Полностью обновленный код со всеми исправлениями
"""

import os
import asyncio
import logging
import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# ==================== НАСТРОЙКИ ====================
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    logging.error("❌ BOT_TOKEN не найден!")
    exit(1)

PORT = int(os.environ.get("PORT", 8083))
DEV_TAG = "@Whylovely05"
MAINTENANCE_MSG = "Бот обновляется, Темный принц уже исправляет это ♥️♥️"
BANNER = "┏━━━━━━━━━━━━━━━━━━┓\n┃  Monopoly Premium  ┃\n┗━━━━━━━━━━━━━━━━━━┛"

# Список разрешенных пользователей для админки
ALLOWED_ADMINS = ["Whylovely05"]  # Твои username
ADMIN_PASSWORD_HASH = hashlib.sha256("darkprince".encode()).hexdigest()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
WAITING_GAMES: Dict[int, Dict] = {}  # {chat_id: {data, timer_task, pinned_message_id}}
ACTIVE_GAMES: Dict[int, Dict] = {}
HIDDEN_MENU_USERS: Dict[int, int] = {}  # {user_id: chat_id} - кто скрыл меню
USER_STATS: Dict[int, Dict] = {}  # Статистика пользователей
STATS = {"maintenance_mode": False}

# ==================== КАРТА МОНОПОЛИИ ====================
BOARD = {
    0: ["СТАРТ", 0, 0, "SPECIAL"],
    1: ["Житная", 60, 4, "BROWN"], 
    2: ["Общественная казна", 0, 0, "CHANCE"], 
    3: ["Нагатинская", 60, 4, "BROWN"], 
    4: ["Налог на роскошь", -200, 0, "TAX"],
    5: ["Рижская ж/д", 200, 25, "RAIL"], 
    6: ["Варшавское ш.", 100, 6, "BLUE"],
    7: ["Шанс", 0, 0, "CHANCE"], 
    8: ["Огородный пр.", 100, 6, "BLUE"],
    9: ["Рижская", 120, 8, "BLUE"], 
    10: ["Тюрьма (посещение)", 0, 0, "JAIL"],
    11: ["Курская", 140, 10, "PINK"], 
    12: ["Электросеть", 150, 10, "UTIL"],
    13: ["Абрамцево", 140, 10, "PINK"], 
    14: ["Пантелеевская", 160, 12, "PINK"],
    15: ["Казанская ж/д", 200, 25, "RAIL"], 
    16: ["Вавилова", 180, 14, "ORANGE"],
    17: ["Общественная казна", 0, 0, "CHEST"], 
    18: ["Тимирязевская", 180, 14, "ORANGE"],
    19: ["Лихоборы", 200, 16, "ORANGE"], 
    20: ["Бесплатная стоянка", 0, 0, "PARKING"],
    21: ["Арбат", 220, 18, "RED"], 
    22: ["Шанс", 0, 0, "CHANCE"],
    23: ["Полянка", 220, 18, "RED"], 
    24: ["Сретенка", 240, 20, "RED"],
    25: ["Курская ж/д", 200, 25, "RAIL"], 
    26: ["Ростовская", 260, 22, "YELLOW"],
    27: ["Рязанский пр.", 260, 22, "YELLOW"],  # Исправлено: было 2, стало 27
    28: ["Водопровод", 150, 10, "UTIL"],
    29: ["Новинский б-р", 280, 24, "YELLOW"], 
    30: ["Отправляйтесь в тюрьму", 0, 0, "GO_TO_JAIL"],
    31: ["Пушкинская", 300, 26, "GREEN"], 
    32: ["Тверская", 300, 26, "GREEN"],
    33: ["Общественная казна", 0, 0, "CHEST"], 
    34: ["Маяковского", 320, 28, "GREEN"],
    35: ["Ленинградская ж/д", 200, 25, "RAIL"], 
    36: ["Шанс", 0, 0, "CHANCE"],
    37: ["Кутузовский", 350, 35, "DARKBLUE"], 
    38: ["Налог на сверхприбыль", -100, 0, "TAX"],
    39: ["Бродвей", 400, 50, "DARKBLUE"]
}

# Карточки шанса
CHANCE_CARDS = [
    "🎲 Продвиньтесь к СТАРТУ и получите 200$",
    "🏦 Банковская ошибка в вашу пользу. Получите 150$",
    "📈 Ваши акции выросли. Получите 100$",
    "🎯 Вы выиграли конкурс. Получите 50$",
    "🏆 Приз за красоту. Получите 25$",
    "💰 Вас оштрафовали за превышение скорости. Заплатите 50$",
    "🏥 Оплатите лечение. Заплатите 100$",
    "🎭 Оплатите обучение. Заплатите 150$",
    "🏛️ Идите в тюрьму. Не проходите СТАРТ, не получайте 200$",
    "🔄 Идите назад на 3 клетки"
]

# Карточки общественной казны
CHEST_CARDS = [
    "🎁 Вторая премия за конкурс. Получите 25$",
    "💼 Оплата страховки. Получите 100$",
    "💸 Налог на наследство. Заплатите 100$",
    "🏅 Вы заняли второе место. Получите 25$",
    "💳 Оплата больничных. Получите 100$",
    "📚 Оплата обучения. Заплатите 150$",
    "🎫 Сбор на уличное освещение. Заплатите 50$",
    "🌲 Оплата за посаженное дерево. Получите 25$"
]

# Цветовые группы
COLOR_GROUPS = {
    "BROWN": [1, 3],
    "BLUE": [6, 8, 9],
    "PINK": [11, 13, 14],
    "ORANGE": [16, 18, 19],
    "RED": [21, 23, 24],
    "YELLOW": [26, 27, 29],
    "GREEN": [31, 32, 34],
    "DARKBLUE": [37, 39],
    "RAIL": [5, 15, 25, 35],
    "UTIL": [12, 28]
}

# Стоимость строительства
BUILDING_COSTS = {
    "BROWN": {"house": 50, "hotel": 50},
    "BLUE": {"house": 50, "hotel": 50},
    "PINK": {"house": 100, "hotel": 100},
    "ORANGE": {"house": 100, "hotel": 100},
    "RED": {"house": 150, "hotel": 150},
    "YELLOW": {"house": 150, "hotel": 150},
    "GREEN": {"house": 200, "hotel": 200},
    "DARKBLUE": {"house": 200, "hotel": 200}
}

# ==================== ФУНКЦИИ ВСПОМОГАТЕЛЬНЫЕ ====================
def load_user_stats():
    """Загрузить статистику пользователей"""
    global USER_STATS
    try:
        with open("user_stats.json", "r", encoding="utf-8") as f:
            USER_STATS = json.load(f)
    except:
        USER_STATS = {}

def save_user_stats():
    """Сохранить статистику пользователей"""
    try:
        with open("user_stats.json", "w", encoding="utf-8") as f:
            json.dump(USER_STATS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

def update_user_stats(user_id: int, username: str, name: str, win: bool = False):
    """Обновить статистику пользователя"""
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {
            "username": username,
            "name": name,
            "games_played": 0,
            "games_won": 0,
            "total_money": 0,
            "properties_bought": 0,
            "last_played": datetime.now().isoformat()
        }
    
    stats = USER_STATS[user_id]
    stats["games_played"] += 1
    if win:
        stats["games_won"] += 1
    stats["last_played"] = datetime.now().isoformat()
    save_user_stats()

def get_top_players(limit: int = 10) -> List[Dict]:
    """Получить топ игроков"""
    players = []
    for user_id, stats in USER_STATS.items():
        if stats["games_played"] > 0:
            win_rate = (stats["games_won"] / stats["games_played"]) * 100
            players.append({
                "user_id": user_id,
                "name": stats["name"],
                "username": stats.get("username", ""),
                "games_played": stats["games_played"],
                "games_won": stats["games_won"],
                "win_rate": win_rate
            })
    
    # Сортировка по победам, затем по количеству игр
    players.sort(key=lambda x: (x["games_won"], x["games_played"]), reverse=True)
    return players[:limit]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_kb(is_group: bool = False) -> types.InlineKeyboardMarkup:
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
    kb.button(text="🏆 Рейтинг игроков", callback_data="show_leaderboard")
    kb.button(text="👨‍💻 О девелопере", callback_data="show_developer")
    
    # Статус системы (только для админов)
    if is_group:
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
        web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
        kb.button(text="🌐 Статус системы", url=f"{web_url}?password=darkprince")
    
    kb.adjust(1)
    return kb.as_markup()

def waiting_room_kb(chat_id: int, user_id: int = None) -> types.InlineKeyboardMarkup:
    """Лобби ожидания - динамическая клавиатура"""
    kb = InlineKeyboardBuilder()
    
    # Основные кнопки для всех
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    
    # Проверяем, есть ли игра и является ли пользователь создателем
    if chat_id in WAITING_GAMES and user_id:
        game = WAITING_GAMES[chat_id]
        if user_id == game.get("creator_id"):
            # Только создатель видит эти кнопки
            kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
            kb.button(text="❌ Отменить сбор", callback_data=f"cancel_gathering_{chat_id}")
            kb.adjust(2, 2)
            return kb.as_markup()
    
    # Обычная клавиатура
    kb.adjust(2)
    return kb.as_markup()

def game_main_kb() -> types.ReplyKeyboardMarkup:
    """Основная игровая клавиатура"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить")
    kb.button(text="📊 Мои активы")
    kb.button(text="🤝 Торговля")
    kb.button(text="💵 Заложить улицу")
    kb.button(text="🗺️ Показать карту")
    kb.button(text="❌ Скрыть меню")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def inline_menu_kb() -> types.InlineKeyboardMarkup:
    """Inline меню для тех кто скрыл основное"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик", callback_data="inline_roll_dice")
    kb.button(text="🏠 Построить", callback_data="inline_build")
    kb.button(text="📊 Мои активы", callback_data="inline_assets")
    kb.button(text="🤝 Торговля", callback_data="inline_trade")
    kb.button(text="💵 Заложить улицу", callback_data="inline_mortgage")
    kb.button(text="🗺️ Показать карту", callback_data="inline_map")
    kb.button(text="📱 Вернуть меню", callback_data="restore_menu")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

def build_property_kb(property_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура для строительства на собственности"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Построить дом (+1)", callback_data=f"build_house_{property_id}")
    kb.button(text="🏨 Построить отель", callback_data=f"build_hotel_{property_id}")
    kb.button(text="🔨 Продать дом (-1)", callback_data=f"sell_house_{property_id}")
    kb.button(text="💵 Заложить", callback_data=f"mortgage_{property_id}")
    kb.button(text="❌ Отмена", callback_data="cancel_build")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

def trade_kb(player_id: int, target_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура для торговли"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Предложить деньги", callback_data=f"offer_money_{player_id}_{target_id}")
    kb.button(text="🏠 Предложить недвижимость", callback_data=f"offer_property_{player_id}_{target_id}")
    kb.button(text="💼 Смешанное предложение", callback_data=f"offer_mixed_{player_id}_{target_id}")
    kb.button(text="❌ Отменить сделку", callback_data="cancel_trade")
    kb.adjust(2, 2)
    return kb.as_markup()

# ==================== АНИМАЦИЯ КУБИКОВ ====================
def get_dice_emoji(value: int) -> str:
    """Получить эмодзи для кубика"""
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    return dice_emojis[value - 1]

async def send_dice_animation(chat_id: int, user_name: str) -> Tuple[int, int]:
    """Отправить анимацию броска кубиков"""
    # Имитация анимации - отправляем несколько сообщений
    messages = []
    
    # Первое сообщение - начало броска
    msg1 = await bot.send_message(
        chat_id,
        f"🎲 *{user_name} бросает кубики...*\n"
        f"⚀ ⚁ ⚂ ⚃ ⚄ ⚅",
        parse_mode="Markdown"
    )
    messages.append(msg1.message_id)
    await asyncio.sleep(0.5)
    
    # Второе сообщение - кубики крутятся
    msg2 = await bot.send_message(
        chat_id,
        f"🎲 *Кубики крутятся...*\n"
        f"🎯 🎯",
        parse_mode="Markdown"
    )
    messages.append(msg2.message_id)
    await asyncio.sleep(0.5)
    
    # Генерируем результат
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    
    # Третье сообщение - результат
    msg3 = await bot.send_message(
        chat_id,
        f"🎲 *Результат броска {user_name}:*\n"
        f"{get_dice_emoji(dice1)} Кубик 1: **{dice1}**\n"
        f"{get_dice_emoji(dice2)} Кубик 2: **{dice2}**\n"
        f"📊 Сумма: **{dice1 + dice2}**",
        parse_mode="Markdown"
    )
    messages.append(msg3.message_id)
    
    # Удаляем предыдущие сообщения через 2 секунды
    await asyncio.sleep(2)
    try:
        await bot.delete_message(chat_id, msg1.message_id)
        await bot.delete_message(chat_id, msg2.message_id)
    except:
        pass
    
    return dice1, dice2

# ==================== КАРТА МОНОПОЛИИ ====================
def generate_map_url(game_id: int, players: List[Dict]) -> str:
    """Генерировать URL для интерактивной карты"""
    # Базовая реализация - можно заменить на реальную генерацию карты
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
    web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
    
    # Формируем данные для карты
    players_data = []
    for player in players:
        players_data.append({
            "id": player["id"],
            "name": player["name"],
            "position": player.get("position", 0),
            "color": player.get("color", "#3498db")
        })
    
    return f"{web_url}/map/{game_id}?players={json.dumps(players_data)}"

def create_simple_map(game: Dict) -> str:
    """Создать простую текстовую карту"""
    players = game.get("players", [])
    properties = game.get("properties", {})
    
    map_text = "🗺️ *Карта игры:*\n\n"
    
    # Создаем простую схему
    for pos in range(40):
        cell_info = BOARD.get(pos, ["", 0, 0, ""])
        cell_name = cell_info[0]
        
        # Определяем кто на клетке
        players_here = []
        for player in players:
            if player.get("position") == pos:
                players_here.append(player["name"][:1])  # Первая буква имени
        
        # Определяем владельца
        owner_symbol = " "
        if pos in properties:
            owner = properties[pos].get("owner")
            if owner:
                for player in players:
                    if player["id"] == owner:
                        owner_symbol = player["name"][:1]
                        break
        
        # Формируем строку
        if players_here:
            map_text += f"[{pos:2d}] {cell_name[:10]:10} 👤{''.join(players_here)}"
        else:
            map_text += f"[{pos:2d}] {cell_name[:10]:10}"
        
        if owner_symbol != " ":
            map_text += f" 🏠{owner_symbol}"
        
        # Специальные клетки
        if cell_info[3] == "JAIL":
            map_text += " ⛓️"
        elif cell_info[3] == "GO_TO_JAIL":
            map_text += " 🚓"
        elif cell_info[3] == "CHANCE":
            map_text += " 🎲"
        elif cell_info[3] == "CHEST":
            map_text += " 💰"
        
        map_text += "\n"
    
    return map_text

# ==================== МЕХАНИКА ТЮРЬМЫ ====================
def handle_jail_mechanic(player: Dict, game: Dict) -> str:
    """Обработка механики тюрьмы"""
    result = ""
    
    if player.get("in_jail", False):
        jail_turns = player.get("jail_turns", 0)
        
        if jail_turns >= 3:
            # Автоматический выход из тюрьмы после 3 ходов
            player["in_jail"] = False
            player["jail_turns"] = 0
            fine = 50
            player["balance"] = player.get("balance", 1500) - fine
            result = f"⛓️ Вы вышли из тюрьмы после 3 ходов. Штраф: {fine}$\n"
        else:
            player["jail_turns"] = jail_turns + 1
            result = f"⛓️ Вы в тюрьме. Ход {jail_turns + 1}/3\n"
    
    return result

# ==================== МЕХАНИКА ЗАЛОГА ====================
def can_mortgage(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок заложить недвижимость"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    if prop.get("owner") != player_id:
        return False
    
    # Нельзя заложить, если есть постройки
    if prop.get("houses", 0) > 0 or prop.get("hotel", False):
        return False
    
    # Нельзя заложить, если уже заложено
    if prop.get("mortgaged", False):
        return False
    
    return True

def mortgage_property(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Заложить недвижимость"""
    if not can_mortgage(property_id, game, player_id):
        return False, "Невозможно заложить эту недвижимость", 0
    
    prop = game["properties"][property_id]
    mortgage_value = BOARD[property_id][1] // 2  # 50% от стоимости
    
    # Закладываем
    prop["mortgaged"] = True
    
    # Даем деньги игроку
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) + mortgage_value
            break
    
    return True, f"Недвижимость заложена! Вы получили {mortgage_value}$", mortgage_value

def can_unmortgage(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок выкупить недвижимость"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    if prop.get("owner") != player_id:
        return False
    
    # Должна быть заложена
    if not prop.get("mortgaged", False):
        return False
    
    # Проверяем достаточно ли денег (110% от залоговой стоимости)
    unmortgage_cost = int(BOARD[property_id][1] // 2 * 1.1)
    
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) >= unmortgage_cost:
                return True
    
    return False

def unmortgage_property(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Выкупить недвижимость из залога"""
    if not can_unmortgage(property_id, game, player_id):
        return False, "Невозможно выкупить эту недвижимость", 0
    
    prop = game["properties"][property_id]
    unmortgage_cost = int(BOARD[property_id][1] // 2 * 1.1)  # 110% от залоговой стоимости
    
    # Выкупаем
    prop["mortgaged"] = False
    
    # Забираем деньги у игрока
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - unmortgage_cost
            break
    
    return True, f"Недвижимость выкуплена из залога за {unmortgage_cost}$", unmortgage_cost

# ==================== ФУНКЦИИ ДЛЯ ТАЙМЕРОВ ====================
async def start_waiting_timer(chat_id: int, game_data: Dict):
    """Запустить таймер ожидания на 3 минуты"""
    async def check_timer():
        await asyncio.sleep(180)  # 3 минуты
        
        if chat_id not in WAITING_GAMES:
            return
            
        game = WAITING_GAMES[chat_id]
        if not game:
            return
            
        player_count = len(game.get("players", []))
        
        # Если 2 или больше игроков - начинаем игру автоматически
        if player_count >= 2:
            await auto_start_game(chat_id, game)
        else:
            # Если меньше 2 игроков - отменяем сбор
            await cancel_gathering_by_timer(chat_id, game)
    
    # Запускаем таймер
    timer_task = asyncio.create_task(check_timer())
    game_data["timer_task"] = timer_task

async def auto_start_game(chat_id: int, game: Dict):
    """Автоматически начать игру после таймера"""
    try:
        # Переносим игру в активные
        ACTIVE_GAMES[chat_id] = {
            "players": game["players"],
            "current_player": 0,
            "started_at": datetime.now(),
            "creator_id": game["creator_id"],
            "properties": {},
            "turn": 1,
            "chance_deck": CHANCE_CARDS.copy(),
            "chest_deck": CHEST_CARDS.copy()
        }
        
        # Перемешиваем колоды
        random.shuffle(ACTIVE_GAMES[chat_id]["chance_deck"])
        random.shuffle(ACTIVE_GAMES[chat_id]["chest_deck"])
        
        # Инициализируем игроков
        colors = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠"]
        for idx, player in enumerate(ACTIVE_GAMES[chat_id]["players"]):
            player["balance"] = 1500
            player["position"] = 0
            player["properties"] = []
            player["in_jail"] = False
            player["jail_turns"] = 0
            player["color"] = colors[idx % len(colors)]
            player["get_out_of_jail_free"] = 0
        
        # Удаляем из ожидающих
        if chat_id in WAITING_GAMES:
            game_data = WAITING_GAMES.pop(chat_id)
            # Отменяем таймер
            if "timer_task" in game_data:
                game_data["timer_task"].cancel()
        
        # УДАЛЯЕМ СООБЩЕНИЕ О СБОРЕ
        if "message_id" in game:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=game["message_id"])
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
        
        # Открепляем сообщение о сборе
        if "pinned_message_id" in game:
            try:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=game["pinned_message_id"])
            except:
                pass
        
        # Формируем список игроков
        players_list = "\n".join([f"• {p['name']}" for p in ACTIVE_GAMES[chat_id]["players"]])
        
        # Отправляем сообщение о начале игры
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎉 <b>Игра началась автоматически!</b>\n\n"
                 f"<b>Участники:</b>\n{players_list}\n\n"
                 f"⏰ <i>3 минуты ожидания истекли</i>\n"
                 f"💰 Стартовый баланс: <b>1500$</b>\n"
                 f"🎲 Первым ходит: <b>{ACTIVE_GAMES[chat_id]['players'][0]['name']}</b>\n"
                 f"🔄 Ход: <b>1</b>",
            parse_mode="HTML"
        )
        
        # Отправляем игровое меню
        first_player = ACTIVE_GAMES[chat_id]["players"][0]
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎮 <b>Игра началась!</b>\n\n"
                 f"📢 <b>{first_player['name']}</b>, ваш ход первый!\n"
                 f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в auto_start_game: {e}")

async def cancel_gathering_by_timer(chat_id: int, game: Dict):
    """Отменить сбор по истечении таймера"""
    try:
        if chat_id in WAITING_GAMES:
            game_data = WAITING_GAMES.pop(chat_id)
            
            # Отменяем таймер
            if "timer_task" in game_data:
                game_data["timer_task"].cancel()
            
            # Открепляем сообщение
            if "pinned_message_id" in game_data:
                try:
                    await bot.unpin_chat_message(chat_id=chat_id, message_id=game_data["pinned_message_id"])
                except:
                    pass
            
            # Удаляем сообщение
            if "message_id" in game_data:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=game_data["message_id"])
                except:
                    pass
            
            # Отправляем сообщение об отмене
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ <b>Сбор игроков отменен!</b>\n\n"
                     f"⏰ <i>3 минуты ожидания истекли</i>\n"
                     f"👥 <b>Не удалось собрать достаточное количество игроков</b>\n"
                     f"Минимум требуется: 2 игрока\n"
                     f"Собрано: {len(game.get('players', []))} игрока(ов)",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в cancel_gathering_by_timer: {e}")

# ==================== ОБРАБОТКА КАРТОЧЕК ====================
def draw_chance_card(game: Dict) -> Tuple[str, Dict]:
    """Вытащить карточку шанса"""
    if not game["chance_deck"]:
        game["chance_deck"] = CHANCE_CARDS.copy()
        random.shuffle(game["chance_deck"])
    
    card = game["chance_deck"].pop(0)
    effect = {"money": 0, "move": 0, "jail": False}
    
    # Обработка карточки
    if "Получите" in card and "$" in card:
        # Извлекаем сумму
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = int(match.group(1))
    elif "Заплатите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = -int(match.group(1))
    elif "Продвиньтесь к СТАРТУ" in card:
        effect["move"] = "start"
    elif "Идите в тюрьму" in card:
        effect["jail"] = True
    elif "Идите назад на 3 клетки" in card:
        effect["move"] = -3
    
    return card, effect

def draw_chest_card(game: Dict) -> Tuple[str, Dict]:
    """Вытащить карточку общественной казны"""
    if not game["chest_deck"]:
        game["chest_deck"] = CHEST_CARDS.copy()
        random.shuffle(game["chest_deck"])
    
    card = game["chest_deck"].pop(0)
    effect = {"money": 0}
    
    # Обработка карточки
    if "Получите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = int(match.group(1))
    elif "Заплатите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = -int(match.group(1))
    
    return card, effect

# ==================== ПОКУПКА И СТРОИТЕЛЬСТВО ====================
def can_build_house(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок построить дом"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что недвижимость не заложена
    if prop.get("mortgaged", False):
        return False
    
    # Получаем цвет группы
    color = BOARD[property_id][3]
    if color not in COLOR_GROUPS:
        return False
    
    # Проверяем, что у игрока есть все улицы этого цвета
    color_properties = COLOR_GROUPS[color]
    for prop_id in color_properties:
        if prop_id not in game["properties"]:
            return False
        if game["properties"][prop_id].get("owner") != player_id:
            return False
    
    # Проверяем максимальное количество домов
    if prop.get("houses", 0) >= 4:
        return False
    
    # Проверяем баланс
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) < house_cost:
                return False
    
    return True

def build_house(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Построить дом"""
    if not can_build_house(property_id, game, player_id):
        return False, "Невозможно построить дом", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    
    # Строим дом
    prop["houses"] = prop.get("houses", 0) + 1
    
    # Обновляем аренду (увеличиваем на 50% за каждый дом)
    base_rent = BOARD[property_id][2]
    if prop["houses"] == 1:
        new_rent = base_rent * 2
    elif prop["houses"] == 2:
        new_rent = base_rent * 3
    elif prop["houses"] == 3:
        new_rent = base_rent * 4
    elif prop["houses"] == 4:
        new_rent = base_rent * 5
    else:
        new_rent = base_rent
    
    prop["current_rent"] = new_rent
    
    # Списание денег
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - house_cost
            break
    
    return True, f"Дом построен! Стоимость: {house_cost}$. Новая аренда: {new_rent}$", house_cost

def can_build_hotel(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок построить отель"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что есть 4 дома
    if prop.get("houses", 0) != 4:
        return False
    
    # Проверяем, что еще нет отеля
    if prop.get("hotel", False):
        return False
    
    # Получаем цвет группы
    color = BOARD[property_id][3]
    if color not in COLOR_GROUPS:
        return False
    
    # Проверяем баланс
    hotel_cost = BUILDING_COSTS.get(color, {}).get("hotel", 50)
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) < hotel_cost:
                return False
    
    return True

def build_hotel(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Построить отель"""
    if not can_build_hotel(property_id, game, player_id):
        return False, "Невозможно построить отель", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    hotel_cost = BUILDING_COSTS.get(color, {}).get("hotel", 50)
    
    # Строим отель
    prop["hotel"] = True
    prop["houses"] = 0  # Убираем дома
    
    # Обновляем аренду (увеличиваем в 6 раз)
    base_rent = BOARD[property_id][2]
    new_rent = base_rent * 6
    prop["current_rent"] = new_rent
    
    # Списание денег
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - hotel_cost
            break
    
    return True, f"Отель построен! Стоимость: {hotel_cost}$. Новая аренда: {new_rent}$", hotel_cost

def can_sell_house(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок продать дом"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что есть дома
    if prop.get("houses", 0) == 0:
        return False
    
    return True

def sell_house(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Продать дом"""
    if not can_sell_house(property_id, game, player_id):
        return False, "Невозможно продать дом", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    refund = house_cost // 2  # 50% от стоимости
    
    # Продаем дом
    prop["houses"] = prop.get("houses", 0) - 1
    
    # Обновляем аренду
    base_rent = BOARD[property_id][2]
    houses = prop["houses"]
    
    if houses == 0:
        new_rent = base_rent
    elif houses == 1:
        new_rent = base_rent * 2
    elif houses == 2:
        new_rent = base_rent * 3
    elif houses == 3:
        new_rent = base_rent * 4
    
    prop["current_rent"] = new_rent
    
    # Возвращаем деньги
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) + refund
            break
    
    return True, f"Дом продан! Вы получили {refund}$. Новая аренда: {new_rent}$", refund

# ==================== ТОРГОВЛЯ ====================
def create_trade_offer(from_player_id: int, to_player_id: int, 
                      money_offer: int = 0, properties_offer: List[int] = None,
                      money_request: int = 0, properties_request: List[int] = None) -> Dict:
    """Создать предложение обмена"""
    return {
        "from_player": from_player_id,
        "to_player": to_player_id,
        "money_offer": money_offer or 0,
        "properties_offer": properties_offer or [],
        "money_request": money_request or 0,
        "properties_request": properties_request or [],
        "created_at": datetime.now().isoformat(),
        "status": "pending"  # pending, accepted, rejected
    }

def validate_trade_offer(trade_offer: Dict, game: Dict) -> Tuple[bool, str]:
    """Проверить валидность предложения обмена"""
    from_player_id = trade_offer["from_player"]
    to_player_id = trade_offer["to_player"]
    
    # Находим игроков
    from_player = None
    to_player = None
    
    for player in game["players"]:
        if player["id"] == from_player_id:
            from_player = player
        if player["id"] == to_player_id:
            to_player = player
    
    if not from_player or not to_player:
        return False, "Игрок не найден"
    
    # Проверяем деньги у отправителя
    if from_player.get("balance", 0) < trade_offer["money_offer"]:
        return False, f"У {from_player['name']} недостаточно денег"
    
    # Проверяем деньги у получателя
    if to_player.get("balance", 0) < trade_offer["money_request"]:
        return False, f"У {to_player['name']} недостаточно денег"
    
    # Проверяем недвижимость у отправителя
    for prop_id in trade_offer["properties_offer"]:
        if prop_id not in game["properties"]:
            return False, f"Недвижимость {prop_id} не существует"
        
        prop = game["properties"][prop_id]
        if prop.get("owner") != from_player_id:
            return False, f"У {from_player['name']} нет недвижимости {BOARD[prop_id][0]}"
        
        # Проверяем, что недвижимость не заложена и без построек
        if prop.get("mortgaged", False):
            return False, f"Недвижимость {BOARD[prop_id][0]} заложена"
        
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            return False, f"На недвижимости {BOARD[prop_id][0]} есть постройки"
    
    # Проверяем недвижимость у получателя
    for prop_id in trade_offer["properties_request"]:
        if prop_id not in game["properties"]:
            return False, f"Недвижимость {prop_id} не существует"
        
        prop = game["properties"][prop_id]
        if prop.get("owner") != to_player_id:
            return False, f"У {to_player['name']} нет недвижимости {BOARD[prop_id][0]}"
        
        # Проверяем, что недвижимость не заложена и без построек
        if prop.get("mortgaged", False):
            return False, f"Недвижимость {BOARD[prop_id][0]} заложена"
        
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            return False, f"На недвижимости {BOARD[prop_id][0]} есть постройки"
    
    return True, "Предложение валидно"

def execute_trade(trade_offer: Dict, game: Dict) -> Tuple[bool, str]:
    """Выполнить обмен"""
    # Проверяем валидность
    valid, message = validate_trade_offer(trade_offer, game)
    if not valid:
        return False, message
    
    from_player_id = trade_offer["from_player"]
    to_player_id = trade_offer["to_player"]
    
    # Обмен деньгами
    for player in game["players"]:
        if player["id"] == from_player_id:
            player["balance"] -= trade_offer["money_offer"]
            player["balance"] += trade_offer["money_request"]
        
        if player["id"] == to_player_id:
            player["balance"] -= trade_offer["money_request"]
            player["balance"] += trade_offer["money_offer"]
    
    # Обмен недвижимостью
    for prop_id in trade_offer["properties_offer"]:
        game["properties"][prop_id]["owner"] = to_player_id
    
    for prop_id in trade_offer["properties_request"]:
        game["properties"][prop_id]["owner"] = from_player_id
    
    return True, "Обмен успешно выполнен"

# ==================== ОБРАБОТКА ХОДА ====================
async def process_player_turn(chat_id: int, game: Dict, player: Dict, dice_result: Tuple[int, int]) -> str:
    """Обработать ход игрока"""
    dice1, dice2 = dice_result
    total = dice1 + dice2
    
    result_text = f"🎲 <b>{player['name']} бросает кубики:</b>\n"
    result_text += f"🎯 {get_dice_emoji(dice1)} Кубик 1: <b>{dice1}</b>\n"
    result_text += f"🎯 {get_dice_emoji(dice2)} Кубик 2: <b>{dice2}</b>\n"
    result_text += f"📊 Сумма: <b>{total}</b>\n"
    
    # Обработка тюрьмы
    jail_result = handle_jail_mechanic(player, game)
    if jail_result and "Вы в тюрьме" in jail_result:
        result_text += f"\n{jail_result}"
        return result_text
    
    # Если игрок в тюрьме, но может выйти
    if player.get("in_jail", False):
        if dice1 == dice2:  # Дубль - выход из тюрьмы
            player["in_jail"] = False
            player["jail_turns"] = 0
            result_text += f"\n🎉 Вы вышли из тюрьмы с дублем!\n"
        else:
            result_text += f"\n{jail_result}"
            return result_text
    
    # Обновляем позицию
    current_pos = player.get("position", 0)
    new_pos = (current_pos + total) % 40
    player["position"] = new_pos
    
    result_text += f"📍 Позиция: {current_pos} → <b>{new_pos}</b>\n"
    
    # Обработка клетки
    if new_pos in BOARD:
        cell_name, price, rent, cell_type = BOARD[new_pos]
        result_text += f"\n🏠 <b>{cell_name}</b>\n"
        
        if cell_type in ["SPECIAL", "TAX", "JAIL", "PARKING", "GO_TO_JAIL", "CHANCE", "CHEST"]:
            result_text += await handle_special_cell(chat_id, game, player, new_pos, cell_type)
        elif cell_type in ["BROWN", "BLUE", "PINK", "ORANGE", "RED", "YELLOW", "GREEN", "DARKBLUE", "RAIL", "UTIL"]:
            result_text += await handle_property_cell(game, player, new_pos, cell_name, price, rent, cell_type)
    
    return result_text

async def handle_special_cell(chat_id: int, game: Dict, player: Dict, position: int, cell_type: str) -> str:
    """Обработка специальных клеток"""
    result = ""
    
    if cell_type == "START":
        # СТАРТ
        player["balance"] = player.get("balance", 1500) + 200
        result += f"🏁 <b>СТАРТ!</b> +200$\n💵 Баланс: {player['balance']}$\n"
    
    elif cell_type == "TAX":
        # Налог
        tax_amount = BOARD[position][1]
        player["balance"] = player.get("balance", 1500) + tax_amount  # tax_amount отрицательный
        result += f"💸 <b>Налог!</b> {tax_amount}$\n💵 Баланс: {player['balance']}$\n"
    
    elif cell_type == "GO_TO_JAIL":
        # Отправка в тюрьму
        player["in_jail"] = True
        player["position"] = 10  # Тюрьма
        player["jail_turns"] = 0
        result += f"🚓 <b>Отправляйтесь в тюрьму!</b>\n"
    
    elif cell_type == "CHANCE":
        # Шанс
        card, effect = draw_chance_card(game)
        result += f"🎲 <b>Шанс:</b> {card}\n"
        
        # Применяем эффект
        if effect["money"] != 0:
            player["balance"] = player.get("balance", 1500) + effect["money"]
            result += f"💵 Изменение баланса: {effect['money']}$\n"
        
        if effect["move"] != 0:
            if effect["move"] == "start":
                player["position"] = 0
                player["balance"] = player.get("balance", 1500) + 200
                result += f"📍 Перемещение к СТАРТУ +200$\n"
            else:
                new_pos = (player["position"] + effect["move"]) % 40
                player["position"] = new_pos
                result += f"📍 Перемещение на {effect['move']} клеток\n"
                # Обрабатываем новую клетку
                if new_pos in BOARD:
                    cell_name = BOARD[new_pos][0]
                    result += f"🏠 Новая клетка: <b>{cell_name}</b>\n"
        
        if effect["jail"]:
            player["in_jail"] = True
            player["position"] = 10
            player["jail_turns"] = 0
            result += f"🚓 Отправка в тюрьму!\n"
    
    elif cell_type == "CHEST":
        # Общественная казна
        card, effect = draw_chest_card(game)
        result += f"💰 <b>Общественная казна:</b> {card}\n"
        
        if effect["money"] != 0:
            player["balance"] = player.get("balance", 1500) + effect["money"]
            result += f"💵 Изменение баланса: {effect['money']}$\n"
    
    elif cell_type == "PARKING":
        # Бесплатная стоянка
        result += f"🅿️ <b>Бесплатная стоянка</b>\nОтдыхайте!\n"
    
    return result

async def handle_property_cell(game: Dict, player: Dict, position: int, 
                              cell_name: str, price: int, rent: int, cell_type: str) -> str:
    """Обработка клеток с недвижимостью"""
    result = ""
    
    if position not in game.get("properties", {}):
        # Свободная недвижимость
        if player.get("balance", 1500) >= price:
            result += f"💰 Цена: {price}$\n🎨 Тип: {cell_type}\n"
            result += f"❓ <b>Свободная недвижимость!</b>\n"
            result += f"Хотите купить {cell_name} за {price}$?\n"
            result += f"Напишите 'купить {position}' или 'пропустить'"
        else:
            result += f"💰 Цена: {price}$ (недостаточно денег)\n"
    else:
        # Недвижимость с владельцем
        prop = game["properties"][position]
        owner_id = prop.get("owner")
        
        if owner_id == player["id"]:
            result += f"✅ <b>Ваша собственность</b>\n"
            
            # Показываем информацию о постройках
            houses = prop.get("houses", 0)
            hotel = prop.get("hotel", False)
            mortgaged = prop.get("mortgaged", False)
            
            if mortgaged:
                result += f"⚠️ <b>Заложена</b>\n"
            elif hotel:
                result += f"🏨 <b>Отель</b>\n"
                result += f"💰 Аренда: {prop.get('current_rent', rent)}$\n"
            elif houses > 0:
                result += f"🏠 <b>Дома: {houses}/4</b>\n"
                result += f"💰 Аренда: {prop.get('current_rent', rent)}$\n"
            else:
                result += f"💰 Базовая аренда: {rent}$\n"
        else:
            # Находим владельца
            owner_name = ""
            for p in game["players"]:
                if p["id"] == owner_id:
                    owner_name = p["name"]
                    break
            
            result += f"👤 Владелец: <b>{owner_name}</b>\n"
            
            # Проверяем залог
            if prop.get("mortgaged", False):
                result += f"⚠️ <b>Недвижимость заложена</b>\n"
                result += f"💰 Аренда не взимается\n"
            else:
                # Расчет аренды
                current_rent = prop.get("current_rent", rent)
                
                # Особые случаи
                if cell_type == "RAIL":
                    # Железные дороги: 25$ за первую, 50$ за вторую, 100$ за третью, 200$ за четвертую
                    rail_count = 0
                    for prop_id in COLOR_GROUPS["RAIL"]:
                        if prop_id in game["properties"]:
                            if game["properties"][prop_id].get("owner") == owner_id:
                                rail_count += 1
                    
                    if rail_count == 1:
                        current_rent = 25
                    elif rail_count == 2:
                        current_rent = 50
                    elif rail_count == 3:
                        current_rent = 100
                    elif rail_count == 4:
                        current_rent = 200
                
                elif cell_type == "UTIL":
                    # Коммунальные услуги: 4x если одна, 10x если две
                    util_count = 0
                    for prop_id in COLOR_GROUPS["UTIL"]:
                        if prop_id in game["properties"]:
                            if game["properties"][prop_id].get("owner") == owner_id:
                                util_count += 1
                    
                    dice1, dice2 = 0, 0  # Временные значения для расчета
                    if util_count == 1:
                        current_rent = (dice1 + dice2) * 4
                    elif util_count == 2:
                        current_rent = (dice1 + dice2) * 10
                
                # Списание аренды
                player["balance"] = player.get("balance", 1500) - current_rent
                
                # Добавление аренды владельцу
                for p in game["players"]:
                    if p["id"] == owner_id:
                        p["balance"] = p.get("balance", 1500) + current_rent
                        break
                
                result += f"💸 <b>Аренда: {current_rent}$</b>\n"
                result += f"💰 Ваш баланс: {player['balance']}$\n"
    
    return result

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ"""
    try:
        # Проверяем тип чата - отвечаем ТОЛЬКО в ЛС
        if message.chat.type not in ["private"]:
            await message.answer(
                "👋 Для управления игрой используйте команду /monopoly в этой группе",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
            f"✨ Premium Edition v3.0\n\n"
            f"Разработчик: {DEV_TAG}",
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=False)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.message(Command("monopoly"))
async def cmd_monopoly(message: types.Message):
    """Главная команда - ТОЛЬКО в группах"""
    try:
        # ПЕРВОЕ ДЕЛО - проверяем режим обслуживания
        if STATS.get("maintenance_mode", False):
            await message.answer(
                f"⚠️ {MAINTENANCE_MSG}\n\n"
                f"👑 Темный Принц уже исправляет это ♥️♥️",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем тип чата - отвечаем ТОЛЬКО в группах
        if message.chat.type not in ["group", "supergroup"]:
            await message.answer(
                "👋 <b>Эту команду можно использовать только в группах!</b>\n\n"
                f"Добавьте бота в группу и используйте /monopoly там.\n"
                f"Разработчик: {DEV_TAG}",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем, скрыл ли пользователь меню
        user_id = message.from_user.id
        if user_id in HIDDEN_MENU_USERS:
            # Пользователь скрыл меню - показываем inline версию
            await show_inline_menu(message)
            return
        
        header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition v3.0</b>\n👑 Версия Темного Принца\n\n"
        header += "🎮 <b>Доступные действия:</b>"
        
        await message.answer(
            header,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_monopoly: {e}")
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

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
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем, участвует ли пользователь в игре
        game = ACTIVE_GAMES[chat_id]
        player_exists = any(p["id"] == user_id for p in game.get("players", []))
        
        if not player_exists:
            await message.answer(
                "❌ <b>Вы не участвуете в этой игре!</b>\n\n"
                "Только игроки могут скрывать меню",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда для просмотра статистики"""
    try:
        user_id = message.from_user.id
        
        if user_id not in USER_STATS:
            await message.answer(
                "📊 <b>Статистика игрока</b>\n\n"
                "У вас еще нет статистики. Сыграйте свою первую игру!",
                parse_mode="HTML"
            )
            return
        
        stats = USER_STATS[user_id]
        win_rate = (stats["games_won"] / stats["games_played"]) * 100 if stats["games_played"] > 0 else 0
        
        stats_text = (
            f"📊 <b>Статистика игрока {stats['name']}</b>\n\n"
            f"🎮 Сыграно игр: <b>{stats['games_played']}</b>\n"
            f"🏆 Побед: <b>{stats['games_won']}</b>\n"
            f"📈 Процент побед: <b>{win_rate:.1f}%</b>\n"
            f"💰 Всего денег: <b>{stats.get('total_money', 0)}$</b>\n"
            f"🏠 Куплено недвижимости: <b>{stats.get('properties_bought', 0)}</b>\n"
            f"📅 Последняя игра: <b>{stats.get('last_played', 'никогда')}</b>"
        )
        
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")

async def show_inline_menu(message: types.Message, for_user_only: bool = False):
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
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

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
        
        # Бросаем кубики с анимацией
        dice1, dice2 = await send_dice_animation(chat_id, current_player["name"])
        
        # Обрабатываем ход
        result_text = await process_player_turn(chat_id, game, current_player, (dice1, dice2))
        
        # Проверяем банкротство
        if current_player.get("balance", 1500) < 0:
            result_text += f"\n💀 <b>БАНКРОТ!</b> {current_player['name']} выбывает из игры!\n"
            
            # Удаляем игрока
            game["players"] = [p for p in game["players"] if p["id"] != user_id]
            
            # Освобождаем его недвижимость
            properties_to_free = []
            for prop_id, prop_info in game.get("properties", {}).items():
                if prop_info.get("owner") == user_id:
                    properties_to_free.append(prop_id)
            
            for prop_id in properties_to_free:
                del game["properties"][prop_id]
            
            # Обновляем статистику
            update_user_stats(user_id, message.from_user.username, message.from_user.first_name, win=False)
            
            # Проверяем конец игры
            if len(game["players"]) == 1:
                winner = game["players"][0]
                result_text += f"\n🏆 <b>ИГРА ОКОНЧЕНА!</b>\n"
                result_text += f"🎉 Победитель: {winner['name']}!\n"
                
                # Обновляем статистику победителя
                update_user_stats(winner["id"], "", winner["name"], win=True)
                
                # Удаляем игру
                del ACTIVE_GAMES[chat_id]
                
                await message.answer(result_text, parse_mode="HTML")
                return
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx] if game["players"] else None
        
        if next_player:
            result_text += f"\n➡️ <b>Следующий: {next_player['name']}</b>"
        
        await message.answer(result_text, parse_mode="HTML")
        
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
        
        # Находим недвижимость игрока, на которой можно строить
        buildable_properties = []
        for prop_id in player.get("properties", []):
            if prop_id in game["properties"]:
                prop = game["properties"][prop_id]
                if prop.get("owner") == user_id and not prop.get("mortgaged", False):
                    # Проверяем цветовую группу
                    color = BOARD[prop_id][3]
                    if color in COLOR_GROUPS:
                        # Проверяем, что у игрока все улицы этого цвета
                        has_all = True
                        for group_prop_id in COLOR_GROUPS[color]:
                            if group_prop_id not in game["properties"]:
                                has_all = False
                                break
                            if game["properties"][group_prop_id].get("owner") != user_id:
                                has_all = False
                                break
                        
                        if has_all:
                            buildable_properties.append(prop_id)
        
        if not buildable_properties:
            await message.answer(
                "❌ <b>Нет доступной недвижимости для строительства!</b>\n\n"
                "Для строительства необходимо:\n"
                "1. Иметь все улицы одного цвета\n"
                "2. Недвижимость не должна быть заложена\n"
                "3. На балансе должны быть средства",
                parse_mode="HTML"
            )
            return
        
        # Показываем список доступной недвижимости
        properties_list = ""
        for prop_id in buildable_properties:
            prop_name = BOARD[prop_id][0]
            houses = game["properties"][prop_id].get("houses", 0)
            hotel = game["properties"][prop_id].get("hotel", False)
            
            properties_list += f"• {prop_name} "
            if hotel:
                properties_list += f"(🏨 Отель)\n"
            else:
                properties_list += f"(🏠 {houses}/4)\n"
        
        await message.answer(
            f"🏗️ <b>Доступная для строительства недвижимость:</b>\n\n"
            f"{properties_list}\n"
            f"📝 Для строительства используйте команду:\n"
            f"/build [номер_улицы]\n"
            f"Например: /build 1",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в build_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("build"))
async def cmd_build(message: types.Message):
    """Команда для строительства"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /build [номер_улицы]\n"
                "Например: /build 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что недвижимость не заложена
        if prop.get("mortgaged", False):
            await message.answer("❌ Невозможно строить на заложенной недвижимости!")
            return
        
        # Показываем меню строительства
        prop_name = BOARD[property_id][0]
        houses = prop.get("houses", 0)
        hotel = prop.get("hotel", False)
        
        info_text = f"🏠 <b>{prop_name}</b>\n"
        
        if hotel:
            info_text += "🏨 Отель построен\n"
        else:
            info_text += f"🏠 Дома: {houses}/4\n"
        
        # Показываем стоимость
        color = BOARD[property_id][3]
        if color in BUILDING_COSTS:
            house_cost = BUILDING_COSTS[color]["house"]
            hotel_cost = BUILDING_COSTS[color]["hotel"]
            info_text += f"💰 Стоимость дома: {house_cost}$\n"
            info_text += f"💰 Стоимость отеля: {hotel_cost}$\n"
        
        await message.answer(
            info_text,
            parse_mode="HTML",
            reply_markup=build_property_kb(property_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_build: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "📊 Мои активы")
async def show_assets_button(message: types.Message):
    """Кнопка показа активов"""
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
        
        # Собираем информацию
        balance = player.get("balance", 1500)
        position = player.get("position", 0)
        in_jail = player.get("in_jail", False)
        
        # Недвижимость игрока
        properties = []
        mortgaged_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                prop_name = BOARD[prop_id][0]
                houses = prop_info.get("houses", 0)
                hotel = prop_info.get("hotel", False)
                mortgaged = prop_info.get("mortgaged", False)
                
                prop_info_str = f"• {prop_name}"
                
                if mortgaged:
                    prop_info_str += " ⚠️ (заложена)"
                    mortgaged_properties.append(prop_info_str)
                elif hotel:
                    prop_info_str += f" 🏨 (отель)"
                    properties.append(prop_info_str)
                elif houses > 0:
                    prop_info_str += f" 🏠 ({houses}/4)"
                    properties.append(prop_info_str)
                else:
                    properties.append(prop_info_str)
        
        assets_text = (
            f"💰 <b>Активы {player['name']}</b>\n\n"
            f"💵 Баланс: <b>{balance}$</b>\n"
            f"📍 Позиция: <b>{position}</b>\n"
        )
        
        if in_jail:
            jail_turns = player.get("jail_turns", 0)
            assets_text += f"⛓️ В тюрьме: <b>ход {jail_turns}/3</b>\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(properties) + len(mortgaged_properties)} объектов</b>\n"
        
        if properties:
            assets_text += "\n📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties:
                assets_text += f"{prop}\n"
        
        if mortgaged_properties:
            assets_text += "\n⚠️ <b>Заложенная недвижимость:</b>\n"
            for prop in mortgaged_properties:
                assets_text += f"{prop}\n"
        
        await message.answer(assets_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в show_assets_button: {e}")
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
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Получаем список других игроков
        other_players = [p for p in game["players"] if p["id"] != user_id]
        
        if not other_players:
            await message.answer(
                "❌ <b>Недостаточно игроков для торговли!</b>\n\n"
                "Нужно минимум 2 игрока в игре",
                parse_mode="HTML"
            )
            return
        
        # Показываем список игроков для торговли
        players_list = ""
        for idx, other_player in enumerate(other_players, 1):
            players_list += f"{idx}. {other_player['name']}\n"
        
        await message.answer(
            "🤝 <b>Выберите игрока для торговли:</b>\n\n"
            f"{players_list}\n"
            f"📝 Используйте команду:\n"
            f"/trade [номер_игрока]\n"
            f"Например: /trade 1",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в trade_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("trade"))
async def cmd_trade(message: types.Message):
    """Команда для начала торговли"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер игрока
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /trade [номер_игрока]\n"
                "Например: /trade 1",
                parse_mode="HTML"
            )
            return
        
        try:
            player_num = int(args[1])
        except ValueError:
            await message.answer("❌ Номер игрока должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим текущего игрока
        from_player = next((p for p in game["players"] if p["id"] == user_id), None)
        if not from_player:
            await message.answer("❌ Вы не участвуете в этой игре!")
            return
        
        # Находим целевого игрока
        other_players = [p for p in game["players"] if p["id"] != user_id]
        if player_num < 1 or player_num > len(other_players):
            await message.answer("❌ Неверный номер игрока!")
            return
        
        target_player = other_players[player_num - 1]
        
        # Показываем меню торговли
        await message.answer(
            f"🤝 <b>Торговля с {target_player['name']}</b>\n\n"
            f"💰 Ваш баланс: {from_player.get('balance', 1500)}$\n"
            f"💰 Баланс {target_player['name']}: {target_player.get('balance', 1500)}$\n\n"
            f"👇 Выберите тип предложения:",
            parse_mode="HTML",
            reply_markup=trade_kb(user_id, target_player["id"])
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_trade: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "💵 Заложить улицу")
async def mortgage_button(message: types.Message):
    """Кнопка залога улицы"""
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
        
        # Находим недвижимость игрока, которую можно заложить
        mortgageable_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                # Нельзя заложить, если есть постройки
                if prop_info.get("houses", 0) == 0 and not prop_info.get("hotel", False):
                    # Проверяем, не заложена ли уже
                    if not prop_info.get("mortgaged", False):
                        mortgageable_properties.append(prop_id)
        
        if not mortgageable_properties:
            await message.answer(
                "❌ <b>Нет доступной недвижимости для залога!</b>\n\n"
                "Для залога необходимо:\n"
                "1. Иметь недвижимость без построек\n"
                "2. Недвижимость не должна быть уже заложена",
                parse_mode="HTML"
            )
            return
        
        # Показываем список доступной недвижимости
        properties_list = ""
        for prop_id in mortgageable_properties:
            prop_name = BOARD[prop_id][0]
            price = BOARD[prop_id][1]
            mortgage_value = price // 2  # 50% от стоимости
            properties_list += f"• {prop_name} (стоимость: {price}$, залог: {mortgage_value}$)\n"
        
        await message.answer(
            f"💵 <b>Доступная для залога недвижимость:</b>\n\n"
            f"{properties_list}\n"
            f"📝 Для залога используйте команду:\n"
            f"/mortgage [номер_улицы]\n"
            f"Например: /mortgage 1\n\n"
            f"💡 Вы получите 50% от стоимости недвижимости",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в mortgage_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("mortgage"))
async def cmd_mortgage(message: types.Message):
    """Команда для залога недвижимости"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /mortgage [номер_улицы]\n"
                "Например: /mortgage 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что на недвижимости нет построек
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            await message.answer("❌ Невозможно заложить недвижимость с постройками!")
            return
        
        # Проверяем, что недвижимость не заложена
        if prop.get("mortgaged", False):
            await message.answer("❌ Эта недвижимость уже заложена!")
            return
        
        # Закладываем недвижимость
        success, message_text, mortgage_value = mortgage_property(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
        
        await message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_mortgage: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(Command("unmortgage"))
async def cmd_unmortgage(message: types.Message):
    """Команда для выкупа недвижимости из залога"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /unmortgage [номер_улицы]\n"
                "Например: /unmortgage 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что недвижимость заложена
        if not prop.get("mortgaged", False):
            await message.answer("❌ Эта недвижимость не заложена!")
            return
        
        # Выкупаем недвижимость
        success, message_text, unmortgage_cost = unmortgage_property(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
        
        await message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_unmortgage: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "🗺️ Показать карту")
async def show_map_button(message: types.Message):
    """Кнопка показа карты"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Создаем простую карту
        map_text = create_simple_map(game)
        
        # Добавляем информацию о текущем игроке
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if current_player:
            map_text += f"\n🎯 <b>Сейчас ходит: {current_player['name']}</b>"
        
        await message.answer(map_text, parse_mode="Markdown")
        
        # Также отправляем ссылку на интерактивную карту (если настроен веб-сервер)
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if domain and 'localhost' not in domain:
            map_url = generate_map_url(chat_id, game["players"])
            await message.answer(
                f"🗺️ <b>Интерактивная карта:</b>\n"
                f"🔗 {map_url}",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в show_map_button: {e}")
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
        
        # Бросаем кубики с анимацией
        dice1, dice2 = await send_dice_animation(chat_id, current_player["name"])
        
        # Обрабатываем ход
        result_text = await process_player_turn(chat_id, game, current_player, (dice1, dice2))
        
        # Проверяем банкротство
        if current_player.get("balance", 1500) < 0:
            result_text += f"\n💀 <b>БАНКРОТ!</b> {current_player['name']} выбывает из игры!\n"
            
            # Удаляем игрока
            game["players"] = [p for p in game["players"] if p["id"] != user_id]
            
            # Освобождаем его недвижимость
            properties_to_free = []
            for prop_id, prop_info in game.get("properties", {}).items():
                if prop_info.get("owner") == user_id:
                    properties_to_free.append(prop_id)
            
            for prop_id in properties_to_free:
                del game["properties"][prop_id]
            
            # Обновляем статистику
            update_user_stats(user_id, c.from_user.username, c.from_user.first_name, win=False)
            
            # Проверяем конец игры
            if len(game["players"]) == 1:
                winner = game["players"][0]
                result_text += f"\n🏆 <b>ИГРА ОКОНЧЕНА!</b>\n"
                result_text += f"🎉 Победитель: {winner['name']}!\n"
                
                # Обновляем статистику победителя
                update_user_stats(winner["id"], "", winner["name"], win=True)
                
                # Удаляем игру
                del ACTIVE_GAMES[chat_id]
                
                await c.message.edit_text(result_text, parse_mode="HTML")
                return
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx] if game["players"] else None
        
        if next_player:
            result_text += f"\n➡️ <b>Следующий: {next_player['name']}</b>"
        
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
        in_jail = player.get("in_jail", False)
        
        # Недвижимость игрока
        properties = []
        mortgaged_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                prop_name = BOARD[prop_id][0]
                houses = prop_info.get("houses", 0)
                hotel = prop_info.get("hotel", False)
                mortgaged = prop_info.get("mortgaged", False)
                
                prop_info_str = f"• {prop_name}"
                
                if mortgaged:
                    prop_info_str += " ⚠️ (заложена)"
                    mortgaged_properties.append(prop_info_str)
                elif hotel:
                    prop_info_str += f" 🏨 (отель)"
                    properties.append(prop_info_str)
                elif houses > 0:
                    prop_info_str += f" 🏠 ({houses}/4)"
                    properties.append(prop_info_str)
                else:
                    properties.append(prop_info_str)
        
        assets_text = (
            f"💰 <b>Активы {player['name']}</b>\n\n"
            f"💵 Баланс: <b>{balance}$</b>\n"
            f"📍 Позиция: <b>{position}</b>\n"
        )
        
        if in_jail:
            jail_turns = player.get("jail_turns", 0)
            assets_text += f"⛓️ В тюрьме: <b>ход {jail_turns}/3</b>\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(properties) + len(mortgaged_properties)} объектов</b>\n"
        
        if properties:
            assets_text += "\n📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties[:5]:  # Ограничиваем 5 свойствами
                assets_text += f"{prop}\n"
        
        if mortgaged_properties:
            assets_text += "\n⚠️ <b>Заложенная недвижимость:</b>\n"
            for prop in mortgaged_properties[:3]:  # Ограничиваем 3 свойствами
                assets_text += f"{prop}\n"
        
        if len(properties) > 5 or len(mortgaged_properties) > 3:
            assets_text += f"\n📄 <i>Используйте обычное меню для полного списка</i>"
        
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

@dp.callback_query(F.data == "inline_build")
async def inline_build(c: types.CallbackQuery):
    """Inline строительство"""
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
        
        # Находим недвижимость игрока, на которой можно строить
        buildable_properties = []
        for prop_id in player.get("properties", []):
            if prop_id in game["properties"]:
                prop = game["properties"][prop_id]
                if prop.get("owner") == user_id and not prop.get("mortgaged", False):
                    # Проверяем цветовую группу
                    color = BOARD[prop_id][3]
                    if color in COLOR_GROUPS:
                        # Проверяем, что у игрока все улицы этого цвета
                        has_all = True
                        for group_prop_id in COLOR_GROUPS[color]:
                            if group_prop_id not in game["properties"]:
                                has_all = False
                                break
                            if game["properties"][group_prop_id].get("owner") != user_id:
                                has_all = False
                                break
                        
                       """
Monopoly Premium Bot - Telegram бот (Часть 1)
👑 Создано Темным Принцем (Dark Prince) 👑
Полностью обновленный код со всеми исправлениями
"""

import os
import asyncio
import logging
import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# ==================== НАСТРОЙКИ ====================
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    logging.error("❌ BOT_TOKEN не найден!")
    exit(1)

PORT = int(os.environ.get("PORT", 8083))
DEV_TAG = "@Whylovely05"
MAINTENANCE_MSG = "Бот обновляется, Темный принц уже исправляет это ♥️♥️"
BANNER = "┏━━━━━━━━━━━━━━━━━━┓\n┃  Monopoly Premium  ┃\n┗━━━━━━━━━━━━━━━━━━┛"

# Список разрешенных пользователей для админки
ALLOWED_ADMINS = ["Whylovely05"]  # Твои username
ADMIN_PASSWORD_HASH = hashlib.sha256("darkprince".encode()).hexdigest()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
WAITING_GAMES: Dict[int, Dict] = {}  # {chat_id: {data, timer_task, pinned_message_id}}
ACTIVE_GAMES: Dict[int, Dict] = {}
HIDDEN_MENU_USERS: Dict[int, int] = {}  # {user_id: chat_id} - кто скрыл меню
USER_STATS: Dict[int, Dict] = {}  # Статистика пользователей
STATS = {"maintenance_mode": False}

# ==================== КАРТА МОНОПОЛИИ ====================
BOARD = {
    0: ["СТАРТ", 0, 0, "SPECIAL"],
    1: ["Житная", 60, 4, "BROWN"], 
    2: ["Общественная казна", 0, 0, "CHANCE"], 
    3: ["Нагатинская", 60, 4, "BROWN"], 
    4: ["Налог на роскошь", -200, 0, "TAX"],
    5: ["Рижская ж/д", 200, 25, "RAIL"], 
    6: ["Варшавское ш.", 100, 6, "BLUE"],
    7: ["Шанс", 0, 0, "CHANCE"], 
    8: ["Огородный пр.", 100, 6, "BLUE"],
    9: ["Рижская", 120, 8, "BLUE"], 
    10: ["Тюрьма (посещение)", 0, 0, "JAIL"],
    11: ["Курская", 140, 10, "PINK"], 
    12: ["Электросеть", 150, 10, "UTIL"],
    13: ["Абрамцево", 140, 10, "PINK"], 
    14: ["Пантелеевская", 160, 12, "PINK"],
    15: ["Казанская ж/д", 200, 25, "RAIL"], 
    16: ["Вавилова", 180, 14, "ORANGE"],
    17: ["Общественная казна", 0, 0, "CHEST"], 
    18: ["Тимирязевская", 180, 14, "ORANGE"],
    19: ["Лихоборы", 200, 16, "ORANGE"], 
    20: ["Бесплатная стоянка", 0, 0, "PARKING"],
    21: ["Арбат", 220, 18, "RED"], 
    22: ["Шанс", 0, 0, "CHANCE"],
    23: ["Полянка", 220, 18, "RED"], 
    24: ["Сретенка", 240, 20, "RED"],
    25: ["Курская ж/д", 200, 25, "RAIL"], 
    26: ["Ростовская", 260, 22, "YELLOW"],
    27: ["Рязанский пр.", 260, 22, "YELLOW"],  # Исправлено: было 2, стало 27
    28: ["Водопровод", 150, 10, "UTIL"],
    29: ["Новинский б-р", 280, 24, "YELLOW"], 
    30: ["Отправляйтесь в тюрьму", 0, 0, "GO_TO_JAIL"],
    31: ["Пушкинская", 300, 26, "GREEN"], 
    32: ["Тверская", 300, 26, "GREEN"],
    33: ["Общественная казна", 0, 0, "CHEST"], 
    34: ["Маяковского", 320, 28, "GREEN"],
    35: ["Ленинградская ж/д", 200, 25, "RAIL"], 
    36: ["Шанс", 0, 0, "CHANCE"],
    37: ["Кутузовский", 350, 35, "DARKBLUE"], 
    38: ["Налог на сверхприбыль", -100, 0, "TAX"],
    39: ["Бродвей", 400, 50, "DARKBLUE"]
}

# Карточки шанса
CHANCE_CARDS = [
    "🎲 Продвиньтесь к СТАРТУ и получите 200$",
    "🏦 Банковская ошибка в вашу пользу. Получите 150$",
    "📈 Ваши акции выросли. Получите 100$",
    "🎯 Вы выиграли конкурс. Получите 50$",
    "🏆 Приз за красоту. Получите 25$",
    "💰 Вас оштрафовали за превышение скорости. Заплатите 50$",
    "🏥 Оплатите лечение. Заплатите 100$",
    "🎭 Оплатите обучение. Заплатите 150$",
    "🏛️ Идите в тюрьму. Не проходите СТАРТ, не получайте 200$",
    "🔄 Идите назад на 3 клетки"
]

# Карточки общественной казны
CHEST_CARDS = [
    "🎁 Вторая премия за конкурс. Получите 25$",
    "💼 Оплата страховки. Получите 100$",
    "💸 Налог на наследство. Заплатите 100$",
    "🏅 Вы заняли второе место. Получите 25$",
    "💳 Оплата больничных. Получите 100$",
    "📚 Оплата обучения. Заплатите 150$",
    "🎫 Сбор на уличное освещение. Заплатите 50$",
    "🌲 Оплата за посаженное дерево. Получите 25$"
]

# Цветовые группы
COLOR_GROUPS = {
    "BROWN": [1, 3],
    "BLUE": [6, 8, 9],
    "PINK": [11, 13, 14],
    "ORANGE": [16, 18, 19],
    "RED": [21, 23, 24],
    "YELLOW": [26, 27, 29],
    "GREEN": [31, 32, 34],
    "DARKBLUE": [37, 39],
    "RAIL": [5, 15, 25, 35],
    "UTIL": [12, 28]
}

# Стоимость строительства
BUILDING_COSTS = {
    "BROWN": {"house": 50, "hotel": 50},
    "BLUE": {"house": 50, "hotel": 50},
    "PINK": {"house": 100, "hotel": 100},
    "ORANGE": {"house": 100, "hotel": 100},
    "RED": {"house": 150, "hotel": 150},
    "YELLOW": {"house": 150, "hotel": 150},
    "GREEN": {"house": 200, "hotel": 200},
    "DARKBLUE": {"house": 200, "hotel": 200}
}

# ==================== ФУНКЦИИ ВСПОМОГАТЕЛЬНЫЕ ====================
def load_user_stats():
    """Загрузить статистику пользователей"""
    global USER_STATS
    try:
        with open("user_stats.json", "r", encoding="utf-8") as f:
            USER_STATS = json.load(f)
    except:
        USER_STATS = {}

def save_user_stats():
    """Сохранить статистику пользователей"""
    try:
        with open("user_stats.json", "w", encoding="utf-8") as f:
            json.dump(USER_STATS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

def update_user_stats(user_id: int, username: str, name: str, win: bool = False):
    """Обновить статистику пользователя"""
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {
            "username": username,
            "name": name,
            "games_played": 0,
            "games_won": 0,
            "total_money": 0,
            "properties_bought": 0,
            "last_played": datetime.now().isoformat()
        }
    
    stats = USER_STATS[user_id]
    stats["games_played"] += 1
    if win:
        stats["games_won"] += 1
    stats["last_played"] = datetime.now().isoformat()
    save_user_stats()

def get_top_players(limit: int = 10) -> List[Dict]:
    """Получить топ игроков"""
    players = []
    for user_id, stats in USER_STATS.items():
        if stats["games_played"] > 0:
            win_rate = (stats["games_won"] / stats["games_played"]) * 100
            players.append({
                "user_id": user_id,
                "name": stats["name"],
                "username": stats.get("username", ""),
                "games_played": stats["games_played"],
                "games_won": stats["games_won"],
                "win_rate": win_rate
            })
    
    # Сортировка по победам, затем по количеству игр
    players.sort(key=lambda x: (x["games_won"], x["games_played"]), reverse=True)
    return players[:limit]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_kb(is_group: bool = False) -> types.InlineKeyboardMarkup:
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
    kb.button(text="🏆 Рейтинг игроков", callback_data="show_leaderboard")
    kb.button(text="👨‍💻 О девелопере", callback_data="show_developer")
    
    # Статус системы (только для админов)
    if is_group:
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
        web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
        kb.button(text="🌐 Статус системы", url=f"{web_url}?password=darkprince")
    
    kb.adjust(1)
    return kb.as_markup()

def waiting_room_kb(chat_id: int, user_id: int = None) -> types.InlineKeyboardMarkup:
    """Лобби ожидания - динамическая клавиатура"""
    kb = InlineKeyboardBuilder()
    
    # Основные кнопки для всех
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    
    # Проверяем, есть ли игра и является ли пользователь создателем
    if chat_id in WAITING_GAMES and user_id:
        game = WAITING_GAMES[chat_id]
        if user_id == game.get("creator_id"):
            # Только создатель видит эти кнопки
            kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
            kb.button(text="❌ Отменить сбор", callback_data=f"cancel_gathering_{chat_id}")
            kb.adjust(2, 2)
            return kb.as_markup()
    
    # Обычная клавиатура
    kb.adjust(2)
    return kb.as_markup()

def game_main_kb() -> types.ReplyKeyboardMarkup:
    """Основная игровая клавиатура"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить")
    kb.button(text="📊 Мои активы")
    kb.button(text="🤝 Торговля")
    kb.button(text="💵 Заложить улицу")
    kb.button(text="🗺️ Показать карту")
    kb.button(text="❌ Скрыть меню")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def inline_menu_kb() -> types.InlineKeyboardMarkup:
    """Inline меню для тех кто скрыл основное"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик", callback_data="inline_roll_dice")
    kb.button(text="🏠 Построить", callback_data="inline_build")
    kb.button(text="📊 Мои активы", callback_data="inline_assets")
    kb.button(text="🤝 Торговля", callback_data="inline_trade")
    kb.button(text="💵 Заложить улицу", callback_data="inline_mortgage")
    kb.button(text="🗺️ Показать карту", callback_data="inline_map")
    kb.button(text="📱 Вернуть меню", callback_data="restore_menu")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

def build_property_kb(property_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура для строительства на собственности"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Построить дом (+1)", callback_data=f"build_house_{property_id}")
    kb.button(text="🏨 Построить отель", callback_data=f"build_hotel_{property_id}")
    kb.button(text="🔨 Продать дом (-1)", callback_data=f"sell_house_{property_id}")
    kb.button(text="💵 Заложить", callback_data=f"mortgage_{property_id}")
    kb.button(text="❌ Отмена", callback_data="cancel_build")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

def trade_kb(player_id: int, target_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура для торговли"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Предложить деньги", callback_data=f"offer_money_{player_id}_{target_id}")
    kb.button(text="🏠 Предложить недвижимость", callback_data=f"offer_property_{player_id}_{target_id}")
    kb.button(text="💼 Смешанное предложение", callback_data=f"offer_mixed_{player_id}_{target_id}")
    kb.button(text="❌ Отменить сделку", callback_data="cancel_trade")
    kb.adjust(2, 2)
    return kb.as_markup()

# ==================== АНИМАЦИЯ КУБИКОВ ====================
def get_dice_emoji(value: int) -> str:
    """Получить эмодзи для кубика"""
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    return dice_emojis[value - 1]

async def send_dice_animation(chat_id: int, user_name: str) -> Tuple[int, int]:
    """Отправить анимацию броска кубиков"""
    # Имитация анимации - отправляем несколько сообщений
    messages = []
    
    # Первое сообщение - начало броска
    msg1 = await bot.send_message(
        chat_id,
        f"🎲 *{user_name} бросает кубики...*\n"
        f"⚀ ⚁ ⚂ ⚃ ⚄ ⚅",
        parse_mode="Markdown"
    )
    messages.append(msg1.message_id)
    await asyncio.sleep(0.5)
    
    # Второе сообщение - кубики крутятся
    msg2 = await bot.send_message(
        chat_id,
        f"🎲 *Кубики крутятся...*\n"
        f"🎯 🎯",
        parse_mode="Markdown"
    )
    messages.append(msg2.message_id)
    await asyncio.sleep(0.5)
    
    # Генерируем результат
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    
    # Третье сообщение - результат
    msg3 = await bot.send_message(
        chat_id,
        f"🎲 *Результат броска {user_name}:*\n"
        f"{get_dice_emoji(dice1)} Кубик 1: **{dice1}**\n"
        f"{get_dice_emoji(dice2)} Кубик 2: **{dice2}**\n"
        f"📊 Сумма: **{dice1 + dice2}**",
        parse_mode="Markdown"
    )
    messages.append(msg3.message_id)
    
    # Удаляем предыдущие сообщения через 2 секунды
    await asyncio.sleep(2)
    try:
        await bot.delete_message(chat_id, msg1.message_id)
        await bot.delete_message(chat_id, msg2.message_id)
    except:
        pass
    
    return dice1, dice2

# ==================== КАРТА МОНОПОЛИИ ====================
def generate_map_url(game_id: int, players: List[Dict]) -> str:
    """Генерировать URL для интерактивной карты"""
    # Базовая реализация - можно заменить на реальную генерацию карты
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
    web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
    
    # Формируем данные для карты
    players_data = []
    for player in players:
        players_data.append({
            "id": player["id"],
            "name": player["name"],
            "position": player.get("position", 0),
            "color": player.get("color", "#3498db")
        })
    
    return f"{web_url}/map/{game_id}?players={json.dumps(players_data)}"

def create_simple_map(game: Dict) -> str:
    """Создать простую текстовую карту"""
    players = game.get("players", [])
    properties = game.get("properties", {})
    
    map_text = "🗺️ *Карта игры:*\n\n"
    
    # Создаем простую схему
    for pos in range(40):
        cell_info = BOARD.get(pos, ["", 0, 0, ""])
        cell_name = cell_info[0]
        
        # Определяем кто на клетке
        players_here = []
        for player in players:
            if player.get("position") == pos:
                players_here.append(player["name"][:1])  # Первая буква имени
        
        # Определяем владельца
        owner_symbol = " "
        if pos in properties:
            owner = properties[pos].get("owner")
            if owner:
                for player in players:
                    if player["id"] == owner:
                        owner_symbol = player["name"][:1]
                        break
        
        # Формируем строку
        if players_here:
            map_text += f"[{pos:2d}] {cell_name[:10]:10} 👤{''.join(players_here)}"
        else:
            map_text += f"[{pos:2d}] {cell_name[:10]:10}"
        
        if owner_symbol != " ":
            map_text += f" 🏠{owner_symbol}"
        
        # Специальные клетки
        if cell_info[3] == "JAIL":
            map_text += " ⛓️"
        elif cell_info[3] == "GO_TO_JAIL":
            map_text += " 🚓"
        elif cell_info[3] == "CHANCE":
            map_text += " 🎲"
        elif cell_info[3] == "CHEST":
            map_text += " 💰"
        
        map_text += "\n"
    
    return map_text

# ==================== МЕХАНИКА ТЮРЬМЫ ====================
def handle_jail_mechanic(player: Dict, game: Dict) -> str:
    """Обработка механики тюрьмы"""
    result = ""
    
    if player.get("in_jail", False):
        jail_turns = player.get("jail_turns", 0)
        
        if jail_turns >= 3:
            # Автоматический выход из тюрьмы после 3 ходов
            player["in_jail"] = False
            player["jail_turns"] = 0
            fine = 50
            player["balance"] = player.get("balance", 1500) - fine
            result = f"⛓️ Вы вышли из тюрьмы после 3 ходов. Штраф: {fine}$\n"
        else:
            player["jail_turns"] = jail_turns + 1
            result = f"⛓️ Вы в тюрьме. Ход {jail_turns + 1}/3\n"
    
    return result

# ==================== МЕХАНИКА ЗАЛОГА ====================
def can_mortgage(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок заложить недвижимость"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    if prop.get("owner") != player_id:
        return False
    
    # Нельзя заложить, если есть постройки
    if prop.get("houses", 0) > 0 or prop.get("hotel", False):
        return False
    
    # Нельзя заложить, если уже заложено
    if prop.get("mortgaged", False):
        return False
    
    return True

def mortgage_property(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Заложить недвижимость"""
    if not can_mortgage(property_id, game, player_id):
        return False, "Невозможно заложить эту недвижимость", 0
    
    prop = game["properties"][property_id]
    mortgage_value = BOARD[property_id][1] // 2  # 50% от стоимости
    
    # Закладываем
    prop["mortgaged"] = True
    
    # Даем деньги игроку
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) + mortgage_value
            break
    
    return True, f"Недвижимость заложена! Вы получили {mortgage_value}$", mortgage_value

def can_unmortgage(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок выкупить недвижимость"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    if prop.get("owner") != player_id:
        return False
    
    # Должна быть заложена
    if not prop.get("mortgaged", False):
        return False
    
    # Проверяем достаточно ли денег (110% от залоговой стоимости)
    unmortgage_cost = int(BOARD[property_id][1] // 2 * 1.1)
    
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) >= unmortgage_cost:
                return True
    
    return False

def unmortgage_property(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Выкупить недвижимость из залога"""
    if not can_unmortgage(property_id, game, player_id):
        return False, "Невозможно выкупить эту недвижимость", 0
    
    prop = game["properties"][property_id]
    unmortgage_cost = int(BOARD[property_id][1] // 2 * 1.1)  # 110% от залоговой стоимости
    
    # Выкупаем
    prop["mortgaged"] = False
    
    # Забираем деньги у игрока
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - unmortgage_cost
            break
    
    return True, f"Недвижимость выкуплена из залога за {unmortgage_cost}$", unmortgage_cost

# ==================== ФУНКЦИИ ДЛЯ ТАЙМЕРОВ ====================
async def start_waiting_timer(chat_id: int, game_data: Dict):
    """Запустить таймер ожидания на 3 минуты"""
    async def check_timer():
        await asyncio.sleep(180)  # 3 минуты
        
        if chat_id not in WAITING_GAMES:
            return
            
        game = WAITING_GAMES[chat_id]
        if not game:
            return
            
        player_count = len(game.get("players", []))
        
        # Если 2 или больше игроков - начинаем игру автоматически
        if player_count >= 2:
            await auto_start_game(chat_id, game)
        else:
            # Если меньше 2 игроков - отменяем сбор
            await cancel_gathering_by_timer(chat_id, game)
    
    # Запускаем таймер
    timer_task = asyncio.create_task(check_timer())
    game_data["timer_task"] = timer_task

async def auto_start_game(chat_id: int, game: Dict):
    """Автоматически начать игру после таймера"""
    try:
        # Переносим игру в активные
        ACTIVE_GAMES[chat_id] = {
            "players": game["players"],
            "current_player": 0,
            "started_at": datetime.now(),
            "creator_id": game["creator_id"],
            "properties": {},
            "turn": 1,
            "chance_deck": CHANCE_CARDS.copy(),
            "chest_deck": CHEST_CARDS.copy()
        }
        
        # Перемешиваем колоды
        random.shuffle(ACTIVE_GAMES[chat_id]["chance_deck"])
        random.shuffle(ACTIVE_GAMES[chat_id]["chest_deck"])
        
        # Инициализируем игроков
        colors = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠"]
        for idx, player in enumerate(ACTIVE_GAMES[chat_id]["players"]):
            player["balance"] = 1500
            player["position"] = 0
            player["properties"] = []
            player["in_jail"] = False
            player["jail_turns"] = 0
            player["color"] = colors[idx % len(colors)]
            player["get_out_of_jail_free"] = 0
        
        # Удаляем из ожидающих
        if chat_id in WAITING_GAMES:
            game_data = WAITING_GAMES.pop(chat_id)
            # Отменяем таймер
            if "timer_task" in game_data:
                game_data["timer_task"].cancel()
        
        # УДАЛЯЕМ СООБЩЕНИЕ О СБОРЕ
        if "message_id" in game:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=game["message_id"])
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
        
        # Открепляем сообщение о сборе
        if "pinned_message_id" in game:
            try:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=game["pinned_message_id"])
            except:
                pass
        
        # Формируем список игроков
        players_list = "\n".join([f"• {p['name']}" for p in ACTIVE_GAMES[chat_id]["players"]])
        
        # Отправляем сообщение о начале игры
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎉 <b>Игра началась автоматически!</b>\n\n"
                 f"<b>Участники:</b>\n{players_list}\n\n"
                 f"⏰ <i>3 минуты ожидания истекли</i>\n"
                 f"💰 Стартовый баланс: <b>1500$</b>\n"
                 f"🎲 Первым ходит: <b>{ACTIVE_GAMES[chat_id]['players'][0]['name']}</b>\n"
                 f"🔄 Ход: <b>1</b>",
            parse_mode="HTML"
        )
        
        # Отправляем игровое меню
        first_player = ACTIVE_GAMES[chat_id]["players"][0]
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎮 <b>Игра началась!</b>\n\n"
                 f"📢 <b>{first_player['name']}</b>, ваш ход первый!\n"
                 f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в auto_start_game: {e}")

async def cancel_gathering_by_timer(chat_id: int, game: Dict):
    """Отменить сбор по истечении таймера"""
    try:
        if chat_id in WAITING_GAMES:
            game_data = WAITING_GAMES.pop(chat_id)
            
            # Отменяем таймер
            if "timer_task" in game_data:
                game_data["timer_task"].cancel()
            
            # Открепляем сообщение
            if "pinned_message_id" in game_data:
                try:
                    await bot.unpin_chat_message(chat_id=chat_id, message_id=game_data["pinned_message_id"])
                except:
                    pass
            
            # Удаляем сообщение
            if "message_id" in game_data:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=game_data["message_id"])
                except:
                    pass
            
            # Отправляем сообщение об отмене
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ <b>Сбор игроков отменен!</b>\n\n"
                     f"⏰ <i>3 минуты ожидания истекли</i>\n"
                     f"👥 <b>Не удалось собрать достаточное количество игроков</b>\n"
                     f"Минимум требуется: 2 игрока\n"
                     f"Собрано: {len(game.get('players', []))} игрока(ов)",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в cancel_gathering_by_timer: {e}")

# ==================== ОБРАБОТКА КАРТОЧЕК ====================
def draw_chance_card(game: Dict) -> Tuple[str, Dict]:
    """Вытащить карточку шанса"""
    if not game["chance_deck"]:
        game["chance_deck"] = CHANCE_CARDS.copy()
        random.shuffle(game["chance_deck"])
    
    card = game["chance_deck"].pop(0)
    effect = {"money": 0, "move": 0, "jail": False}
    
    # Обработка карточки
    if "Получите" in card and "$" in card:
        # Извлекаем сумму
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = int(match.group(1))
    elif "Заплатите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = -int(match.group(1))
    elif "Продвиньтесь к СТАРТУ" in card:
        effect["move"] = "start"
    elif "Идите в тюрьму" in card:
        effect["jail"] = True
    elif "Идите назад на 3 клетки" in card:
        effect["move"] = -3
    
    return card, effect

def draw_chest_card(game: Dict) -> Tuple[str, Dict]:
    """Вытащить карточку общественной казны"""
    if not game["chest_deck"]:
        game["chest_deck"] = CHEST_CARDS.copy()
        random.shuffle(game["chest_deck"])
    
    card = game["chest_deck"].pop(0)
    effect = {"money": 0}
    
    # Обработка карточки
    if "Получите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = int(match.group(1))
    elif "Заплатите" in card and "$" in card:
        import re
        match = re.search(r'(\d+)\$', card)
        if match:
            effect["money"] = -int(match.group(1))
    
    return card, effect

# ==================== ПОКУПКА И СТРОИТЕЛЬСТВО ====================
def can_build_house(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок построить дом"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что недвижимость не заложена
    if prop.get("mortgaged", False):
        return False
    
    # Получаем цвет группы
    color = BOARD[property_id][3]
    if color not in COLOR_GROUPS:
        return False
    
    # Проверяем, что у игрока есть все улицы этого цвета
    color_properties = COLOR_GROUPS[color]
    for prop_id in color_properties:
        if prop_id not in game["properties"]:
            return False
        if game["properties"][prop_id].get("owner") != player_id:
            return False
    
    # Проверяем максимальное количество домов
    if prop.get("houses", 0) >= 4:
        return False
    
    # Проверяем баланс
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) < house_cost:
                return False
    
    return True

def build_house(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Построить дом"""
    if not can_build_house(property_id, game, player_id):
        return False, "Невозможно построить дом", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    
    # Строим дом
    prop["houses"] = prop.get("houses", 0) + 1
    
    # Обновляем аренду (увеличиваем на 50% за каждый дом)
    base_rent = BOARD[property_id][2]
    if prop["houses"] == 1:
        new_rent = base_rent * 2
    elif prop["houses"] == 2:
        new_rent = base_rent * 3
    elif prop["houses"] == 3:
        new_rent = base_rent * 4
    elif prop["houses"] == 4:
        new_rent = base_rent * 5
    else:
        new_rent = base_rent
    
    prop["current_rent"] = new_rent
    
    # Списание денег
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - house_cost
            break
    
    return True, f"Дом построен! Стоимость: {house_cost}$. Новая аренда: {new_rent}$", house_cost

def can_build_hotel(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок построить отель"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что есть 4 дома
    if prop.get("houses", 0) != 4:
        return False
    
    # Проверяем, что еще нет отеля
    if prop.get("hotel", False):
        return False
    
    # Получаем цвет группы
    color = BOARD[property_id][3]
    if color not in COLOR_GROUPS:
        return False
    
    # Проверяем баланс
    hotel_cost = BUILDING_COSTS.get(color, {}).get("hotel", 50)
    for player in game["players"]:
        if player["id"] == player_id:
            if player.get("balance", 1500) < hotel_cost:
                return False
    
    return True

def build_hotel(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Построить отель"""
    if not can_build_hotel(property_id, game, player_id):
        return False, "Невозможно построить отель", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    hotel_cost = BUILDING_COSTS.get(color, {}).get("hotel", 50)
    
    # Строим отель
    prop["hotel"] = True
    prop["houses"] = 0  # Убираем дома
    
    # Обновляем аренду (увеличиваем в 6 раз)
    base_rent = BOARD[property_id][2]
    new_rent = base_rent * 6
    prop["current_rent"] = new_rent
    
    # Списание денег
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) - hotel_cost
            break
    
    return True, f"Отель построен! Стоимость: {hotel_cost}$. Новая аренда: {new_rent}$", hotel_cost

def can_sell_house(property_id: int, game: Dict, player_id: int) -> bool:
    """Может ли игрок продать дом"""
    if property_id not in game.get("properties", {}):
        return False
    
    prop = game["properties"][property_id]
    
    # Проверяем владельца
    if prop.get("owner") != player_id:
        return False
    
    # Проверяем, что есть дома
    if prop.get("houses", 0) == 0:
        return False
    
    return True

def sell_house(property_id: int, game: Dict, player_id: int) -> Tuple[bool, str, int]:
    """Продать дом"""
    if not can_sell_house(property_id, game, player_id):
        return False, "Невозможно продать дом", 0
    
    prop = game["properties"][property_id]
    color = BOARD[property_id][3]
    house_cost = BUILDING_COSTS.get(color, {}).get("house", 50)
    refund = house_cost // 2  # 50% от стоимости
    
    # Продаем дом
    prop["houses"] = prop.get("houses", 0) - 1
    
    # Обновляем аренду
    base_rent = BOARD[property_id][2]
    houses = prop["houses"]
    
    if houses == 0:
        new_rent = base_rent
    elif houses == 1:
        new_rent = base_rent * 2
    elif houses == 2:
        new_rent = base_rent * 3
    elif houses == 3:
        new_rent = base_rent * 4
    
    prop["current_rent"] = new_rent
    
    # Возвращаем деньги
    for player in game["players"]:
        if player["id"] == player_id:
            player["balance"] = player.get("balance", 1500) + refund
            break
    
    return True, f"Дом продан! Вы получили {refund}$. Новая аренда: {new_rent}$", refund

# ==================== ТОРГОВЛЯ ====================
def create_trade_offer(from_player_id: int, to_player_id: int, 
                      money_offer: int = 0, properties_offer: List[int] = None,
                      money_request: int = 0, properties_request: List[int] = None) -> Dict:
    """Создать предложение обмена"""
    return {
        "from_player": from_player_id,
        "to_player": to_player_id,
        "money_offer": money_offer or 0,
        "properties_offer": properties_offer or [],
        "money_request": money_request or 0,
        "properties_request": properties_request or [],
        "created_at": datetime.now().isoformat(),
        "status": "pending"  # pending, accepted, rejected
    }

def validate_trade_offer(trade_offer: Dict, game: Dict) -> Tuple[bool, str]:
    """Проверить валидность предложения обмена"""
    from_player_id = trade_offer["from_player"]
    to_player_id = trade_offer["to_player"]
    
    # Находим игроков
    from_player = None
    to_player = None
    
    for player in game["players"]:
        if player["id"] == from_player_id:
            from_player = player
        if player["id"] == to_player_id:
            to_player = player
    
    if not from_player or not to_player:
        return False, "Игрок не найден"
    
    # Проверяем деньги у отправителя
    if from_player.get("balance", 0) < trade_offer["money_offer"]:
        return False, f"У {from_player['name']} недостаточно денег"
    
    # Проверяем деньги у получателя
    if to_player.get("balance", 0) < trade_offer["money_request"]:
        return False, f"У {to_player['name']} недостаточно денег"
    
    # Проверяем недвижимость у отправителя
    for prop_id in trade_offer["properties_offer"]:
        if prop_id not in game["properties"]:
            return False, f"Недвижимость {prop_id} не существует"
        
        prop = game["properties"][prop_id]
        if prop.get("owner") != from_player_id:
            return False, f"У {from_player['name']} нет недвижимости {BOARD[prop_id][0]}"
        
        # Проверяем, что недвижимость не заложена и без построек
        if prop.get("mortgaged", False):
            return False, f"Недвижимость {BOARD[prop_id][0]} заложена"
        
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            return False, f"На недвижимости {BOARD[prop_id][0]} есть постройки"
    
    # Проверяем недвижимость у получателя
    for prop_id in trade_offer["properties_request"]:
        if prop_id not in game["properties"]:
            return False, f"Недвижимость {prop_id} не существует"
        
        prop = game["properties"][prop_id]
        if prop.get("owner") != to_player_id:
            return False, f"У {to_player['name']} нет недвижимости {BOARD[prop_id][0]}"
        
        # Проверяем, что недвижимость не заложена и без построек
        if prop.get("mortgaged", False):
            return False, f"Недвижимость {BOARD[prop_id][0]} заложена"
        
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            return False, f"На недвижимости {BOARD[prop_id][0]} есть постройки"
    
    return True, "Предложение валидно"

def execute_trade(trade_offer: Dict, game: Dict) -> Tuple[bool, str]:
    """Выполнить обмен"""
    # Проверяем валидность
    valid, message = validate_trade_offer(trade_offer, game)
    if not valid:
        return False, message
    
    from_player_id = trade_offer["from_player"]
    to_player_id = trade_offer["to_player"]
    
    # Обмен деньгами
    for player in game["players"]:
        if player["id"] == from_player_id:
            player["balance"] -= trade_offer["money_offer"]
            player["balance"] += trade_offer["money_request"]
        
        if player["id"] == to_player_id:
            player["balance"] -= trade_offer["money_request"]
            player["balance"] += trade_offer["money_offer"]
    
    # Обмен недвижимостью
    for prop_id in trade_offer["properties_offer"]:
        game["properties"][prop_id]["owner"] = to_player_id
    
    for prop_id in trade_offer["properties_request"]:
        game["properties"][prop_id]["owner"] = from_player_id
    
    return True, "Обмен успешно выполнен"

# ==================== ОБРАБОТКА ХОДА ====================
async def process_player_turn(chat_id: int, game: Dict, player: Dict, dice_result: Tuple[int, int]) -> str:
    """Обработать ход игрока"""
    dice1, dice2 = dice_result
    total = dice1 + dice2
    
    result_text = f"🎲 <b>{player['name']} бросает кубики:</b>\n"
    result_text += f"🎯 {get_dice_emoji(dice1)} Кубик 1: <b>{dice1}</b>\n"
    result_text += f"🎯 {get_dice_emoji(dice2)} Кубик 2: <b>{dice2}</b>\n"
    result_text += f"📊 Сумма: <b>{total}</b>\n"
    
    # Обработка тюрьмы
    jail_result = handle_jail_mechanic(player, game)
    if jail_result and "Вы в тюрьме" in jail_result:
        result_text += f"\n{jail_result}"
        return result_text
    
    # Если игрок в тюрьме, но может выйти
    if player.get("in_jail", False):
        if dice1 == dice2:  # Дубль - выход из тюрьмы
            player["in_jail"] = False
            player["jail_turns"] = 0
            result_text += f"\n🎉 Вы вышли из тюрьмы с дублем!\n"
        else:
            result_text += f"\n{jail_result}"
            return result_text
    
    # Обновляем позицию
    current_pos = player.get("position", 0)
    new_pos = (current_pos + total) % 40
    player["position"] = new_pos
    
    result_text += f"📍 Позиция: {current_pos} → <b>{new_pos}</b>\n"
    
    # Обработка клетки
    if new_pos in BOARD:
        cell_name, price, rent, cell_type = BOARD[new_pos]
        result_text += f"\n🏠 <b>{cell_name}</b>\n"
        
        if cell_type in ["SPECIAL", "TAX", "JAIL", "PARKING", "GO_TO_JAIL", "CHANCE", "CHEST"]:
            result_text += await handle_special_cell(chat_id, game, player, new_pos, cell_type)
        elif cell_type in ["BROWN", "BLUE", "PINK", "ORANGE", "RED", "YELLOW", "GREEN", "DARKBLUE", "RAIL", "UTIL"]:
            result_text += await handle_property_cell(game, player, new_pos, cell_name, price, rent, cell_type)
    
    return result_text

async def handle_special_cell(chat_id: int, game: Dict, player: Dict, position: int, cell_type: str) -> str:
    """Обработка специальных клеток"""
    result = ""
    
    if cell_type == "START":
        # СТАРТ
        player["balance"] = player.get("balance", 1500) + 200
        result += f"🏁 <b>СТАРТ!</b> +200$\n💵 Баланс: {player['balance']}$\n"
    
    elif cell_type == "TAX":
        # Налог
        tax_amount = BOARD[position][1]
        player["balance"] = player.get("balance", 1500) + tax_amount  # tax_amount отрицательный
        result += f"💸 <b>Налог!</b> {tax_amount}$\n💵 Баланс: {player['balance']}$\n"
    
    elif cell_type == "GO_TO_JAIL":
        # Отправка в тюрьму
        player["in_jail"] = True
        player["position"] = 10  # Тюрьма
        player["jail_turns"] = 0
        result += f"🚓 <b>Отправляйтесь в тюрьму!</b>\n"
    
    elif cell_type == "CHANCE":
        # Шанс
        card, effect = draw_chance_card(game)
        result += f"🎲 <b>Шанс:</b> {card}\n"
        
        # Применяем эффект
        if effect["money"] != 0:
            player["balance"] = player.get("balance", 1500) + effect["money"]
            result += f"💵 Изменение баланса: {effect['money']}$\n"
        
        if effect["move"] != 0:
            if effect["move"] == "start":
                player["position"] = 0
                player["balance"] = player.get("balance", 1500) + 200
                result += f"📍 Перемещение к СТАРТУ +200$\n"
            else:
                new_pos = (player["position"] + effect["move"]) % 40
                player["position"] = new_pos
                result += f"📍 Перемещение на {effect['move']} клеток\n"
                # Обрабатываем новую клетку
                if new_pos in BOARD:
                    cell_name = BOARD[new_pos][0]
                    result += f"🏠 Новая клетка: <b>{cell_name}</b>\n"
        
        if effect["jail"]:
            player["in_jail"] = True
            player["position"] = 10
            player["jail_turns"] = 0
            result += f"🚓 Отправка в тюрьму!\n"
    
    elif cell_type == "CHEST":
        # Общественная казна
        card, effect = draw_chest_card(game)
        result += f"💰 <b>Общественная казна:</b> {card}\n"
        
        if effect["money"] != 0:
            player["balance"] = player.get("balance", 1500) + effect["money"]
            result += f"💵 Изменение баланса: {effect['money']}$\n"
    
    elif cell_type == "PARKING":
        # Бесплатная стоянка
        result += f"🅿️ <b>Бесплатная стоянка</b>\nОтдыхайте!\n"
    
    return result

async def handle_property_cell(game: Dict, player: Dict, position: int, 
                              cell_name: str, price: int, rent: int, cell_type: str) -> str:
    """Обработка клеток с недвижимостью"""
    result = ""
    
    if position not in game.get("properties", {}):
        # Свободная недвижимость
        if player.get("balance", 1500) >= price:
            result += f"💰 Цена: {price}$\n🎨 Тип: {cell_type}\n"
            result += f"❓ <b>Свободная недвижимость!</b>\n"
            result += f"Хотите купить {cell_name} за {price}$?\n"
            result += f"Напишите 'купить {position}' или 'пропустить'"
        else:
            result += f"💰 Цена: {price}$ (недостаточно денег)\n"
    else:
        # Недвижимость с владельцем
        prop = game["properties"][position]
        owner_id = prop.get("owner")
        
        if owner_id == player["id"]:
            result += f"✅ <b>Ваша собственность</b>\n"
            
            # Показываем информацию о постройках
            houses = prop.get("houses", 0)
            hotel = prop.get("hotel", False)
            mortgaged = prop.get("mortgaged", False)
            
            if mortgaged:
                result += f"⚠️ <b>Заложена</b>\n"
            elif hotel:
                result += f"🏨 <b>Отель</b>\n"
                result += f"💰 Аренда: {prop.get('current_rent', rent)}$\n"
            elif houses > 0:
                result += f"🏠 <b>Дома: {houses}/4</b>\n"
                result += f"💰 Аренда: {prop.get('current_rent', rent)}$\n"
            else:
                result += f"💰 Базовая аренда: {rent}$\n"
        else:
            # Находим владельца
            owner_name = ""
            for p in game["players"]:
                if p["id"] == owner_id:
                    owner_name = p["name"]
                    break
            
            result += f"👤 Владелец: <b>{owner_name}</b>\n"
            
            # Проверяем залог
            if prop.get("mortgaged", False):
                result += f"⚠️ <b>Недвижимость заложена</b>\n"
                result += f"💰 Аренда не взимается\n"
            else:
                # Расчет аренды
                current_rent = prop.get("current_rent", rent)
                
                # Особые случаи
                if cell_type == "RAIL":
                    # Железные дороги: 25$ за первую, 50$ за вторую, 100$ за третью, 200$ за четвертую
                    rail_count = 0
                    for prop_id in COLOR_GROUPS["RAIL"]:
                        if prop_id in game["properties"]:
                            if game["properties"][prop_id].get("owner") == owner_id:
                                rail_count += 1
                    
                    if rail_count == 1:
                        current_rent = 25
                    elif rail_count == 2:
                        current_rent = 50
                    elif rail_count == 3:
                        current_rent = 100
                    elif rail_count == 4:
                        current_rent = 200
                
                elif cell_type == "UTIL":
                    # Коммунальные услуги: 4x если одна, 10x если две
                    util_count = 0
                    for prop_id in COLOR_GROUPS["UTIL"]:
                        if prop_id in game["properties"]:
                            if game["properties"][prop_id].get("owner") == owner_id:
                                util_count += 1
                    
                    dice1, dice2 = 0, 0  # Временные значения для расчета
                    if util_count == 1:
                        current_rent = (dice1 + dice2) * 4
                    elif util_count == 2:
                        current_rent = (dice1 + dice2) * 10
                
                # Списание аренды
                player["balance"] = player.get("balance", 1500) - current_rent
                
                # Добавление аренды владельцу
                for p in game["players"]:
                    if p["id"] == owner_id:
                        p["balance"] = p.get("balance", 1500) + current_rent
                        break
                
                result += f"💸 <b>Аренда: {current_rent}$</b>\n"
                result += f"💰 Ваш баланс: {player['balance']}$\n"
    
    return result

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ"""
    try:
        # Проверяем тип чата - отвечаем ТОЛЬКО в ЛС
        if message.chat.type not in ["private"]:
            await message.answer(
                "👋 Для управления игрой используйте команду /monopoly в этой группе",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
            f"✨ Premium Edition v3.0\n\n"
            f"Разработчик: {DEV_TAG}",
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=False)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.message(Command("monopoly"))
async def cmd_monopoly(message: types.Message):
    """Главная команда - ТОЛЬКО в группах"""
    try:
        # ПЕРВОЕ ДЕЛО - проверяем режим обслуживания
        if STATS.get("maintenance_mode", False):
            await message.answer(
                f"⚠️ {MAINTENANCE_MSG}\n\n"
                f"👑 Темный Принц уже исправляет это ♥️♥️",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем тип чата - отвечаем ТОЛЬКО в группах
        if message.chat.type not in ["group", "supergroup"]:
            await message.answer(
                "👋 <b>Эту команду можно использовать только в группах!</b>\n\n"
                f"Добавьте бота в группу и используйте /monopoly там.\n"
                f"Разработчик: {DEV_TAG}",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем, скрыл ли пользователь меню
        user_id = message.from_user.id
        if user_id in HIDDEN_MENU_USERS:
            # Пользователь скрыл меню - показываем inline версию
            await show_inline_menu(message)
            return
        
        header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition v3.0</b>\n👑 Версия Темного Принца\n\n"
        header += "🎮 <b>Доступные действия:</b>"
        
        await message.answer(
            header,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_monopoly: {e}")
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

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
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Проверяем, участвует ли пользователь в игре
        game = ACTIVE_GAMES[chat_id]
        player_exists = any(p["id"] == user_id for p in game.get("players", []))
        
        if not player_exists:
            await message.answer(
                "❌ <b>Вы не участвуете в этой игре!</b>\n\n"
                "Только игроки могут скрывать меню",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда для просмотра статистики"""
    try:
        user_id = message.from_user.id
        
        if user_id not in USER_STATS:
            await message.answer(
                "📊 <b>Статистика игрока</b>\n\n"
                "У вас еще нет статистики. Сыграйте свою первую игру!",
                parse_mode="HTML"
            )
            return
        
        stats = USER_STATS[user_id]
        win_rate = (stats["games_won"] / stats["games_played"]) * 100 if stats["games_played"] > 0 else 0
        
        stats_text = (
            f"📊 <b>Статистика игрока {stats['name']}</b>\n\n"
            f"🎮 Сыграно игр: <b>{stats['games_played']}</b>\n"
            f"🏆 Побед: <b>{stats['games_won']}</b>\n"
            f"📈 Процент побед: <b>{win_rate:.1f}%</b>\n"
            f"💰 Всего денег: <b>{stats.get('total_money', 0)}$</b>\n"
            f"🏠 Куплено недвижимости: <b>{stats.get('properties_bought', 0)}</b>\n"
            f"📅 Последняя игра: <b>{stats.get('last_played', 'никогда')}</b>"
        )
        
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")

async def show_inline_menu(message: types.Message, for_user_only: bool = False):
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
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
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
        await message.answer(
            f"🤖 {MAINTENANCE_MSG}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

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
        
        # Бросаем кубики с анимацией
        dice1, dice2 = await send_dice_animation(chat_id, current_player["name"])
        
        # Обрабатываем ход
        result_text = await process_player_turn(chat_id, game, current_player, (dice1, dice2))
        
        # Проверяем банкротство
        if current_player.get("balance", 1500) < 0:
            result_text += f"\n💀 <b>БАНКРОТ!</b> {current_player['name']} выбывает из игры!\n"
            
            # Удаляем игрока
            game["players"] = [p for p in game["players"] if p["id"] != user_id]
            
            # Освобождаем его недвижимость
            properties_to_free = []
            for prop_id, prop_info in game.get("properties", {}).items():
                if prop_info.get("owner") == user_id:
                    properties_to_free.append(prop_id)
            
            for prop_id in properties_to_free:
                del game["properties"][prop_id]
            
            # Обновляем статистику
            update_user_stats(user_id, message.from_user.username, message.from_user.first_name, win=False)
            
            # Проверяем конец игры
            if len(game["players"]) == 1:
                winner = game["players"][0]
                result_text += f"\n🏆 <b>ИГРА ОКОНЧЕНА!</b>\n"
                result_text += f"🎉 Победитель: {winner['name']}!\n"
                
                # Обновляем статистику победителя
                update_user_stats(winner["id"], "", winner["name"], win=True)
                
                # Удаляем игру
                del ACTIVE_GAMES[chat_id]
                
                await message.answer(result_text, parse_mode="HTML")
                return
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx] if game["players"] else None
        
        if next_player:
            result_text += f"\n➡️ <b>Следующий: {next_player['name']}</b>"
        
        await message.answer(result_text, parse_mode="HTML")
        
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
        
        # Находим недвижимость игрока, на которой можно строить
        buildable_properties = []
        for prop_id in player.get("properties", []):
            if prop_id in game["properties"]:
                prop = game["properties"][prop_id]
                if prop.get("owner") == user_id and not prop.get("mortgaged", False):
                    # Проверяем цветовую группу
                    color = BOARD[prop_id][3]
                    if color in COLOR_GROUPS:
                        # Проверяем, что у игрока все улицы этого цвета
                        has_all = True
                        for group_prop_id in COLOR_GROUPS[color]:
                            if group_prop_id not in game["properties"]:
                                has_all = False
                                break
                            if game["properties"][group_prop_id].get("owner") != user_id:
                                has_all = False
                                break
                        
                        if has_all:
                            buildable_properties.append(prop_id)
        
        if not buildable_properties:
            await message.answer(
                "❌ <b>Нет доступной недвижимости для строительства!</b>\n\n"
                "Для строительства необходимо:\n"
                "1. Иметь все улицы одного цвета\n"
                "2. Недвижимость не должна быть заложена\n"
                "3. На балансе должны быть средства",
                parse_mode="HTML"
            )
            return
        
        # Показываем список доступной недвижимости
        properties_list = ""
        for prop_id in buildable_properties:
            prop_name = BOARD[prop_id][0]
            houses = game["properties"][prop_id].get("houses", 0)
            hotel = game["properties"][prop_id].get("hotel", False)
            
            properties_list += f"• {prop_name} "
            if hotel:
                properties_list += f"(🏨 Отель)\n"
            else:
                properties_list += f"(🏠 {houses}/4)\n"
        
        await message.answer(
            f"🏗️ <b>Доступная для строительства недвижимость:</b>\n\n"
            f"{properties_list}\n"
            f"📝 Для строительства используйте команду:\n"
            f"/build [номер_улицы]\n"
            f"Например: /build 1",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в build_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("build"))
async def cmd_build(message: types.Message):
    """Команда для строительства"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /build [номер_улицы]\n"
                "Например: /build 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что недвижимость не заложена
        if prop.get("mortgaged", False):
            await message.answer("❌ Невозможно строить на заложенной недвижимости!")
            return
        
        # Показываем меню строительства
        prop_name = BOARD[property_id][0]
        houses = prop.get("houses", 0)
        hotel = prop.get("hotel", False)
        
        info_text = f"🏠 <b>{prop_name}</b>\n"
        
        if hotel:
            info_text += "🏨 Отель построен\n"
        else:
            info_text += f"🏠 Дома: {houses}/4\n"
        
        # Показываем стоимость
        color = BOARD[property_id][3]
        if color in BUILDING_COSTS:
            house_cost = BUILDING_COSTS[color]["house"]
            hotel_cost = BUILDING_COSTS[color]["hotel"]
            info_text += f"💰 Стоимость дома: {house_cost}$\n"
            info_text += f"💰 Стоимость отеля: {hotel_cost}$\n"
        
        await message.answer(
            info_text,
            parse_mode="HTML",
            reply_markup=build_property_kb(property_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_build: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "📊 Мои активы")
async def show_assets_button(message: types.Message):
    """Кнопка показа активов"""
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
        
        # Собираем информацию
        balance = player.get("balance", 1500)
        position = player.get("position", 0)
        in_jail = player.get("in_jail", False)
        
        # Недвижимость игрока
        properties = []
        mortgaged_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                prop_name = BOARD[prop_id][0]
                houses = prop_info.get("houses", 0)
                hotel = prop_info.get("hotel", False)
                mortgaged = prop_info.get("mortgaged", False)
                
                prop_info_str = f"• {prop_name}"
                
                if mortgaged:
                    prop_info_str += " ⚠️ (заложена)"
                    mortgaged_properties.append(prop_info_str)
                elif hotel:
                    prop_info_str += f" 🏨 (отель)"
                    properties.append(prop_info_str)
                elif houses > 0:
                    prop_info_str += f" 🏠 ({houses}/4)"
                    properties.append(prop_info_str)
                else:
                    properties.append(prop_info_str)
        
        assets_text = (
            f"💰 <b>Активы {player['name']}</b>\n\n"
            f"💵 Баланс: <b>{balance}$</b>\n"
            f"📍 Позиция: <b>{position}</b>\n"
        )
        
        if in_jail:
            jail_turns = player.get("jail_turns", 0)
            assets_text += f"⛓️ В тюрьме: <b>ход {jail_turns}/3</b>\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(properties) + len(mortgaged_properties)} объектов</b>\n"
        
        if properties:
            assets_text += "\n📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties:
                assets_text += f"{prop}\n"
        
        if mortgaged_properties:
            assets_text += "\n⚠️ <b>Заложенная недвижимость:</b>\n"
            for prop in mortgaged_properties:
                assets_text += f"{prop}\n"
        
        await message.answer(assets_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в show_assets_button: {e}")
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
        player = next((p for p in game.get("players", []) if p["id"] == user_id), None)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Получаем список других игроков
        other_players = [p for p in game["players"] if p["id"] != user_id]
        
        if not other_players:
            await message.answer(
                "❌ <b>Недостаточно игроков для торговли!</b>\n\n"
                "Нужно минимум 2 игрока в игре",
                parse_mode="HTML"
            )
            return
        
        # Показываем список игроков для торговли
        players_list = ""
        for idx, other_player in enumerate(other_players, 1):
            players_list += f"{idx}. {other_player['name']}\n"
        
        await message.answer(
            "🤝 <b>Выберите игрока для торговли:</b>\n\n"
            f"{players_list}\n"
            f"📝 Используйте команду:\n"
            f"/trade [номер_игрока]\n"
            f"Например: /trade 1",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в trade_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("trade"))
async def cmd_trade(message: types.Message):
    """Команда для начала торговли"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер игрока
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /trade [номер_игрока]\n"
                "Например: /trade 1",
                parse_mode="HTML"
            )
            return
        
        try:
            player_num = int(args[1])
        except ValueError:
            await message.answer("❌ Номер игрока должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Находим текущего игрока
        from_player = next((p for p in game["players"] if p["id"] == user_id), None)
        if not from_player:
            await message.answer("❌ Вы не участвуете в этой игре!")
            return
        
        # Находим целевого игрока
        other_players = [p for p in game["players"] if p["id"] != user_id]
        if player_num < 1 or player_num > len(other_players):
            await message.answer("❌ Неверный номер игрока!")
            return
        
        target_player = other_players[player_num - 1]
        
        # Показываем меню торговли
        await message.answer(
            f"🤝 <b>Торговля с {target_player['name']}</b>\n\n"
            f"💰 Ваш баланс: {from_player.get('balance', 1500)}$\n"
            f"💰 Баланс {target_player['name']}: {target_player.get('balance', 1500)}$\n\n"
            f"👇 Выберите тип предложения:",
            parse_mode="HTML",
            reply_markup=trade_kb(user_id, target_player["id"])
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_trade: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "💵 Заложить улицу")
async def mortgage_button(message: types.Message):
    """Кнопка залога улицы"""
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
        
        # Находим недвижимость игрока, которую можно заложить
        mortgageable_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                # Нельзя заложить, если есть постройки
                if prop_info.get("houses", 0) == 0 and not prop_info.get("hotel", False):
                    # Проверяем, не заложена ли уже
                    if not prop_info.get("mortgaged", False):
                        mortgageable_properties.append(prop_id)
        
        if not mortgageable_properties:
            await message.answer(
                "❌ <b>Нет доступной недвижимости для залога!</b>\n\n"
                "Для залога необходимо:\n"
                "1. Иметь недвижимость без построек\n"
                "2. Недвижимость не должна быть уже заложена",
                parse_mode="HTML"
            )
            return
        
        # Показываем список доступной недвижимости
        properties_list = ""
        for prop_id in mortgageable_properties:
            prop_name = BOARD[prop_id][0]
            price = BOARD[prop_id][1]
            mortgage_value = price // 2  # 50% от стоимости
            properties_list += f"• {prop_name} (стоимость: {price}$, залог: {mortgage_value}$)\n"
        
        await message.answer(
            f"💵 <b>Доступная для залога недвижимость:</b>\n\n"
            f"{properties_list}\n"
            f"📝 Для залога используйте команду:\n"
            f"/mortgage [номер_улицы]\n"
            f"Например: /mortgage 1\n\n"
            f"💡 Вы получите 50% от стоимости недвижимости",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в mortgage_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

@dp.message(Command("mortgage"))
async def cmd_mortgage(message: types.Message):
    """Команда для залога недвижимости"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /mortgage [номер_улицы]\n"
                "Например: /mortgage 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что на недвижимости нет построек
        if prop.get("houses", 0) > 0 or prop.get("hotel", False):
            await message.answer("❌ Невозможно заложить недвижимость с постройками!")
            return
        
        # Проверяем, что недвижимость не заложена
        if prop.get("mortgaged", False):
            await message.answer("❌ Эта недвижимость уже заложена!")
            return
        
        # Закладываем недвижимость
        success, message_text, mortgage_value = mortgage_property(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
        
        await message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_mortgage: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(Command("unmortgage"))
async def cmd_unmortgage(message: types.Message):
    """Команда для выкупа недвижимости из залога"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        # Получаем номер улицы
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "Используйте: /unmortgage [номер_улицы]\n"
                "Например: /unmortgage 1",
                parse_mode="HTML"
            )
            return
        
        try:
            property_id = int(args[1])
        except ValueError:
            await message.answer("❌ Номер улицы должен быть числом!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что недвижимость существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что игрок владеет этой недвижимостью
        if property_id not in game.get("properties", {}):
            await message.answer("❌ Эта улица не куплена!")
            return
        
        prop = game["properties"][property_id]
        if prop.get("owner") != user_id:
            await message.answer("❌ Вы не владеете этой улицей!")
            return
        
        # Проверяем, что недвижимость заложена
        if not prop.get("mortgaged", False):
            await message.answer("❌ Эта недвижимость не заложена!")
            return
        
        # Выкупаем недвижимость
        success, message_text, unmortgage_cost = unmortgage_property(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
        
        await message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_unmortgage: {e}")
        await message.answer("❌ Ошибка при обработке команды")

@dp.message(F.text == "🗺️ Показать карту")
async def show_map_button(message: types.Message):
    """Кнопка показа карты"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Создаем простую карту
        map_text = create_simple_map(game)
        
        # Добавляем информацию о текущем игроке
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if current_player:
            map_text += f"\n🎯 <b>Сейчас ходит: {current_player['name']}</b>"
        
        await message.answer(map_text, parse_mode="Markdown")
        
        # Также отправляем ссылку на интерактивную карту (если настроен веб-сервер)
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if domain and 'localhost' not in domain:
            map_url = generate_map_url(chat_id, game["players"])
            await message.answer(
                f"🗺️ <b>Интерактивная карта:</b>\n"
                f"🔗 {map_url}",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в show_map_button: {e}")
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
        
        # Бросаем кубики с анимацией
        dice1, dice2 = await send_dice_animation(chat_id, current_player["name"])
        
        # Обрабатываем ход
        result_text = await process_player_turn(chat_id, game, current_player, (dice1, dice2))
        
        # Проверяем банкротство
        if current_player.get("balance", 1500) < 0:
            result_text += f"\n💀 <b>БАНКРОТ!</b> {current_player['name']} выбывает из игры!\n"
            
            # Удаляем игрока
            game["players"] = [p for p in game["players"] if p["id"] != user_id]
            
            # Освобождаем его недвижимость
            properties_to_free = []
            for prop_id, prop_info in game.get("properties", {}).items():
                if prop_info.get("owner") == user_id:
                    properties_to_free.append(prop_id)
            
            for prop_id in properties_to_free:
                del game["properties"][prop_id]
            
            # Обновляем статистику
            update_user_stats(user_id, c.from_user.username, c.from_user.first_name, win=False)
            
            # Проверяем конец игры
            if len(game["players"]) == 1:
                winner = game["players"][0]
                result_text += f"\n🏆 <b>ИГРА ОКОНЧЕНА!</b>\n"
                result_text += f"🎉 Победитель: {winner['name']}!\n"
                
                # Обновляем статистику победителя
                update_user_stats(winner["id"], "", winner["name"], win=True)
                
                # Удаляем игру
                del ACTIVE_GAMES[chat_id]
                
                await c.message.edit_text(result_text, parse_mode="HTML")
                return
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx] if game["players"] else None
        
        if next_player:
            result_text += f"\n➡️ <b>Следующий: {next_player['name']}</b>"
        
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
        in_jail = player.get("in_jail", False)
        
        # Недвижимость игрока
        properties = []
        mortgaged_properties = []
        for prop_id, prop_info in game.get("properties", {}).items():
            if prop_info.get("owner") == user_id:
                prop_name = BOARD[prop_id][0]
                houses = prop_info.get("houses", 0)
                hotel = prop_info.get("hotel", False)
                mortgaged = prop_info.get("mortgaged", False)
                
                prop_info_str = f"• {prop_name}"
                
                if mortgaged:
                    prop_info_str += " ⚠️ (заложена)"
                    mortgaged_properties.append(prop_info_str)
                elif hotel:
                    prop_info_str += f" 🏨 (отель)"
                    properties.append(prop_info_str)
                elif houses > 0:
                    prop_info_str += f" 🏠 ({houses}/4)"
                    properties.append(prop_info_str)
                else:
                    properties.append(prop_info_str)
        
        assets_text = (
            f"💰 <b>Активы {player['name']}</b>\n\n"
            f"💵 Баланс: <b>{balance}$</b>\n"
            f"📍 Позиция: <b>{position}</b>\n"
        )
        
        if in_jail:
            jail_turns = player.get("jail_turns", 0)
            assets_text += f"⛓️ В тюрьме: <b>ход {jail_turns}/3</b>\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(properties) + len(mortgaged_properties)} объектов</b>\n"
        
        if properties:
            assets_text += "\n📋 <b>Ваша недвижимость:</b>\n"
            for prop in properties[:5]:  # Ограничиваем 5 свойствами
                assets_text += f"{prop}\n"
        
        if mortgaged_properties:
            assets_text += "\n⚠️ <b>Заложенная недвижимость:</b>\n"
            for prop in mortgaged_properties[:3]:  # Ограничиваем 3 свойствами
                assets_text += f"{prop}\n"
        
        if len(properties) > 5 or len(mortgaged_properties) > 3:
            assets_text += f"\n📄 <i>Используйте обычное меню для полного списка</i>"
        
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

@dp.callback_query(F.data == "inline_build")
async def inline_build(c: types.CallbackQuery):
    """Inline строительство"""
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
        
        # Находим недвижимость игрока, на которой можно строить
        buildable_properties = []
        for prop_id in player.get("properties", []):
            if prop_id in game["properties"]:
                prop = game["properties"][prop_id]
                if prop.get("owner") == user_id and not prop.get("mortgaged", False):
                    # Проверяем цветовую группу
                    color = BOARD[prop_id][3]
                    if color in COLOR_GROUPS:
                        # Проверяем, что у игрока все улицы этого цвета
                        has_all = True
                        for group_prop_id in COLOR_GROUPS[color]:
                            if group_prop_id not in game["properties"]:
                                has_all = False
                                break
                            if game["properties"][group_prop_id].get("owner") != user_id:
                                has_all = False
                                break
                        
                        if has_all:
                            buildable_properties.append(prop_id)
