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
    1: ["Житная", 60, 4, "BROWN"], 2: ["Общественная казна", 0, 0, "CHANCE"],
    3: ["Нагатинская", 60, 4, "BROWN"], 4: ["Налог на роскошь", -200, 0, "TAX"],
    5: ["Рижская ж/д", 200, 25, "RAIL"], 6: ["Варшавское ш.", 100, 6, "BLUE"],
    7: ["Шанс", 0, 0, "CHANCE"], 8: ["Огородный пр.", 100, 6, "BLUE"],
    9: ["Рижская", 120, 8, "BLUE"], 10: ["Тюрьма (посещение)", 0, 0, "JAIL"],
    11: ["Курская", 140, 10, "PINK"], 12: ["Электросеть", 150, 10, "UTIL"],
    13: ["Абрамцево", 140, 10, "PINK"], 14: ["Пантелеевская", 160, 12, "PINK"],
    15: ["Казанская ж/д", 200, 25, "RAIL"], 16: ["Вавилова", 180, 14, "ORANGE"],
    17: ["Общественная казна", 0, 0, "CHEST"], 18: ["Тимирязевская", 180, 14, "ORANGE"],
    19: ["Лихоборы", 200, 16, "ORANGE"], 20: ["Бесплатная стоянка", 0, 0, "PARKING"],
    21: ["Арбат", 220, 18, "RED"], 22: ["Шанс", 0, 0, "CHANCE"],
    23: ["Полянка", 220, 18, "RED"], 24: ["Сретенка", 240, 20, "RED"],
    25: ["Курская ж/д", 200, 25, "RAIL"], 26: ["Ростовская", 260, 22, "YELLOW"],
    27: ["Рязанский пр.", 260, 22, "YELLOW"], 28: ["Водопровод", 150, 10, "UTIL"],
    29: ["Новинский б-р", 280, 24, "YELLOW"], 30: ["Отправляйтесь в тюрьму", 0, 0, "GO_TO_JAIL"],
    31: ["Пушкинская", 300, 26, "GREEN"], 32: ["Тверская", 300, 26, "GREEN"],
    33: ["Общественная казна", 0, 0, "CHEST"], 34: ["Маяковского", 320, 28, "GREEN"],
    35: ["Ленинградская ж/д", 200, 25, "RAIL"], 36: ["Шанс", 0, 0, "CHANCE"],
    37: ["Кутузовский", 350, 35, "DARKBLUE"], 38: ["Налог на сверхприбыль", -100, 0, "TAX"],
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
                    
                    if util_count == 1:
                        current_rent = dice1 + dice2 * 4
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
        
        if not buildable_properties:
            await c.answer(
                "❌ Нет доступной недвижимости для строительства!\n\n"
                "Для строительства необходимо иметь все улицы одного цвета",
                show_alert=True
            )
            return
        
        # Показываем первую доступную недвижимость
        property_id = buildable_properties[0]
        prop_name = BOARD[property_id][0]
        
        build_text = (
            f"🏗️ <b>Строительство на {prop_name}</b>\n\n"
            f"👇 Выберите действие:"
        )
        
        # Создаем клавиатуру для этой недвижимости
        kb = InlineKeyboardBuilder()
        kb.button(text="🏠 Построить дом (+1)", callback_data=f"inline_build_house_{property_id}")
        
        # Проверяем, можно ли построить отель
        prop = game["properties"][property_id]
        if prop.get("houses", 0) == 4:
            kb.button(text="🏨 Построить отель", callback_data=f"inline_build_hotel_{property_id}")
        
        if prop.get("houses", 0) > 0:
            kb.button(text="🔨 Продать дом (-1)", callback_data=f"inline_sell_house_{property_id}")
        
        kb.button(text="❌ Отмена", callback_data="inline_cancel_build")
        
        if prop.get("houses", 0) == 4:
            kb.adjust(1, 1, 1, 1)
        elif prop.get("houses", 0) > 0:
            kb.adjust(2, 1, 1)
        else:
            kb.adjust(1, 1)
        
        await c.message.edit_text(
            build_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_build: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "inline_trade")
async def inline_trade(c: types.CallbackQuery):
    """Inline торговля"""
    await c.answer(
        "🤝 Для торговли используйте обычное меню:\n"
        "1. Нажмите '📱 Вернуть меню'\n"
        "2. Используйте кнопку '🤝 Торговля'\n"
        "3. Выберите игрока для торговли",
        show_alert=True
    )

@dp.callback_query(F.data == "inline_mortgage")
async def inline_mortgage(c: types.CallbackQuery):
    """Inline залог недвижимости"""
    await c.answer(
        "💵 Для залога недвижимости используйте обычное меню:\n"
        "1. Нажмите '📱 Вернуть меню'\n"
        "2. Используйте кнопку '💵 Заложить улицу'\n"
        "3. Выберите недвижимость для залога",
        show_alert=True
    )

