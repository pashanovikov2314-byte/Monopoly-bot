"""
Main menu keyboards (preserving your style)
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
from typing import Optional, List, Dict, Any

from config import (
    PORT,
    ADMIN_USER_IDS,
    DEV_TAG
)

def main_menu_kb(is_group: bool = False, user_id: Optional[int] = None, 
                 is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню - РАЗНЫЕ кнопки для групп и ЛС (сохранен ваш стиль)"""
    
    kb = ReplyKeyboardBuilder()
    
    if is_group:
        # Меню для ГРУППЫ (ваш стиль)
        kb.button(text="🎮 Начать сбор игроков")
        kb.button(text="📊 Рейтинг игроков")
        kb.button(text="📖 Правила игры")
        kb.button(text="🗺️ Пример карты")
        
        if is_admin:
            kb.button(text="⚙️ Админ панель")
            kb.button(text="🔄 Сбросить игру")
        
        # Кнопка разработчика
        kb.button(text="👨‍💻 О девелопере")
        
    else:
        # Меню для ЛИЧНЫХ СООБЩЕНИЙ (ваш стиль)
        kb.button(text="➕ Добавить в группу")
        kb.button(text="📊 Рейтинг игроков")
        kb.button(text="📖 Правила игры")
        kb.button(text="👨‍💻 О девелопере")
        
        if is_admin:
            kb.button(text="⚙️ Админ панель")
    
    # Статус системы (URL кнопка)
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', f'localhost:{PORT}')
    web_url = f"https://{domain}" if 'localhost' not in domain else f"http://localhost:{PORT}"
    kb.button(text="🌐 Статус системы")
    
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def waiting_room_kb(chat_id: int, is_creator: bool = False) -> InlineKeyboardBuilder:
    """Лобби ожидания (кнопки не убираются после захода)"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    
    if is_creator:
        kb.button(text="▶️ Начать игру", callback_data=f"start_real_game_{chat_id}")
        kb.button(text="❌ Прекратить набор", callback_data=f"cancel_gathering_{chat_id}")
    
    kb.adjust(2, 1)
    return kb


def game_main_kb() -> ReplyKeyboardMarkup:
    """Основная игровая клавиатура (ваш стиль)"""
    kb = ReplyKeyboardBuilder()
    
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить")
    kb.button(text="💰 Банк")
    kb.button(text="🤝 Торговля")
    kb.button(text="📊 Мои активы")
    kb.button(text="🗺️ Карта игры")
    kb.button(text="🏛️ Тюрьма")
    kb.button(text="📈 Статистика")
    kb.button(text="❌ Скрыть меню")  # Оставляем как у вас
    
    kb.adjust(2, 2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True, selective=True)


def inline_menu_kb(player_name: str = "", balance: int = 0, is_turn: bool = False) -> InlineKeyboardBuilder:
    """Inline меню для тех кто скрыл основное (ваш стиль)"""
    kb = InlineKeyboardBuilder()
    
    if is_turn:
        kb.button(text="🎲 Бросить кубик (ВАШ ХОД!)", callback_data="inline_roll_dice")
    else:
        kb.button(text="🎲 Бросить кубик", callback_data="inline_roll_dice_disabled")
    
    kb.button(text="🏠 Управление недвижимостью", callback_data="inline_build")
    kb.button(text="💰 Банк (залог/выкуп)", callback_data="inline_bank")
    kb.button(text="🤝 Торговля с игроками", callback_data="inline_trade")
    kb.button(text="📊 Мои активы и статус", callback_data="inline_assets")
    kb.button(text="🗺️ Показать карту", callback_data="inline_map")
    kb.button(text="🏛️ Действия в тюрьме", callback_data="inline_jail")
    kb.button(text="📈 Статистика игры", callback_data="inline_stats")
    kb.button(text="📱 Вернуть меню", callback_data="restore_menu")  # Как у вас
    
    kb.adjust(1)
    return kb


def admin_panel_kb(user_id: int) -> InlineKeyboardBuilder:
    """Панель администратора"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="👥 Управление админами", callback_data=f"admin_manage_{user_id}")
    kb.button(text="🔄 Перезапустить бота", callback_data=f"admin_restart_{user_id}")
    kb.button(text="🚫 Режим обслуживания", callback_data=f"admin_maintenance_{user_id}")
    kb.button(text="📊 Статистика бота", callback_data=f"admin_stats_{user_id}")
    kb.button(text="🔗 Получить ссылку запуска", callback_data=f"admin_link_{user_id}")
    kb.button(text="🗑️ Очистить старые игры", callback_data=f"admin_cleanup_{user_id}")
    kb.button(text="⬅️ Назад в меню", callback_data="back_to_main")
    
    kb.adjust(2)
    return kb


def rating_menu_kb(user_id: int) -> InlineKeyboardBuilder:
    """Меню рейтинга игроков"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🏆 Топ-10 по победам", callback_data=f"rating_wins_{user_id}")
    kb.button(text="💰 Топ-10 по деньгам", callback_data=f"rating_money_{user_id}")
    kb.button(text="📊 Моя статистика", callback_data=f"my_stats_{user_id}")
    kb.button(text="📈 Общая статистика", callback_data=f"global_stats_{user_id}")
    kb.button(text="⬅️ Назад", callback_data="back_to_main")
    
    kb.adjust(2)
    return kb
