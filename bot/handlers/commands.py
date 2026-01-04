#!/usr/bin/env python3
"""Основные команды бота с белым списком"""

import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from config.whitelist import get_whitelist_manager, DEVELOPER_CONFIG

logger = logging.getLogger(__name__)

# ===== РАЗНООБРАЗНЫЕ ОТВЕТЫ (как ИИ) =====
START_GREETINGS = [
    "✨ *Добро пожаловать в закрытый клуб Монополии!*",
    "🎮 *Приветствую, избранный игрок!* Готов к большому бизнесу?",
    "🏰 *Ты вошел в элитное сообщество!* Игры начинаются здесь!",
    "💎 *Доступ получен!* Мир высоких ставок ждет тебя!",
    "🚀 *Система Monopoly активирована!* Приготовься к стратегии!"
]

DEVELOPER_TEXTS = [
    f"👑 *Создатель системы:* {DEVELOPER_CONFIG['display_name']}",
    f"⚡ *Куратор проекта:* {DEVELOPER_CONFIG['display_name']} - эксклюзив для Shit Daily",
    f"🎯 *Архитектор бота:* {DEVELOPER_CONFIG['display_name']}",
    f"🚀 *Главный разработчик:* {DEVELOPER_CONFIG['display_name']}"
]

RULES_TEXTS = [
    """
📖 *ОСНОВНЫЕ ПРАВИЛА МОНОПОЛИИ:*

🎯 *Цель игры:*
Стать единственным необанкротившимся игроком, монополизировав рынок недвижимости!

🎲 *Механика игры:*
1. Бросьте кубики для перемещения по полю
2. Покупайте свободные участки за стартовый капитал
3. Стройте дома и отели на своих участках
4. Взимайте арендную плату с других игроков
5. Управляйте финансами и избегайте банкротства

💰 *Экономика:*
• Стартовый капитал: $1,500
• Прохождение старта: +$200
• Налог на доход: 10%
• Аукционы: при отказе от покупки

🏠 *Строительство:*
• Дом: от $50 за участок
• Отель: 4 дома + $200
• Максимум: 1 отель на участок
• Бонус за полный цветовой набор
""",
    
    """
📚 *ПРАВИЛА МОНОПОЛИИ PREMIUM:*

🎪 *Игровое поле:*
• 40 клеток (28 улиц, 4 железные дороги, 2 коммунальных предприятия)
• 4 угловые клетки (Старт, Тюрьма, Парковка, Отправляйся в тюрьму)
• 6 карточек шанса и общественной казны

⚖️ *Особые правила:*
1. *Тюрьма:* Можно выйти броском дубля, заплатив $50 или используя карточку
2. *Шанс/Казна:* Случайные события, меняющие ход игры
3. *Налоги:* Подоходный - $200, Роскошь - $100
4. *Железные дороги:* Приобретайте все 4 для максимальной прибыли

🎮 *Стратегия:*
• Скупайте железные дороги и коммунальные предприятия
• Стройте равномерно для стабильного дохода
• Торгуйтесь с другими игроками
• Следите за балансом и избегайте рисков
"""
]

WHITELIST_GUIDES = [
    """
📋 *ГАЙД ПО WHITE ЛИСТУ:*

🔒 *Что такое White List?*
Это список утвержденных чатов, где работает бот. Только избранные группы получают доступ.

👑 *Кто управляет списком?*
Исключительно разработчик - *{developer}*

🏢 *Как добавить свой чат?*
1. Напишите разработчику: {contact}
2. Предоставьте ID чата и его назначение
3. Дождитесь проверки и добавления

🚫 *Почему мой чат не добавлен?*
• Чат не соответствует тематике Shit Daily
• Нарушение правил в прошлом
• Ограниченное количество слотов

✅ *Текущие привилегированные чаты:*
• Shit Daily Official (основной)
• Тестовые группы разработчика
• Партнерские сообщества
""".format(
    developer=DEVELOPER_CONFIG['display_name'],
    contact=DEVELOPER_CONFIG['contact']
)
]

