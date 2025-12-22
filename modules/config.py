"""
CONFIG.PY - Конфигурация и константы бота
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import os
import logging
from datetime import datetime
import json
from typing import Dict, List, Tuple, Any

# ==================== БАЗОВЫЕ НАСТРОЙКИ ====================
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    logging.error("❌ BOT_TOKEN не найден! Установи переменную окружения BOT_TOKEN")
    exit(1)

PORT = int(os.environ.get("PORT", 8083))
DEV_TAG = "@Whylovely05"
MAINTENANCE_MSG = "👑 Бот обновляется, Темный принц уже исправляет это ♥️"
BANNER = "┏━━━━━━━━━━━━━━━━━━┓\n┃  Monopoly Premium  ┃\n┗━━━━━━━━━━━━━━━━━━┛"

# Админы бота (Telegram ID)
ADMINS = [123456789, 987654321]  # Добавь свой ID первым

# Время ожидания в лобби (3 минуты)
LOBBY_TIMEOUT = 180  # секунды

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monopoly_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
# Инициализируются в main.py
WAITING_GAMES: Dict[int, Dict] = {}
ACTIVE_GAMES: Dict[int, Dict] = {}
HIDDEN_MENU_USERS: Dict[int, int] = {}
GAME_STATS: Dict[str, Any] = {
    "maintenance_mode": False,
    "total_games": 0,
    "active_players": 0
}
USER_STATS: Dict[int, Dict] = {}  # Статистика игроков

# ==================== ДОСКА МОНОПОЛИИ ====================
# 40 клеток, полностью соответствует оригинальной Monopoly
BOARD: Dict[int, Dict[str, Any]] = {
    0: {  # СТАРТ
        "name": "СТАРТ", 
        "price": 0, 
        "rent": [0, 0, 0, 0, 0], 
        "color": "SPECIAL", 
        "type": "start", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    1: {  # Коричневые
        "name": "Житная", 
        "price": 60, 
        "rent": [2, 10, 30, 90, 160, 250], 
        "color": "BROWN", 
        "type": "property", 
        "mortgage": 30,
        "house_cost": 50,
        "hotel_cost": 50
    },
    2: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    3: {
        "name": "Нагатинская", 
        "price": 60, 
        "rent": [4, 20, 60, 180, 320, 450], 
        "color": "BROWN", 
        "type": "property", 
        "mortgage": 30,
        "house_cost": 50,
        "hotel_cost": 50
    },
    4: {  # Налог
        "name": "Налог", 
        "price": 200, 
        "rent": [0], 
        "color": "TAX", 
        "type": "tax", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    5: {  # Железная дорога
        "name": "Рижская ж/д", 
        "price": 200, 
        "rent": [25, 50, 100, 200], 
        "color": "RAIL", 
        "type": "railroad", 
        "mortgage": 100,
        "house_cost": 0,
        "hotel_cost": 0
    },
    6: {  # Голубые
        "name": "Варшавское ш.", 
        "price": 100, 
        "rent": [6, 30, 90, 270, 400, 550], 
        "color": "BLUE", 
        "type": "property", 
        "mortgage": 50,
        "house_cost": 50,
        "hotel_cost": 50
    },
    7: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    8: {
        "name": "Огородный пр.", 
        "price": 100, 
        "rent": [6, 30, 90, 270, 400, 550], 
        "color": "BLUE", 
        "type": "property", 
        "mortgage": 50,
        "house_cost": 50,
        "hotel_cost": 50
    },
    9: {
        "name": "Рижская", 
        "price": 120, 
        "rent": [8, 40, 100, 300, 450, 600], 
        "color": "BLUE", 
        "type": "property", 
        "mortgage": 60,
        "house_cost": 50,
        "hotel_cost": 50
    },
    10: {  # Тюрьма/Посещение
        "name": "Тюрьма/Посещение", 
        "price": 0, 
        "rent": [0], 
        "color": "JAIL", 
        "type": "jail", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    11: {  # Розовые
        "name": "Курская", 
        "price": 140, 
        "rent": [10, 50, 150, 450, 625, 750], 
        "color": "PINK", 
        "type": "property", 
        "mortgage": 70,
        "house_cost": 100,
        "hotel_cost": 100
    },
    12: {  # Коммунальное предприятие
        "name": "Электросеть", 
        "price": 150, 
        "rent": [4, 10], 
        "color": "UTIL", 
        "type": "utility", 
        "mortgage": 75,
        "house_cost": 0,
        "hotel_cost": 0
    },
    13: {
        "name": "Абрамцево", 
        "price": 140, 
        "rent": [10, 50, 150, 450, 625, 750], 
        "color": "PINK", 
        "type": "property", 
        "mortgage": 70,
        "house_cost": 100,
        "hotel_cost": 100
    },
    14: {
        "name": "Пантелеевская", 
        "price": 160, 
        "rent": [12, 60, 180, 500, 700, 900], 
        "color": "PINK", 
        "type": "property", 
        "mortgage": 80,
        "house_cost": 100,
        "hotel_cost": 100
    },
    15: {  # Железная дорога
        "name": "Казанская ж/д", 
        "price": 200, 
        "rent": [25, 50, 100, 200], 
        "color": "RAIL", 
        "type": "railroad", 
        "mortgage": 100,
        "house_cost": 0,
        "hotel_cost": 0
    },
    16: {  # Оранжевые
        "name": "Вавилова", 
        "price": 180, 
        "rent": [14, 70, 200, 550, 750, 950], 
        "color": "ORANGE", 
        "type": "property", 
        "mortgage": 90,
        "house_cost": 100,
        "hotel_cost": 100
    },
    17: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    18: {
        "name": "Тимирязевская", 
        "price": 180, 
        "rent": [14, 70, 200, 550, 750, 950], 
        "color": "ORANGE", 
        "type": "property", 
        "mortgage": 90,
        "house_cost": 100,
        "hotel_cost": 100
    },
    19: {
        "name": "Лихоборы", 
        "price": 200, 
        "rent": [16, 80, 220, 600, 800, 1000], 
        "color": "ORANGE", 
        "type": "property", 
        "mortgage": 100,
        "house_cost": 100,
        "hotel_cost": 100
    },
    20: {  # Бесплатная стоянка
        "name": "Бесплатная стоянка", 
        "price": 0, 
        "rent": [0], 
        "color": "FREE", 
        "type": "free", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    21: {  # Красные
        "name": "Арбат", 
        "price": 220, 
        "rent": [18, 90, 250, 700, 875, 1050], 
        "color": "RED", 
        "type": "property", 
        "mortgage": 110,
        "house_cost": 150,
        "hotel_cost": 150
    },
    22: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    23: {
        "name": "Полянка", 
        "price": 220, 
        "rent": [18, 90, 250, 700, 875, 1050], 
        "color": "RED", 
        "type": "property", 
        "mortgage": 110,
        "house_cost": 150,
        "hotel_cost": 150
    },
    24: {
        "name": "Сретенка", 
        "price": 240, 
        "rent": [20, 100, 300, 750, 925, 1100], 
        "color": "RED", 
        "type": "property", 
        "mortgage": 120,
        "house_cost": 150,
        "hotel_cost": 150
    },
    25: {  # Железная дорога
        "name": "Курская ж/д", 
        "price": 200, 
        "rent": [25, 50, 100, 200], 
        "color": "RAIL", 
        "type": "railroad", 
        "mortgage": 100,
        "house_cost": 0,
        "hotel_cost": 0
    },
    26: {  # Желтые
        "name": "Ростовская", 
        "price": 260, 
        "rent": [22, 110, 330, 800, 975, 1150], 
        "color": "YELLOW", 
        "type": "property", 
        "mortgage": 130,
        "house_cost": 150,
        "hotel_cost": 150
    },
    27: {
        "name": "Рязанский пр.", 
        "price": 260, 
        "rent": [22, 110, 330, 800, 975, 1150], 
        "color": "YELLOW", 
        "type": "property", 
        "mortgage": 130,
        "house_cost": 150,
        "hotel_cost": 150
    },
    28: {  # Коммунальное предприятие
        "name": "Водопровод", 
        "price": 150, 
        "rent": [4, 10], 
        "color": "UTIL", 
        "type": "utility", 
        "mortgage": 75,
        "house_cost": 0,
        "hotel_cost": 0
    },
    29: {
        "name": "Новинский б-р", 
        "price": 280, 
        "rent": [24, 120, 360, 850, 1025, 1200], 
        "color": "YELLOW", 
        "type": "property", 
        "mortgage": 140,
        "house_cost": 150,
        "hotel_cost": 150
    },
    30: {  # Идите в тюрьму
        "name": "Идите в тюрьму", 
        "price": 0, 
        "rent": [0], 
        "color": "GO_JAIL", 
        "type": "go_jail", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    31: {  # Зеленые
        "name": "Пушкинская", 
        "price": 300, 
        "rent": [26, 130, 390, 900, 1100, 1275], 
        "color": "GREEN", 
        "type": "property", 
        "mortgage": 150,
        "house_cost": 200,
        "hotel_cost": 200
    },
    32: {
        "name": "Тверская", 
        "price": 300, 
        "rent": [26, 130, 390, 900, 1100, 1275], 
        "color": "GREEN", 
        "type": "property", 
        "mortgage": 150,
        "house_cost": 200,
        "hotel_cost": 200
    },
    33: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    34: {
        "name": "Маяковского", 
        "price": 320, 
        "rent": [28, 150, 450, 1000, 1200, 1400], 
        "color": "GREEN", 
        "type": "property", 
        "mortgage": 160,
        "house_cost": 200,
        "hotel_cost": 200
    },
    35: {  # Железная дорога
        "name": "Ленинградская ж/д", 
        "price": 200, 
        "rent": [25, 50, 100, 200], 
        "color": "RAIL", 
        "type": "railroad", 
        "mortgage": 100,
        "house_cost": 0,
        "hotel_cost": 0
    },
    36: {  # Шанс
        "name": "Шанс", 
        "price": 0, 
        "rent": [0], 
        "color": "CHANCE", 
        "type": "chance", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    37: {  # Темно-синие
        "name": "Кутузовский", 
        "price": 350, 
        "rent": [35, 175, 500, 1100, 1300, 1500], 
        "color": "DARKBLUE", 
        "type": "property", 
        "mortgage": 175,
        "house_cost": 200,
        "hotel_cost": 200
    },
    38: {  # Налог на роскошь
        "name": "Налог на роскошь", 
        "price": 100, 
        "rent": [0], 
        "color": "TAX", 
        "type": "tax", 
        "mortgage": 0,
        "house_cost": 0,
        "hotel_cost": 0
    },
    39: {
        "name": "Бродвей", 
        "price": 400, 
        "rent": [50, 200, 600, 1400, 1700, 2000], 
        "color": "DARKBLUE", 
        "type": "property", 
        "mortgage": 200,
        "house_cost": 200,
        "hotel_cost": 200
    }
}

# ==================== ЦВЕТОВАЯ КАРТА ====================
COLOR_MAP = {
    "BROWN": "#8B4513",
    "BLUE": "#87CEEB",
    "PINK": "#FFC0CB",
    "ORANGE": "#FFA500",
    "RED": "#FF0000",
    "YELLOW": "#FFFF00",
    "GREEN": "#008000",
    "DARKBLUE": "#00008B",
    "RAIL": "#A9A9A9",
    "UTIL": "#FFFFE0",
    "SPECIAL": "#FFFFFF",
    "TAX": "#FFD700",
    "CHANCE": "#32CD32",
    "JAIL": "#696969",
    "GO_JAIL": "#FF4500",
    "FREE": "#90EE90"
}

# ==================== КАРТОЧКИ ШАНСА ====================
CHANCE_CARDS = [
    "Пройдите на СТАРТ и получите 200$",
    "Идите в тюрьму. Не проходите СТАРТ, не получайте 200$",
    "Заплатите за ремонт улиц: по 40$ за каждый дом, 115$ за каждый отель",
    "Освобождение из тюрьмы. Карту можно сохранить или продать",
    "Аванс на три хода вперед",
    "Банковская ошибка в вашу пользу. Получите 200$",
    "Вы выиграли конкурс красоты. Получите 100$",
    "Заплатите штраф за превышение скорости 15$",
    "Вас выбрали председателем правления. Заплатите каждому игроку по 50$",
    "Ваш срок инвестиций истек. Получите 150$",
    "Вернитесь на три шага назад",
    "Отправляйтесь на ближайшую железную дорогу",
    "Отправляйтесь на ближайшее коммунальное предприятие"
]

# ==================== КАРТОЧКИ КАЗНАЧЕЙСТВА ====================
COMMUNITY_CHEST_CARDS = [
    "Рождественский фонд выплачивает вам 100$",
    "Оплатите лечение в больнице 100$",
    "Вы получили наследство 100$",
    "Продайте акции и получите 50$",
    "Вы заняли второе место в конкурсе. Получите 10$",
    "Оплатите страховку 50$",
    "Школа требует плату 150$",
    "Вас оштрафовали за парковку 10$",
    "Верните кредит банку 150$",
    "Получите проценты по вкладу 25$"
]

# ==================== СТАРТОВЫЕ НАСТРОЙКИ ИГРЫ ====================
STARTING_BALANCE = 1500
JAIL_FINE = 50
MAX_HOUSES = 4
MAX_HOTELS = 1
MAX_PLAYERS = 8
MIN_PLAYERS = 2

# ==================== ПУТИ К ФАЙЛАМ ====================
DATA_DIR = "data"
STATS_FILE = f"{DATA_DIR}/user_stats.json"
GAMES_LOG = f"{DATA_DIR}/games_log.txt"
"""
CONFIG.PY - ПРОДОЛЖЕНИЕ (функции и утилиты)
"""

import os
import sys
from pathlib import Path

# ==================== УТИЛИТЫ КОНФИГУРАЦИИ ====================

def ensure_data_dir():
    """Создает папку data если её нет"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"📁 Создана папка {DATA_DIR}")

