"""
KEYBOARDS.PY - Все клавиатуры бота
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from aiogram import Bot
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, WebAppInfo
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder, 
    ReplyKeyboardBuilder
)

from modules.config import (
    BOARD, COLOR_MAP, ADMINS, DEV_TAG, 
    logger, BOARD_COORDS, EMOJI_MAP,
    get_color_name, get_property_set
)

# ==================== ОСНОВНЫЕ КЛАВИАТУРЫ ====================

def main_menu_kb(is_group: bool = False, user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Главное меню - РАЗНЫЕ кнопки для групп и ЛС"""
    kb = InlineKeyboardBuilder()
    
    if is_group:
        # Меню для ГРУППЫ
        kb.button(text="🎮 Начать сбор игроков", callback_data="start_player_gathering")
        kb.button(text="📊 Рейтинг игроков", callback_data="show_rating")
        kb.button(text="📖 Правила игры", callback_data="show_rules")
        kb.button(text="👨‍💻 О разработчике", callback_data="show_developer")
        
        # Кнопка для админов
        if user_id and user_id in ADMINS:
            kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    else:
        # Меню для ЛИЧНЫХ СООБЩЕНИЙ
        kb.button(text="➕ Добавить в группу", 
                 url="https://t.me/MonopolyPremiumBot?startgroup=true")
        kb.button(text="📊 Рейтинг игроков", callback_data="show_rating")
        kb.button(text="📖 Правила игры", callback_data="show_rules")
        kb.button(text="👨‍💻 О разработчике", callback_data="show_developer")
        
        # Кнопка для админов
        if user_id and user_id in ADMINS:
            kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    
    kb.adjust(1)
    return kb.as_markup()

def waiting_room_kb(chat_id: int, is_creator: bool = False) -> InlineKeyboardMarkup:
    """Лобби ожидания с таймером"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="✅ Присоединиться", callback_data=f"join_game_{chat_id}")
    kb.button(text="🚪 Выйти", callback_data=f"leave_game_{chat_id}")
    
    if is_creator:
        kb.button(text="▶️ Начать игру", callback_data=f"start_game_{chat_id}")
        kb.button(text="⏹️ Прекратить набор", callback_data=f"stop_gathering_{chat_id}")
    
    # Таймер 3 минуты
    kb.button(text="⏱️ 3:00", callback_data="timer_info")
    
    kb.adjust(2, 2)
    return kb.as_markup()

def game_main_kb(game_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    """Основная игровая клавиатура"""
    kb = ReplyKeyboardBuilder()
    
    kb.button(text="🎲 Бросить кубик")
    kb.button(text="🏠 Построить/Заложить")
    kb.button(text="📊 Мои активы")
    kb.button(text="🤝 Торговля")
    kb.button(text="🗺️ Карта доски")
    kb.button(text="❌ Скрыть меню")
    
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False)

def inline_menu_kb() -> InlineKeyboardMarkup:
    """Inline меню для тех кто скрыл основное"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🎲 Бросить кубик", callback_data="inline_roll_dice")
    kb.button(text="🏠 Построить", callback_data="inline_build_menu")
    kb.button(text="💸 Заложить", callback_data="inline_mortgage_menu")
    kb.button(text="📊 Мои активы", callback_data="inline_assets")
    
    kb.button(text="🤝 Торговля", callback_data="inline_trade_menu")
    kb.button(text="🗺️ Карта", callback_data="inline_board_map")
    kb.button(text="📱 Вернуть меню", callback_data="restore_menu")
    
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ ТОРГОВЛИ ====================

