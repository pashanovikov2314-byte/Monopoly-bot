"""
🎮 Монополия Telegram Bot
Работает на Render через веб-хуки
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder
)
from flask import Flask, render_template, request, jsonify, Response

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
class Config:
    BOT_TOKEN = os.getenv('TOKEN', '7957782509:AAFQ7zEe1xoKxNvjZGVMvOCdmrJTijpHGrQ')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://monopoly-bot.onrender.com').rstrip('/')
    PORT = int(os.getenv('PORT', 8080))
    ADMIN_ID = 795778250
    WHITELIST_PATH = Path('config/whitelist.json')
    
    # Сообщения
    BOT_DOWN_MESSAGE = "🎮 Бот не работает, или сломался - Темный принц уже исправляет!"
    DEVELOPER_INFO = "👑 Разработчик: qulms - Темный принц (only for Shit Daily)"
    RULES_URL = "https://telegra.ph/Pravila-igry-Monopoliya-v-Telegram-bote-01-04"

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
application = None
whitelist_manager = None
game_manager = None

# ========== WHITELIST МЕНЕДЖЕР ==========
class WhitelistManager:
    def __init__(self):
        self.whitelist_path = Config.WHITELIST_PATH
        self.load_whitelist()
    
    def load_whitelist(self):
        """Загрузка белого списка"""
        try:
            if self.whitelist_path.exists():
                with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"✅ Белый список загружен: {len(self.data.get('allowed_chats', []))} чатов")
            else:
                self.data = {
                    "allowed_chats": [],
                    "admin_users": [Config.ADMIN_ID],
                    "web_access_users": [Config.ADMIN_ID],
                    "settings": {}
                }
                self.save_whitelist()
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки whitelist: {e}")
            self.data = {
                "allowed_chats": [],
                "admin_users": [Config.ADMIN_ID],
                "web_access_users": [Config.ADMIN_ID],
                "settings": {}
            }
    
    def save_whitelist(self):
        """Сохранение белого списка"""
        try:
            self.whitelist_path.parent.mkdir(exist_ok=True)
            with open(self.whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения whitelist: {e}")
            return False
    
    def is_chat_allowed(self, chat_id: int) -> bool:
        """Проверка, разрешен ли чат"""
        for chat in self.data["allowed_chats"]:
            if chat["chat_id"] == chat_id and chat.get("active", True):
                return True
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.data["admin_users"]

# ========== ИГРОВОЙ МЕНЕДЖЕР ==========
class GameManager:
    """Менеджер игр в памяти"""
    
    def __init__(self):
        self.active_games = {}
        self.lobbies = {}
        self.leaderboard = {}
        logger.info("✅ Игровой менеджер инициализирован")
    
    def create_lobby(self, chat_id: int, creator_id: int, creator_name: str):
        """Создание лобби"""
        lobby_id = f"{chat_id}_{int(datetime.now().timestamp())}"
        self.lobbies[lobby_id] = {
            "chat_id": chat_id,
            "creator_id": creator_id,
            "creator_name": creator_name,
            "players": [{"id": creator_id, "name": creator_name}],
            "created_at": datetime.now().isoformat(),
            "status": "waiting"
        }
        logger.info(f"✅ Создано лобби: {lobby_id}")
        return lobby_id
    
    def join_lobby(self, lobby_id: str, player_id: int, player_name: str):
        """Присоединение к лобби"""
        if lobby_id in self.lobbies:
            lobby = self.lobbies[lobby_id]
            
            # Проверяем, не присоединился ли уже
            for player in lobby["players"]:
                if player["id"] == player_id:
                    return False, "Вы уже в лобби"
            
            # Добавляем игрока (максимум 4)
            if len(lobby["players"]) >= 4:
                return False, "Лобби заполнено (макс. 4 игрока)"
            
            lobby["players"].append({"id": player_id, "name": player_name})
            logger.info(f"✅ Игрок {player_name} присоединился к лобби {lobby_id}")
            return True, "Вы присоединились к лобби"
        return False, "Лобби не найдено"

# ========== РАЗНООБРАЗНЫЕ СООБЩЕНИЯ ==========
class MessageVariants:
    """Класс для разнообразных ответов бота"""
    
    @staticmethod
    def get_greeting():
        variants = [
            "Приветствую, повелитель монополий! 🎮",
            "О, великий стратег, я к вашим услугам! 👑",
            "Добро пожаловать в мир Монополии! 🏙️",
            "Готов покорять бизнес-мир? Я помогу! 💼",
            "Салют, будущий монополист! Да начнется игра! 🎯"
        ]
        import random
        return random.choice(variants)
    
    @staticmethod
    def get_error():
        variants = [
            "Ой, что-то пошло не так... 🫣",
            "Кажется, у нас технические шоколадки... 🍫",
            "Этого я не ожидал... Давай попробуем еще раз? 🤔",
            "Моя логика дала сбой... перезагрузка! 🔄",
            "Упс! Кажется, я запутался в проводах... 🔌"
        ]
        import random
        return random.choice(variants)

# ========== КЛАВИАТУРЫ ==========
class Keyboards:
    """Класс для создания клавиатур"""
    
    @staticmethod
    def get_start_keyboard():
        """Клавиатура для команды /start"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Добавить в группу", callback_data="add_to_group"),
                InlineKeyboardButton("👑 Разработчик", callback_data="developer_info")
            ],
            [
                InlineKeyboardButton("📜 Правила игры", callback_data="rules"),
                InlineKeyboardButton("📝 Гайд по white листу", callback_data="whitelist_guide")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_monopoly_keyboard():
        """Клавиатура для команды /monopoly"""
        keyboard = [
            [
                InlineKeyboardButton("🎮 Начать сбор игроков", callback_data="start_lobby"),
                InlineKeyboardButton("📊 Лидерборд", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("📜 Правила игры", callback_data="rules"),
                InlineKeyboardButton("👑 Разработчик", callback_data="developer_info")
            ],
            [
                InlineKeyboardButton("❓ Помощь по боту", callback_data="bot_help"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_game_keyboard(player_id: int):
        """Клавиатура во время игры"""
        keyboard = [
            [
                InlineKeyboardButton("🎲 Бросить кубики", callback_data=f"roll_{player_id}"),
                InlineKeyboardButton("🏠 Купить/Улучшить", callback_data=f"buy_{player_id}")
            ],
            [
                InlineKeyboardButton("💼 Торговать", callback_data=f"trade_{player_id}"),
                InlineKeyboardButton("🏦 Банк", callback_data=f"bank_{player_id}")
            ],
            [
                InlineKeyboardButton("📊 Статус", callback_data=f"status_{player_id}"),
                InlineKeyboardButton("🎭 Скрыть меню", callback_data=f"hide_menu_{player_id}")
            ],
            [
                InlineKeyboardButton("↩️ Вернуть меню", callback_data=f"show_menu_{player_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_lobby_keyboard(lobby_id: str):
        """Клавиатура для лобби"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Войти в игру", callback_data=f"join_{lobby_id}"),
                InlineKeyboardButton("🚪 Выйти", callback_data=f"leave_{lobby_id}")
            ],
            [
                InlineKeyboardButton("▶️ Начать игру (от 2 игроков)", callback_data=f"start_game_{lobby_id}"),
                InlineKeyboardButton("📋 Список игроков", callback_data=f"players_{lobby_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Проверяем разрешен ли чат (только для групповых чатов)
    if chat.type != 'private' and not whitelist_manager.is_chat_allowed(chat.id):
        await update.message.reply_text(
            "❌ Этот бот недоступен для этой группы.\n"
            "Обратитесь к разработчику для добавления в белый список."
        )
        return
    
    greeting = MessageVariants.get_greeting()
    message = f"{greeting}\n\n👤 Игрок: {user.first_name}\n🆔 ID: {user.id}"
    
    await update.message.reply_text(
        message,
        reply_markup=Keyboards.get_start_keyboard()
    )

async def monopoly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /monopoly"""
    chat = update.effective_chat
    
    # Проверяем разрешен ли чат
    if chat.type != 'private' and not whitelist_manager.is_chat_allowed(chat.id):
        await update.message.reply_text(
            "❌ Команда доступна только в разрешенных чатах."
        )
        return
    
    message = (
        "🎮 *Меню Монополии*\n\n"
        "Выберите действие из меню ниже:"
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.get_monopoly_keyboard()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    chat = update.effective_chat
    
    try:
        if data == "add_to_group":
            message = (
                "🤖 *Как добавить бота в группу:*\n\n"
                "1. Создайте группу в Telegram\n"
                "2. Добавьте этого бота как участника\n"
                "3. Бот автоматически проверит доступность\n"
                "4. Если группа не в белом списке, обратитесь к разработчику\n\n"
                "⚠️ Бот работает только в разрешенных чатах!"
            )
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "developer_info":
            message = f"👑 *Информация о разработчике:*\n\n{Config.DEVELOPER_INFO}"
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "rules":
            message = (
                "📜 *Правила игры в Монополию:*\n\n"
                "Основные правила классической Монополии.\n"
                f"Полные правила: {Config.RULES_URL}\n\n"
                "1. Игроки ходят по очереди\n"
                "2. Покупайте собственность и стройте дома\n"
                "3. Собирайте ренту с других игроков\n"
                "4. Цель - остаться единственным не обанкротившимся"
            )
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "whitelist_guide":
            message = (
                "📝 *Гайд по White List:*\n\n"
                "Бот работает только в определенных группах.\n\n"
                "✅ *Как попасть в белый список:*\n"
                "1. Напишите разработчику\n"
                "2. Укажите ID вашей группы\n"
                "3. Дождитесь подтверждения\n\n"
                "🛡️ *Текущие ограничения:*\n"
                "• Максимум 1 активная игра на чат\n"
                "• Только проверенные группы\n"
                "• Приватные чаты не поддерживаются"
            )
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "start_lobby":
            # Проверяем разрешен ли чат
            if chat.type != 'private' and not whitelist_manager.is_chat_allowed(chat.id):
                await query.edit_message_text(
                    "❌ Создание лобби доступно только в разрешенных чатах."
                )
                return
            
            # Создаем лобби
            lobby_id = game_manager.create_lobby(chat.id, user.id, user.first_name)
            lobby = game_manager.lobbies[lobby_id]
            
            players_list = "\n".join([f"• {p['name']}" for p in lobby["players"]])
            message = (
                f"🎮 *Лобби создано!*\n\n"
                f"👥 Игроки ({len(lobby['players'])}/4):\n{players_list}\n\n"
                f"👤 Создатель: {user.first_name}\n"
                f"🆔 ID лобби: `{lobby_id[:8]}`\n\n"
                f"Присоединяйтесь, чтобы начать игру!"
            )
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=Keyboards.get_lobby_keyboard(lobby_id)
            )
        
        elif data.startswith("join_"):
            lobby_id = data.split("join_")[1]
            success, result = game_manager.join_lobby(lobby_id, user.id, user.first_name)
            
            if success:
                lobby = game_manager.lobbies[lobby_id]
                players_list = "\n".join([f"• {p['name']}" for p in lobby["players"]])
                message = (
                    f"✅ *{user.first_name} присоединился!*\n\n"
                    f"👥 Игроки ({len(lobby['players'])}/4):\n{players_list}"
                )
                
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=Keyboards.get_lobby_keyboard(lobby_id)
                )
            else:
                await query.answer(result, show_alert=True)
        
        elif data.startswith("players_"):
            lobby_id = data.split("players_")[1]
            if lobby_id in game_manager.lobbies:
                lobby = game_manager.lobbies[lobby_id]
                players_list = "\n".join([f"• {p['name']}" for p in lobby["players"]])
                message = f"👥 *Игроки в лобби:*\n\n{players_list}"
                await query.answer(message, show_alert=True)
        
        elif data.startswith("hide_menu_"):
            player_id = int(data.split("_")[2])
            if user.id == player_id:
                game_message = (
                    f"🎮 *Игровое меню (персональное) для {user.first_name}:*\n\n"
                    f"Кнопки скрыты. Используйте 'вернуть меню' для восстановления."
                )
                await context.bot.send_message(
                    chat_id=user.id if chat.type == 'private' else chat.id,
                    text=game_message,
                    parse_mode='Markdown'
                )
                await query.edit_message_text("✅ Меню скрыто. Напишите 'вернуть меню' для восстановления.")
        
        elif data.startswith("show_menu_"):
            player_id = int(data.split("_")[2])
            if user.id == player_id:
                await query.edit_message_text(
                    "✅ Меню возвращено!",
                    reply_markup=Keyboards.get_game_keyboard(user.id)
                )
        
        elif data == "bot_help":
            message = (
                "❓ *Помощь по взаимодействию с ботом:*\n\n"
                "🎮 *Основные команды:*\n"
                "• /start - Запуск бота\n"
                "• /monopoly - Меню игры\n\n"
                "🕹️ *Кнопки в игре:*\n"
                "• 🎲 - Бросить кубики\n"
                "• 🏠 - Купить/улучшить\n"
                "• 💼 - Торговать\n"
                "• 🏦 - Взаимодействие с банком\n"
                "• 📊 - Статус игры\n"
                "• 🎭 - Скрыть/показать меню\n\n"
                "⚙️ *Особенности:*\n"
                "• Меню можно скрыть для себя\n"
                "• Кнопки возвращаются командой 'вернуть меню'\n"
                "• Игра доступна только в белом списке"
            )
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "leaderboard":
            if game_manager.leaderboard:
                top_players = sorted(game_manager.leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
                leaderboard_text = "\n".join([f"{i+1}. {name}: {score}" for i, (name, score) in enumerate(top_players)])
                message = f"📊 *Топ 10 игроков:*\n\n{leaderboard_text}"
            else:
                message = (
                    "📊 *Лидерборд*\n\n"
                    "Пока никто не играл. Будьте первым!\n"
                    "Сыграйте несколько игр, чтобы попасть в таблицу лидеров!"
                )
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "settings":
            message = (
                "⚙️ *Настройки бота:*\n\n"
                "• 🛡️ Режим белого списка: Включен\n"
                "• 👥 Максимум игроков: 4\n"
                "• 💰 Стартовый капитал: 1500\n"
                "• 🏠 Домов на улице: 4\n"
                "• 🏨 Отелей: 1\n\n"
                "Для изменения настроек обратитесь к разработчику."
            )
            await query.edit_message_text(message, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Ошибка в обработке callback: {e}")
        await query.answer(MessageVariants.get_error(), show_alert=True)

async def return_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текста 'вернуть меню'"""
    if update.message.text.lower() == "вернуть меню":
        await update.message.reply_text(
            "✅ Меню возвращено!",
            reply_markup=Keyboards.get_game_keyboard(update.effective_user.id)
        )
    elif update.message.text.lower() == "бот сломался":
        await update.message.reply_text(Config.BOT_DOWN_MESSAGE)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "🤔 Не понимаю эту команду.\n"
        "Попробуйте /start или /monopoly"
    )

# ========== ВЕБ-СЕРВЕР ДЛЯ МОНИТОРИНГА ==========
app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница веб-панели"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API для проверки статуса бота"""
    try:
        status = {
            "status": "online",
            "bot_name": "Monopoly Bot",
            "version": "2.0.0",
            "whitelisted_chats": len(whitelist_manager.data.get("allowed_chats", [])),
            "active_games": len(game_manager.active_games),
            "active_lobbies": len(game_manager.lobbies),
            "total_players": sum(len(lobby.get("players", [])) for lobby in game_manager.lobbies.values()),
            "developer": "qulms - Темный принц",
            "bot_token_set": bool(Config.BOT_TOKEN),
            "webhook_url": Config.WEBHOOK_URL,
            "server_time": datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Ошибка в API статуса: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route(f'/{Config.BOT_TOKEN}', methods=['POST'])
async def webhook():
    """Endpoint для веб-хуков от Telegram"""
    if request.is_json:
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        
        # Обрабатываем update асинхронно
        await application.process_update(update)
        
        logger.info(f"✅ Веб-хук обработан: {update.update_id}")
        return Response(status=200)
    
    return Response(status=400)

# ========== ИНИЦИАЛИЗАЦИЯ И ЗАПУСК ==========
def setup_handlers(app: Application):
    """Настройка обработчиков"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("monopoly", monopoly_command))
    app.add_handler(CommandHandler("help", unknown_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, return_menu_text))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

async def setup_webhook():
    """Настройка веб-хука"""
    webhook_url = f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}"
    
    try:
        await application.bot.set_webhook(
            url=webhook_url,
            max_connections=50,
            drop_pending_updates=True
        )
        
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"✅ Веб-хук установлен: {webhook_url}")
        logger.info(f"ℹ️  Информация веб-хука: {webhook_info}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка установки веб-хука: {e}")
        return False

def init_managers():
    """Инициализация менеджеров"""
    global whitelist_manager, game_manager
    whitelist_manager = WhitelistManager()
    game_manager = GameManager()

def run_flask():
    """Запуск Flask сервера"""
    logger.info(f"🚀 Запуск Flask сервера на порту {Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=False, threaded=True)

async def main_async():
    """Асинхронная основная функция"""
    global application
    
    if not Config.BOT_TOKEN:
        logger.error("❌ Токен бота не найден! Установите переменную TOKEN")
        sys.exit(1)
    
    # Создаем приложение
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    setup_handlers(application)
    
    # Инициализируем менеджеры
    init_managers()
    
    # Настраиваем веб-хук если есть WEBHOOK_URL
    if Config.WEBHOOK_URL:
        logger.info("🔧 Настройка веб-хука для Render...")
        await setup_webhook()
    else:
        logger.warning("⚠️ WEBHOOK_URL не установлен. Используется polling режим.")
    
    # Инициализируем приложение
    await application.initialize()
    
    # Запускаем Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("✅ Бот успешно запущен!")
    logger.info(f"🌐 Веб-панель доступна по адресу: http://0.0.0.0:{Config.PORT}")
    logger.info(f"🤖 Токен бота: {'Установлен' if Config.BOT_TOKEN else 'Не установлен'}")
    logger.info(f"🛡️  Чатов в белом списке: {len(whitelist_manager.data.get('allowed_chats', []))}")
    
    # Бесконечный цикл для поддержания работы
    try:
        while True:
            await asyncio.sleep(3600)  # Спим 1 час
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота...")
        await application.stop()
        await application.shutdown()

def main():
    """Точка входа"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

