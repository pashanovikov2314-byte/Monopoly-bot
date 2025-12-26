"""
Game control keyboards
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import Optional, List, Dict, Any
import os

def get_reply_keyboard_for_text(text: str) -> Optional[ReplyKeyboardMarkup]:
    """Получить ReplyKeyboard для текстовых команд (ваш стиль)"""
    kb = ReplyKeyboardBuilder()
    
    if text == "🎲 Бросить кубик":
        kb.button(text="🎲 Бросить кубики (1-й бросок)")
        kb.button(text="🎲 Бросить кубики (2-й бросок при дубле)")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "🏠 Построить":
        kb.button(text="🏠 Построить дом")
        kb.button(text="🏨 Построить отель")
        kb.button(text="💵 Продать постройки")
        kb.button(text="🏦 Управление залогом")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "💰 Банк":
        kb.button(text="🏦 Заложить недвижимость")
        kb.button(text="💰 Выкупить из залога")
        kb.button(text="💸 Взять кредит")
        kb.button(text="💳 Погасить кредит")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "🤝 Торговля":
        kb.button(text="🤝 Предложить сделку")
        kb.button(text="📋 Мои предложения")
        kb.button(text="📨 Предложения мне")
        kb.button(text="📝 Активные сделки")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "📊 Мои активы":
        kb.button(text="🏠 Моя недвижимость")
        kb.button(text="💰 Мой баланс")
        kb.button(text="🎫 Мои карточки")
        kb.button(text="📈 Стоимость активов")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "🗺️ Карта игры":
        kb.button(text="🗺️ Показать карту")
        kb.button(text="📍 Где я сейчас")
        kb.button(text="👥 Позиции игроков")
        kb.button(text="🏠 Купленные улицы")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "🏛️ Тюрьма":
        kb.button(text="🎲 Попытаться выйти")
        kb.button(text="💰 Заплатить 50$")
        kb.button(text="🎫 Использовать карточку")
        kb.button(text="⏳ Ожидать (3 хода)")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    elif text == "📈 Статистика":
        kb.button(text="📊 Моя статистика")
        kb.button(text="🏆 Рейтинг игроков")
        kb.button(text="📈 Статистика игры")
        kb.button(text="🎮 История ходов")
        kb.button(text="⬅️ Назад в меню")
        kb.adjust(1)
        return kb.as_markup(resize_keyboard=True)
    
    return None


def dice_roll_kb(player_id: int) -> InlineKeyboardBuilder:
    """Клавиатура для броска кубиков"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🎲 Бросить кубики", callback_data=f"roll_dice_{player_id}")
    kb.button(text="🎲 Случайный бросок", callback_data=f"random_roll_{player_id}")
    kb.button(text="⬅️ Назад", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def build_menu_kb(properties: List[Dict], player_id: int) -> InlineKeyboardBuilder:
    """Меню строительства"""
    kb = InlineKeyboardBuilder()
    
    # Кнопки для улиц, где можно строить
    for prop in properties:
        if prop.get('can_build', False):
            name = prop.get('name', 'Неизвестно')
            houses = prop.get('houses', 0)
            
            if houses < 4:
                kb.button(text=f"➕ {name} (+дом, ${prop.get('house_price', 50)})", 
                         callback_data=f"build_house_{prop['id']}_{player_id}")
            elif houses == 4:
                kb.button(text=f"🏨 {name} (отель, ${prop.get('hotel_price', 100)})", 
                         callback_data=f"build_hotel_{prop['id']}_{player_id}")
    
    kb.button(text="💵 Продать постройки", callback_data=f"sell_buildings_{player_id}")
    kb.button(text="🏦 Управление залогом", callback_data=f"mortgage_menu_{player_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def bank_menu_kb(player_id: int) -> InlineKeyboardBuilder:
    """Меню банковских операций"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🏦 Заложить недвижимость", callback_data=f"bank_mortgage_{player_id}")
    kb.button(text="💰 Выкупить из залога", callback_data=f"bank_unmortgage_{player_id}")
    kb.button(text="💸 Взять кредит (10% от баланса)", callback_data=f"bank_loan_{player_id}")
    kb.button(text="💳 Погасить кредит", callback_data=f"bank_repay_{player_id}")
    kb.button(text="📊 Баланс банка", callback_data=f"bank_balance_{player_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def trade_menu_kb(game_players: List[Dict], current_player_id: int) -> InlineKeyboardBuilder:
    """Меню торговли"""
    kb = InlineKeyboardBuilder()
    
    for player in game_players:
        if player["id"] != current_player_id and not player.get("is_bankrupt", False):
            kb.button(text=f"🤝 {player['name']} (${player['balance']})", 
                     callback_data=f"start_trade_{player['id']}_{current_player_id}")
    
    kb.button(text="📋 Мои активные предложения", callback_data=f"my_trades_{current_player_id}")
    kb.button(text="📨 Предложения мне", callback_data=f"offers_to_me_{current_player_id}")
    kb.button(text="📝 Активные сделки", callback_data=f"active_trades_{current_player_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def assets_menu_kb(player_id: int) -> InlineKeyboardBuilder:
    """Меню активов"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🏠 Список недвижимости", callback_data=f"list_properties_{player_id}")
    kb.button(text="💰 Текущий баланс", callback_data=f"show_balance_{player_id}")
    kb.button(text="🎫 Мои карточки", callback_data=f"show_cards_{player_id}")
    kb.button(text="📈 Оценить активы", callback_data=f"evaluate_assets_{player_id}")
    kb.button(text="💼 Сводка по имуществу", callback_data=f"property_summary_{player_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def map_menu_kb(chat_id: int, game_id: Optional[int] = None) -> InlineKeyboardBuilder:
    """Кнопки для карты игры"""
    kb = InlineKeyboardBuilder()
    
    if game_id:
        # Интерактивная карта через WebApp
        domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
        web_app_url = f"https://{domain}/map/{game_id}" if domain != 'localhost' else f"http://localhost:{PORT}/map/{game_id}"
        kb.button(text="🗺️ Открыть интерактивную карту", web_app={"url": web_app_url})
    
    kb.button(text="🔄 Обновить позиции", callback_data=f"refresh_map_{chat_id}")
    kb.button(text="📱 Текстовая карта", callback_data=f"text_map_{chat_id}")
    kb.button(text="📍 Моя позиция", callback_data=f"my_position_{chat_id}")
    kb.button(text="👥 Позиции всех игроков", callback_data=f"all_positions_{chat_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def jail_menu_kb(player_id: int, turns_in_jail: int, has_jail_card: bool) -> InlineKeyboardBuilder:
    """Меню действий в тюрьме"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🎲 Попытаться выбросить дубль", 
             callback_data=f"jail_roll_{player_id}")
    kb.button(text="💰 Заплатить 50$ за выход", 
             callback_data=f"jail_pay_{player_id}")
    
    if has_jail_card:
        kb.button(text="🎫 Использовать карточку освобождения", 
                 callback_data=f"jail_card_{player_id}")
    
    kb.button(text=f"⏳ Ожидать ({turns_in_jail}/3 хода)", 
             callback_data=f"jail_wait_{player_id}")
    kb.button(text="📊 Статус в тюрьме", 
             callback_data=f"jail_status_{player_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def stats_menu_kb(chat_id: int) -> InlineKeyboardBuilder:
    """Меню статистики"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="📊 Моя статистика", callback_data=f"my_game_stats_{chat_id}")
    kb.button(text="🏆 Рейтинг игроков", callback_data=f"game_rating_{chat_id}")
    kb.button(text="📈 Статистика игры", callback_data=f"game_statistics_{chat_id}")
    kb.button(text="🎮 История ходов", callback_data=f"turn_history_{chat_id}")
    kb.button(text="💰 Банк игры", callback_data=f"game_bank_{chat_id}")
    kb.button(text="⬅️ Назад в игру", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def properties_menu_kb(properties: List[Dict], player_id: int, 
                      can_build: bool = False) -> InlineKeyboardBuilder:
    """Меню управления недвижимостью"""
    kb = InlineKeyboardBuilder()
    
    for prop in properties:
        name = prop['name']
        status = ""
        
        if prop.get('is_mortgaged'):
            status = " (💸 заложено)"
        elif prop.get('houses', 0) > 0:
            status = f" (🏠×{prop['houses']})"
        elif prop.get('hotels', 0) > 0:
            status = " (🏨)"
        
        if can_build and not prop.get('is_mortgaged'):
            if prop.get('houses', 0) < 4:
                kb.button(text=f"➕ {name}{status} (+дом, ${prop.get('house_price', 0)})", 
                         callback_data=f"build_house_{prop['position']}_{player_id}")
            elif prop.get('houses', 0) == 4 and not prop.get('hotels', 0):
                kb.button(text=f"🏨 {name}{status} (отель, ${prop.get('hotel_price', 0)})", 
                         callback_data=f"build_hotel_{prop['position']}_{player_id}")
        else:
            kb.button(text=f"ℹ️ {name}{status}", 
                     callback_data=f"info_{prop['position']}_{player_id}")
    
    # Кнопки управления залогом
    kb.button(text="🏦 Управление залогом", callback_data=f"mortgage_menu_{player_id}")
    kb.button(text="💵 Продать дома/отели", callback_data=f"sell_buildings_{player_id}")
    kb.button(text="📊 Сводка по имуществу", callback_data=f"property_summary_{player_id}")
    kb.button(text="⬅️ Назад к игре", callback_data="back_to_game")
    
    kb.adjust(1)
    return kb


def mortgage_menu_kb(properties: List[Dict], player_id: int) -> InlineKeyboardBuilder:
    """Меню залога/выкупа недвижимости"""
    kb = InlineKeyboardBuilder()
    
    for prop in properties:
        name = prop['name']
        mortgage_value = prop.get('mortgage_value', prop.get('price', 0) // 2)
        
        if prop.get('is_mortgaged'):
            kb.button(text=f"💰 Выкупить {name} (${mortgage_value})", 
                     callback_data=f"unmortgage_{prop['position']}_{player_id}")
        else:
            # Проверяем нет ли домов/отелей
            if prop.get('houses', 0) == 0 and prop.get('hotels', 0) == 0:
                kb.button(text=f"🏦 Заложить {name} (${mortgage_value})", 
                         callback_data=f"mortgage_{prop['position']}_{player_id}")
            else:
                kb.button(text=f"❌ {name} (есть постройки)", 
                         callback_data="cannot_mortgage")
    
    kb.button(text="📊 Сводка по залогам", callback_data=f"mortgage_summary_{player_id}")
    kb.button(text="⬅️ Назад к недвижимости", callback_data=f"properties_{player_id}")
    
    kb.adjust(1)
    return kb