def trade_menu_kb() -> InlineKeyboardMarkup:
    """Меню торговли"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="💰 Предложить деньги", callback_data="trade_offer_money")
    kb.button(text="🏠 Предложить недвижимость", callback_data="trade_offer_property")
    kb.button(text="🔄 Обменять недвижимость", callback_data="trade_swap_property")
    kb.button(text="📜 Мои предложения", callback_data="trade_my_offers")
    
    kb.button(text="📨 Входящие предложения", callback_data="trade_incoming")
    kb.button(text="❌ Отменить предложение", callback_data="trade_cancel")
    kb.button(text="◀️ Назад", callback_data="back_to_game")
    
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()

def trade_select_player_kb(players: List[Dict], exclude_id: int) -> InlineKeyboardMarkup:
    """Выбор игрока для торговли"""
    kb = InlineKeyboardBuilder()
    
    for player in players:
        if player["id"] != exclude_id:
            kb.button(
                text=f"👤 {player['name']}",
                callback_data=f"trade_select_{player['id']}"
            )
    
    kb.button(text="◀️ Назад", callback_data="trade_menu")
    kb.adjust(1)
    return kb.as_markup()

def trade_confirm_kb(trade_id: str) -> InlineKeyboardMarkup:
    """Подтверждение торговой сделки"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="✅ Принять сделку", callback_data=f"trade_accept_{trade_id}")
    kb.button(text="❌ Отклонить сделку", callback_data=f"trade_reject_{trade_id}")
    kb.button(text="🤝 Контрпредложение", callback_data=f"trade_counter_{trade_id}")
    
    kb.adjust(2, 1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ СТРОИТЕЛЬСТВА ====================

def build_menu_kb(player_properties: List[int]) -> InlineKeyboardMarkup:
    """Меню строительства домов"""
    kb = InlineKeyboardBuilder()
    
    if not player_properties:
        kb.button(text="❌ Нет доступной недвижимости", callback_data="no_properties")
        kb.button(text="◀️ Назад", callback_data="back_to_game")
        kb.adjust(1)
        return kb.as_markup()
    
    # Группируем по цветам
    color_groups = {}
    for prop_id in player_properties:
        if prop_id in BOARD:
            color = BOARD[prop_id]["color"]
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(prop_id)
    
    # Создаем кнопки для каждого цвета
    for color, props in color_groups.items():
        if len(props) >= 2:  # Минимум 2 свойства одного цвета для строительства
            color_name = get_color_name(color)
            emoji = "🏠" if BOARD[props[0]]["type"] == "property" else "🚂"
            
            # Проверяем, есть ли полный набор
            full_set = get_property_set(color)
            has_full_set = all(p in props for p in full_set)
            
            if has_full_set:
                kb.button(
                    text=f"{emoji} {color_name} (полный набор)",
                    callback_data=f"build_color_{color}"
                )
    
    kb.button(text="🏘️ Информация о домах", callback_data="build_info")
    kb.button(text="◀️ Назад", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb.as_markup()

def property_build_kb(property_id: int, current_houses: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для строительства на конкретной улице"""
    kb = InlineKeyboardBuilder()
    
    if property_id not in BOARD:
        return kb.as_markup()
    
    property_info = BOARD[property_id]
    
    # Кнопки для строительства
    if current_houses < 4:
        house_cost = property_info.get("house_cost", 50)
        kb.button(
            text=f"🏠 Построить дом (+{house_cost}$)",
            callback_data=f"build_house_{property_id}"
        )
    
    if current_houses == 4:
        hotel_cost = property_info.get("hotel_cost", 50)
        kb.button(
            text=f"🏨 Построить отель (+{hotel_cost}$)",
            callback_data=f"build_hotel_{property_id}"
        )
    
    # Кнопки для продажи
    if current_houses > 0:
        sell_price = property_info.get("house_cost", 50) // 2
        if current_houses == 5:  # Отель
            sell_price = property_info.get("hotel_cost", 50) // 2
            kb.button(
                text=f"🏨 Продать отель (+{sell_price}$)",
                callback_data=f"sell_hotel_{property_id}"
            )
        else:
            kb.button(
                text=f"🏠 Продать дом (+{sell_price}$)",
                callback_data=f"sell_house_{property_id}"
            )
    
    kb.button(text="📊 Информация", callback_data=f"property_info_{property_id}")
    kb.button(text="◀️ Назад", callback_data="build_menu")
    
    kb.adjust(1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ ЗАЛОГА ====================

def mortgage_menu_kb(player_properties: List[int], mortgaged_props: List[int]) -> InlineKeyboardMarkup:
    """Меню залога недвижимости"""
    kb = InlineKeyboardBuilder()
    
    if not player_properties:
        kb.button(text="❌ Нет доступной недвижимости", callback_data="no_properties")
        kb.button(text="◀️ Назад", callback_data="back_to_game")
        kb.adjust(1)
        return kb.as_markup()
    
    # Разделяем на заложенные и свободные
    free_props = [p for p in player_properties if p not in mortgaged_props]
    mortgaged = [p for p in player_properties if p in mortgaged_props]
    
    # Свободная недвижимость для залога
    if free_props:
        kb.button(text="💸 Заложить недвижимость", callback_data="mortgage_properties")
    
    # Заложенная недвижимость для выкупа
    if mortgaged:
        kb.button(text="💰 Выкупить из залога", callback_data="unmortgage_properties")
    
    kb.button(text="📊 Информация о залоге", callback_data="mortgage_info")
    kb.button(text="◀️ Назад", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb.as_markup()

def mortgage_select_kb(properties: List[int], action: str = "mortgage") -> InlineKeyboardMarkup:
    """Выбор недвижимости для залога/выкупа"""
    kb = InlineKeyboardBuilder()
    
    for prop_id in properties:
        if prop_id in BOARD:
            prop_info = BOARD[prop_id]
            mortgage_value = prop_info.get("mortgage", 0)
            
            if action == "mortgage":
                text = f"💸 {prop_info['name']} (+{mortgage_value}$)"
                callback_data = f"mortgage_{prop_id}"
            else:  # unmortgage
                unmortgage_cost = int(mortgage_value * 1.1)
                text = f"💰 {prop_info['name']} (-{unmortgage_cost}$)"
                callback_data = f"unmortgage_{prop_id}"
            
            kb.button(text=text, callback_data=callback_data)
    
    kb.button(text="✅ Подтвердить все", callback_data=f"{action}_all")
    kb.button(text="◀️ Назад", callback_data="mortgage_menu")
    
    kb.adjust(1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ КАРТЫ ====================

def board_map_kb(current_position: int = 0, players_positions: Dict[int, int] = None) -> InlineKeyboardMarkup:
    """Клавиатура для навигации по карте"""
    kb = InlineKeyboardBuilder()
    
    # Группы клеток по рядам
    top_row = list(range(0, 10))  # 0-9
    right_row = list(range(10, 20))  # 10-19
    bottom_row = list(range(20, 30))  # 20-29
    left_row = list(range(30, 40))  # 30-39
    
    kb.button(text="⬆️ Верхний ряд", callback_data="map_top_row")
    kb.button(text="➡️ Правый ряд", callback_data="map_right_row")
    kb.button(text="⬇️ Нижний ряд", callback_data="map_bottom_row")
    kb.button(text="⬅️ Левый ряд", callback_data="map_left_row")
    
    # Кнопка текущей позиции
    if current_position in BOARD:
        cell_name = BOARD[current_position]["name"]
        kb.button(text=f"📍 Вы здесь: {cell_name}", callback_data="current_position")
    
    # Кнопка информации о клетке
    kb.button(text="ℹ️ Информация о клетке", callback_data="map_cell_info")
    
    # Кнопка для генерации картинки
    kb.button(text="🖼️ Сгенерировать карту", callback_data="generate_map_image")
    
    kb.button(text="◀️ Назад", callback_data="back_to_game")
    
    kb.adjust(2, 2, 1, 1, 1, 1)
    return kb.as_markup()

def map_row_kb(row_type: str, positions: List[int]) -> InlineKeyboardMarkup:
    """Клавиатура для конкретного ряда на карте"""
    kb = InlineKeyboardBuilder()
    
    for pos in positions:
        if pos in BOARD:
            cell_info = BOARD[pos]
            emoji = EMOJI_MAP.get(cell_info["type"], "⬜")
            
            # Сокращаем длинные названия
            name = cell_info["name"]
            if len(name) > 12:
                name = name[:10] + "..."
            
            kb.button(
                text=f"{emoji} {name}",
                callback_data=f"map_cell_{pos}"
            )
    
    kb.button(text="◀️ Назад к карте", callback_data="board_map")
    kb.adjust(1)
    return kb.as_markup()

def cell_info_kb(position: int) -> InlineKeyboardMarkup:
    """Информация о конкретной клетке"""
    kb = InlineKeyboardBuilder()
    
    if position not in BOARD:
        return kb.as_markup()
    
    cell_info = BOARD[position]
    
    # Разные кнопки в зависимости от типа
    if cell_info["type"] == "property":
        kb.button(text="💰 Цена покупки", callback_data=f"cell_price_{position}")
        kb.button(text="🏠 Арендная плата", callback_data=f"cell_rent_{position}")
        kb.button(text="🎨 Цвет", callback_data=f"cell_color_{position}")
        
    elif cell_info["type"] in ["railroad", "utility"]:
        kb.button(text="💰 Цена покупки", callback_data=f"cell_price_{position}")
        kb.button(text="🏠 Арендная плата", callback_data=f"cell_rent_{position}")
    
    elif cell_info["type"] == "chance":
        kb.button(text="🎲 Пример карточки", callback_data="chance_example")
    
    elif cell_info["type"] == "jail":
        kb.button(text="⛓️ Как выйти из тюрьмы?", callback_data="jail_info")
    
    kb.button(text="🗺️ Показать на карте", callback_data=f"map_show_{position}")
    kb.button(text="◀️ Назад к карте", callback_data="board_map")
    
    kb.adjust(2, 2, 1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ ТЮРЬМЫ ====================

def jail_menu_kb(in_jail: bool = True, has_get_out_card: bool = False) -> InlineKeyboardMarkup:
    """Меню для игрока в тюрьме"""
    kb = InlineKeyboardBuilder()
    
    if in_jail:
        kb.button(text="🎲 Попытаться выйти (двойной дубль)", callback_data="jail_roll_dice")
        kb.button(text="💰 Заплатить 50$", callback_data="jail_pay_fine")
        
        if has_get_out_card:
            kb.button(text="🎫 Использовать карту освобождения", callback_data="jail_use_card")
        
        kb.button(text="⏳ Пропустить ход", callback_data="jail_skip_turn")
        kb.button(text="📖 Правила тюрьмы", callback_data="jail_rules")
    
    kb.button(text="◀️ Назад", callback_data="back_to_game")
    
    kb.adjust(2, 2, 1)
    return kb.as_markup()

# ==================== АДМИН КЛАВИАТУРЫ ====================

def admin_panel_kb() -> InlineKeyboardMarkup:
    """Админ панель"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="📊 Статистика бота", callback_data="admin_stats")
    kb.button(text="👥 Активные игры", callback_data="admin_active_games")
    kb.button(text="🔄 Перезагрузить конфиг", callback_data="admin_reload_config")
    
    kb.button(text="🔧 Режим обслуживания", callback_data="admin_toggle_maintenance")
    kb.button(text="🧹 Очистить неактивные игры", callback_data="admin_cleanup")
    kb.button(text="📁 Экспорт статистики", callback_data="admin_export_stats")
    
    # Кнопка для добавления/удаления админов
    kb.button(text="👑 Управление админами", callback_data="admin_manage_admins")
    
    kb.button(text="◀️ Назад в меню", callback_data="back_to_main")
    
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()

def admin_manage_admins_kb() -> InlineKeyboardMarkup:
    """Управление админами"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="➕ Добавить админа", callback_data="admin_add_admin")
    kb.button(text="➖ Удалить админа", callback_data="admin_remove_admin")
    kb.button(text="📋 Список админов", callback_data="admin_list_admins")
    
    kb.button(text="◀️ Назад в админку", callback_data="admin_panel")
    
    kb.adjust(1)
    return kb.as_markup()

# ==================== КЛАВИАТУРЫ ДЛЯ РЕЙТИНГА ====================

def rating_menu_kb() -> InlineKeyboardMarkup:
    """Меню рейтинга"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🏆 Топ 10 игроков", callback_data="rating_top_10")
    kb.button(text="📊 Моя статистика", callback_data="rating_my_stats")
    kb.button(text="👑 Чемпионы по победам", callback_data="rating_top_wins")
    kb.button(text="💰 Самые богатые", callback_data="rating_top_money")
    
    kb.button(text="📈 График прогресса", callback_data="rating_progress")
    kb.button(text="◀️ Назад", callback_data="back_to_main")
    
    kb.adjust(2, 2, 2)
    return kb.as_markup()

def rating_period_kb() -> InlineKeyboardMarkup:
    """Выбор периода для рейтинга"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="📅 За все время", callback_data="rating_all_time")
    kb.button(text="🗓️ За месяц", callback_data="rating_month")
    kb.button(text="📆 За неделю", callback_data="rating_week")
    kb.button(text="📅 За сегодня", callback_data="rating_today")
    
    kb.button(text="◀️ Назад", callback_data="rating_menu")
    
    kb.adjust(2, 2, 1)
    return kb.as_markup()

# ==================== УТИЛИТЫ ДЛЯ КЛАВИАТУР ====================

def back_button_kb(back_to: str = "main") -> InlineKeyboardMarkup:
    """Простая кнопка 'Назад'"""
    kb = InlineKeyboardBuilder()
    
    if back_to == "main":
        kb.button(text="◀️ Назад в меню", callback_data="back_to_main")
    elif back_to == "game":
        kb.button(text="◀️ Назад к игре", callback_data="back_to_game")
    elif back_to == "admin":
        kb.button(text="◀️ Назад в админку", callback_data="admin_panel")
    else:
        kb.button(text="◀️ Назад", callback_data=f"back_to_{back_to}")
    
    return kb.as_markup()

def yes_no_kb(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="✅ Да", callback_data=yes_callback)
    kb.button(text="❌ Нет", callback_data=no_callback)
    
    kb.adjust(2)
    return kb.as_markup()

def numeric_kb(start: int, end: int, prefix: str = "num_") -> InlineKeyboardMarkup:
    """Числовая клавиатура"""
    kb = InlineKeyboardBuilder()
    
    for i in range(start, end + 1):
        kb.button(text=str(i), callback_data=f"{prefix}{i}")
    
    kb.adjust(5)  # 5 кнопок в ряд
    return kb.as_markup()

def dice_animation_kb() -> InlineKeyboardMarkup:
    """Клавиатура для анимации кубиков"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🎲 Запустить анимацию", callback_data="dice_animate")
    kb.button(text="⚡ Быстрый бросок", callback_data="dice_quick")
    kb.button(text="🎯 Бросить снова", callback_data="dice_reroll")
    
    kb.adjust(2, 1)
    return kb.as_markup()

# ==================== ОБНОВЛЕНИЕ КЛАВИАТУР ====================

async def update_waiting_room(bot: Bot, chat_id: int, message_id: int, 
                            game_data: Dict, creator_id: int) -> None:
    """Обновляет сообщение лобби"""
    try:
        # Формируем список игроков
        players_text = "👥 <b>Игроки в ожидании:</b>\n"
        for i, player in enumerate(game_data.get("players", []), 1):
            players_text += f"{i}. {player['name']}"
            if player.get('username'):
                players_text += f" (@{player['username']})"
            players_text += "\n"
        
        # Считаем время - ИСПРАВЛЕННАЯ ЧАСТЬ
        created_at = game_data.get("created_at")
        if created_at:
            try:
                # Используем полное имя для избежания конфликта
                from datetime import datetime as dt_class
                
                if isinstance(created_at, str):
                    created_dt = dt_class.fromisoformat(created_at)
                else:
                    # Если уже datetime объект
                    created_dt = created_at
                
                # Получаем текущее время
                current_time = dt_class.now()
                
                # Вычисляем разницу в секундах
                time_diff = current_time - created_dt
                elapsed_seconds = int(time_diff.total_seconds())
                
                # Оставшееся время (3 минуты = 180 секунд)
                remaining_seconds = max(0, 180 - elapsed_seconds)
                
                # Форматируем время
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                timer_text = f"⏱️ {minutes}:{seconds:02d}"
                
                # Если время вышло, показываем 0:00
                if remaining_seconds <= 0:
                    timer_text = "⏱️ 0:00"
                    
            except Exception as time_err:
                logger.error(f"Ошибка расчета таймера: {time_err}")
                timer_text = "⏱️ 3:00"
        else:
            timer_text = "⏱️ 3:00"
        
        # Формируем сообщение
        message_text = (
            f"🎮 <b>Сбор игроков начат!</b>\n"
            f"👑 Создатель: {game_data['creator_name']}\n\n"
            f"{players_text}\n"
            f"{timer_text} до автоматического старта\n\n"
            f"✅ Нажмите 'Присоединиться' чтобы войти в игру\n"
            f"🚪 'Выйти' - чтобы покинуть лобби\n"
            f"▶️ Создатель может начать игру когда все готовы"
        )
        
        # Проверяем, является ли текущий пользователь создателем
        is_creator = (creator_id == game_data["creator_id"])
        
        # Обновляем сообщение
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=waiting_room_kb(chat_id, is_creator=is_creator)
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления лобби: {e}")
