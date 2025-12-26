import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

PORT = int(os.environ.get("PORT", 8083))
DEV_TAG = "@Whylovely05"
MAINTENANCE_MSG = "Бот обновляется, Темный принц уже исправляет это ♥️♥️"
BANNER = "┏━━━━━━━━━━━━━━━━━━┓\n┃  Monopoly Premium  ┃\n┗━━━━━━━━━━━━━━━━━━┛"

# Список администраторов (ваш ID + другие)
ADMIN_USER_IDS = [
    123456789,  # Ваш ID
    987654321,  # Другой админ
]

# Список пользователей, которые могут запускать бот через ссылку
ALLOWED_LAUNCH_USERS = ADMIN_USER_IDS + [
    111222333,  # Дополнительные пользователи
]

# Настройки игр
MAX_PLAYERS = 8
MIN_PLAYERS = 2
INITIAL_BALANCE = 1500
JAIL_FINE = 50
AUTO_START_MINUTES = 3  # Автостарт через 3 минуты
INACTIVE_GAME_HOURS = 24  # Удаление неактивных игр

# Настройки защиты от DDoS
MAX_REQUESTS_PER_MINUTE = 30
MAX_MESSAGES_PER_SECOND = 5
BAN_DURATION_MINUTES = 60

# Настройки базы данных
DB_PATH = "data/monopoly.db"
DB_BACKUP_INTERVAL = 3600  # секунды

# Настройки веб-сервера
WEB_HOST = "0.0.0.0"
WEB_PORT = PORT
LAUNCH_SECRET = os.environ.get("LAUNCH_SECRET", "darkprince123")

# Цвета групп недвижимости
PROPERTY_COLORS = {
    "BROWN": {"color": "#8B4513", "price": 60, "rent": [2, 10, 30, 90, 160, 250]},
    "BLUE": {"color": "#87CEEB", "price": 100, "rent": [6, 30, 90, 270, 400, 550]},
    "PINK": {"color": "#FF69B4", "price": 140, "rent": [10, 50, 150, 450, 625, 750]},
    "ORANGE": {"color": "#FFA500", "price": 180, "rent": [14, 70, 200, 550, 750, 950]},
    "RED": {"color": "#FF0000", "price": 220, "rent": [18, 90, 250, 700, 875, 1050]},
    "YELLOW": {"color": "#FFFF00", "price": 260, "rent": [22, 110, 330, 800, 975, 1150]},
    "GREEN": {"color": "#00FF00", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275]},
    "DARKBLUE": {"color": "#00008B", "price": 350, "rent": [35, 175, 500, 1100, 1300, 1500]},
    "RAIL": {"color": "#808080", "price": 200, "rent": [25, 50, 100, 200]},
    "UTIL": {"color": "#000000", "price": 150, "rent_multiplier": [4, 10]},
}

# Пути к файлам
BOARD_DATA_PATH = "data/board.json"
CHANCE_CARDS_PATH = "data/chance_cards.json"
CHEST_CARDS_PATH = "data/chest_cards.json"

# Эмодзи для игры
EMOJIS = {
    "dice": "🎲",
    "money": "💰",
    "property": "🏠",
    "hotel": "🏨",
    "jail": "🏛️",
    "trade": "🤝",
    "bank": "🏦",
    "card": "🎫",
    "railroad": "🚂",
    "utility": "⚡",
    "auction": "🔨",
    "map": "🗺️",
    "stats": "📊",
    "settings": "⚙️",
    "back": "⬅️",
    "close": "❌",
    "check": "✅",
    "warning": "⚠️",
    "info": "ℹ️",
}