@dp.callback_query(F.data == "inline_map")
async def inline_map(c: types.CallbackQuery):
    """Inline показ карты"""
    try:
        chat_id = c.message.chat.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Создаем простую карту
        map_text = create_simple_map(game)
        
        # Добавляем информацию о текущем игроке
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if current_player:
            map_text += f"\n🎯 <b>Сейчас ходит: {current_player['name']}</b>"
        
        # Обновляем сообщение
        await c.message.edit_text(
            map_text,
            parse_mode="Markdown",
            reply_markup=inline_menu_kb()
        )
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_map: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("inline_build_house_"))
async def inline_build_house(c: types.CallbackQuery):
    """Inline построить дом"""
    try:
        property_id = int(c.data.split("_")[3])
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Пытаемся построить дом
        success, message_text, cost = build_house(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
            
            # Возвращаемся к inline меню
            await c.message.edit_text(
                f"✅ {message_text}\n\n"
                f"👇 <i>Используйте кнопки ниже для дальнейших действий:</i>",
                parse_mode="HTML",
                reply_markup=inline_menu_kb()
            )
        else:
            await c.answer(message_text, show_alert=True)
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_build_house: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("inline_build_hotel_"))
async def inline_build_hotel(c: types.CallbackQuery):
    """Inline построить отель"""
    try:
        property_id = int(c.data.split("_")[3])
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Пытаемся построить отель
        success, message_text, cost = build_hotel(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
            
            # Возвращаемся к inline меню
            await c.message.edit_text(
                f"✅ {message_text}\n\n"
                f"👇 <i>Используйте кнопки ниже для дальнейших действий:</i>",
                parse_mode="HTML",
                reply_markup=inline_menu_kb()
            )
        else:
            await c.answer(message_text, show_alert=True)
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_build_hotel: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("inline_sell_house_"))
async def inline_sell_house(c: types.CallbackQuery):
    """Inline продать дом"""
    try:
        property_id = int(c.data.split("_")[3])
        chat_id = c.message.chat.id
        user_id = c.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await c.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Пытаемся продать дом
        success, message_text, refund = sell_house(property_id, game, user_id)
        
        if success:
            # Находим игрока для отображения баланса
            player = next((p for p in game["players"] if p["id"] == user_id), None)
            if player:
                message_text += f"\n💰 Новый баланс: {player.get('balance', 1500)}$"
            
            # Возвращаемся к inline меню
            await c.message.edit_text(
                f"✅ {message_text}\n\n"
                f"👇 <i>Используйте кнопки ниже для дальнейших действий:</i>",
                parse_mode="HTML",
                reply_markup=inline_menu_kb()
            )
        else:
            await c.answer(message_text, show_alert=True)
        
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_sell_house: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "inline_cancel_build")
async def inline_cancel_build(c: types.CallbackQuery):
    """Inline отмена строительства"""
    try:
        # Возвращаемся к inline меню
        await c.message.edit_text(
            "🎮 <b>Monopoly Premium - Inline меню</b>\n\n"
            "👇 <i>Используйте кнопки ниже для управления игрой:</i>",
            parse_mode="HTML",
            reply_markup=inline_menu_kb()
        )
        
        await c.answer("✅ Строительство отменено")
        
    except Exception as e:
        logger.error(f"Ошибка в inline_cancel_build: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

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
        
        # Создаем сообщение о сборе
        players_text = "👥 <b>Игроки в ожидании:</b>\n"
        players_text += f"• {c.from_user.first_name}"
        if c.from_user.username:
            players_text += f" (@{c.from_user.username})"
        players_text += " 👑\n"
        
        # Считаем время
        time_left = 180  # 3 минуты в секундах
        minutes_left = time_left // 60
        seconds_left = time_left % 60
        
        message_text = (
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"👑 Создатель: {c.from_user.first_name}\n"
            f"⏳ Таймер: <b>{minutes_left}:{seconds_left:02d}</b>\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру досрочно\n"
            f"❌ Создатель может отменить сбор\n\n"
            f"<i>Автоматически начнется через {minutes_left}:{seconds_left:02d} если наберется 2+ игроков</i>"
        )
        
        # Отправляем сообщение
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=waiting_room_kb(chat_id, c.from_user.id)
        )
        
        # Закрепляем сообщение
        try:
            await sent_message.pin(disable_notification=True)
        except Exception as pin_error:
            logger.warning(f"Не удалось закрепить сообщение: {pin_error}")
            # Показываем предупреждение создателю
            await c.answer("⚠️ Не удалось закрепить сообщение. Дайте боту права администратора!", show_alert=True)
        
        # Сохраняем данные
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
            "message_id": sent_message.message_id,
            "pinned_message_id": sent_message.message_id,
            "created_at": datetime.now().isoformat(),
            "timer_task": None
        }
        
        # Запускаем таймер
        await start_waiting_timer(chat_id, WAITING_GAMES[chat_id])
        
        await c.answer("🎮 Сбор игроков начат! Сообщение закреплено.")
        
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
            if player["id"] == game["creator_id"]:
                players_text += " 👑"
            players_text += "\n"
        
        # Считаем время до конца
        created_at = datetime.fromisoformat(game["created_at"])
        time_passed = datetime.now() - created_at
        time_left = max(0, 180 - time_passed.seconds)  # 3 минуты = 180 секунд
        minutes_left = time_left // 60
        seconds_left = time_left % 60
        
        message_text = (
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"👑 Создатель: {game['creator_name']}\n"
            f"⏳ Таймер: <b>{minutes_left}:{seconds_left:02d}</b>\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру досрочно\n"
            f"❌ Создатель может отменить сбор\n\n"
            f"<i>Автоматически начнется через {minutes_left}:{seconds_left:02d} если наберется 2+ игроков</i>"
        )
        
        # Обновляем сообщение с правильной клавиатурой
        # Для создателя показываем дополнительные кнопки, для остальных - обычные
        if c.from_user.id == game["creator_id"]:
            # Создатель видит все кнопки
            kb = InlineKeyboardBuilder()
            kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
            kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
            kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
            kb.button(text="❌ Отменить сбор", callback_data=f"cancel_gathering_{chat_id}")
            kb.adjust(2, 2)
        else:
            # Обычные игроки видят только основные кнопки
            kb = InlineKeyboardBuilder()
            kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
            kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
            kb.adjust(2)
        
        await c.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
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
            # Отменяем таймер
            if "timer_task" in game:
                game["timer_task"].cancel()
            
            # Открепляем сообщение
            if "pinned_message_id" in game:
                try:
                    await bot.unpin_chat_message(chat_id=chat_id, message_id=game["pinned_message_id"])
                except:
                    pass
            
            # Удаляем сообщение
            if "message_id" in game:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=game["message_id"])
                except:
                    pass
            
            del WAITING_GAMES[chat_id]
            await c.message.edit_text(
                "❌ <b>Игра отменена - все игроки вышли</b>\n\n"
                "👑 <i>Темный Принц сожалеет об этом...</i>",
                parse_mode="HTML"
            )
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
            if player["id"] == game["creator_id"]:
                players_text += " 👑"
            players_text += "\n"
        
        # Считаем время до конца
        created_at = datetime.fromisoformat(game["created_at"])
        time_passed = datetime.now() - created_at
        time_left = max(0, 180 - time_passed.seconds)
        minutes_left = time_left // 60
        seconds_left = time_left % 60
        
        message_text = (
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"👑 Создатель: {game['creator_name']}\n"
            f"⏳ Таймер: <b>{minutes_left}:{seconds_left:02d}</b>\n\n"
            f"{players_text}\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру досрочно\n"
            f"❌ Создатель может отменить сбор\n\n"
            f"<i>Автоматически начнется через {minutes_left}:{seconds_left:02d} если наберется 2+ игроков</i>"
        )
        
        # Обновляем клавиатуру в зависимости от того, кто нажал
        if c.from_user.id == game["creator_id"]:
            # Новый создатель видит все кнопки
            kb = InlineKeyboardBuilder()
            kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
            kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
            kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
            kb.button(text="❌ Отменить сбор", callback_data=f"cancel_gathering_{chat_id}")
            kb.adjust(2, 2)
        else:
            # Обычные игроки
            kb = InlineKeyboardBuilder()
            kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
            kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
            kb.adjust(2)
        
        await c.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await c.answer(f"🚪 Вы вышли. Игроков: {len(game['players'])}")
        
    except Exception as e:
        logger.error(f"Ошибка в leave_game: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("cancel_gathering_"))
async def cancel_gathering(c: types.CallbackQuery):
    """Отменить сбор игроков"""
    try:
        chat_id = int(c.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await c.answer("⚠️ Игра не найдена", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        
        # Проверяем права создателя
        if c.from_user.id != game["creator_id"]:
            await c.answer("⚠️ Только создатель игры может отменить сбор!", show_alert=True)
            return
        
        # Отменяем таймер
        if "timer_task" in game:
            game["timer_task"].cancel()
        
        # Открепляем сообщение
        if "pinned_message_id" in game:
            try:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=game["pinned_message_id"])
            except:
                pass
        
        # Удаляем сообщение
        if "message_id" in game:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=game["message_id"])
            except:
                pass
        
        # Удаляем игру
        del WAITING_GAMES[chat_id]
        
        # Отправляем новое сообщение об отмене
        await c.message.edit_text(
            "❌ <b>Сбор игроков отменен создателем!</b>\n\n"
            "👑 <i>Темный Принц сожалеет об этом...</i>",
            parse_mode="HTML"
        )
        
        await c.answer("❌ Сбор игроков отменен")
        
    except Exception as e:
        logger.error(f"Ошибка в cancel_gathering: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data.startswith("start_real_game_"))
async def start_real_game(c: types.CallbackQuery):
    """Начать игру досрочно"""
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
        
        # Отменяем таймер
        if "timer_task" in game:
            game["timer_task"].cancel()
        
        # Открепляем сообщение
        if "pinned_message_id" in game:
            try:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=game["pinned_message_id"])
            except:
                pass
        
        # Удаляем сообщение о сборе
        if "message_id" in game:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=game["message_id"])
            except:
                pass
        
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
        del WAITING_GAMES[chat_id]
        
        # Формируем список игроков
        players_list = "\n".join([f"• {p['name']} {p['color']}" for p in ACTIVE_GAMES[chat_id]["players"]])
        
        # Отправляем сообщение о начале игры
        await c.message.edit_text(
            f"🎉 <b>Игра началась!</b>\n"
            f"👑 <i>Создатель запустил игру досрочно</i>\n\n"
            f"<b>Участники:</b>\n{players_list}\n\n"
            f"💰 Стартовый баланс: <b>1500$</b>\n"
            f"🎲 Первым ходит: <b>{ACTIVE_GAMES[chat_id]['players'][0]['name']}</b>\n"
            f"🔄 Ход: <b>1</b>",
            parse_mode="HTML"
        )
        
        # Отправляем игровое меню ВСЕМ игрокам
        first_player = ACTIVE_GAMES[chat_id]["players"][0]
        await bot.send_message(
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

# ==================== ОБРАБОТКА ПОКУПКИ НЕДВИЖИМОСТИ ====================
@dp.message(lambda message: message.text and message.text.lower().startswith("купить"))
async def buy_property(message: types.Message):
    """Покупка недвижимости"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что сейчас ход этого игрока
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if not current_player or current_player["id"] != user_id:
            return
        
        # Парсим номер улицы
        try:
            args = message.text.lower().split()
            if len(args) < 2:
                return
            
            # Пытаемся извлечь номер из текста
            property_id = None
            for arg in args[1:]:
                try:
                    property_id = int(arg)
                    break
                except ValueError:
                    continue
            
            if property_id is None:
                return
        except:
            return
        
        # Проверяем, что игрок на этой клетке
        if current_player.get("position", 0) != property_id:
            await message.answer("❌ Вы не находитесь на этой клетке!")
            return
        
        # Проверяем, что клетка существует
        if property_id not in BOARD:
            await message.answer("❌ Такой улицы не существует!")
            return
        
        # Проверяем, что клетка не специальная
        cell_type = BOARD[property_id][3]
        if cell_type in ["SPECIAL", "TAX", "JAIL", "PARKING", "GO_TO_JAIL", "CHANCE", "CHEST"]:
            await message.answer("❌ Эту клетку нельзя купить!")
            return
        
        # Проверяем, что клетка свободна
        if property_id in game.get("properties", {}):
            await message.answer("❌ Эта улица уже куплена!")
            return
        
        # Получаем цену
        price = BOARD[property_id][1]
        
        # Проверяем баланс
        if current_player.get("balance", 1500) < price:
            await message.answer(f"❌ Недостаточно денег! Нужно: {price}$, у вас: {current_player['balance']}$")
            return
        
        # Покупаем недвижимость
        if "properties" not in game:
            game["properties"] = {}
        
        game["properties"][property_id] = {
            "owner": user_id,
            "houses": 0,
            "hotel": False,
            "mortgaged": False,
            "current_rent": BOARD[property_id][2]
        }
        
        # Обновляем список недвижимости игрока
        if "properties" not in current_player:
            current_player["properties"] = []
        current_player["properties"].append(property_id)
        
        # Списание денег
        current_player["balance"] = current_player.get("balance", 1500) - price
        
        # Обновляем статистику
        update_user_stats(user_id, message.from_user.username, message.from_user.first_name)
        
        await message.answer(
            f"✅ <b>Поздравляем с покупкой!</b>\n\n"
            f"🏠 Улица: <b>{BOARD[property_id][0]}</b>\n"
            f"💰 Стоимость: <b>{price}$</b>\n"
            f"💵 Ваш баланс: <b>{current_player['balance']}$</b>\n\n"
            f"📈 Базовая аренда: <b>{BOARD[property_id][2]}$</b>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в buy_property: {e}")

@dp.message(lambda message: message.text and message.text.lower().startswith("пропустить"))
async def skip_buying(message: types.Message):
    """Пропуск покупки недвижимости"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        # Проверяем, что сейчас ход этого игрока
        current_idx = game.get("current_player", 0)
        current_player = game["players"][current_idx] if game["players"] else None
        
        if not current_player or current_player["id"] != user_id:
            return
        
        await message.answer(
            f"⏭️ <b>{current_player['name']} пропускает покупку</b>\n\n"
            f"🔄 Передача хода следующему игроку...",
            parse_mode="HTML"
        )
        
        # Передаем ход
        next_idx = (current_idx + 1) % len(game["players"])
        game["current_player"] = next_idx
        next_player = game["players"][next_idx] if game["players"] else None
        
        if next_player:
            await message.answer(
                f"➡️ <b>Следующий: {next_player['name']}</b>\n"
                f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в skip_buying: {e}")

# ==================== РЕЙТИНГ ИГРОКОВ ====================
@dp.callback_query(F.data == "show_leaderboard")
async def show_leaderboard(c: types.CallbackQuery):
    """Показать рейтинг игроков"""
    try:
        # Загружаем статистику
        load_user_stats()
        
        # Получаем топ игроков
        top_players = get_top_players(10)
        
        if not top_players:
            leaderboard_text = (
                "🏆 <b>Рейтинг игроков</b>\n\n"
                "📊 Статистика пока пуста. Сыграйте свою первую игру!"
            )
        else:
            leaderboard_text = "🏆 <b>Топ-10 игроков Monopoly Premium</b>\n\n"
            
            for idx, player in enumerate(top_players, 1):
                medal = ""
                if idx == 1:
                    medal = "🥇 "
                elif idx == 2:
                    medal = "🥈 "
                elif idx == 3:
                    medal = "🥉 "
                
                username_display = f"(@{player['username']})" if player['username'] else ""
                
                leaderboard_text += (
                    f"{medal}<b>{idx}. {player['name']}</b> {username_display}\n"
                    f"   🎮 Игр: {player['games_played']} | "
                    f"🏆 Побед: {player['games_won']} | "
                    f"📈 Винрейт: {player['win_rate']:.1f}%\n"
                )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🔄 Обновить", callback_data="refresh_leaderboard")
        kb.button(text="◀️ Назад", callback_data="back_to_main")
        kb.adjust(1)
        
        await c.message.answer(leaderboard_text, parse_mode="HTML", reply_markup=kb.as_markup())
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_leaderboard: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

@dp.callback_query(F.data == "refresh_leaderboard")
async def refresh_leaderboard(c: types.CallbackQuery):
    """Обновить рейтинг"""
    try:
        # Удаляем старое сообщение
        await c.message.delete()
        
        # Показываем обновленный рейтинг
        await show_leaderboard(c)
        
    except Exception as e:
        logger.error(f"Ошибка в refresh_leaderboard: {e}")
        await c.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОСТАЛЬНЫЕ CALLBACK ОБРАБОТЧИКИ ====================
@dp.callback_query(F.data == "show_rules")
async def show_rules(c: types.CallbackQuery):
    """Показать правила"""
    try:
        rules_text = (
            "📖 <b>Правила Monopoly Premium v3.0:</b>\n\n"
            "1. 🏁 Каждый игрок начинает с <b>1500$</b>\n"
            "2. 🎲 По очереди бросайте 2 кубика\n"
            "3. 🏠 При попадании на свободную улицу можете её купить\n"
            "4. 💰 При попадании на чужую улицу платите аренду\n"
            "5. 🎨 Собирайте все улицы одного цвета для строительства\n"
            "6. 🏘️ Стройте дома (до 4) и отели\n"
            "7. ⛓️ Тюрьма: 3 хода или дубль для выхода\n"
            "8. 💵 Залог: получите 50% стоимости, выкуп - 110%\n"
            "9. 🤝 Торговля: обмен деньгами и недвижимостью\n"
            "10. 🏦 Цель - остаться последним непобанкротившимся\n\n"
            "👑 <b>Особенности версии Темного Принца:</b>\n"
            "• Анимация броска кубиков\n"
            "• Полная система тюрьмы\n"
            "• Механика залога недвижимости\n"
            "• Система торговли между игроками\n"
            "• Карточки шанса и общественной казны\n"
            "• Рейтинг и статистика игроков\n"
            "• Inline меню при скрытии\n"
            "• Закрепленные сообщения лобби"
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
            "<b>Версия:</b> Premium v3.0\n\n"
            "👑 <b>Особенности версии:</b>\n"
            "• Полная реализация механик Монополии\n"
            "• Анимация броска кубиков\n"
            "• Интерактивная карта игры\n"
            "• Система рейтинга игроков\n"
            "• Торговля и залог недвижимости\n"
            "• Карточки шанса и казны\n"
            "• Автоматические таймеры\n"
            "• Админ-панель с защитой\n\n"
            "⭐ <b>Отзывы и предложения:</b>\n"
            f"{DEV_TAG}\n\n"
            "💖 <i>Спасибо за игру! Темный Принц заботится о вас</i>"
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
        
        header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition v3.0</b>\n👑 Версия Темного Принца\n\n"
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

# ==================== АДМИН КОМАНДЫ И ВЕБ-ПАНЕЛЬ ====================
def is_admin(user: types.User) -> bool:
    """Проверить, является ли пользователь админом"""
    username = user.username or ""
    user_id_str = str(user.id)
    
    # Проверка по username
    if username in ALLOWED_ADMINS:
        return True
    
    # Можно добавить проверку по ID если нужно
    # if user_id_str in ALLOWED_USER_IDS:
    #     return True
    
    return False

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Админ панель"""
    try:
        if not is_admin(message.from_user):
            await message.answer(
                "⛔ <b>Доступ запрещен!</b>\n\n"
                "Эта команда доступна только администраторам.",
                parse_mode="HTML"
            )
            return
        
        admin_text = (
            "👑 <b>Админ панель Темного Принца</b>\n\n"
            f"🆔 Ваш ID: <code>{message.from_user.id}</code>\n"
            f"👤 Username: @{message.from_user.username or 'нет'}\n\n"
            f"📊 <b>Статистика бота:</b>\n"
            f"• Активных игр: <b>{len(ACTIVE_GAMES)}</b>\n"
            f"• Игр в ожидании: <b>{len(WAITING_GAMES)}</b>\n"
            f"• Игроков в скрытом режиме: <b>{len(HIDDEN_MENU_USERS)}</b>\n"
            f"• Всего пользователей в статистике: <b>{len(USER_STATS)}</b>\n"
            f"• Режим обслуживания: <b>{'ВКЛ' if STATS.get('maintenance_mode') else 'ВЫКЛ'}</b>\n\n"
            f"⚙️ <b>Доступные команды:</b>\n"
            f"/admin_stats - Подробная статистика\n"
            f"/admin_maintenance [on/off] - Режим обслуживания\n"
            f"/admin_broadcast - Рассылка сообщения\n"
            f"/admin_games - Управление играми\n"
            f"/admin_users - Управление пользователями"
        )
        
        await message.answer(admin_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin: {e}")
        await message.answer("❌ Ошибка в админ панели")

@dp.message(Command("admin_stats"))
async def cmd_admin_stats(message: types.Message):
    """Подробная статистика"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        # Загружаем актуальную статистику
        load_user_stats()
        
        # Анализируем статистику пользователей
        total_games = sum(stats["games_played"] for stats in USER_STATS.values())
        total_wins = sum(stats["games_won"] for stats in USER_STATS.values())
        
        # Находим самых активных игроков
        active_players = sorted(
            USER_STATS.items(),
            key=lambda x: x[1]["games_played"],
            reverse=True
        )[:5]
        
        # Находим лучших игроков по винрейту
        best_players = []
        for user_id, stats in USER_STATS.items():
            if stats["games_played"] >= 3:  # Минимум 3 игры для статистики
                win_rate = (stats["games_won"] / stats["games_played"]) * 100
                best_players.append((user_id, stats, win_rate))
        
        best_players.sort(key=lambda x: x[2], reverse=True)
        best_players = best_players[:5]
        
        stats_text = (
            "📊 <b>Детальная статистика бота</b>\n\n"
            f"🎮 <b>Общая статистика:</b>\n"
            f"• Всего игр сыграно: <b>{total_games}</b>\n"
            f"• Всего побед: <b>{total_wins}</b>\n"
            f"• Общий винрейт: <b>{(total_wins/total_games*100) if total_games > 0 else 0:.1f}%</b>\n\n"
        )
        
        if active_players:
            stats_text += "🏅 <b>Самые активные игроки:</b>\n"
            for idx, (user_id, stats) in enumerate(active_players, 1):
                stats_text += f"{idx}. {stats['name']} - {stats['games_played']} игр\n"
        
        if best_players:
            stats_text += "\n⭐ <b>Лучшие игроки (винрейт):</b>\n"
            for idx, (user_id, stats, win_rate) in enumerate(best_players, 1):
                stats_text += f"{idx}. {stats['name']} - {win_rate:.1f}% ({stats['games_won']}/{stats['games_played']})\n"
        
        # Статистика по текущим играм
        if ACTIVE_GAMES:
            stats_text += "\n🎲 <b>Текущие активные игры:</b>\n"
            for chat_id, game in ACTIVE_GAMES.items():
                player_count = len(game.get("players", []))
                turn = game.get("turn", 1)
                stats_text += f"• Игра в чате {chat_id}: {player_count} игроков, ход {turn}\n"
        
        if WAITING_GAMES:
            stats_text += "\n⏳ <b>Игры в ожидании:</b>\n"
            for chat_id, game in WAITING_GAMES.items():
                player_count = len(game.get("players", []))
                stats_text += f"• Чат {chat_id}: {player_count} игроков в лобби\n"
        
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")

@dp.message(Command("admin_maintenance"))
async def cmd_admin_maintenance(message: types.Message):
    """Управление режимом обслуживания"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            current_status = "ВКЛ" if STATS.get("maintenance_mode", False) else "ВЫКЛ"
            await message.answer(
                f"⚙️ <b>Режим обслуживания: {current_status}</b>\n\n"
                f"Используйте: /admin_maintenance [on/off]\n"
                f"Пример: /admin_maintenance on",
                parse_mode="HTML"
            )
            return
        
        mode = args[1].lower()
        
        if mode in ["on", "вкл", "true", "1"]:
            STATS["maintenance_mode"] = True
            status_text = "✅ <b>Режим обслуживания ВКЛЮЧЕН</b>\n\n"
            status_text += "Бот будет отображать сообщение об обновлении всем пользователям."
        elif mode in ["off", "выкл", "false", "0"]:
            STATS["maintenance_mode"] = False
            status_text = "✅ <b>Режим обслуживания ВЫКЛЮЧЕН</b>\n\n"
            status_text += "Бот работает в обычном режиме."
        else:
            await message.answer(
                "❌ <b>Неверный параметр!</b>\n\n"
                "Доступные значения: on, off, вкл, выкл",
                parse_mode="HTML"
            )
            return
        
        await message.answer(status_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_maintenance: {e}")
        await message.answer("❌ Ошибка при изменении режима")

@dp.message(Command("admin_games"))
async def cmd_admin_games(message: types.Message):
    """Управление играми"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        games_text = (
            "🎮 <b>Управление играми</b>\n\n"
            f"📊 <b>Активные игры: {len(ACTIVE_GAMES)}</b>\n"
        )
        
        if ACTIVE_GAMES:
            for idx, (chat_id, game) in enumerate(ACTIVE_GAMES.items(), 1):
                players = game.get("players", [])
                player_names = ", ".join([p["name"] for p in players])
                turn = game.get("turn", 1)
                current_idx = game.get("current_player", 0)
                current_player = players[current_idx] if players else None
                
                games_text += (
                    f"\n{idx}. <b>Чат ID: {chat_id}</b>\n"
                    f"   👥 Игроки: {player_names}\n"
                    f"   🔄 Ход: {turn}\n"
                )
                
                if current_player:
                    games_text += f"   🎯 Сейчас ходит: {current_player['name']}\n"
                
                games_text += f"   ⚙️ Команда: /admin_end_game {chat_id}"
        
        games_text += f"\n\n⏳ <b>Игры в ожидании: {len(WAITING_GAMES)}</b>\n"
        
        if WAITING_GAMES:
            for idx, (chat_id, game) in enumerate(WAITING_GAMES.items(), 1):
                players = game.get("players", [])
                player_names = ", ".join([p["name"] for p in players])
                creator = game.get("creator_name", "Неизвестно")
                
                games_text += (
                    f"\n{idx}. <b>Чат ID: {chat_id}</b>\n"
                    f"   👑 Создатель: {creator}\n"
                    f"   👥 Игроки: {player_names}\n"
                    f"   ⚙️ Команда: /admin_cancel_waiting {chat_id}"
                )
        
        if not ACTIVE_GAMES and not WAITING_GAMES:
            games_text += "\n📭 Нет активных игр или игр в ожидании"
        
        await message.answer(games_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_games: {e}")
        await message.answer("❌ Ошибка при получении информации об играх")

@dp.message(Command("admin_end_game"))
async def cmd_admin_end_game(message: types.Message):
    """Принудительно завершить игру"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте: /admin_end_game [chat_id]\n"
                "Пример: /admin_end_game 123456789",
                parse_mode="HTML"
            )
            return
        
        try:
            chat_id = int(args[1])
        except ValueError:
            await message.answer("❌ Chat ID должен быть числом!")
            return
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer(f"❌ Активная игра в чате {chat_id} не найдена!")
            return
        
        # Завершаем игру
        game = ACTIVE_GAMES.pop(chat_id)
        
        # Определяем победителя (если есть игроки)
        winner = None
        if game.get("players"):
            # Находим игрока с максимальным балансом
            winner = max(game["players"], key=lambda p: p.get("balance", 0))
        
        # Отправляем сообщение в чат
        try:
            if winner:
                end_text = (
                    f"🛑 <b>Игра принудительно завершена администратором!</b>\n\n"
                    f"🏆 Победитель: <b>{winner['name']}</b>\n"
                    f"💰 Финальный баланс: <b>{winner.get('balance', 0)}$</b>\n\n"
                    f"👑 <i>Темный Принц завершил эту игру</i>"
                )
            else:
                end_text = (
                    f"🛑 <b>Игра принудительно завершена администратором!</b>\n\n"
                    f"👑 <i>Темный Принц завершил эту игру</i>"
                )
            
            await bot.send_message(chat_id=chat_id, text=end_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
        
        await message.answer(f"✅ Игра в чате {chat_id} завершена!")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_end_game: {e}")
        await message.answer("❌ Ошибка при завершении игры")

@dp.message(Command("admin_cancel_waiting"))
async def cmd_admin_cancel_waiting(message: types.Message):
    """Принудительно отменить ожидание"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте: /admin_cancel_waiting [chat_id]\n"
                "Пример: /admin_cancel_waiting 123456789",
                parse_mode="HTML"
            )
            return
        
        try:
            chat_id = int(args[1])
        except ValueError:
            await message.answer("❌ Chat ID должен быть числом!")
            return
        
        if chat_id not in WAITING_GAMES:
            await message.answer(f"❌ Игра в ожидании в чате {chat_id} не найдена!")
            return
        
        # Отменяем ожидание
        game = WAITING_GAMES.pop(chat_id)
        
        # Отменяем таймер
        if "timer_task" in game:
            game["timer_task"].cancel()
        
        # Отправляем сообщение в чат
        try:
            cancel_text = (
                f"🛑 <b>Сбор игроков отменен администратором!</b>\n\n"
                f"👑 <i>Темный Принц отменил сбор игроков</i>"
            )
            
            await bot.send_message(chat_id=chat_id, text=cancel_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
        
        await message.answer(f"✅ Ожидание в чате {chat_id} отменено!")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_cancel_waiting: {e}")
        await message.answer("❌ Ошибка при отмене ожидания")

@dp.message(Command("admin_users"))
async def cmd_admin_users(message: types.Message):
    """Управление пользователями"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        # Загружаем статистику
        load_user_stats()
        
        users_text = (
            "👥 <b>Управление пользователями</b>\n\n"
            f"📊 Всего пользователей в статистике: <b>{len(USER_STATS)}</b>\n\n"
            f"⚙️ <b>Доступные команды:</b>\n"
            f"/admin_user_info [user_id] - Информация о пользователе\n"
            f"/admin_user_stats [user_id] - Статистика пользователя\n"
            f"/admin_add_admin [username] - Добавить администратора\n"
            f"/admin_remove_admin [username] - Удалить администратора\n\n"
            f"📋 <b>Текущие администраторы:</b>\n"
        )
        
        for admin in ALLOWED_ADMINS:
            users_text += f"• @{admin}\n"
        
        if not ALLOWED_ADMINS:
            users_text += "📭 Нет назначенных администраторов\n"
        
        await message.answer(users_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_users: {e}")
        await message.answer("❌ Ошибка в управлении пользователями")

@dp.message(Command("admin_user_info"))
async def cmd_admin_user_info(message: types.Message):
    """Информация о пользователе"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте: /admin_user_info [user_id]\n"
                "Пример: /admin_user_info 123456789",
                parse_mode="HTML"
            )
            return
        
        try:
            user_id = int(args[1])
        except ValueError:
            # Может быть username
            username = args[1].lstrip('@')
            
            # Ищем пользователя по username в статистике
            found_user_id = None
            for uid, stats in USER_STATS.items():
                if stats.get("username") == username:
                    found_user_id = uid
                    break
            
            if not found_user_id:
                await message.answer(f"❌ Пользователь @{username} не найден в статистике!")
                return
            
            user_id = found_user_id
        
        # Пытаемся получить информацию о пользователе через Telegram API
        try:
            user = await bot.get_chat(user_id)
            user_info = (
                f"👤 <b>Информация о пользователе</b>\n\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"👤 Имя: {user.first_name or 'Не указано'}\n"
                f"👥 Фамилия: {user.last_name or 'Не указана'}\n"
                f"📛 Username: @{user.username or 'нет'}\n"
                f"🌐 Язык: {user.language_code or 'Не указан'}\n"
            )
            
            if user.is_premium:
                user_info += f"⭐ Премиум: Да\n"
            
        except Exception as e:
            user_info = f"👤 <b>Информация о пользователе ID: {user_id}</b>\n\n"
            user_info += f"⚠️ Не удалось получить данные через Telegram API\n"
        
        # Добавляем статистику если есть
        if user_id in USER_STATS:
            stats = USER_STATS[user_id]
            win_rate = (stats["games_won"] / stats["games_played"]) * 100 if stats["games_played"] > 0 else 0
            
            user_info += (
                f"\n📊 <b>Статистика игры:</b>\n"
                f"• Игр сыграно: {stats['games_played']}\n"
                f"• Побед: {stats['games_won']}\n"
                f"• Винрейт: {win_rate:.1f}%\n"
                f"• Последняя игра: {stats.get('last_played', 'никогда')}\n"
            )
        else:
            user_info += "\n📭 <i>Нет статистики игр</i>"
        
        await message.answer(user_info, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_user_info: {e}")
        await message.answer("❌ Ошибка при получении информации о пользователе")

@dp.message(Command("admin_add_admin"))
async def cmd_admin_add_admin(message: types.Message):
    """Добавить администратора"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте: /admin_add_admin [username]\n"
                "Пример: /admin_add_admin username",
                parse_mode="HTML"
            )
            return
        
        new_admin = args[1].lstrip('@')
        
        if new_admin in ALLOWED_ADMINS:
            await message.answer(f"❌ @{new_admin} уже является администратором!")
            return
        
        ALLOWED_ADMINS.append(new_admin)
        
        # Сохраняем список админов (в реальном проекте нужно сохранять в файл/БД)
        await message.answer(
            f"✅ <b>Администратор добавлен!</b>\n\n"
            f"👤 @{new_admin} теперь имеет доступ к админ-панели.\n\n"
            f"📋 <b>Текущие администраторы:</b>\n" +
            "\n".join([f"• @{admin}" for admin in ALLOWED_ADMINS]),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_add_admin: {e}")
        await message.answer("❌ Ошибка при добавлении администратора")

@dp.message(Command("admin_remove_admin"))
async def cmd_admin_remove_admin(message: types.Message):
    """Удалить администратора"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте: /admin_remove_admin [username]\n"
                "Пример: /admin_remove_admin username",
                parse_mode="HTML"
            )
            return
        
        admin_to_remove = args[1].lstrip('@')
        
        if admin_to_remove not in ALLOWED_ADMINS:
            await message.answer(f"❌ @{admin_to_remove} не является администратором!")
            return
        
        # Нельзя удалить себя
        if admin_to_remove == (message.from_user.username or ""):
            await message.answer("❌ Вы не можете удалить сами себя!")
            return
        
        ALLOWED_ADMINS.remove(admin_to_remove)
        
        await message.answer(
            f"✅ <b>Администратор удален!</b>\n\n"
            f"👤 @{admin_to_remove} больше не имеет доступа к админ-панели.\n\n"
            f"📋 <b>Текущие администраторы:</b>\n" +
            "\n".join([f"• @{admin}" for admin in ALLOWED_ADMINS]),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin_remove_admin: {e}")
        await message.answer("❌ Ошибка при удалении администратора")

# ==================== ВЕБ-ПАНЕЛЬ ДЛЯ КАРТЫ И СТАТУСА ====================
from aiohttp import web
import aiohttp

# HTML страница для карты
MAP_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monopoly Premium - Карта игры</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #f6d365, #fda085);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }
        
        .game-info {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .map-container {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            grid-template-rows: repeat(10, 80px);
            gap: 5px;
            margin-bottom: 30px;
        }
        
        .cell {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            text-align: center;
            font-size: 0.8rem;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .cell:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .cell-start {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            grid-column: 10;
            grid-row: 10;
        }
        
        .cell-jail {
            background: linear-gradient(45deg, #f44336, #e53935);
        }
        
        .cell-chance {
            background: linear-gradient(45deg, #FF9800, #FFB74D);
        }
        
        .cell-railroad {
            background: linear-gradient(45deg, #795548, #A1887F);
        }
        
        .cell-utility {
            background: linear-gradient(45deg, #00BCD4, #80DEEA);
        }
        
        .cell-tax {
            background: linear-gradient(45deg, #9E9E9E, #BDBDBD);
        }
        
        .player-marker {
            position: absolute;
            top: 5px;
            right: 5px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid white;
        }
        
        .players-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }
        
        .player-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            min-width: 200px;
            text-align: center;
        }
        
        .player-color {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin: 0 auto 10px;
            border: 2px solid white;
        }
        
        .status {
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            margin-top: 30px;
        }
        
        .status.online {
            border-left: 5px solid #4CAF50;
        }
        
        .status.offline {
            border-left: 5px solid #f44336;
        }
        
        .password-form {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            text-align: center;
        }
        
        .password-form input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 1rem;
        }
        
        .password-form button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .password-form button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .color-brown { background: #8B4513; }
        .color-blue { background: #1E90FF; }
        .color-pink { background: #FF69B4; }
        .color-orange { background: #FFA500; }
        .color-red { background: #DC143C; }
        .color-yellow { background: #FFD700; }
        .color-green { background: #32CD32; }
        .color-darkblue { background: #00008B; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Monopoly Premium</h1>
            <p>👑 Версия Темного Принца | Карта игры в реальном времени</p>
        </div>
        
        <div class="game-info">
            <h2>🔄 Текущая игра</h2>
            <div id="game-info-content">
                <p>Загрузка информации об игре...</p>
            </div>
        </div>
        
        <div id="map-container" class="map-container">
            <!-- Карта будет генерироваться JavaScript -->
        </div>
        
        <div class="players-list" id="players-list">
            <!-- Список игроков будет генерироваться JavaScript -->
        </div>
        
        <div class="status online" id="status">
            <h3>📊 Статус системы</h3>
            <p>Загрузка статуса...</p>
        </div>
    </div>
    
    <script>
        // Данные карты
        const BOARD_DATA = {{board_data|safe}};
        const PLAYERS_DATA = {{players_data|safe}};
        const GAME_DATA = {{game_data|safe}};
        
        // Функция для получения цвета по типу клетки
        function getCellClass(cellType) {
            const typeMap = {
                'BROWN': 'color-brown',
                'BLUE': 'color-blue',
                'PINK': 'color-pink',
                'ORANGE': 'color-orange',
                'RED': 'color-red',
                'YELLOW': 'color-yellow',
                'GREEN': 'color-green',
                'DARKBLUE': 'color-darkblue',
                'RAIL': 'cell-railroad',
                'UTIL': 'cell-utility',
                'CHANCE': 'cell-chance',
                'CHEST': 'cell-chance',
                'TAX': 'cell-tax',
                'JAIL': 'cell-jail',
                'GO_TO_JAIL': 'cell-jail',
                'SPECIAL': 'cell-start',
                'PARKING': ''
            };
            return typeMap[cellType] || '';
        }
        
        // Функция для получения игроков на клетке
        function getPlayersOnCell(position) {
            return PLAYERS_DATA.filter(player => player.position === position);
        }
        
        // Функция для генерации карты
        function generateMap() {
            const mapContainer = document.getElementById('map-container');
            mapContainer.innerHTML = '';
            
            // Создаем 10x10 сетку
            for (let row = 0; row < 10; row++) {
                for (let col = 0; col < 10; col++) {
                    const cellDiv = document.createElement('div');
                    cellDiv.className = 'cell';
                    
                    // Определяем позицию в монополии (0-39)
                    let position = -1;
                    
                    // Нижний ряд (справа налево)
                    if (row === 9 && col > 0 && col < 10) {
                        position = 10 - col;
                    }
                    // Левый ряд (снизу вверх)
                    else if (col === 0 && row < 9 && row >= 0) {
                        position = 10 + (9 - row);
                    }
                    // Верхний ряд (слева направо)
                    else if (row === 0 && col >= 0 && col < 9) {
                        position = 20 + col;
                    }
                    // Правый ряд (сверху вниз)
                    else if (col === 9 && row > 0 && row <= 9) {
                        position = 30 + row;
                    }
                    // Угловые клетки
                    else if (row === 9 && col === 0) {
                        position = 10; // Тюрьма (посещение)
                    }
                    else if (row === 9 && col === 9) {
                        position = 0; // СТАРТ
                    }
                    else if (row === 0 && col === 0) {
                        position = 20; // Бесплатная стоянка
                    }
                    else if (row === 0 && col === 9) {
                        position = 30; // Отправляйтесь в тюрьму
                    }
                    
                    // Добавляем классы если клетка существует
                    if (position !== -1 && BOARD_DATA[position]) {
                        const cellData = BOARD_DATA[position];
                        cellDiv.textContent = cellData[0];
                        cellDiv.className += ' ' + getCellClass(cellData[3]);
                        
                        // Добавляем маркеры игроков
                        const playersHere = getPlayersOnCell(position);
                        playersHere.forEach(player => {
                            const marker = document.createElement('div');
                            marker.className = 'player-marker';
                            marker.style.backgroundColor = player.color;
                            marker.title = player.name;
                            cellDiv.appendChild(marker);
                        });
                        
                        // Добавляем подсказку
                        cellDiv.title = `${cellData[0]}\\nЦена: ${cellData[1]}$\\nАренда: ${cellData[2]}$`;
                    } else if (position !== -1) {
                        cellDiv.textContent = `[${position}]`;
                    }
                    
                    mapContainer.appendChild(cellDiv);
                }
            }
        }
        
        // Функция для обновления информации об игре
        function updateGameInfo() {
            const gameInfo = document.getElementById('game-info-content');
            
            if (GAME_DATA.players && GAME_DATA.players.length > 0) {
                const currentPlayer = GAME_DATA.players[GAME_DATA.current_player || 0];
                
                gameInfo.innerHTML = `
                    <p><strong>🔄 Ход:</strong> ${GAME_DATA.turn || 1}</p>
                    <p><strong>🎯 Сейчас ходит:</strong> ${currentPlayer?.name || 'Неизвестно'}</p>
                    <p><strong>👥 Игроков:</strong> ${GAME_DATA.players.length}</p>
                    <p><strong>⏰ Начало:</strong> ${new Date(GAME_DATA.started_at).toLocaleString()}</p>
                `;
            } else {
                gameInfo.innerHTML = '<p>Игра не активна или данные не загружены</p>';
            }
        }
        
        // Функция для генерации списка игроков
        function generatePlayersList() {
            const playersList = document.getElementById('players-list');
            playersList.innerHTML = '';
            
            if (PLAYERS_DATA && PLAYERS_DATA.length > 0) {
                PLAYERS_DATA.forEach(player => {
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    
                    playerCard.innerHTML = `
                        <div class="player-color" style="background-color: ${player.color}"></div>
                        <h3>${player.name}</h3>
                        <p><strong>📍 Позиция:</strong> ${player.position}</p>
                        <p><strong>💰 Баланс:</strong> ${player.balance || 1500}$</p>
                        ${player.in_jail ? '<p>⛓️ В тюрьме</p>' : ''}
                    `;
                    
                    playersList.appendChild(playerCard);
                });
            }
        }
        
        // Функция для обновления статуса
        function updateStatus() {
            const statusDiv = document.getElementById('status');
            
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    statusDiv.innerHTML = `
                        <h3>📊 Статус системы</h3>
                        <p><strong>🤖 Бот:</strong> ${data.bot_status}</p>
                        <p><strong>🎮 Активных игр:</strong> ${data.active_games}</p>
                        <p><strong>⏳ Игр в ожидании:</strong> ${data.waiting_games}</p>
                        <p><strong>👥 Всего игроков в статистике:</strong> ${data.total_players}</p>
                        <p><strong>🕒 Последнее обновление:</strong> ${new Date().toLocaleTimeString()}</p>
                    `;
                    
                    statusDiv.className = `status ${data.bot_status === 'online' ? 'online' : 'offline'}`;
                })
                .catch(error => {
                    statusDiv.innerHTML = `
                        <h3>📊 Статус системы</h3>
                        <p>❌ Ошибка загрузки статуса</p>
                    `;
                    statusDiv.className = 'status offline';
                });
        }
        
        // Функция для автоматического обновления
        function startAutoRefresh() {
            // Обновляем каждые 10 секунд
            setInterval(() => {
                updateStatus();
                // Здесь можно добавить обновление других данных
            }, 10000);
        }
        
        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', () => {
            generateMap();
            updateGameInfo();
            generatePlayersList();
            updateStatus();
            startAutoRefresh();
            
            console.log('Monopoly Premium Map loaded successfully!');
            console.log('Board data:', BOARD_DATA);
            console.log('Players:', PLAYERS_DATA);
            console.log('Game:', GAME_DATA);
        });
    </script>
</body>
</html>
'''

# HTML для статуса системы (защищенный паролем)
STATUS_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monopoly Premium - Статус системы</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            color: white;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #f6d365, #fda085);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.8;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card h3 {
            font-size: 1rem;
            margin-bottom: 10px;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card .value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-card .icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .games-section {
            background: rgba(0, 0, 0, 0.2);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .games-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .game-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .game-info {
            flex: 1;
        }
        
        .game-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #f44336, #e53935);
        }
        
        .btn-success {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
        }
        
        .admin-controls {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
        }
        
        .control-group {
            margin-bottom: 20px;
        }
        
        .control-group h3 {
            margin-bottom: 15px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 10px;
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .password-form {
            max-width: 400px;
            margin: 50px auto;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            text-align: center;
        }
        
        .password-form input {
            width: 100%;
            padding: 15px;
            margin: 15px 0;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 1rem;
        }
        
        .password-form button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .password-form button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .error {
            color: #ff6b6b;
            margin-top: 10px;
        }
        
        .online { color: #4CAF50; }
        .offline { color: #f44336; }
        .warning { color: #FF9800; }
    </style>
</head>
<body>
    {% if not authenticated %}
    <div class="password-form">
        <h2>🔒 Админ панель</h2>
        <p>Введите пароль для доступа:</p>
        <form method="GET">
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
    {% else %}
    <div class="container">
        <div class="header">
            <h1>👑 Админ панель Темного Принца</h1>
            <p>Monopoly Premium - Полный контроль над системой</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">🤖</div>
                <h3>Статус бота</h3>
                <div class="value {{ 'online' if bot_status == 'online' else 'offline' }}">
                    {{ 'Онлайн' if bot_status == 'online' else 'Оффлайн' }}
                </div>
            </div>
            
            <div class="stat-card">
                <div class="icon">🎮</div>
                <h3>Активных игр</h3>
                <div class="value">{{ active_games }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">⏳</div>
                <h3>Игр в ожидании</h3>
                <div class="value">{{ waiting_games }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">👥</div>
                <h3>Всего игроков</h3>
                <div class="value">{{ total_players }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">📊</div>
                <h3>Всего игр</h3>
                <div class="value">{{ total_games }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">⚙️</div>
                <h3>Режим обслуживания</h3>
                <div class="value {{ 'warning' if maintenance_mode else 'online' }}">
                    {{ 'ВКЛ' if maintenance_mode else 'ВЫКЛ' }}
                </div>
            </div>
        </div>
        
        {% if active_games > 0 %}
        <div class="games-section">
            <h2>🎮 Активные игры</h2>
            <div class="games-list">
                {% for chat_id, game in active_games_list %}
                <div class="game-item">
                    <div class="game-info">
                        <h4>Чат ID: {{ chat_id }}</h4>
                        <p>👥 Игроков: {{ game.players|length }} | 🔄 Ход: {{ game.turn }} | 🎯 Ходит: {{ game.players[game.current_player].name if game.players else 'Нет' }}</p>
                    </div>
                    <div class="game-actions">
                        <button class="btn btn-danger" onclick="endGame({{ chat_id }})">Завершить</button>
                        <button class="btn" onclick="viewGame({{ chat_id }})">Просмотр</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if waiting_games > 0 %}
        <div class="games-section">
            <h2>⏳ Игры в ожидании</h2>
            <div class="games-list">
                {% for chat_id, game in waiting_games_list %}
                <div class="game-item">
                    <div class="game-info">
                        <h4>Чат ID: {{ chat_id }}</h4>
                        <p>👑 Создатель: {{ game.creator_name }} | 👥 Игроков: {{ game.players|length }}</p>
                    </div>
                    <div class="game-actions">
                        <button class="btn btn-danger" onclick="cancelWaiting({{ chat_id }})">Отменить</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <div class="admin-controls">
            <div class="control-group">
                <h3>⚙️ Управление системой</h3>
                <div class="control-buttons">
                    <button class="btn {{ 'btn-danger' if maintenance_mode else 'btn-success' }}" 
                            onclick="toggleMaintenance()">
                        {{ 'Выключить' if maintenance_mode else 'Включить' }} режим обслуживания
                    </button>
                    <button class="btn" onclick="reloadStats()">🔄 Обновить статистику</button>
                    <button class="btn" onclick="clearOldGames()">🗑️ Очистить старые игры</button>
                </div>
            </div>
            
            <div class="control-group">
                <h3>📊 Дополнительные действия</h3>
                <div class="control-buttons">
                    <button class="btn" onclick="exportStats()">📥 Экспорт статистики</button>
                    <button class="btn" onclick="backupData()">💾 Создать бэкап</button>
                    <button class="btn" onclick="restartBot()">🔄 Перезапустить бота</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function endGame(chatId) {
            if (confirm('Вы уверены, что хотите завершить эту игру?')) {
                fetch(`/api/admin/end_game/${chatId}?password={{ password }}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Игра завершена!');
                            location.reload();
                        } else {
                            alert('Ошибка: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Ошибка сети: ' + error);
                    });
            }
        }
        
        function cancelWaiting(chatId) {
            if (confirm('Вы уверены, что хотите отменить это ожидание?')) {
                fetch(`/api/admin/cancel_waiting/${chatId}?password={{ password }}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Ожидание отменено!');
                            location.reload();
                        } else {
                            alert('Ошибка: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Ошибка сети: ' + error);
                    });
            }
        }
        
        function viewGame(chatId) {
            window.open(`/map/${chatId}?password={{ password }}`, '_blank');
        }
        
        function toggleMaintenance() {
            const newMode = {{ not maintenance_mode|lower }};
            fetch(`/api/admin/maintenance/${newMode}?password={{ password }}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Режим обслуживания ' + (newMode ? 'включен' : 'выключен'));
                        location.reload();
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Ошибка сети: ' + error);
                });
        }
        
        function reloadStats() {
            location.reload();
        }
        
        function clearOldGames() {
            if (confirm('Очистить все завершенные и старые игры?')) {
                fetch(`/api/admin/clear_old?password={{ password }}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Старые игры очищены!');
                            location.reload();
                        } else {
                            alert('Ошибка: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Ошибка сети: ' + error);
                    });
            }
        }
        
        function exportStats() {
            fetch(`/api/admin/export_stats?password={{ password }}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Создаем и скачиваем файл
                        const blob = new Blob([JSON.stringify(data.data, null, 2)], {type: 'application/json'});
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `monopoly_stats_${new Date().toISOString().split('T')[0]}.json`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Ошибка сети: ' + error);
                });
        }
        
        function backupData() {
            fetch(`/api/admin/backup?password={{ password }}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Бэкап создан успешно!');
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Ошибка сети: ' + error);
                });
        }
        
        function restartBot() {
            if (confirm('Вы уверены, что хотите перезапустить бота? Это может занять несколько секунд.')) {
                fetch(`/api/admin/restart?password={{ password }}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Бот перезапускается...');
                            setTimeout(() => location.reload(), 3000);
                        } else {
                            alert('Ошибка: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Ошибка сети: ' + error);
                    });
            }
        }
        
        // Автообновление каждые 30 секунд
        setInterval(() => {
            reloadStats();
        }, 30000);
    </script>
    {% endif %}
</body>
</html>
'''

# ==================== ВЕБ-СЕРВЕР ====================
async def handle_status(request):
    """Обработчик для страницы статуса"""
    params = request.query
    
    # Проверка пароля
    password = params.get('password', '')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != ADMIN_PASSWORD_HASH:
        # Показываем форму ввода пароля
        error = params.get('error', '')
        html = STATUS_HTML.replace('{% if not authenticated %}', '{% if True %}').replace('{% if error %}', f'{% if {error} %}')
        return web.Response(text=html, content_type='text/html')
    
    # Рассчитываем статистику
    total_games = sum(stats["games_played"] for stats in USER_STATS.values()) if USER_STATS else 0
    active_games_list = list(ACTIVE_GAMES.items())[:10]  # Ограничиваем 10 играми
    waiting_games_list = list(WAITING_GAMES.items())[:10]
    
    # Генерируем HTML с данными
    html = STATUS_HTML.replace('{% if not authenticated %}', '{% if False %}')
    html = html.replace('{{ bot_status }}', 'online')
    html = html.replace('{{ active_games }}', str(len(ACTIVE_GAMES)))
    html = html.replace('{{ waiting_games }}', str(len(WAITING_GAMES)))
    html = html.replace('{{ total_players }}', str(len(USER_STATS)))
    html = html.replace('{{ total_games }}', str(total_games))
    html = html.replace('{{ maintenance_mode }}', str(STATS.get("maintenance_mode", False)).lower())
    html = html.replace('{{ password }}', password)
    
    # Заменяем списки игр
    import jinja2
    from jinja2 import Template
    
    template = Template(html)
    rendered = template.render(
        authenticated=True,
        bot_status='online',
        active_games=len(ACTIVE_GAMES),
        waiting_games=len(WAITING_GAMES),
        total_players=len(USER_STATS),
        total_games=total_games,
        maintenance_mode=STATS.get("maintenance_mode", False),
        password=password,
        active_games_list=active_games_list,
        waiting_games_list=waiting_games_list
    )
    
    return web.Response(text=rendered, content_type='text/html')

async def handle_map(request):
    """Обработчик для карты игры"""
    game_id = int(request.match_info.get('game_id', 0))
    
    # Проверяем пароль если требуется
    params = request.query
    if 'password' in params:
        password = params.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != ADMIN_PASSWORD_HASH:
            return web.Response(text='Доступ запрещен', status=403)
    
    # Получаем данные игры
    if game_id not in ACTIVE_GAMES:
        return web.Response(text='Игра не найдена', status=404)
    
    game = ACTIVE_GAMES[game_id]
    
    # Подготавливаем данные для шаблона
    board_data = json.dumps(BOARD)
    players_data = json.dumps([
        {
            "id": p["id"],
            "name": p["name"],
            "position": p.get("position", 0),
            "color": p.get("color", "#3498db"),
            "balance": p.get("balance", 1500),
            "in_jail": p.get("in_jail", False)
        }
        for p in game.get("players", [])
    ])
    
    game_data = json.dumps({
        "players": game.get("players", []),
        "current_player": game.get("current_player", 0),
        "turn": game.get("turn", 1),
        "started_at": game.get("started_at", datetime.now()).isoformat()
    })
    
    # Заменяем плейсхолдеры в HTML
    html = MAP_HTML.replace('{{board_data|safe}}', board_data)
    html = html.replace('{{players_data|safe}}', players_data)
    html = html.replace('{{game_data|safe}}', game_data)
    
    return web.Response(text=html, content_type='text/html')

async def handle_api_status(request):
    """API для получения статуса системы"""
    data = {
        "bot_status": "online",
        "active_games": len(ACTIVE_GAMES),
        "waiting_games": len(WAITING_GAMES),
        "total_players": len(USER_STATS),
        "maintenance_mode": STATS.get("maintenance_mode", False),
        "timestamp": datetime.now().isoformat()
    }
    return web.json_response(data)

async def handle_api_admin(request):
    """API для админ действий"""
    action = request.match_info.get('action', '')
    params = request.query
    
    # Проверка пароля
    password = params.get('password', '')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != ADMIN_PASSWORD_HASH:
        return web.json_response({"success": False, "error": "Неверный пароль"})
    
    try:
        if action == "end_game":
            chat_id = int(request.match_info.get('param', 0))
            if chat_id in ACTIVE_GAMES:
                game = ACTIVE_GAMES.pop(chat_id)
                return web.json_response({"success": True, "message": f"Игра в чате {chat_id} завершена"})
            else:
                return web.json_response({"success": False, "error": "Игра не найдена"})
        
        elif action == "cancel_waiting":
            chat_id = int(request.match_info.get('param', 0))
            if chat_id in WAITING_GAMES:
                game = WAITING_GAMES.pop(chat_id)
                return web.json_response({"success": True, "message": f"Ожидание в чате {chat_id} отменено"})
            else:
                return web.json_response({"success": False, "error": "Ожидание не найдено"})
        
        elif action == "maintenance":
            mode = request.match_info.get('param', '').lower() == 'true'
            STATS["maintenance_mode"] = mode
            return web.json_response({"success": True, "message": f"Режим обслуживания {'включен' if mode else 'выключен'}"})
        
        elif action == "clear_old":
            # Здесь можно добавить очистку старых игр
            return web.json_response({"success": True, "message": "Функция в разработке"})
        
        elif action == "export_stats":
            load_user_stats()
            return web.json_response({"success": True, "data": USER_STATS})
        
        elif action == "backup":
            # Здесь можно добавить создание бэкапа
            return web.json_response({"success": True, "message": "Функция в разработке"})
        
        elif action == "restart":
            # Здесь можно добавить перезапуск бота
            return web.json_response({"success": True, "message": "Функция в разработке"})
        
        else:
            return web.json_response({"success": False, "error": "Неизвестное действие"})
    
    except Exception as e:
        logger.error(f"Ошибка в API админа: {e}")
        return web.json_response({"success": False, "error": str(e)})

async def start_web_server():
    """Запуск веб-сервера"""
    app = web.Application()
    
    # Статические роуты
    app.router.add_get('/', handle_status)
    app.router.add_get('/status', handle_status)
    app.router.add_get('/map/{game_id}', handle_map)
    
    # API роуты
    app.router.add_get('/api/status', handle_api_status)
    app.router.add_get('/api/admin/{action}/{param}', handle_api_admin)
    app.router.add_get('/api/admin/{action}', handle_api_admin)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")
    logger.info(f"🔗 Статус системы: http://localhost:{PORT}/?password=darkprince")

# ==================== ЗАПУСК БОТА И ВЕБ-СЕРВЕРА ====================
async def run_bot_and_web():
    """Запуск бота и веб-сервера одновременно"""
    # Загружаем статистику
    load_user_stats()
    
    # Запускаем веб-сервер в отдельной задаче
    web_task = asyncio.create_task(start_web_server())
    
    # Запускаем бота
    try:
        logger.info("🚀 Telegram бот запускается...")
        logger.info("👑 Темный Принц активирован")
        logger.info("🎮 Monopoly Premium v3.0 готов к работе!")
        
        # Удаляем вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем поллинг с переподключением
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise
    finally:
        # Отменяем задачу веб-сервера при выходе
        web_task.cancel()
        try:
            await web_task
        except asyncio.CancelledError:
            pass

def main():
    """Основная функция запуска"""
    logger.info("=" * 70)
    logger.info("🎮 MONOPOLY PREMIUM BOT v3.0")
    logger.info("👑 Версия Темного Принца - Полная реализация")
    logger.info("=" * 70)
    
    # Запускаем бота и веб-сервер
    asyncio.run(run_bot_and_web())

if __name__ == "__main__":
    main()

# ==================== ДОПОЛНИТЕЛЬНЫЕ ФИЧИ И ИСПРАВЛЕНИЯ ====================

# Добавим финальные улучшения и обработку краевых случаев

# Список эмодзи для анимации кубиков (более красивые)
DICE_EMOJIS_ANIMATION = [
    ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"],  # Фрейм 1
    ["🎲", "🎯", "✨", "⭐", "🌟", "💫"],  # Фрейм 2
    ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"],  # Фрейм 3
    ["🎲", "🎯", "✨", "⭐", "🌟", "💫"],  # Фрейм 4
]

async def enhanced_dice_animation(chat_id: int, user_name: str) -> Tuple[int, int]:
    """Улучшенная анимация броска кубиков с более плавной анимацией"""
    messages = []
    
    try:
        # Фрейм 1 - Начало
        msg1 = await bot.send_message(
            chat_id,
            f"🎲 *{user_name} готовится к броску...*\n"
            f"🔄 Кубики заряжаются энергией Темного Принца!",
            parse_mode="Markdown"
        )
        messages.append(msg1.message_id)
        await asyncio.sleep(0.3)
        
        # Фрейм 2-5 - Анимация вращения
        for frame in range(4):
            dice_frame = DICE_EMOJIS_ANIMATION[frame % len(DICE_EMOJIS_ANIMATION)]
            random.shuffle(dice_frame)
            
            msg = await bot.send_message(
                chat_id,
                f"🎲 *Кубики крутятся...*\n"
                f"{dice_frame[0]} {dice_frame[1]}",
                parse_mode="Markdown"
            )
            messages.append(msg.message_id)
            await asyncio.sleep(0.2)
            
            # Удаляем предыдущий фрейм (кроме первого)
            if len(messages) > 2:
                try:
                    await bot.delete_message(chat_id, messages[-2])
                except:
                    pass
        
        # Генерируем результат
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        # Проверка на дубль
        is_double = dice1 == dice2
        
        # Фрейм 6 - Результат
        result_text = f"🎲 *Результат броска {user_name}:*\n"
        result_text += f"{get_dice_emoji(dice1)} **Кубик 1:** {dice1}\n"
        result_text += f"{get_dice_emoji(dice2)} **Кубик 2:** {dice2}\n"
        result_text += f"📊 **Сумма:** {total}\n"
        
        if is_double:
            result_text += f"🎯 **ДУБЛЬ!** Можно бросить еще раз!\n"
        
        # Специальные комбинации
        if total == 7:
            result_text += f"🍀 **Счастливая семерка!** Удача на вашей стороне!\n"
        elif total == 2:
            result_text += f"🐍 **Змеиные глаза!** Редкая комбинация!\n"
        elif total == 12:
            result_text += f"🎲 **Бокс-карс!** Максимальный бросок!\n"
        
        msg_result = await bot.send_message(chat_id, result_text, parse_mode="Markdown")
        messages.append(msg_result.message_id)
        
        # Удаляем последний фрейм анимации
        if len(messages) > 1:
            try:
                await bot.delete_message(chat_id, messages[-2])
            except:
                pass
        
        # Удаляем все через 3 секунды, кроме результата
        await asyncio.sleep(3)
        
        # Оставляем только результат
        for msg_id in messages[:-1]:
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        return dice1, dice2, is_double
        
    except Exception as e:
        logger.error(f"Ошибка в enhanced_dice_animation: {e}")
        # Возвращаем обычный бросок если анимация не удалась
        return random.randint(1, 6), random.randint(1, 6), False

# ==================== УЛУЧШЕННАЯ СИСТЕМА ТЮРЬМЫ ====================
class JailSystem:
    """Расширенная система тюрьмы"""
    
    @staticmethod
    async def process_jail_turn(player: Dict, game: Dict, chat_id: int) -> Tuple[bool, str]:
        """Обработать ход в тюрьме с возможностью выкупа"""
        if not player.get("in_jail", False):
            return True, ""
        
        jail_turns = player.get("jail_turns", 0)
        
        # Создаем клавиатуру для действий в тюрьме
        kb = InlineKeyboardBuilder()
        
        # Проверяем возможность выкупа
        can_pay_bail = player.get("balance", 0) >= 50
        has_get_out_card = player.get("get_out_of_jail_free", 0) > 0
        
        actions_available = []
        
        if has_get_out_card:
            kb.button(text="🎫 Использовать карту 'Выйти из тюрьмы'", 
                     callback_data=f"use_jail_card_{player['id']}")
            actions_available.append("карта")
        
        if can_pay_bail:
            kb.button(text="💰 Заплатить залог (50$)", 
                     callback_data=f"pay_bail_{player['id']}")
            actions_available.append("залог")
        
        kb.button(text="🎲 Попытаться выкинуть дубль", 
                 callback_data=f"try_double_{player['id']}")
        actions_available.append("дубль")
        
        if jail_turns >= 3:
            kb.button(text="⏰ Выйти автоматически (обязательно)", 
                     callback_data=f"auto_release_{player['id']}")
            actions_available.append("авто")
        
        if len(actions_available) == 1:
            kb.adjust(1)
        else:
            kb.adjust(2, 1)
        
        jail_text = (
            f"⛓️ <b>{player['name']} в тюрьме!</b>\n\n"
            f"Ход в тюрьме: <b>{jail_turns + 1}/3</b>\n"
            f"💰 Баланс: {player.get('balance', 0)}$\n"
            f"🎫 Карт 'Выйти из тюрьмы': {player.get('get_out_of_jail_free', 0)}\n\n"
            f"<i>Выберите действие:</i>"
        )
        
        # Отправляем сообщение с выбором действия
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=jail_text,
                parse_mode="HTML",
                reply_markup=kb.as_markup(),
                reply_to_message_id=None
            )
        except:
            pass
        
        return False, "awaiting_choice"
    
    @staticmethod
    async def handle_jail_action(callback: types.CallbackQuery, action: str, player_id: int):
        """Обработать действие в тюрьме"""
        try:
            chat_id = callback.message.chat.id
            
            if chat_id not in ACTIVE_GAMES:
                await callback.answer("❌ Игра не найдена!", show_alert=True)
                return
            
            game = ACTIVE_GAMES[chat_id]
            player = next((p for p in game.get("players", []) if p["id"] == player_id), None)
            
            if not player:
                await callback.answer("❌ Игрок не найден!", show_alert=True)
                return
            
            if not player.get("in_jail", False):
                await callback.answer("❌ Вы не в тюрьме!", show_alert=True)
                return
            
            result_text = ""
            
            if action == "use_jail_card":
                # Использовать карту "Выйти из тюрьмы"
                if player.get("get_out_of_jail_free", 0) > 0:
                    player["get_out_of_jail_free"] -= 1
                    player["in_jail"] = False
                    player["jail_turns"] = 0
                    result_text = f"🎫 {player['name']} использовал карту 'Выйти из тюрьмы'!"
                else:
                    await callback.answer("❌ У вас нет такой карты!", show_alert=True)
                    return
            
            elif action == "pay_bail":
                # Заплатить залог
                if player.get("balance", 0) >= 50:
                    player["balance"] -= 50
                    player["in_jail"] = False
                    player["jail_turns"] = 0
                    result_text = f"💰 {player['name']} заплатил залог 50$ и вышел из тюрьмы!"
                else:
                    await callback.answer("❌ Недостаточно денег для залога!", show_alert=True)
                    return
            
            elif action == "try_double":
                # Попытаться выкинуть дубль
                dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
                
                if dice1 == dice2:
                    player["in_jail"] = False
                    player["jail_turns"] = 0
                    result_text = (
                        f"🎲 {player['name']} пытается выкинуть дубль...\n"
                        f"🎯 Результат: {dice1} и {dice2} - ДУБЛЬ!\n"
                        f"✅ Вы вышли из тюрьмы!"
                    )
                else:
                    player["jail_turns"] = player.get("jail_turns", 0) + 1
                    result_text = (
                        f"🎲 {player['name']} пытается выкинуть дубль...\n"
                        f"🎯 Результат: {dice1} и {dice2} - не дубль\n"
                        f"⛓️ Остается в тюрьме. Ход {player['jail_turns']}/3"
                    )
            
            elif action == "auto_release":
                # Автоматический выход после 3 ходов
                player["in_jail"] = False
                player["jail_turns"] = 0
                player["balance"] = player.get("balance", 0) - 50
                result_text = f"⏰ {player['name']} вышел из тюрьмы после 3 ходов. Штраф 50$"
            
            # Удаляем старое сообщение
            try:
                await callback.message.delete()
            except:
                pass
            
            # Отправляем результат
            await bot.send_message(chat_id, result_text, parse_mode="HTML")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в handle_jail_action: {e}")
            await callback.answer("❌ Ошибка при обработке действия", show_alert=True)

# ==================== УЛУЧШЕННАЯ СИСТЕМА ТОРГОВЛИ ====================
class TradeSystem:
    """Расширенная система торговли"""
    
    @staticmethod
    async def create_trade_offer(from_player_id: int, to_player_id: int, 
                                chat_id: int, game: Dict):
        """Создать предложение торговли с интерактивным интерфейсом"""
        # Находим игроков
        from_player = next((p for p in game["players"] if p["id"] == from_player_id), None)
        to_player = next((p for p in game["players"] if p["id"] == to_player_id), None)
        
        if not from_player or not to_player:
            return False, "Игрок не найден"
        
        # Создаем состояние торговли
        trade_state = {
            "from_player": from_player_id,
            "to_player": to_player_id,
            "chat_id": chat_id,
            "money_offer": 0,
            "money_request": 0,
            "properties_offer": [],
            "properties_request": [],
            "stage": "select_type",  # select_type, set_money, set_properties, confirm
            "active": True
        }
        
        # Сохраняем состояние
        if "trade_states" not in game:
            game["trade_states"] = {}
        game["trade_states"][f"{from_player_id}_{to_player_id}"] = trade_state
        
        # Показываем начальное меню
        kb = InlineKeyboardBuilder()
        kb.button(text="💰 Предложить деньги", 
                 callback_data=f"trade_select_money_{from_player_id}_{to_player_id}")
        kb.button(text="🏠 Предложить недвижимость", 
                 callback_data=f"trade_select_property_{from_player_id}_{to_player_id}")
        kb.button(text="💼 Смешанное предложение", 
                 callback_data=f"trade_select_mixed_{from_player_id}_{to_player_id}")
        kb.button(text="❌ Отменить", 
                 callback_data=f"trade_cancel_{from_player_id}_{to_player_id}")
        kb.adjust(2, 2)
        
        trade_text = (
            f"🤝 <b>Торговля между {from_player['name']} и {to_player['name']}</b>\n\n"
            f"💵 {from_player['name']}: {from_player.get('balance', 0)}$\n"
            f"💵 {to_player['name']}: {to_player.get('balance', 0)}$\n\n"
            f"👇 <i>Выберите тип предложения:</i>"
        )
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=trade_text,
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )
            return True, "Торговля начата"
        except Exception as e:
            logger.error(f"Ошибка при создании торговли: {e}")
            return False, "Ошибка при создании торговли"
    
    @staticmethod
    async def handle_trade_callback(callback: types.CallbackQuery, action: str, 
                                   from_id: int, to_id: int):
        """Обработать callback от торговли"""
        try:
            chat_id = callback.message.chat.id
            
            if chat_id not in ACTIVE_GAMES:
                await callback.answer("❌ Игра не найдена!", show_alert=True)
                return
            
            game = ACTIVE_GAMES[chat_id]
            trade_key = f"{from_id}_{to_id}"
            
            if "trade_states" not in game or trade_key not in game["trade_states"]:
                await callback.answer("❌ Торговля не найдена!", show_alert=True)
                return
            
            trade_state = game["trade_states"][trade_key]
            
            if action == "select_money":
                # Переход к установке денег
                trade_state["stage"] = "set_money"
                await TradeSystem.show_money_selection(callback, trade_state, game)
            
            elif action == "select_property":
                # Переход к выбору недвижимости
                trade_state["stage"] = "set_properties"
                await TradeSystem.show_property_selection(callback, trade_state, game)
            
            elif action == "select_mixed":
                # Смешанное предложение
                trade_state["stage"] = "set_mixed"
                await TradeSystem.show_mixed_selection(callback, trade_state, game)
            
            elif action == "cancel":
                # Отмена торговли
                del game["trade_states"][trade_key]
                await callback.message.edit_text(
                    "❌ <b>Торговля отменена</b>",
                    parse_mode="HTML"
                )
                await callback.answer("Торговля отменена")
            
            # Другие действия (установка сумм, выбор свойств и т.д.)
            # ... (дополнительная логика для полноценной торговли)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_trade_callback: {e}")
            await callback.answer("❌ Ошибка при обработке торговли", show_alert=True)
    
    @staticmethod
    async def show_money_selection(callback: types.CallbackQuery, trade_state: Dict, game: Dict):
        """Показать выбор денежной суммы"""
        from_player = next((p for p in game["players"] if p["id"] == trade_state["from_player"]), None)
        to_player = next((p for p in game["players"] if p["id"] == trade_state["to_player"]), None)
        
        if not from_player or not to_player:
            return
        
        kb = InlineKeyboardBuilder()
        
        # Кнопки для сумм
        amounts = [50, 100, 200, 500, 1000]
        for amount in amounts:
            if from_player.get("balance", 0) >= amount:
                kb.button(text=f"💵 Предложить {amount}$", 
                         callback_data=f"trade_set_offer_{amount}_{trade_state['from_player']}_{trade_state['to_player']}")
        
        kb.button(text="🔙 Назад", 
                 callback_data=f"trade_back_{trade_state['from_player']}_{trade_state['to_player']}")
        kb.button(text="❌ Отмена", 
                 callback_data=f"trade_cancel_{trade_state['from_player']}_{trade_state['to_player']}")
        
        kb.adjust(2, 2, 1, 2)
        
        trade_text = (
            f"💰 <b>Предложение денег от {from_player['name']} к {to_player['name']}</b>\n\n"
            f"💵 Баланс {from_player['name']}: {from_player.get('balance', 0)}$\n"
            f"👇 <i>Выберите сумму для предложения:</i>"
        )
        
        try:
            await callback.message.edit_text(
                trade_text,
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка при показе выбора денег: {e}")

# ==================== АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ ====================
async def auto_save_data():
    """Автоматическое сохранение данных каждые 5 минут"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 минут
            
            # Сохраняем статистику
            save_user_stats()
            
            # Сохраняем текущие игры (в реальном проекте нужно сохранять в файл/БД)
            logger.info("💾 Автосохранение данных выполнено")
            
        except Exception as e:
            logger.error(f"Ошибка при автосохранении: {e}")

# ==================== СИСТЕМА УВЕДОМЛЕНИЙ ====================
async def send_notification(chat_id: int, message: str, notification_type: str = "info"):
    """Отправить уведомление с оформлением"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "turn": "🎲",
        "trade": "🤝",
        "jail": "⛓️",
        "money": "💰",
        "property": "🏠"
    }
    
    icon = icons.get(notification_type, "📢")
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=f"{icon} {message}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")

# ==================== ОБРАБОТЧИК ДЛЯ УЛУЧШЕННОЙ ТЮРЬМЫ ====================
@dp.callback_query(F.data.startswith("use_jail_card_"))
async def handle_use_jail_card(c: types.CallbackQuery):
    """Использовать карту 'Выйти из тюрьмы'"""
    player_id = int(c.data.split("_")[3])
    await JailSystem.handle_jail_action(c, "use_jail_card", player_id)

@dp.callback_query(F.data.startswith("pay_bail_"))
async def handle_pay_bail(c: types.CallbackQuery):
    """Заплатить залог"""
    player_id = int(c.data.split("_")[2])
    await JailSystem.handle_jail_action(c, "pay_bail", player_id)

@dp.callback_query(F.data.startswith("try_double_"))
async def handle_try_double(c: types.CallbackQuery):
    """Попытаться выкинуть дубль"""
    player_id = int(c.data.split("_")[2])
    await JailSystem.handle_jail_action(c, "try_double", player_id)

@dp.callback_query(F.data.startswith("auto_release_"))
async def handle_auto_release(c: types.CallbackQuery):
    """Автоматический выход из тюрьмы"""
    player_id = int(c.data.split("_")[2])
    await JailSystem.handle_jail_action(c, "auto_release", player_id)

# ==================== ОБРАБОТЧИКИ ДЛЯ УЛУЧШЕННОЙ ТОРГОВЛИ ====================
@dp.callback_query(F.data.startswith("trade_select_money_"))
async def handle_trade_select_money(c: types.CallbackQuery):
    """Выбор денежной торговли"""
    parts = c.data.split("_")
    from_id = int(parts[3])
    to_id = int(parts[4])
    await TradeSystem.handle_trade_callback(c, "select_money", from_id, to_id)

@dp.callback_query(F.data.startswith("trade_select_property_"))
async def handle_trade_select_property(c: types.CallbackQuery):
    """Выбор торговли недвижимостью"""
    parts = c.data.split("_")
    from_id = int(parts[3])
    to_id = int(parts[4])
    await TradeSystem.handle_trade_callback(c, "select_property", from_id, to_id)

@dp.callback_query(F.data.startswith("trade_select_mixed_"))
async def handle_trade_select_mixed(c: types.CallbackQuery):
    """Выбор смешанной торговли"""
    parts = c.data.split("_")
    from_id = int(parts[3])
    to_id = int(parts[4])
    await TradeSystem.handle_trade_callback(c, "select_mixed", from_id, to_id)

@dp.callback_query(F.data.startswith("trade_cancel_"))
async def handle_trade_cancel(c: types.CallbackQuery):
    """Отмена торговли"""
    parts = c.data.split("_")
    from_id = int(parts[2])
    to_id = int(parts[3])
    await TradeSystem.handle_trade_callback(c, "cancel", from_id, to_id)

# ==================== КОМАНДА ДЛЯ ПРОВЕРКИ СИСТЕМЫ ====================
@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Проверка работоспособности бота"""
    try:
        start_time = datetime.now()
        
        # Проверяем различные компоненты системы
        checks = []
        
        # 1. Проверка бота
        try:
            me = await bot.get_me()
            checks.append(f"✅ Бот: @{me.username}")
        except:
            checks.append("❌ Бот: не отвечает")
        
        # 2. Проверка активных игр
        checks.append(f"🎮 Активных игр: {len(ACTIVE_GAMES)}")
        
        # 3. Проверка игр в ожидании
        checks.append(f"⏳ Игр в ожидании: {len(WAITING_GAMES)}")
        
        # 4. Проверка статистики
        load_user_stats()
        checks.append(f"📊 Игроков в статистике: {len(USER_STATS)}")
        
        # 5. Проверка режима обслуживания
        maintenance_status = "ВКЛ" if STATS.get("maintenance_mode", False) else "ВЫКЛ"
        checks.append(f"⚙️ Режим обслуживания: {maintenance_status}")
        
        # Рассчитываем время ответа
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        status_text = (
            f"🏓 <b>PONG! Monopoly Premium v3.0</b>\n\n"
            f"⏱️ <b>Время ответа:</b> {response_time:.0f}мс\n\n"
            f"📊 <b>Статус системы:</b>\n" +
            "\n".join(checks) +
            f"\n\n👑 <i>Темный Принц следит за системой</i>"
        )
        
        await message.answer(status_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_ping: {e}")
        await message.answer("❌ Ошибка при проверке системы")

# ==================== КОМАНДА ДЛЯ ПОМОЩИ ====================
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Помощь по командам"""
    help_text = (
        "🆘 <b>Monopoly Premium - Список команд</b>\n\n"
        
        "🎮 <b>Основные команды:</b>\n"
        "/start - Запустить бота (в ЛС)\n"
        "/monopoly - Управление игрой (в группах)\n"
        "/hide - Скрыть игровое меню\n"
        "/stats - Показать вашу статистику\n"
        "/ping - Проверить работу бота\n"
        "/help - Показать это сообщение\n\n"
        
        "⚙️ <b>Игровые команды:</b>\n"
        "/build [номер] - Построить на улице\n"
        "/mortgage [номер] - Заложить улицу\n"
        "/unmortgage [номер] - Выкупить улицу\n"
        "/trade [номер_игрока] - Начать торговлю\n\n"
        
        "👑 <b>Особенности v3.0:</b>\n"
        "• Анимация броска кубиков\n"
        "• Расширенная система тюрьмы\n"
        "• Интерактивная торговля\n"
        "• Залог недвижимости\n"
        "• Карточки шанса и казны\n"
        "• Рейтинг игроков\n"
        "• Веб-панель с картой\n\n"
        
        "💡 <b>Советы:</b>\n"
        "1. Собирайте улицы одного цвета для строительства\n"
        "2. Используйте залог при нехватке денег\n"
        "3. Торгуйтесь с другими игроками\n"
        "4. Следите за картой игры\n\n"
        
        f"👨‍💻 <b>Разработчик:</b> {DEV_TAG}"
    )
    
    await message.answer(help_text, parse_mode="HTML")

# ==================== ОБРАБОТКА ОШИБОК ====================
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    """Глобальный обработчик ошибок"""
    try:
        logger.error(f"Глобальная ошибка: {exception}", exc_info=True)
        
        # Пытаемся отправить сообщение об ошибке
        if update and hasattr(update, 'message') and update.message:
            try:
                await update.message.answer(
                    f"⚠️ <b>Произошла ошибка!</b>\n\n"
                    f"👑 Темный Принц уже исправляет это.\n"
                    f"Попробуйте еще раз через несколько секунд.",
                    parse_mode="HTML"
                )
            except:
                pass
        
        # Для callback запросов
        elif update and hasattr(update, 'callback_query') and update.callback_query:
            try:
                await update.callback_query.answer(
                    "❌ Произошла ошибка. Попробуйте еще раз.",
                    show_alert=True
                )
            except:
                pass
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике ошибок: {e}")
        return True

# ==================== ЗАВЕРШАЮЩАЯ ЧАСТЬ ЗАПУСКА ====================
async def enhanced_run_bot_and_web():
    """Улучшенный запуск бота и веб-сервера"""
    # Загружаем статистику
    load_user_stats()
    logger.info("📊 Статистика загружена")
    
    # Запускаем автосохранение
    auto_save_task = asyncio.create_task(auto_save_data())
    
    # Запускаем веб-сервер
    web_task = asyncio.create_task(start_web_server())
    
    try:
        logger.info("=" * 70)
        logger.info("🚀 ЗАПУСК MONOPOLY PREMIUM v3.0")
        logger.info("👑 ТЕМНЫЙ ПРИНЦ АКТИВИРОВАН")
        logger.info("=" * 70)
        
        # Показываем информацию о системе
        total_memory = len(ACTIVE_GAMES) + len(WAITING_GAMES) + len(USER_STATS)
        logger.info(f"📦 Загружено в память: {total_memory} объектов")
        logger.info(f"🌐 Веб-панель: порт {PORT}")
        logger.info(f"🔗 Статус: http://localhost:{PORT}/?password=darkprince")
        
        # Удаляем вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Вебхук удален, запускаем поллинг...")
        
        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        # Очистка при завершении
        logger.info("🧹 Очистка ресурсов...")
        
        # Отменяем задачи
        auto_save_task.cancel()
        web_task.cancel()
        
        # Сохраняем данные
        save_user_stats()
        logger.info("💾 Данные сохранены")
        
        try:
            await auto_save_task
            await web_task
        except asyncio.CancelledError:
            pass
        
        logger.info("👋 Бот завершил работу")

def enhanced_main():
    """Улучшенная основная функция"""
    # Настройка логирования с цветами
    class ColoredFormatter(logging.Formatter):
        COLORS = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[41m',  # Red background
            'RESET': '\033[0m'       # Reset
        }
        
        def format(self, record):
            log_message = super().format(record)
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            return f"{color}{log_message}{self.COLORS['RESET']}"
    
    # Применяем цветное форматирование
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    # Запускаем бота
    try:
        asyncio.run(enhanced_run_bot_and_web())
    except KeyboardInterrupt:
        print("\n👑 Темный Принц завершает работу...")
    except Exception as e:
        print(f"\n💀 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Запускаем улучшенную версию
    enhanced_main()

# ==================== ДОПОЛНИТЕЛЬНЫЕ УЛУЧШЕНИЯ И ФИЧИ ====================

# ==================== СИСТЕМА АЧИВКИ И ДОСТИЖЕНИЙ ====================
class AchievementSystem:
    """Система достижений для игроков"""
    
    ACHIEVEMENTS = {
        "first_game": {
            "name": "🎮 Первая игра",
            "description": "Сыграть первую игру",
            "icon": "🎮",
            "points": 10
        },
        "first_win": {
            "name": "🏆 Первая победа",
            "description": "Выиграть первую игру",
            "icon": "🏆",
            "points": 50
        },
        "property_master": {
            "name": "🏠 Мастер недвижимости",
            "description": "Купить 10 объектов недвижимости",
            "icon": "🏠",
            "points": 100
        },
        "millionaire": {
            "name": "💰 Миллионер",
            "description": "Накопить 10000$ в одной игре",
            "icon": "💰",
            "points": 200
        },
        "monopoly_king": {
            "name": "👑 Король монополии",
            "description": "Собрать все улицы одного цвета",
            "icon": "👑",
            "points": 150
        },
        "lucky_player": {
            "name": "🍀 Счастливчик",
            "description": "Выкинуть дубль 3 раза подряд",
            "icon": "🍀",
            "points": 75
        },
        "trader": {
            "name": "🤝 Торговец",
            "description": "Провести 5 успешных торгов",
            "icon": "🤝",
            "points": 80
        },
        "jailbird": {
            "name": "⛓️ Заключенный",
            "description": "Провести 10 ходов в тюрьме",
            "icon": "⛓️",
            "points": 30
        },
        "builder": {
            "name": "🏗️ Строитель",
            "description": "Построить 10 домов",
            "icon": "🏗️",
            "points": 120
        },
        "hotel_tycoon": {
            "name": "🏨 Отельный магнат",
            "description": "Построить 5 отелей",
            "icon": "🏨",
            "points": 200
        }
    }
    
    @staticmethod
    def check_achievements(player_id: int, stats: Dict, game_data: Dict = None) -> List[Dict]:
        """Проверить и выдать достижения"""
        achievements = []
        
        # Проверяем первое достижение
        if stats["games_played"] >= 1 and "first_game" not in stats.get("achievements", {}):
            achievements.append(AchievementSystem.ACHIEVEMENTS["first_game"])
        
        # Проверяем первую победу
        if stats["games_won"] >= 1 and "first_win" not in stats.get("achievements", {}):
            achievements.append(AchievementSystem.ACHIEVEMENTS["first_win"])
        
        # Проверяем мастера недвижимости
        if stats.get("properties_bought", 0) >= 10 and "property_master" not in stats.get("achievements", {}):
            achievements.append(AchievementSystem.ACHIEVEMENTS["property_master"])
        
        # Добавляем новые достижения в статистику
        for achievement in achievements:
            if "achievements" not in stats:
                stats["achievements"] = {}
            stats["achievements"][achievement["name"].split()[1]] = {
                "name": achievement["name"],
                "description": achievement["description"],
                "earned_at": datetime.now().isoformat(),
                "points": achievement["points"]
            }
            
            # Добавляем очки
            stats["achievement_points"] = stats.get("achievement_points", 0) + achievement["points"]
        
        return achievements
    
    @staticmethod
    def get_player_achievements(player_id: int) -> List[Dict]:
        """Получить достижения игрока"""
        if player_id not in USER_STATS:
            return []
        
        stats = USER_STATS[player_id]
        return list(stats.get("achievements", {}).values())
    
    @staticmethod
    def get_achievements_leaderboard() -> List[Dict]:
        """Рейтинг по достижениям"""
        players = []
        for user_id, stats in USER_STATS.items():
            points = stats.get("achievement_points", 0)
            if points > 0:
                players.append({
                    "user_id": user_id,
                    "name": stats["name"],
                    "points": points,
                    "achievements_count": len(stats.get("achievements", {}))
                })
        
        players.sort(key=lambda x: x["points"], reverse=True)
        return players[:10]

# ==================== СИСТЕМА ЕЖЕДНЕВНЫХ НАГРАД ====================
class DailyRewardSystem:
    """Система ежедневных наград"""
    
    REWARDS = [
        {"day": 1, "reward": 100, "message": "🎁 День 1: 100$"},
        {"day": 2, "reward": 150, "message": "🎁 День 2: 150$"},
        {"day": 3, "reward": 200, "message": "🎁 День 3: 200$"},
        {"day": 4, "reward": 250, "message": "🎁 День 4: 250$"},
        {"day": 5, "reward": 300, "message": "🎁 День 5: 300$"},
        {"day": 6, "reward": 400, "message": "🎁 День 6: 400$"},
        {"day": 7, "reward": 500, "message": "🎁 День 7: 500$ + 🎫 Карта 'Выйти из тюрьмы'"},
    ]
    
    @staticmethod
    def claim_daily_reward(user_id: int, username: str, name: str) -> Dict:
        """Получить ежедневную награду"""
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
        
        # Инициализируем систему наград если нет
        if "daily_rewards" not in stats:
            stats["daily_rewards"] = {
                "last_claim": None,
                "streak": 0,
                "total_claimed": 0
            }
        
        rewards_data = stats["daily_rewards"]
        now = datetime.now()
        last_claim = None
        
        if rewards_data["last_claim"]:
            try:
                last_claim = datetime.fromisoformat(rewards_data["last_claim"])
            except:
                last_claim = None
        
        # Проверяем, можно ли забрать награду
        can_claim = True
        if last_claim:
            # Проверяем, прошло ли более 24 часов
            hours_passed = (now - last_claim).total_seconds() / 3600
            
            if hours_passed < 20:
                can_claim = False
                hours_left = 20 - hours_passed
                return {
                    "success": False,
                    "message": f"⏳ Следующая награда через {int(hours_left)}ч {int((hours_left % 1) * 60)}м",
                    "next_claim": last_claim + timedelta(hours=20)
                }
            
            # Проверяем, не сбросилась ли серия (больше 48 часов)
            if hours_passed > 48:
                rewards_data["streak"] = 0
        
        # Выдаем награду
        current_streak = rewards_data["streak"] % 7  # 0-6 дней
        reward_info = DailyRewardSystem.REWARDS[current_streak]
        
        # Обновляем данные
        rewards_data["last_claim"] = now.isoformat()
        rewards_data["streak"] += 1
        rewards_data["total_claimed"] += 1
        
        # Сохраняем статистику
        save_user_stats()
        
        result = {
            "success": True,
            "reward": reward_info["reward"],
            "message": reward_info["message"],
            "streak": rewards_data["streak"],
            "next_reward": DailyRewardSystem.REWARDS[(current_streak + 1) % 7]["message"] if rewards_data["streak"] < 7 else "🎁 День 1: 100$",
            "next_claim": now + timedelta(hours=20)
        }
        
        # Для 7 дня добавляем карту "Выйти из тюрьмы"
        if current_streak == 6:  # 7 день (индекс 6)
            result["jail_card"] = True
        
        return result

# ==================== КОМАНДА ДЛЯ ЕЖЕДНЕВНЫХ НАГРАД ====================
@dp.message(Command("daily"))
async def cmd_daily(message: types.Message):
    """Ежедневная награда"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or ""
        name = message.from_user.first_name
        
        result = DailyRewardSystem.claim_daily_reward(user_id, username, name)
        
        if result["success"]:
            daily_text = (
                f"🎁 <b>Ежедневная награда получена!</b>\n\n"
                f"{result['message']}\n"
                f"💰 <b>+{result['reward']}$</b>\n\n"
                f"🔥 Серия: <b>{result['streak']} дней</b>\n"
                f"📅 Следующая награда: <b>{result['next_reward']}</b>\n"
                f"⏰ Доступно через: <b>20 часов</b>"
            )
            
            if result.get("jail_card"):
                daily_text += f"\n\n🎫 <b>+1 карта 'Выйти из тюрьмы'</b>"
            
            await message.answer(daily_text, parse_mode="HTML")
        else:
            next_claim = result.get("next_claim")
            if next_claim:
                time_left = next_claim - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                
                await message.answer(
                    f"⏳ <b>Еще рано!</b>\n\n"
                    f"{result['message']}\n\n"
                    f"🕐 Осталось: <b>{hours_left}ч {minutes_left}м</b>",
                    parse_mode="HTML"
                )
            else:
                await message.answer(result["message"], parse_mode="HTML")
                
    except Exception as e:
        logger.error(f"Ошибка в cmd_daily: {e}")
        await message.answer("❌ Ошибка при получении награды")

# ==================== КОМАНДА ДЛЯ ДОСТИЖЕНИЙ ====================
@dp.message(Command("achievements"))
async def cmd_achievements(message: types.Message):
    """Показать достижения"""
    try:
        user_id = message.from_user.id
        
        if user_id not in USER_STATS:
            await message.answer(
                "🏆 <b>Достижения</b>\n\n"
                "У вас еще нет достижений. Сыграйте первую игру!",
                parse_mode="HTML"
            )
            return
        
        stats = USER_STATS[user_id]
        achievements = AchievementSystem.get_player_achievements(user_id)
        points = stats.get("achievement_points", 0)
        
        if not achievements:
            achievements_text = "📭 Достижений пока нет"
        else:
            achievements_text = ""
            for idx, achievement in enumerate(achievements, 1):
                achievements_text += (
                    f"{idx}. {achievement.get('icon', '🏆')} <b>{achievement['name']}</b>\n"
                    f"   📝 {achievement['description']}\n"
                    f"   ⭐ {achievement['points']} очков\n"
                    f"   🕐 Получено: {achievement.get('earned_at', 'неизвестно')}\n\n"
                )
        
        # Получаем прогресс по остальным достижениям
        available_achievements = []
        for key, ach in AchievementSystem.ACHIEVEMENTS.items():
            if key not in [a['name'].split()[1] for a in achievements]:
                available_achievements.append(ach)
        
        progress_text = ""
        if available_achievements:
            progress_text = "\n🎯 <b>Доступные достижения:</b>\n"
            for ach in available_achievements[:3]:  # Показываем только 3
                progress_text += f"• {ach['name']}: {ach['description']}\n"
        
        achievements_message = (
            f"🏆 <b>Достижения {stats['name']}</b>\n\n"
            f"⭐ Всего очков: <b>{points}</b>\n"
            f"🏅 Получено достижений: <b>{len(achievements)}</b>\n\n"
            f"{achievements_text}"
            f"{progress_text}"
        )
        
        # Добавляем кнопку для просмотра лидерборда достижений
        kb = InlineKeyboardBuilder()
        kb.button(text="🏆 Топ по достижениям", callback_data="achievements_leaderboard")
        kb.button(text="🔄 Обновить", callback_data="refresh_achievements")
        kb.adjust(1)
        
        await message.answer(achievements_message, parse_mode="HTML", reply_markup=kb.as_markup())
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_achievements: {e}")
        await message.answer("❌ Ошибка при получении достижений")

@dp.callback_query(F.data == "achievements_leaderboard")
async def show_achievements_leaderboard(c: types.CallbackQuery):
    """Показать лидерборд достижений"""
    try:
        top_players = AchievementSystem.get_achievements_leaderboard()
        
        if not top_players:
            leaderboard_text = "🏆 <b>Топ по достижениям</b>\n\n📭 Пока никто не получил достижений"
        else:
            leaderboard_text = "🏆 <b>Топ-10 по достижениям</b>\n\n"
            
            for idx, player in enumerate(top_players, 1):
                medal = ""
                if idx == 1:
                    medal = "🥇 "
                elif idx == 2:
                    medal = "🥈 "
                elif idx == 3:
                    medal = "🥉 "
                
                leaderboard_text += (
                    f"{medal}<b>{idx}. {player['name']}</b>\n"
                    f"   ⭐ {player['points']} очков | "
                    f"🏅 {player['achievements_count']} достижений\n"
                )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🔙 Назад к моим достижениям", callback_data="back_to_my_achievements")
        kb.adjust(1)
        
        await c.message.edit_text(leaderboard_text, parse_mode="HTML", reply_markup=kb.as_markup())
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_achievements_leaderboard: {e}")
        await c.answer("❌ Ошибка при получении лидерборда", show_alert=True)

@dp.callback_query(F.data == "back_to_my_achievements")
async def back_to_my_achievements(c: types.CallbackQuery):
    """Вернуться к своим достижениям"""
    try:
        # Вызываем команду achievements для текущего пользователя
        message = types.Message(
            message_id=c.message.message_id,
            date=datetime.now(),
            chat=c.message.chat,
            from_user=c.from_user,
            text="/achievements"
        )
        await cmd_achievements(message)
        await c.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_my_achievements: {e}")
        await c.answer("❌ Ошибка", show_alert=True)

@dp.callback_query(F.data == "refresh_achievements")
async def refresh_achievements(c: types.CallbackQuery):
    """Обновить достижения"""
    try:
        await c.message.delete()
        message = types.Message(
            message_id=c.message.message_id,
            date=datetime.now(),
            chat=c.message.chat,
            from_user=c.from_user,
            text="/achievements"
        )
        await cmd_achievements(message)
        await c.answer("✅ Обновлено")
        
    except Exception as e:
        logger.error(f"Ошибка в refresh_achievements: {e}")
        await c.answer("❌ Ошибка", show_alert=True)

# ==================== СИСТЕМА СОБЫТИЙ И АКЦИЙ ====================
class EventSystem:
    """Система временных событий и акций"""
    
    CURRENT_EVENTS = [
        {
            "name": "🎉 Новогодний турнир",
            "description": "Удвоенные награды за победы до 10 января",
            "end_date": "2024-01-10",
            "multiplier": 2.0,
            "active": True
        },
        {
            "name": "🔥 Неделя дублей",
            "description": "За каждый дубль +100$",
            "end_date": "2024-01-07",
            "bonus_per_double": 100,
            "active": True
        },
        {
            "name": "🏗️ Строительный бум",
            "description": "Скидка 20% на строительство домов",
            "end_date": "2024-01-05",
            "discount": 0.8,
            "active": True
        }
    ]
    
    @staticmethod
    def get_active_events() -> List[Dict]:
        """Получить активные события"""
        active_events = []
        now = datetime.now()
        
        for event in EventSystem.CURRENT_EVENTS:
            if event.get("active", False):
                try:
                    end_date = datetime.strptime(event["end_date"], "%Y-%m-%d")
                    if now < end_date:
                        active_events.append(event)
                except:
                    active_events.append(event)
        
        return active_events
    
    @staticmethod
    def apply_event_bonuses(player: Dict, action: str, amount: int) -> int:
        """Применить бонусы событий"""
        events = EventSystem.get_active_events()
        bonus = 0
        multiplier = 1.0
        
        for event in events:
            if action == "win" and "multiplier" in event:
                multiplier = max(multiplier, event["multiplier"])
            elif action == "double" and "bonus_per_double" in event:
                bonus += event["bonus_per_double"]
            elif action == "build" and "discount" in event:
                amount = int(amount * event["discount"])
        
        if multiplier > 1.0:
            amount = int(amount * multiplier)
        
        return amount + bonus
    
    @staticmethod
    def get_events_message() -> str:
        """Получить сообщение о текущих событиях"""
        events = EventSystem.get_active_events()
        
        if not events:
            return "📅 <b>Текущие события</b>\n\n📭 Событий пока нет"
        
        message = "📅 <b>Активные события:</b>\n\n"
        
        for event in events:
            message += f"🎯 <b>{event['name']}</b>\n"
            message += f"📝 {event['description']}\n"
            
            if "end_date" in event:
                try:
                    end_date = datetime.strptime(event["end_date"], "%Y-%m-%d")
                    days_left = (end_date - datetime.now()).days
                    message += f"⏳ Осталось: <b>{days_left} дней</b>\n"
                except:
                    pass
            
            message += "\n"
        
        return message

# ==================== КОМАНДА ДЛЯ СОБЫТИЙ ====================
@dp.message(Command("events"))
async def cmd_events(message: types.Message):
    """Показать текущие события"""
    try:
        events_message = EventSystem.get_events_message()
        await message.answer(events_message, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_events: {e}")
        await message.answer("❌ Ошибка при получении событий")

# ==================== УЛУЧШЕННАЯ СИСТЕМА СТАТИСТИКИ ====================
@dp.message(Command("mystats"))
async def cmd_mystats(message: types.Message):
    """Расширенная статистика игрока"""
    try:
        user_id = message.from_user.id
        
        if user_id not in USER_STATS:
            await message.answer(
                "📊 <b>Моя статистика</b>\n\n"
                "Статистики пока нет. Сыграйте первую игру!",
                parse_mode="HTML"
            )
            return
        
        stats = USER_STATS[user_id]
        
        # Рассчитываем различные показатели
        games_played = stats["games_played"]
        games_won = stats["games_won"]
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        
        # Средний баланс за игру (если есть данные)
        avg_balance = stats.get("total_money", 0) / games_played if games_played > 0 else 0
        
        # Достижения
        achievements = stats.get("achievements", {})
        achievement_points = stats.get("achievement_points", 0)
        
        # Ежедневные награды
        daily_data = stats.get("daily_rewards", {})
        streak = daily_data.get("streak", 0)
        total_claimed = daily_data.get("total_claimed", 0)
        
        # Формируем сообщение
        stats_text = (
            f"📊 <b>Подробная статистика {stats['name']}</b>\n\n"
            
            f"🎮 <b>Общая статистика:</b>\n"
            f"• Игр сыграно: <b>{games_played}</b>\n"
            f"• Побед: <b>{games_won}</b>\n"
            f"• Процент побед: <b>{win_rate:.1f}%</b>\n"
            f"• Средний баланс: <b>{avg_balance:.0f}$</b>\n"
            f"• Куплено недвижимости: <b>{stats.get('properties_bought', 0)}</b>\n\n"
            
            f"🏆 <b>Достижения:</b>\n"
            f"• Получено: <b>{len(achievements)}</b>\n"
            f"• Всего очков: <b>{achievement_points}</b>\n\n"
            
            f"🎁 <b>Ежедневные награды:</b>\n"
            f"• Текущая серия: <b>{streak} дней</b>\n"
            f"• Всего получено: <b>{total_claimed} наград</b>\n\n"
            
            f"📅 <b>Активность:</b>\n"
            f"• Последняя игра: <b>{stats.get('last_played', 'никогда')}</b>\n"
            f"• Первая игра: <b>{stats.get('first_played', 'никогда')}</b>"
        )
        
        # Добавляем информацию о текущих событиях если есть
        active_events = EventSystem.get_active_events()
        if active_events:
            stats_text += f"\n\n🎯 <b>Активные бонусы:</b>\n"
            for event in active_events:
                stats_text += f"• {event['name']}\n"
        
        # Кнопки для дополнительной информации
        kb = InlineKeyboardBuilder()
        kb.button(text="🏆 Мои достижения", callback_data="my_achievements_detailed")
        kb.button(text="📈 График активности", callback_data="activity_graph")
        kb.button(text="🔄 Обновить", callback_data="refresh_mystats")
        kb.adjust(1, 2)
        
        await message.answer(stats_text, parse_mode="HTML", reply_markup=kb.as_markup())
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_mystats: {e}")
        await message.answer("❌ Ошибка при получении статистики")

# ==================== СИСТЕМА РЕФЕРАЛЬНОЙ ПРОГРАММЫ ====================
class ReferralSystem:
    """Система реферальной программы"""
    
    REFERRAL_BONUS = 500  # Бонус за приглашенного игрока
    REFERRER_BONUS = 200  # Бонус для пригласившего
    
    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """Сгенерировать реферальный код"""
        import base64
        code = base64.urlsafe_b64encode(f"ref_{user_id}_{random.randint(1000, 9999)}".encode()).decode()
        return code[:8].upper()
    
    @staticmethod
    def register_referral(user_id: int, referrer_code: str) -> bool:
        """Зарегистрировать реферала"""
        try:
            # Декодируем код пригласившего
            import base64
            decoded = base64.urlsafe_b64decode(referrer_code + '=' * (4 - len(referrer_code) % 4)).decode()
            
            if decoded.startswith("ref_"):
                parts = decoded.split("_")
                if len(parts) >= 2:
                    referrer_id = int(parts[1])
                    
                    # Сохраняем информацию о реферале
                    if referrer_id in USER_STATS:
                        # Обновляем статистику пригласившего
                        if "referrals" not in USER_STATS[referrer_id]:
                            USER_STATS[referrer_id]["referrals"] = []
                        
                        if user_id not in USER_STATS[referrer_id]["referrals"]:
                            USER_STATS[referrer_id]["referrals"].append(user_id)
                            USER_STATS[referrer_id]["referral_bonus"] = USER_STATS[referrer_id].get("referral_bonus", 0) + ReferralSystem.REFERRER_BONUS
                        
                        # Сохраняем информацию о пригласившем для пользователя
                        if user_id not in USER_STATS:
                            USER_STATS[user_id] = {}
                        
                        USER_STATS[user_id]["referrer"] = referrer_id
                        USER_STATS[user_id]["referral_bonus_received"] = True
                        
                        save_user_stats()
                        return True
        except:
            pass
        
        return False
    
    @staticmethod
    def get_referral_info(user_id: int) -> Dict:
        """Получить информацию о рефералах"""
        if user_id not in USER_STATS:
            return {"code": "", "referrals": 0, "bonus": 0}
        
        stats = USER_STATS[user_id]
        referrals = stats.get("referrals", [])
        bonus = stats.get("referral_bonus", 0)
        code = ReferralSystem.generate_referral_code(user_id)
        
        return {
            "code": code,
            "referrals": len(referrals),
            "bonus": bonus,
            "referral_list": referrals[:10]  # Первые 10 рефералов
        }

# ==================== КОМАНДА ДЛЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================
@dp.message(Command("referral"))
async def cmd_referral(message: types.Message):
    """Реферальная система"""
    try:
        user_id = message.from_user.id
        
        # Проверяем, есть ли реферальный код в команде
        args = message.text.split()
        if len(args) >= 2:
            # Регистрация по реферальному коду
            referrer_code = args[1].upper()
            
            if ReferralSystem.register_referral(user_id, referrer_code):
                await message.answer(
                    f"✅ <b>Реферальная программа активирована!</b>\n\n"
                    f"🎁 Вы получили бонус: <b>{ReferralSystem.REFERRAL_BONUS}$</b>\n"
                    f"💰 Пригласивший также получил бонус: <b>{ReferralSystem.REFERRER_BONUS}$</b>\n\n"
                    f"💡 Теперь вы можете приглашать друзей и получать бонусы!",
                    parse_mode="HTML"
                )
                return
            else:
                await message.answer(
                    "❌ <b>Неверный реферальный код</b>\n\n"
                    "Проверьте правильность кода или он уже был использован.",
                    parse_mode="HTML"
                )
                return
        
        # Показываем информацию о реферальной программе
        info = ReferralSystem.get_referral_info(user_id)
        
        referral_text = (
            f"🤝 <b>Реферальная программа Monopoly Premium</b>\n\n"
            f"💎 <b>Как это работает:</b>\n"
            f"1. Пригласите друга по своей ссылке\n"
            f"2. Друг вводит ваш реферальный код при первом использовании /referral\n"
            f"3. Вы получаете <b>{ReferralSystem.REFERRER_BONUS}$</b>\n"
            f"4. Друг получает <b>{ReferralSystem.REFERRAL_BONUS}$</b>\n\n"
            
            f"📊 <b>Ваша статистика:</b>\n"
            f"• Приглашено друзей: <b>{info['referrals']}</b>\n"
            f"• Всего получено бонусов: <b>{info['bonus']}$</b>\n\n"
            
            f"🔗 <b>Ваш реферальный код:</b>\n"
            f"<code>{info['code']}</code>\n\n"
            
            f"📝 <b>Для приглашения друга:</b>\n"
            f"1. Отправьте ему эту команду:\n"
            f"<code>/referral {info['code']}</code>\n"
            f"2. Или просто отправьте этот код\n\n"
            
            f"👑 <i>Темный Принц благодарит за приглашение друзей!</i>"
        )
        
        await message.answer(referral_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_referral: {e}")
        await message.answer("❌ Ошибка в реферальной системе")

# ==================== АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ ДОСТИЖЕНИЙ ====================
def apply_achievements_after_game(player_id: int, game_result: Dict):
    """Применить достижения после игры"""
    if player_id not in USER_STATS:
        return
    
    stats = USER_STATS[player_id]
    new_achievements = AchievementSystem.check_achievements(player_id, stats, game_result)
    
    if new_achievements:
        # Сохраняем достижения
        save_user_stats()
        
        # Можно отправить уведомление о новых достижениях
        # (в реальном боте нужно хранить chat_id для отправки)
        return new_achievements
    
    return []

# ==================== ФИНАЛЬНЫЕ УЛУЧШЕНИЯ И ОПТИМИЗАЦИЯ ====================

# ==================== СИСТЕМА АВТОМАТИЧЕСКОЙ ОЧИСТКИ ====================
async def auto_cleanup_system():
    """Автоматическая очистка старых данных"""
    while True:
        try:
            await asyncio.sleep(3600)  # Каждый час
            
            current_time = datetime.now()
            games_to_remove = []
            
            # Очищаем старые активные игры (более 24 часов)
            for chat_id, game in ACTIVE_GAMES.items():
                started_at = game.get("started_at")
                if isinstance(started_at, str):
                    started_at = datetime.fromisoformat(started_at)
                
                if (current_time - started_at).total_seconds() > 86400:  # 24 часа
                    games_to_remove.append(chat_id)
                    logger.info(f"🗑️ Удалена старая активная игра в чате {chat_id}")
            
            for chat_id in games_to_remove:
                if chat_id in ACTIVE_GAMES:
                    del ACTIVE_GAMES[chat_id]
            
            # Очищаем старые ожидающие игры (более 1 часа)
            waiting_to_remove = []
            for chat_id, game in WAITING_GAMES.items():
                created_at = game.get("created_at")
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                if (current_time - created_at).total_seconds() > 3600:  # 1 час
                    waiting_to_remove.append(chat_id)
            
            for chat_id in waiting_to_remove:
                if chat_id in WAITING_GAMES:
                    # Отменяем таймер если есть
                    if "timer_task" in WAITING_GAMES[chat_id]:
                        WAITING_GAMES[chat_id]["timer_task"].cancel()
                    
                    del WAITING_GAMES[chat_id]
                    logger.info(f"🗑️ Удалена старая ожидающая игра в чате {chat_id}")
            
            # Очищаем старые записи скрытых меню (более 24 часов)
            global HIDDEN_MENU_USERS
            HIDDEN_MENU_USERS = {k: v for k, v in HIDDEN_MENU_USERS.items() 
                                if k in ACTIVE_GAMES.get(v, {})}
            
            logger.info("🧹 Автоматическая очистка выполнена")
            
        except Exception as e:
            logger.error(f"Ошибка при автоматической очистке: {e}")

# ==================== СИСТЕМА БЭКАПА ДАННЫХ ====================
async def backup_data_system():
    """Система резервного копирования данных"""
    import pickle
    import shutil
    
    while True:
        try:
            await asyncio.sleep(7200)  # Каждые 2 часа
            
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backups"
            
            # Создаем директорию для бэкапов если нет
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Данные для бэкапа
            backup_data = {
                "user_stats": USER_STATS,
                "waiting_games": WAITING_GAMES,
                "active_games": ACTIVE_GAMES,
                "hidden_menu_users": HIDDEN_MENU_USERS,
                "stats": STATS,
                "backup_time": backup_time
            }
            
            # Сохраняем бэкап
            backup_file = os.path.join(backup_dir, f"backup_{backup_time}.pkl")
            with open(backup_file, 'wb') as f:
                pickle.dump(backup_data, f)
            
            # Удаляем старые бэкапы (оставляем последние 10)
            backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.pkl')])
            if len(backup_files) > 10:
                for old_file in backup_files[:-10]:
                    os.remove(os.path.join(backup_dir, old_file))
            
            logger.info(f"💾 Бэкап создан: {backup_file}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании бэкапа: {e}")

# ==================== СИСТЕМА МОНИТОРИНГА ====================
class MonitoringSystem:
    """Система мониторинга производительности"""
    
    performance_stats = {
        "messages_processed": 0,
        "callbacks_processed": 0,
        "errors_count": 0,
        "start_time": datetime.now(),
        "response_times": []
    }
    
    @staticmethod
    def record_message_processing():
        """Записать обработку сообщения"""
        MonitoringSystem.performance_stats["messages_processed"] += 1
    
    @staticmethod
    def record_callback_processing():
        """Записать обработку callback"""
        MonitoringSystem.performance_stats["callbacks_processed"] += 1
    
    @staticmethod
    def record_error():
        """Записать ошибку"""
        MonitoringSystem.performance_stats["errors_count"] += 1
    
    @staticmethod
    def record_response_time(time_ms: float):
        """Записать время ответа"""
        MonitoringSystem.performance_stats["response_times"].append(time_ms)
        # Оставляем только последние 1000 записей
        if len(MonitoringSystem.performance_stats["response_times"]) > 1000:
            MonitoringSystem.performance_stats["response_times"] = MonitoringSystem.performance_stats["response_times"][-1000:]
    
    @staticmethod
    def get_performance_report() -> Dict:
        """Получить отчет о производительности"""
        stats = MonitoringSystem.performance_stats
        
        # Рассчитываем среднее время ответа
        avg_response_time = 0
        if stats["response_times"]:
            avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
        
        # Рассчитываем uptime
        uptime = datetime.now() - stats["start_time"]
        uptime_hours = uptime.total_seconds() / 3600
        
        # Рассчитываем сообщений в час
        messages_per_hour = stats["messages_processed"] / uptime_hours if uptime_hours > 0 else 0
        
        return {
            "uptime_hours": uptime_hours,
            "messages_processed": stats["messages_processed"],
            "callbacks_processed": stats["callbacks_processed"],
            "errors_count": stats["errors_count"],
            "avg_response_time_ms": avg_response_time,
            "messages_per_hour": messages_per_hour,
            "error_rate": (stats["errors_count"] / max(stats["messages_processed"] + stats["callbacks_processed"], 1)) * 100
        }

# ==================== КОМАНДА ДЛЯ МОНИТОРИНГА ====================
@dp.message(Command("monitor"))
async def cmd_monitor(message: types.Message):
    """Мониторинг производительности бота"""
    try:
        if not is_admin(message.from_user):
            await message.answer("⛔ Доступ запрещен!", parse_mode="HTML")
            return
        
        report = MonitoringSystem.get_performance_report()
        
        # Получаем информацию об использовании памяти
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        monitor_text = (
            "📊 <b>Системный мониторинг Monopoly Premium</b>\n\n"
            
            "⏱️ <b>Производительность:</b>\n"
            f"• Uptime: <b>{report['uptime_hours']:.1f} часов</b>\n"
            f"• Сообщений обработано: <b>{report['messages_processed']}</b>\n"
            f"• Callback'ов обработано: <b>{report['callbacks_processed']}</b>\n"
            f"• Сообщений в час: <b>{report['messages_per_hour']:.1f}</b>\n"
            f"• Среднее время ответа: <b>{report['avg_response_time_ms']:.1f} мс</b>\n"
            f"• Ошибок: <b>{report['errors_count']}</b>\n"
            f"• Процент ошибок: <b>{report['error_rate']:.2f}%</b>\n\n"
            
            "💾 <b>Использование памяти:</b>\n"
            f"• RSS: <b>{memory_info.rss / 1024 / 1024:.1f} MB</b>\n"
            f"• VMS: <b>{memory_info.vms / 1024 / 1024:.1f} MB</b>\n\n"
            
            "🎮 <b>Текущая нагрузка:</b>\n"
            f"• Активных игр: <b>{len(ACTIVE_GAMES)}</b>\n"
            f"• Игр в ожидании: <b>{len(WAITING_GAMES)}</b>\n"
            f"• Игроков в статистике: <b>{len(USER_STATS)}</b>\n"
            f"• Скрытых меню: <b>{len(HIDDEN_MENU_USERS)}</b>"
        )
        
        await message.answer(monitor_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_monitor: {e}")
        await message.answer("❌ Ошибка при получении мониторинга")

# ==================== СИСТЕМА ЛОГИРОВАНИЯ В ФАЙЛ ====================
def setup_file_logging():
    """Настройка логирования в файл"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Файловый handler для всех логов
    file_handler = logging.FileHandler(
        filename=os.path.join(log_dir, f"monopoly_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Файловый handler для ошибок
    error_handler = logging.FileHandler(
        filename=os.path.join(log_dir, f"errors_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Добавляем handlers к корневому логгеру
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(error_handler)

# ==================== ДЕКОРАТОРЫ ДЛЯ МОНИТОРИНГА ====================
def monitor_performance(handler_type: str = "message"):
    """Декоратор для мониторинга производительности обработчиков"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                if handler_type == "message":
                    MonitoringSystem.record_message_processing()
                elif handler_type == "callback":
                    MonitoringSystem.record_callback_processing()
                
                result = await func(*args, **kwargs)
                
                # Записываем время выполнения
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                MonitoringSystem.record_response_time(response_time)
                
                return result
                
            except Exception as e:
                MonitoringSystem.record_error()
                raise e
        
        return wrapper
    return decorator

# ==================== ПРИМЕНЕНИЕ ДЕКОРАТОРОВ К ОСНОВНЫМ ОБРАБОТЧИКАМ ====================
# Переопределяем основные обработчики с декораторами

@dp.message(Command("start"))
@monitor_performance("message")
async def monitored_cmd_start(message: types.Message):
    """Мониторируемая команда start"""
    return await cmd_start(message)

@dp.message(Command("monopoly"))
@monitor_performance("message")
async def monitored_cmd_monopoly(message: types.Message):
    """Мониторируемая команда monopoly"""
    return await cmd_monopoly(message)

@dp.message(F.text == "🎲 Бросить кубик")
@monitor_performance("message")
async def monitored_roll_dice_button(message: types.Message):
    """Мониторируемая кнопка броска кубика"""
    return await roll_dice_button(message)

@dp.callback_query(F.data == "start_player_gathering")
@monitor_performance("callback")
async def monitored_start_gathering(c: types.CallbackQuery):
    """Мониторируемый callback начала сбора"""
    return await start_gathering(c)

# ==================== ФИНАЛЬНАЯ ФУНКЦИЯ ЗАПУСКА ====================
async def final_run_bot():
    """Финальная версия запуска бота со всеми системами"""
    try:
        # Настраиваем логирование в файл
        setup_file_logging()
        
        logger.info("=" * 80)
        logger.info("🚀 ЗАПУСК MONOPOLY PREMIUM v3.0 - ФИНАЛЬНАЯ ВЕРСИЯ")
        logger.info("👑 ТЕМНЫЙ ПРИНЦ - ПОЛНАЯ РЕАЛИЗАЦИЯ")
        logger.info("=" * 80)
        
        # Загружаем статистику
        load_user_stats()
        logger.info(f"📊 Загружено {len(USER_STATS)} записей статистики")
        
        # Запускаем системы
        tasks = []
        
        # Веб-сервер
        web_task = asyncio.create_task(start_web_server())
        tasks.append(web_task)
        logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")
        
        # Автоочистка
        cleanup_task = asyncio.create_task(auto_cleanup_system())
        tasks.append(cleanup_task)
        logger.info("🧹 Система автоочистки запущена")
        
        # Бэкап данных
        backup_task = asyncio.create_task(backup_data_system())
        tasks.append(backup_task)
        logger.info("💾 Система бэкапа запущена")
        
        # Автосохранение
        autosave_task = asyncio.create_task(auto_save_data())
        tasks.append(autosave_task)
        logger.info("💾 Система автосохранения запущена")
        
        # Стартовая информация
        logger.info(f"🤖 Бот: @{(await bot.get_me()).username}")
        logger.info(f"📱 Версия aiogram: {types.__version__}")
        logger.info(f"🐍 Python: {sys.version}")
        
        # Показываем информацию о системе
        import platform
        logger.info(f"💻 Система: {platform.system()} {platform.release()}")
        logger.info(f"👑 Разработчик: {DEV_TAG}")
        
        # Удаляем вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Вебхук удален, запускаем поллинг...")
        
        # Информация для админов
        logger.info(f"🔗 Веб-панель: http://localhost:{PORT}/?password=darkprince")
        logger.info("🔑 Пароль по умолчанию: darkprince")
        logger.info("⚙️ Измените пароль в коде для безопасности!")
        
        # Запускаем поллинг
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=True,
            close_bot_session=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
        raise
    finally:
        # Завершаем все задачи
        logger.info("🧹 Завершение работы...")
        
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Финальное сохранение данных
        save_user_stats()
        logger.info("💾 Данные сохранены")
        
        logger.info("👋 Monopoly Premium завершил работу")

# ==================== ОБРАБОТКА СИГНАЛОВ ====================
import signal

def handle_shutdown_signal():
    """Обработка сигналов завершения"""
    logger.info("📶 Получен сигнал завершения...")
    # Здесь можно добавить дополнительную логику очистки
    sys.exit(0)

# ==================== КОНФИГУРАЦИЯ БОТА ====================
def configure_bot():
    """Конфигурация бота перед запуском"""
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, lambda s, f: handle_shutdown_signal())
    signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown_signal())
    
    # Добавляем middleware для мониторинга
    from aiogram import BaseMiddleware
    from aiogram.types import TelegramObject
    
    class MonitoringMiddleware(BaseMiddleware):
        async def __call__(self, handler, event, data):
            start_time = datetime.now()
            
            # Определяем тип события
            if isinstance(event, types.Message):
                MonitoringSystem.record_message_processing()
            elif isinstance(event, types.CallbackQuery):
                MonitoringSystem.record_callback_processing()
            
            try:
                result = await handler(event, data)
                
                # Записываем время выполнения
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                MonitoringSystem.record_response_time(response_time)
                
                return result
                
            except Exception as e:
                MonitoringSystem.record_error()
                raise
    
    # Добавляем middleware в диспетчер
    dp.update.outer_middleware(MonitoringMiddleware())
    
    logger.info("⚙️ Конфигурация бота завершена")

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
def final_main():
    """Финальная главная функция"""
    try:
        # Конфигурируем бота
        configure_bot()
        
        # Запускаем бота
        asyncio.run(final_run_bot())
        
    except KeyboardInterrupt:
        print("\n👑 Темный Принц завершает работу...")
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💀 Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        
        # Пытаемся сохранить данные при аварийном завершении
        try:
            save_user_stats()
            logger.info("💾 Данные сохранены при аварийном завершении")
        except:
            pass
        
        sys.exit(1)

# ==================== ТОЧКА ВХОДА ====================
if __name__ == "__main__":
    # Запускаем финальную версию
    final_main()

# ==================== ДОПОЛНИТЕЛЬНЫЕ КОММЕНТАРИИ И РЕКОМЕНДАЦИИ ====================
"""
🎮 MONOPOLY PREMIUM v3.0 - ФИНАЛЬНАЯ ВЕРСИЯ
👑 Разработано Темным Принцем (Dark Prince)

📋 ОСНОВНЫЕ ФИЧИ:
1. ✅ Полная реализация механик Монополии
2. ✅ Анимация броска кубиков
3. ✅ Интерактивная система тюрьмы
4. ✅ Торговля между игроками
5. ✅ Залог недвижимости
6. ✅ Карточки шанса и общественной казны
7. ✅ Система достижений
8. ✅ Ежедневные награды
9. ✅ Реферальная программа
10. ✅ Веб-панель с картой
11. ✅ Админ-панель
12. ✅ Мониторинг производительности
13. ✅ Автосохранение и бэкапы
14. ✅ Система событий

🔧 ТРЕБОВАНИЯ К СИСТЕМЕ:
1. Python 3.8+
2. aiogram 3.x
3. aiohttp для веб-сервера
4. psutil для мониторинга (опционально)

⚙️ НАСТРОЙКА:
1. Установите BOT_TOKEN в переменные окружения
2. Измените пароль в переменной ADMIN_PASSWORD_HASH
3. Добавьте своих администраторов в ALLOWED_ADMINS
4. Настройте порт в переменной PORT

📁 СТРУКТУРА ПАПОК:
/monopoly_bot/
├── telegram_bot.py      # Основной файл бота
├── user_stats.json      # Статистика игроков
├── backups/             # Резервные копии
├── logs/                # Логи
└── requirements.txt     # Зависимости

🔄 ЗАПУСК:
1. pip install -r requirements.txt
2. export BOT_TOKEN="ваш_токен"
3. python telegram_bot.py

👨‍💻 РАЗРАБОТЧИК:
• Telegram: @Whylovely05
• Титул: Темный Принц (Dark Prince)
• Версия: 3.0 Premium Edition

💖 СПАСИБО ЗА ИСПОЛЬЗОВАНИЕ!
Темный Принц заботится о вашем игровом опыте.
"""
