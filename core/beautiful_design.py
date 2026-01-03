"""
✨ BEAUTIFUL DESIGN MODULE FOR MONOPOLY BOT
Полностью переработанный визуальный дизайн
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold, hitalic, hcode, hpre, hlink
import random

class BeautifulDesign:
    """Современный дизайн с анимациями и градиентами"""
    
    # Цветовые темы
    THEMES = {
        "default": ["🔷", "🔶", "💎", "✨", "🌟"],
        "premium": ["🟣", "🟠", "💫", "⚡", "🎇"],
        "gold": ["🏆", "🥇", "💰", "💎", "👑"]
    }
    
    @staticmethod
    def get_theme_icons(theme="default"):
        """Получить иконки для темы"""
        return BeautifulDesign.THEMES.get(theme, BeautifulDesign.THEMES["default"])
    
    @staticmethod
    def create_main_menu(user_data=None):
        """Главное меню с современным дизайном"""
        icons = BeautifulDesign.get_theme_icons()
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Основные кнопки с эмодзи
        menu_buttons = [
            (f"{icons[0]} Новая игра", "new_game"),
            (f"{icons[1]} Продолжить", "continue_game"),
            (f"{icons[2]} Статистика", "stats"),
            (f"{icons[3]} Правила", "rules"),
            (f"👥 Пригласить друзей", "invite"),
            (f"⚙️ Настройки", "settings"),
            (f"💎 Премиум", "premium"),
            (f"🏆 Лидерборд", "leaderboard"),
            (f"🎁 Ежедневный бонус", "daily_bonus"),
            (f"🛍 Магазин", "shop"),
            (f"❓ Помощь", "help"),
            (f"ℹ️ О проекте", "about")
        ]
        
        # Создаем красивую сетку кнопок
        for i in range(0, len(menu_buttons), 2):
            if i+1 < len(menu_buttons):
                keyboard.row(
                    InlineKeyboardButton(menu_buttons[i][0], callback_data=menu_buttons[i][1]),
                    InlineKeyboardButton(menu_buttons[i+1][0], callback_data=menu_buttons[i+1][1])
                )
            else:
                keyboard.row(InlineKeyboardButton(menu_buttons[i][0], callback_data=menu_buttons[i][1]))
        
        # Дополнительная строка с функциональными кнопками
        keyboard.row(
            InlineKeyboardButton("👁️ Скрыть меню", callback_data="hide_menu"),
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
        )
        
        return keyboard
    
    @staticmethod
    def create_game_interface(game_state):
        """Игровой интерфейс с кнопками управления"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        # Игровые действия с красивыми иконками
        game_actions = [
            ("🎲 Бросить кубики", "roll_dice"),
            ("💵 Купить участок", "buy_property"),
            ("🏗️ Построить дом", "build_house"),
            ("🏢 Построить отель", "build_hotel"),
            ("💳 Торговать", "trade"),
            ("🏦 Взять ипотеку", "mortgage"),
            ("🔄 Обменять", "exchange"),
            ("⏸️ Пропустить ход", "skip_turn"),
            ("📊 Статус игры", "game_status"),
            ("🎯 Стратегия", "strategy"),
            ("💬 Чат игры", "game_chat"),
            ("🏳️ Сдаться", "surrender")
        ]
        
        # Добавляем кнопки в сетку 3x4
        for i in range(0, len(game_actions), 3):
            row_buttons = []
            for j in range(3):
                if i+j < len(game_actions):
                    row_buttons.append(InlineKeyboardButton(
                        game_actions[i+j][0], 
                        callback_data=game_actions[i+j][1]
                    ))
            if row_buttons:
                keyboard.row(*row_buttons)
        
        # Управление интерфейсом
        keyboard.row(
            InlineKeyboardButton("👁️ Скрыть меню", callback_data="hide_game_menu"),
            InlineKeyboardButton("📱 Компактный вид", callback_data="compact_view"),
            InlineKeyboardButton("✨ Показать меню", callback_data="show_menu")
        )
        
        return keyboard
    
    @staticmethod
    def welcome_message(user):
        """Красивое приветственное сообщение"""
        icons = BeautifulDesign.get_theme_icons("premium")
        
        return f"""{icons[4]} {hbold('MONOPOLY PREMIUM EDITION')} {icons[4]}

{icons[2]} {hitalic('Добро пожаловать,')} {hbold(user.first_name)}! {icons[2]}

{icons[0]} {hbold('🌟 Ваш профиль:')}
• 🆔 ID: {hcode(str(user.id))}
• 📅 Регистрация: сегодня
• 🏅 Уровень: Новичок
• 💰 Стартовый капитал: {hbold('$1,500,000')}

{icons[1]} {hbold('🎮 Доступные режимы:')}
✓ Классическая монополия
✓ Турнирный режим
✓ Быстрая игра (10 мин)
✓ Мультиплеер до 8 игроков

{icons[3]} {hbold('⚡ Быстрый старт:')}
1. Нажмите «Новая игра»
2. Выберите режим
3. Пригласите друзей
4. Начинайте играть!

👇 {hitalic('Выберите действие из меню ниже:')}"""
    
    @staticmethod
    def game_board_display(board_data, player_position):
        """Красивое отображение игрового поля"""
        icons = BeautifulDesign.get_theme_icons("gold")
        
        display = f"""{icons[0]} {hbold('🎪 ИГРОВОЕ ПОЛЕ МОНОПОЛИИ')} {icons[0]}

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
"""
        
        # Создаем визуализацию поля
        cells = board_data.get("cells", [])
        for i in range(0, len(cells), 4):
            row = cells[i:i+4]
            row_display = "┃ "
            
            for j, cell in enumerate(row):
                cell_num = i + j + 1
                emoji = BeautifulDesign.get_cell_emoji(cell.get("type", ""))
                
                # Подсвечиваем текущую позицию игрока
                if cell_num == player_position:
                    row_display += f"{icons[2]}{emoji}{cell.get('name', '')[0:5]:5}{icons[2]} "
                else:
                    row_display += f"{emoji}{cell.get('name', '')[0:5]:5} "
            
            row_display += "┃"
            display += row_display + "\n"
        
        display += """┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 Статус:
• 🎯 Ваша позиция: """ + hbold(f"Клетка #{player_position}") + """
• 💼 Баланс: """ + hbold(f"${board_data.get('balance', 0):,}") + """
• 🏠 Владения: """ + hbold(str(board_data.get("properties", 0))) + """
• 🎲 Следующий бросок через: 15 сек

✨ Совет: Купите 3 участка одного цвета для получения бонуса!"""
        
        return display
    
    @staticmethod
    def get_cell_emoji(cell_type):
        """Эмодзи для типов клеток с улучшенным дизайном"""
        emoji_map = {
            "property": "🏠",
            "railroad": "🚅",
            "utility": "⚡", 
            "chance": "🎭",
            "community": "📬",
            "tax": "💸",
            "luxury_tax": "💎",
            "jail": "🚨",
            "go": "🚀",
            "free_parking": "🅿️",
            "go_to_jail": "⚠️",
            "station": "🚉",
            "company": "🏢"
        }
        return emoji_map.get(cell_type, "⬜")
    
    @staticmethod
    def create_stats_display(stats):
        """Красивое отображение статистики"""
        icons = BeautifulDesign.get_theme_icons()
        
        return f"""{icons[3]} {hbold('📈 ВАША СТАТИСТИКА')} {icons[3]}

┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃        Параметр         ┃ Значение  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━┫
┃ 🎮 Всего сыграно игр    ┃ {hbold(str(stats.get('total_games', 0))):>8} ┃
┃ 🏆 Побед                ┃ {hbold(str(stats.get('wins', 0))):>8} ┃
┃ 💰 Максимальный баланс  ┃ {hbold(f"${stats.get('max_balance', 0):,}"):>8} ┃
┃ ⏱️ Среднее время игры   ┃ {hbold(f"{stats.get('avg_time', 0)}м"):>8} ┃
┃ 🤝 Успешных сделок      ┃ {hbold(str(stats.get('trades', 0))):>8} ┃
┃ 🏠 Построено домов      ┃ {hbold(str(stats.get('houses', 0))):>8} ┃
┃ 🏢 Построено отелей     ┃ {hbold(str(stats.get('hotels', 0))):>8} ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━┛

{icons[1]} {hitalic('🏅 Достижения:')}
""" + "\n".join([f"• {achievement}" for achievement in stats.get("achievements", [])]) + f"""

{icons[2]} {hitalic('📊 Рейтинг среди игроков:')} #{stats.get('rank', 'N/A')}
"""
    
    @staticmethod
    def notification(type="info", message=""):
        """Красивые уведомления"""
        icons = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "money": "💰",
            "dice": "🎲",
            "property": "🏠",
            "event": "🎭"
        }
        
        icon = icons.get(type, "💬")
        border = "═" * 30
        
        return f"""{icon} {hbold(type.upper())} {icon}
{border}
{message}
{border}"""
