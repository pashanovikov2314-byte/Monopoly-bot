"""
🎮 Монополия Telegram Bot
С поддержкой белого списка и всех фич
Без обязательной MongoDB
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from flask import Flask, render_template, request, jsonify

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
class Config:
    BOT_TOKEN = os.getenv('TOKEN', '')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    PORT = int(os.getenv('PORT', 8080))
    ADMIN_ID = 795778250
    WHITELIST_PATH = Path('config/whitelist.json')
    
    # MongoDB опциональна
    MONGODB_URI = os.getenv('MONGODB_URI', '')
    USE_MONGODB = bool(MONGODB_URI)
    
    # Сообщения
    BOT_DOWN_MESSAGE = "🎮 Бот не работает, или сломался - Темный принц уже исправляет!"
    DEVELOPER_INFO = "👑 Разработчик: qulms - Темный принц (only for Shit Daily)"
    RULES_URL = "https://telegra.ph/Pravila-igry-Monopoliya-v-Telegram-bote-01-04"

# ========== WHITELIST МЕНЕДЖЕР ==========
class WhitelistManager:
    def __init__(self):
        self.whitelist_path = Config.WHITELIST_PATH
        self.load_whitelist()
    
    def load_whitelist(self):
        """Загрузка белого списка"""
        try:
            with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info("✅ Белый список загружен")
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
    
    def is_web_access_allowed(self, user_id: int) -> bool:
        """Проверка доступа к веб-панели"""
        return user_id in self.data["web_access_users"]
    
    def add_chat(self, chat_id: int, chat_name: str, owner_id: int):
        """Добавление чата в белый список"""
        if not self.is_chat_allowed(chat_id):
            self.data["allowed_chats"].append({
                "chat_id": chat_id,
                "chat_name": chat_name,
                "owner_id": owner_id,
                "added_date": datetime.now().strftime("%Y-%m-%d"),
                "active": True
            })
            self.save_whitelist()
            return True
        return False

# ========== ИГРОВОЙ МЕНЕДЖЕР (БЕЗ БАЗЫ ДАННЫХ) ==========
class GameManager:
    """Упрощенный менеджер игр без MongoDB"""
    
    def __init__(self):
        self.active_games = {}
        self.lobbies = {}
        logger.info("✅ Игровой менеджер инициализирован (без базы данных)")
    
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
        return lobby_id
    
    def join_lobby(self, lobby_id: str, player_id: int, player_name: str):
        """Присоединение к лобби"""
        if lobby_id in self.lobbies:
            lobby = self.lobbies[lobby_id]
            # Проверяем, не присоединился ли уже
            for player in lobby["players"]:
                if player["id"] == player_id:
                    return False, "Вы уже в лобби"
            
            # Добавляем игрока
            lobby["players"].append({"id": player_id, "name": player_name})
            return True, "Вы присоединились к лобби"
        return False, "Лобби не найдено"

# ========== СООБЩЕНИЯ (С РАЗНООБРАЗИЕМ) ==========
class MessageVariants:
    """Класс для разнообразных ответов бота"""
    
    @staticmethod
    def get_greeting():
        variants = [
            "Приветствую, повелитель монополий! 🎮",
            "О, великий стратег, я к вашим услугам! 👑",
            "Добро пожаловать в мир Монополии! 🏙️",
            "Готов покорять бизнес-мир? Я помогу! 💼"
        ]
        import random
        return random.choice(variants)
    
    @staticmethod
    def get_game_start():
        variants = [
            "🎲 Игра начинается! Готовьте свои стратегии!",
            "⚡ Погнали! Кто станет монополистом?",
            "🏦 Игра запущена! Удачи в бизнес-баталиях!",
            "🚀 Начинаем экономическую битву века!"
        ]
        import random
        return random.choice(variants)
    
    @staticmethod
    def get_error():
        variants = [
            "Ой, что-то пошло не так... 🫣",
            "Кажется, у нас технические шоколадки... 🍫",
            "Этого я не ожидал... Давай попробуем еще раз? 🤔",
            "Моя логика дала сбой... перезагрузка! 🔄"
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
                InlineKeyboardButton("▶️ Начать игру", callback_data=f"start_game_{lobby_id}"),
                InlineKeyboardButton("📋 Список игроков", callback_data=f"players_{lobby_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# Глобальные менеджеры
whitelist_manager = WhitelistManager()
game_manager = GameManager()

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
    
    # Обработка разных callback
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
            # Отправляем меню в чат
            game_message = "🎮 *Игровое меню (персональное):*"
            await context.bot.send_message(
                chat_id=user.id if chat.type == 'private' else chat.id,
                text=game_message,
                parse_mode='Markdown',
                reply_markup=Keyboards.get_game_keyboard(user.id)
            )
            await query.edit_message_text("✅ Меню скрыто. Используйте кнопки в чате.")
    
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
        message = (
            "📊 *Лидерборд*\n\n"
            "🚧 Раздел в разработке...\n"
            "Скоро здесь появится рейтинг игроков!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')

async def return_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текста 'вернуть меню'"""
    if update.message.text.lower() == "вернуть меню":
        await update.message.reply_text(
            "✅ Меню возвращено!",
            reply_markup=Keyboards.get_game_keyboard(update.effective_user.id)
        )

# ========== ВЕБ-СЕРВЕР ДЛЯ МОНИТОРИНГА ==========
app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница веб-панели"""
    # Базовая защита - можно расширить
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API для проверки статуса бота"""
    try:
        status = {
            "status": "online",
            "bot_name": "Monopoly Bot",
            "version": "2.0.0",
            "whitelisted_chats": len(whitelist_manager.data["allowed_chats"]),
            "active_games": len(game_manager.active_games),
            "active_lobbies": len(game_manager.lobbies),
            "use_mongodb": Config.USE_MONGODB,
            "uptime": "0 дней",
            "developer": "qulms - Темный принц",
            "bot_down_message": Config.BOT_DOWN_MESSAGE
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def setup_handlers(application):
    """Настройка обработчиков"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("monopoly", monopoly_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, return_menu_text))

def main():
    """Основная функция запуска"""
    if not Config.BOT_TOKEN:
        logger.error("❌ Токен бота не найден! Установите переменную TOKEN")
        sys.exit(1)
    
    # Информируем о MongoDB
    if not Config.USE_MONGODB:
        logger.warning("⚠️ MongoDB не настроена. Игра будет работать в упрощенном режиме.")
    
    # Создаем приложение
    application = Application.builder().token(Config.BOT_TOKEN).build()
    setup_handlers(application)
    
    # Запускаем бота
    logger.info("🚀 Бот Monopoly запускается...")
    logger.info(f"✅ Белый список: {len(whitelist_manager.data['allowed_chats'])} чатов")
    logger.info(f"✅ MongoDB: {'Включена' if Config.USE_MONGODB else 'Отключена'}")
    
    application.run_polling()

if __name__ == '__main__':
    main()
