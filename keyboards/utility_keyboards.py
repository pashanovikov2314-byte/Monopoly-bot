"""
Utility keyboards for confirmation, navigation, etc.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional

def confirm_kb(action: str, yes_data: str, no_data: str = "cancel") -> InlineKeyboardBuilder:
    """Клавиатура подтверждения"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="✅ Да", callback_data=yes_data)
    kb.button(text="❌ Нет", callback_data=no_data)
    
    kb.adjust(2)
    return kb


def back_kb(back_to: str = "main") -> InlineKeyboardBuilder:
    """Кнопка назад"""
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data=f"back_to_{back_to}")
    return kb


def cancel_kb() -> InlineKeyboardBuilder:
    """Кнопка отмены"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel")
    return kb


def numeric_kb(min_val: int = 1, max_val: int = 1000, callback_prefix: str = "amount_") -> InlineKeyboardBuilder:
    """Клавиатура с числовыми кнопками (для торговли, залога)"""
    kb = InlineKeyboardBuilder()
    
    # Быстрые кнопки
    quick_values = [10, 50, 100, 200, 500, 1000, 1500, 2000]
    for val in quick_values:
        if min_val <= val <= max_val:
            kb.button(text=f"{val}$", callback_data=f"{callback_prefix}{val}")
    
    # Диапазонные кнопки
    ranges = [
        (f"{min_val}-{min_val+99}", f"{callback_prefix}range_{min_val}_{min_val+99}"),
        (f"{min_val+100}-{min_val+499}", f"{callback_prefix}range_{min_val+100}_{min_val+499}"),
        (f"{min_val+500}-{max_val}", f"{callback_prefix}range_{min_val+500}_{max_val}")
    ]
    
    for label, callback in ranges:
        kb.button(text=f"🔢 {label}$", callback_data=callback)
    
    kb.button(text="✏️ Ввести сумму", callback_data=f"{callback_prefix}custom")
    kb.button(text="⬅️ Назад", callback_data="back_to_bank")
    
    kb.adjust(2, 2, 2, 2)
    return kb


def yes_no_kb(yes_text: str = "✅ Да", no_text: str = "❌ Нет", 
              yes_data: str = "yes", no_data: str = "no") -> InlineKeyboardBuilder:
    """Да/Нет клавиатура"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text=yes_text, callback_data=yes_data)
    kb.button(text=no_text, callback_data=no_data)
    
    kb.adjust(2)
    return kb


def list_navigation_kb(current_page: int, total_pages: int, 
                       prefix: str = "page") -> InlineKeyboardBuilder:
    """Навигация по страницам списка"""
    kb = InlineKeyboardBuilder()
    
    if current_page > 1:
        kb.button(text="⬅️ Предыдущая", callback_data=f"{prefix}_{current_page-1}")
    
    kb.button(text=f"{current_page}/{total_pages}", callback_data="current_page")
    
    if current_page < total_pages:
        kb.button(text="Следующая ➡️", callback_data=f"{prefix}_{current_page+1}")
    
    kb.adjust(3)
    return kb


def selection_kb(items: list, callback_prefix: str = "select", 
                 items_per_row: int = 2) -> InlineKeyboardBuilder:
    """Клавиатура для выбора из списка"""
    kb = InlineKeyboardBuilder()
    
    for i, item in enumerate(items):
        if isinstance(item, dict):
            text = item.get('text', f"Item {i+1}")
            data = item.get('data', f"{callback_prefix}_{i}")
        else:
            text = str(item)
            data = f"{callback_prefix}_{i}"
        
        kb.button(text=text, callback_data=data)
    
    kb.adjust(items_per_row)
    return kb