def load_user_stats():
    """Загружает статистику игроков из файла"""
    global USER_STATS
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                USER_STATS = json.load(f)
            logger.info(f"📊 Загружена статистика {len(USER_STATS)} игроков")
        else:
            USER_STATS = {}
            logger.info("📊 Создана новая статистика")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки статистики: {e}")
        USER_STATS = {}

def save_user_stats():
    """Сохраняет статистику игроков в файл"""
    try:
        ensure_data_dir()
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(USER_STATS, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Статистика сохранена ({len(USER_STATS)} игроков)")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения статистики: {e}")

def log_game_event(event: str):
    """Логирует события игры"""
    try:
        ensure_data_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(GAMES_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {event}\n")
    except Exception as e:
        logger.error(f"❌ Ошибка логирования: {e}")

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMINS

def get_color_name(color_code: str) -> str:
    """Возвращает русское название цвета"""
    color_names = {
        "BROWN": "Коричневый",
        "BLUE": "Голубой",
        "PINK": "Розовый",
        "ORANGE": "Оранжевый",
        "RED": "Красный",
        "YELLOW": "Желтый",
        "GREEN": "Зеленый",
        "DARKBLUE": "Темно-синий",
        "RAIL": "Железная дорога",
        "UTIL": "Коммунальное предприятие",
        "SPECIAL": "Особая",
        "TAX": "Налог",
        "CHANCE": "Шанс",
        "JAIL": "Тюрьма",
        "GO_JAIL": "В тюрьму",
        "FREE": "Бесплатная стоянка"
    }
    return color_names.get(color_code, color_code)

def get_property_set(color: str) -> List[int]:
    """Возвращает индексы свойств одного цвета"""
    sets = {
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
    return sets.get(color, [])

def get_rent(position: int, level: int = 0) -> int:
    """Возвращает арендную плату для клетки"""
    if position not in BOARD:
        return 0
    
    cell = BOARD[position]
    if cell["type"] in ["property", "railroad", "utility"]:
        rents = cell["rent"]
        if level < len(rents):
            return rents[level]
    
    return cell.get("rent", [0])[0]

def can_build_houses(position: int) -> bool:
    """Можно ли строить дома на этой клетке"""
    if position not in BOARD:
        return False
    
    cell = BOARD[position]
    return cell["type"] == "property" and cell["house_cost"] > 0

def get_mortgage_value(position: int) -> int:
    """Возвращает сумму залога"""
    if position in BOARD:
        return BOARD[position].get("mortgage", 0)
    return 0

def get_unmortgage_cost(position: int) -> int:
    """Возвращает стоимость выкупа из залога (на 10% больше)"""
    mortgage = get_mortgage_value(position)
    return int(mortgage * 1.1)

# ==================== КОНСТАНТЫ ДЛЯ ВИЗУАЛИЗАЦИИ ====================
BOARD_SIZE = 40
CELL_WIDTH = 120
CELL_HEIGHT = 120
BOARD_IMAGE_WIDTH = 1200
BOARD_IMAGE_HEIGHT = 1200

# Координаты для отрисовки доски (для мини-карты)
BOARD_COORDS = {
    # Верхний ряд (слева направо)
    0: (10, 10),   # СТАРТ
    1: (130, 10),
    2: (250, 10),
    3: (370, 10),
    4: (490, 10),
    5: (610, 10),
    6: (730, 10),
    7: (850, 10),
    8: (970, 10),
    9: (1090, 10),  # Рижская
    
    # Правый ряд (сверху вниз)
    10: (1090, 130),  # Тюрьма/Посещение
    11: (1090, 250),
    12: (1090, 370),
    13: (1090, 490),
    14: (1090, 610),
    15: (1090, 730),
    16: (1090, 850),
    17: (1090, 970),
    18: (1090, 1090),
    19: (1090, 1210),  # Лихоборы
    
    # Нижний ряд (справа налево)
    20: (970, 1210),   # Бесплатная стоянка
    21: (850, 1210),
    22: (730, 1210),
    23: (610, 1210),
    24: (490, 1210),
    25: (370, 1210),
    26: (250, 1210),
    27: (130, 1210),
    28: (10, 1210),
    29: (-110, 1210),  # Новинский б-р
    
    # Левый ряд (снизу вверх)
    30: (-110, 1090),  # Идите в тюрьму
    31: (-110, 970),
    32: (-110, 850),
    33: (-110, 730),
    34: (-110, 610),
    35: (-110, 490),
    36: (-110, 370),
    37: (-110, 250),
    38: (-110, 130),
    39: (-110, 10)     # Бродвей
}

# Эмодзи для типов клеток
EMOJI_MAP = {
    "start": "🏁",
    "property": "🏠",
    "railroad": "🚂",
    "utility": "💡",
    "chance": "🎲",
    "tax": "💸",
    "jail": "🚓",
    "go_jail": "⛓️",
    "free": "🅿️"
}

# ==================== НАСТРОЙКИ БОТА ====================
BOT_VERSION = "3.0 Premium"
BOT_AUTHOR = "Темный Принц"
BOT_GITHUB = "https://github.com/DarkPrinceAI/MonopolyBot"

# Текст для /help
HELP_TEXT = f"""
👑 <b>Monopoly Premium Bot v{BOT_VERSION}</b>

<b>Основные команды:</b>
/monopoly - Главное меню
/start - Начало работы (в ЛС)
/hide - Скрыть меню (в игре)
/show - Показать меню
/stats - Моя статистика
/rating - Рейтинг игроков
/admin - Админ панель (только для админов)

<b>Как начать игру:</b>
1. Добавьте бота в группу
2. Дайте права администратора
3. Напишите /monopoly
4. Начните сбор игроков

<b>Разработчик:</b> {BOT_AUTHOR}
<b>Версия:</b> {BOT_VERSION}
"""

# ==================== ФУНКЦИИ ДЛЯ РЕЙТИНГА ====================

def update_user_stats(user_id: int, username: str, first_name: str, 
                      win: bool = False, money: int = 0):
    """Обновляет статистику пользователя"""
    try:
        if user_id not in USER_STATS:
            USER_STATS[user_id] = {
                "username": username,
                "first_name": first_name,
                "games": 0,
                "wins": 0,
                "total_money": 0,
                "last_played": datetime.now().isoformat()
            }
        
        stats = USER_STATS[user_id]
        stats["games"] += 1
        stats["total_money"] += money
        stats["last_played"] = datetime.now().isoformat()
        
        if win:
            stats["wins"] += 1
        
        # Сохраняем изменения
        save_user_stats()
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления статистики: {e}")

def get_user_rating(user_id: int) -> Dict:
    """Возвращает рейтинг пользователя"""
    if user_id not in USER_STATS:
        return {"games": 0, "wins": 0, "win_rate": 0, "rank": "Новичок"}
    
    stats = USER_STATS[user_id]
    games = stats["games"]
    wins = stats["wins"]
    win_rate = (wins / games * 100) if games > 0 else 0
    
    # Определяем ранг
    if games == 0:
        rank = "Новичок"
    elif win_rate >= 60:
        rank = "👑 Чемпион"
    elif win_rate >= 40:
        rank = "🏆 Профи"
    elif win_rate >= 20:
        rank = "⭐ Игрок"
    else:
        rank = "🎮 Новичок"
    
    return {
        "games": games,
        "wins": wins,
        "win_rate": round(win_rate, 1),
        "rank": rank,
        "total_money": stats.get("total_money", 0)
    }

def get_top_players(limit: int = 10) -> List[Dict]:
    """Возвращает топ игроков"""
    players = []
    
    for user_id, stats in USER_STATS.items():
        games = stats["games"]
        wins = stats["wins"]
        win_rate = (wins / games * 100) if games > 0 else 0
        
        players.append({
            "user_id": user_id,
            "username": stats.get("username", ""),
            "first_name": stats.get("first_name", ""),
            "games": games,
            "wins": wins,
            "win_rate": win_rate,
            "total_money": stats.get("total_money", 0)
        })
    
    # Сортируем по win_rate, затем по победам
    players.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)
    return players[:limit]

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

def init_config():
    """Инициализация конфигурации"""
    logger.info("⚙️ Инициализация конфигурации...")
    ensure_data_dir()
    load_user_stats()
    logger.info(f"✅ Конфигурация загружена. Админов: {len(ADMINS)}")
    
    # Проверяем токен бота
    if not API_TOKEN or API_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Токен бота не настроен!")
        logger.error("Установи переменную окружения BOT_TOKEN")
        sys.exit(1)

# Автоматическая инициализация при импорте
if __name__ != "__main__":
    init_config()

