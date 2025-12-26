from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Главное меню Monopoly - как в оригинале"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🎮 Начать игру', callback_data='start_game'),
                InlineKeyboardButton(text='👥 Присоединиться', callback_data='join_game')
            ],
            [
                InlineKeyboardButton(text='📊 Статистика', callback_data='show_stats'),
                InlineKeyboardButton(text='👤 Профиль', callback_data='show_profile')
            ],
            [
                InlineKeyboardButton(text='⚙️ Настройки', callback_data='open_settings'),
                InlineKeyboardButton(text='❓ Помощь', callback_data='show_help')
            ],
            [
                InlineKeyboardButton(text='🎲 Бросить кубики', callback_data='roll_dice'),
                InlineKeyboardButton(text='🏦 Банк', callback_data='open_bank')
            ]
        ]
    )
    return keyboard

def get_game_keyboard():
    """Клавиатура для игры"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🎲 Бросить кубики', callback_data='roll_dice'),
                InlineKeyboardButton(text='🏠 Купить', callback_data='buy_property')
            ],
            [
                InlineKeyboardButton(text='🏦 Банк', callback_data='open_bank'),
                InlineKeyboardButton(text='🔄 Обмен', callback_data='trade')
            ],
            [
                InlineKeyboardButton(text='⏭ Пропуск', callback_data='skip_turn'),
                InlineKeyboardButton(text='🚪 Выйти', callback_data='leave_game')
            ]
        ]
    )
    return keyboard

BANNER = '''
====================================
🎮 MONOPOLY PREMIUM BOT
👑 Версия Темного Принца
====================================
'''
