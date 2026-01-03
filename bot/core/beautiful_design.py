"""
✨ BEAUTIFUL DESIGN MODULE FOR MONOPOLY BOT
Адаптирован для python-telegram-bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class BeautifulDesign:
    """Современный дизайн для бота"""
    
    # Цветовые темы
    THEMES = {
        "default": ["🔷", "🔶", "💎", "✨", "🌟"],
        "premium": ["🟣", "🟠", "💫", "⚡", "🎇"],
        "gold": ["🏆", "🥇", "💰", "💎", "👑"]
    }
    
    @staticmethod
    def create_main_menu():
        """Главное меню с современным дизайном"""
        keyboard = [
            [
                InlineKeyboardButton("🎮 Новая игра", callback_data='new_game'),
                InlineKeyboardButton("📊 Статистика", callback_data='stats')
            ],
            [
                InlineKeyboardButton("📖 Правила", callback_data='rules'),
                InlineKeyboardButton("👥 Пригласить", callback_data='invite')
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data='settings'),
                InlineKeyboardButton("💎 Премиум", callback_data='premium')
            ],
            [
                InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_menu'),
                InlineKeyboardButton("🔄 Обновить", callback_data='refresh')
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_game_interface():
        """Игровой интерфейс с кнопками управления"""
        keyboard = [
            [
                InlineKeyboardButton("🎲 Бросить кубики", callback_data='roll_dice'),
                InlineKeyboardButton("💵 Купить участок", callback_data='buy_property')
            ],
            [
                InlineKeyboardButton("🏗️ Строить дом", callback_data='build_house'),
                InlineKeyboardButton("🏢 Построить отель", callback_data='build_hotel')
            ],
            [
                InlineKeyboardButton("💳 Торговать", callback_data='trade'),
                InlineKeyboardButton("🏦 Ипотека", callback_data='mortgage')
            ],
            [
                InlineKeyboardButton("📊 Статус игры", callback_data='game_status'),
                InlineKeyboardButton("⏸️ Пропустить ход", callback_data='skip_turn')
            ],
            [
                InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_game_menu'),
                InlineKeyboardButton("✨ Показать меню", callback_data='show_menu')
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def welcome_message(user_name: str) -> str:
        """Красивое приветственное сообщение"""
        return f"""✨ *MONOPOLY PREMIUM EDITION* ✨

🌟 *Добро пожаловать, {user_name}!* 🌟

🎯 *Ваш профиль:*
• 📅 Регистрация: сегодня
• 🏅 Уровень: Новичок
• 💰 Стартовый капитал: *$1,500,000*

🎮 *Доступные режимы:*
✓ Классическая монополия
✓ Турнирный режим
✓ Быстрая игра (10 мин)
✓ Мультиплеер до 8 игроков

⚡ *Быстрый старт:*
1. Нажмите «Новая игра»
2. Выберите режим
3. Пригласите друзей
4. Начинайте играть!

👇 *Выберите действие из меню ниже:*"""
    
    @staticmethod
    def game_board_display(board_data: dict, player_position: int) -> str:
        """Красивое отображение игрового поля"""
        display = f"""🎪 *ИГРОВОЕ ПОЛЕ МОНОПОЛИИ* 🎪

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
"""
        
        # Простая визуализация (можно улучшить)
        cells = board_data.get("cells", [])
        for i in range(0, min(8, len(cells))):
            cell = cells[i]
            emoji = BeautifulDesign.get_cell_emoji(cell.get("type", ""))
            marker = "📍" if (i + 1) == player_position else "  "
            display += f"┃ {marker} {emoji} {cell.get('name', 'Unknown'):20} ┃\n"
        
        display += """┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 *Статус:*
• 🎯 Ваша позиция: клетка *#{player_position}*
• 💼 Баланс: *${board_data.get('balance', 0):,}*
• 🏠 Владения: *{board_data.get('properties', 0)}*

✨ *Совет:* Купите 3 участка одного цвета для бонуса!"""
        
        return display
    
    @staticmethod
    def get_cell_emoji(cell_type: str) -> str:
        """Эмодзи для типов клеток"""
        emoji_map = {
            "property": "🏠",
            "railroad": "🚅",
            "utility": "⚡",
            "chance": "🎭",
            "community": "📬",
            "tax": "💸",
            "jail": "🚨",
            "go": "🚀",
            "free_parking": "🅿️"
        }
        return emoji_map.get(cell_type, "⬜")
    
    @staticmethod
    def create_stats_display(stats: dict) -> str:
        """Красивое отображение статистики"""
        return f"""📈 *ВАША СТАТИСТИКА* 📈

🎮 *Игры:*
• Всего сыграно: *{stats.get('total_games', 0)}*
• Побед: *{stats.get('wins', 0)}* ({stats.get('win_rate', 0)}%)
• Поражений: *{stats.get('losses', 0)}*

💰 *Финансы:*
• Максимальный баланс: *${stats.get('max_balance', 0):,}*
• Средний доход: *${stats.get('avg_income', 0):,}*
• Налоги уплачено: *${stats.get('taxes_paid', 0):,}*

🏆 *Достижения:*
{chr(10).join([f'• {ach}' for ach in stats.get('achievements', [])])}

📊 *Рейтинг среди игроков:* *#{stats.get('rank', 'N/A')}*"""
    
    @staticmethod
    def notification(type: str = "info", message: str = "") -> str:
        """Красивые уведомления"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "money": "💰",
            "dice": "🎲",
            "property": "🏠"
        }
        
        icon = icons.get(type, "💬")
        return f"{icon} *{type.upper()}*\n{message}"