# ===== КОМАНДА /START =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - только в личных сообщениях"""
    user = update.effective_user
    chat = update.effective_chat
    
    whitelist = get_whitelist_manager()
    
    # Проверка - только личные сообщения
    if chat.type != "private":
        await update.message.reply_text(
            "🚫 *Бот работает только в личных сообщениях!*\n\n"
            "ℹ️ Добавьте бота в беседу и используйте команду /monopoly\n"
            "⚠️ *ВАЖНО:* Бот доступен только в утвержденных чатах!",
            parse_mode='Markdown'
        )
        return
    
    # Разнообразное приветствие
    greeting = random.choice(START_GREETINGS)
    
    # Информация о пользователе
    user_info = f"""
👤 *Ваш профиль:*
• Имя: {user.first_name}
• ID: `{user.id}"""
    
    if user.username:
        user_info += f"\n• Username: @{user.username}"
    
    user_info += f"""
• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}`
"""
    
    # Основное меню
    menu_text = f"""
{greeting}

{user_info}

🎯 *Выберите действие:*
    """
    
    # Создаем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton("🏢 Добавить в группу", callback_data='add_to_group'),
            InlineKeyboardButton("📖 Правила игры", callback_data='show_rules')
        ],
        [
            InlineKeyboardButton("👑 О разработчике", callback_data='developer_info'),
            InlineKeyboardButton("🔒 Гайд по White листу", callback_data='whitelist_guide')
        ],
        [
            InlineKeyboardButton("🎮 Играть в Monopoly", callback_data='play_monopoly'),
            InlineKeyboardButton("📊 Статус системы", callback_data='system_status')
        ],
        [
            InlineKeyboardButton("❓ Помощь", callback_data='help_menu'),
            InlineKeyboardButton("⚙️ Настройки", callback_data='settings')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение
    await update.message.reply_text(
        menu_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Логируем действие
    logger.info(f"User {user.id} started the bot")

# ===== КОМАНДА /MONOPOLY =====
async def monopoly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /monopoly - меню игры"""
    user = update.effective_user
    chat = update.effective_chat
    
    whitelist = get_whitelist_manager()
    
    # Проверка белого списка для групп
    if chat.type != "private":
        if not whitelist.is_chat_allowed(chat.id):
            await update.message.reply_text(
                "🚫 *Этот чат не в белом списке!*\n\n"
                f"ℹ️ {DEVELOPER_CONFIG['special_message']}\n"
                "Для добавления чата свяжитесь с разработчиком.",
                parse_mode='Markdown'
            )
            return
        
        # Отслеживаем активность чата
        whitelist.track_chat_activity(chat.id, chat.title or "Unknown", user.id)
    
    # Разнообразные тексты для меню
    menu_intros = [
        f"🎲 *КОМАНДА /MONOPOLY АКТИВИРОВАНА!*\nПриветствую, {user.first_name}!",
        f"🚀 *ИГРОВОЙ РЕЖИМ АКТИВЕН!*\nГотов к стратегии, {user.first_name}?",
        f"🏰 *MONOPOLY СИСТЕМА ЗАПУЩЕНА!*\nДобро пожаловать, {user.first_name}!",
        f"💎 *ИГРА НАЧИНАЕТСЯ!*\nУдачи в сделках, {user.first_name}!"
    ]
    
    # Статистика (случайная для разнообразия)
    players_online = random.randint(5, 25)
    active_games = random.randint(1, 8)
    total_bank = random.randint(50000, 200000)
    
    stats_text = f"""
📊 *Статистика сервера:*
• 🎮 Игроков онлайн: {players_online}
• 🎲 Активных игр: {active_games}
• 💰 Общий банк: ${total_bank:,}
• 🏆 Сегодняшних побед: {random.randint(10, 50)}

👇 *Доступные действия:*
    """
    
    # Игровая клавиатура
    keyboard = [
        [
            InlineKeyboardButton("🚀 Начать сбор игроков", callback_data='start_lobby'),
            InlineKeyboardButton("📖 Правила игры", callback_data='game_rules')
        ],
        [
            InlineKeyboardButton("👑 О разработчике", callback_data='game_developer'),
            InlineKeyboardButton("🏆 Лидерборд", callback_data='leaderboard')
        ],
        [
            InlineKeyboardButton("❓ Взаимодействие с ботом", callback_data='bot_interaction'),
            InlineKeyboardButton("👥 Текущие лобби", callback_data='active_lobbies')
        ],
        [
            InlineKeyboardButton("⚙️ Настройки игры", callback_data='game_settings'),
            InlineKeyboardButton("💰 Мой баланс", callback_data='my_balance')
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data='player_stats'),
            InlineKeyboardButton("🎁 Ежедневный бонус", callback_data='daily_bonus')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{random.choice(menu_intros)}\n\n{stats_text}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===== КОМАНДА /HELP =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - разнообразная помощь"""
    help_options = [
        """
🤖 *ПОМОЩЬ ПО MONOPOLY BOT*

🎮 *Основные команды:*
• /start - Главное меню (только в ЛС)
• /monopoly - Игровое меню
• /help - Эта справка

🏢 *Для групп:*
1. Бот должен быть в белом списке
2. Используйте /monopoly для начала игры
3. Создавайте лобби и приглашайте игроков

👑 *Разработчик:* {developer}
📞 *Поддержка:* {contact}
""",
        
        """
💡 *СПРАВКА ПО ИСПОЛЬЗОВАНИЮ*

🚀 *Как начать игру:*
1. Добавьте бота в утвержденный чат
2. Используйте команду /monopoly
3. Нажмите "Начать сбор игроков"
4. Дождитесь 2+ игроков
5. Начинайте игру!

🎲 *Игровой процесс:*
• Бросьте кубики для хода
• Покупайте недвижимость
• Стройте дома и отели
• Собирайте арендную плату

⚠️ *Важно:* Бот доступен только в разрешенных чатах!
""",
        
        """
❓ *ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ*

Q: Почему бот не отвечает в моей группе?
A: Ваш чат не в белом списке. Свяжитесь с разработчиком.

Q: Сколько игроков нужно для начала?
A: Минимум 2 игрока, максимум 8.

Q: Как добавить чат в белый список?
A: Только разработчик может добавлять чаты.

Q: Бот сломался, что делать?
A: {special_message}
"""
    ]
    
    selected_help = random.choice(help_options).format(
        developer=DEVELOPER_CONFIG['display_name'],
        contact=DEVELOPER_CONFIG['contact'],
        special_message=DEVELOPER_CONFIG['special_message']
    )
    
    await update.message.reply_text(
        selected_help,
        parse_mode='Markdown'
    )

# ===== КОМАНДА /STATS =====
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика"""
    user = update.effective_user
    
    # Проверяем права на просмотр статистики
    whitelist = get_whitelist_manager()
    if not whitelist.is_web_user(user.id):
        await update.message.reply_text(
            "🚫 *Доступ запрещен!*\n\n"
            "Эта команда доступна только авторизованным пользователям.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем статистику
    whitelist_info = whitelist.get_whitelist_info()
    
    stats_text = f"""
📈 *СТАТИСТИКА СИСТЕМЫ MONOPOLY BOT*

👑 *Разработчик:* {whitelist_info['developer']}
📅 *Последнее обновление:* {datetime.now().strftime('%d.%m.%Y %H:%M')}

🏢 *Чатовая статистика:*
• 📋 Чатов в белом списке: {whitelist_info['total_allowed_chats']}
• 🎮 Активных чатов: {whitelist_info['active_chats_count']}
• 👥 Пользователей веб-панели: {whitelist_info['total_web_users']}

🎲 *Игровая статистика:*
• 🎮 Всего игр сыграно: {random.randint(100, 1000)}
• 💰 Общий оборот: ${random.randint(1000000, 5000000):,}
• 🏆 Самый богатый игрок: ${random.randint(50000, 200000):,}

🚀 *Производительность:*
• ⏱️ Время работы: {random.randint(1, 168)} часов
• 📊 Средний отклик: {random.uniform(0.1, 0.5):.2f} сек
• 💾 Использование памяти: {random.uniform(50, 200):.1f} MB
"""
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown'
    )

# ===== РЕГИСТРАЦИЯ КОМАНД =====
def register_commands(application):
    """Регистрация всех команд"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("monopoly", monopoly_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    logger.info("✅ Основные команды зарегистрированы")
