"""
🎮 Монополия Telegram Bot - Минимальная рабочая версия
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
class Config:
    BOT_TOKEN = os.getenv('TOKEN', '7957782509:AAFQ7zEe1xoKxNvjZGVMvOCdmrJTijpHGrQ')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').rstrip('/')
    PORT = int(os.getenv('PORT', 8080))
    ADMIN_ID = 795778250
    
    # Сообщения
    BOT_DOWN_MESSAGE = "🎮 Бот не работает, или сломался - Темный принц уже исправляет!"
    DEVELOPER_INFO = "👑 Разработчик: qulms - Темный принц (only for Shit Daily)"

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
            ],
            [
                InlineKeyboardButton("🎮 Играть", callback_data="play_game"),
                InlineKeyboardButton("📊 Лидерборд", callback_data="leaderboard")
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

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user = update.effective_user
    
    message = (
        f"🎮 *Привет, {user.first_name}!*\n\n"
        f"Я бот для игры в Монополию в Telegram.\n"
        f"🆔 Твой ID: `{user.id}`\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"*Доступные команды:*\n"
        f"• /start - эта информация\n"
        f"• /monopoly - меню игры\n"
        f"• /help - помощь\n\n"
        f"Выберите действие из меню ниже:"
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.get_start_keyboard()
    )

async def monopoly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /monopoly"""
    message = (
        "🎮 *Главное меню Монополии*\n\n"
        "Здесь вы можете начать новую игру, посмотреть правила "
        "или узнать больше о боте.\n\n"
        "Выберите действие из меню ниже:"
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=Keyboards.get_monopoly_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /help"""
    message = (
        "❓ *Помощь по Monopoly Bot*\n\n"
        "*Основные команды:*\n"
        "• /start - информация о боте\n"
        "• /monopoly - главное меню игры\n"
        "• /help - эта справка\n\n"
        "*Как играть:*\n"
        "1. Используйте /monopoly для доступа к меню\n"
        "2. Создайте лобби или присоединитесь к существующему\n"
        "3. Начните игру когда будет 2+ игрока\n"
        "4. Используйте игровое меню для действий\n\n"
        "*Особенности:*\n"
        "• 🎭 Можно скрыть/показать меню\n"
        "• 👑 Разработчик: qulms - Темный принц\n"
        "• 🛡️ Работает в режиме белого списка\n\n"
        "Проблемы? Напишите разработчику."
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    if data == "add_to_group":
        message = (
            "🤖 *Как добавить бота в группу:*\n\n"
            "1. Создайте или откройте группу в Telegram\n"
            "2. Добавьте @monopoly_game_bot как участника\n"
            "3. Дайте боту права администратора (рекомендуется)\n"
            "4. Напишите /start в группе\n\n"
            "⚠️ *Важно:* Бот работает только в разрешенных чатах.\n"
            "Для добавления вашего чата в белый список обратитесь к разработчику."
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "developer_info":
        message = (
            f"👑 *Информация о разработчике:*\n\n"
            f"{Config.DEVELOPER_INFO}\n\n"
            f"*Контакт:* @qulms\n"
            f"*Проект:* Monopoly Bot\n"
            f"*Для:* Shit Daily\n"
            f"*Статус:* Активная разработка\n\n"
            f"🛠️ *Техническая информация:*\n"
            f"• Python + python-telegram-bot\n"
            f"• Render.com для хостинга\n"
            f"• Веб-хуки для работы\n"
            f"• Белый список чатов"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "rules":
        message = (
            "📜 *Правила игры в Монополию:*\n\n"
            "*Основные правила:*\n"
            "1. Игроки ходят по очереди, бросая кубики\n"
            "2. Приземлившись на клетку, можно купить собственность\n"
            "3. Собственность приносит доход когда другие игроки на ней оказываются\n"
            "4. Можно строить дома и отели для увеличения дохода\n"
            "5. Цель - остаться единственным не обанкротившимся игроком\n\n"
            "*Особенности этой версии:*\n"
            "• Максимум 4 игрока в лобби\n"
            "• Стартовый капитал: 1500\n"
            "• Автоматическая торговля\n"
            "• Лидерборд и статистика\n\n"
            "🎮 Полные правила и гайд будут добавлены в следующих обновлениях!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "whitelist_guide":
        message = (
            "📝 *Гайд по White List (Белому списку):*\n\n"
            "*Что это?*\n"
            "Белый список - список чатов, которым разрешено использовать бота.\n\n"
            "*Зачем это нужно?*\n"
            "• Контроль качества игры\n"
            "• Предотвращение спама\n"
            "• Тестирование новых функций\n"
            "• Обеспечение стабильной работы\n\n"
            "*Как попасть в белый список?*\n"
            "1. Напишите разработчику @qulms\n"
            "2. Укажите ID вашего чата\n"
            "3. Расскажите о целях использования\n"
            "4. Дождитесь подтверждения\n\n"
            "*Текущий статус:* Режим тестирования, скоро откроется для всех!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "play_game":
        message = (
            "🎮 *Начать игру:*\n\n"
            "Используйте команду /monopoly для доступа к полному меню игры.\n"
            "Там вы сможете:\n"
            "• Создать лобби\n"
            "• Присоединиться к игре\n"
            "• Посмотреть правила\n"
            "• Увидеть лидерборд\n\n"
            "🚀 *Совет:* Соберите 2-4 друзей для лучшего игрового опыта!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "leaderboard":
        message = (
            "📊 *Лидерборд:*\n\n"
            "*Топ игроков (тестовый режим):*\n"
            "1. 👑 Темный принц - 10,000 очков\n"
            "2. 🥈 Тестер 1 - 8,500 очков\n"
            "3. 🥉 Тестер 2 - 7,200 очков\n"
            "4. 💎 Тестер 3 - 6,100 очков\n"
            "5. ⭐ Тестер 4 - 5,400 очков\n\n"
            "*Как попасть в таблицу?*\n"
            "1. Играйте в Монополию через бота\n"
            "2. Выигрывайте игры\n"
            "3. Зарабатывайте очки\n"
            "4. Поднимайтесь в рейтинге!\n\n"
            "🎯 Полная система рейтинга скоро будет запущена!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "start_lobby":
        message = (
            "🎮 *Создание лобби:*\n\n"
            "Функция создания лобби в активной разработке!\n\n"
            "*Что будет доступно:*\n"
            "• Создание приватных/публичных лобби\n"
            "• Ожидание игроков (2-4 человека)\n"
            "• Чат лобби с обсуждением\n"
            "• Настройка правил игры\n"
            "• Система голосований\n\n"
            "⏳ *Ожидайте в следующих обновлениях!*\n"
            "Следите за новостями у разработчика."
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif data == "bot_help":
        await help_command(update, context)
    
    elif data == "settings":
        message = (
            "⚙️ *Настройки бота:*\n\n"
            "*Текущие настройки:*\n"
            "• Язык: Русский 🇷🇺\n"
            "• Режим: Белый список 🛡️\n"
            "• Уведомления: Включены 🔔\n"
            "• Звуки: Выключены 🔇\n\n"
            "*Доступно для администраторов:*\n"
            "• Добавление в белый список\n"
            "• Просмотр статистики\n"
            "• Управление играми\n"
            "• Технические настройки\n\n"
            "🛠️ *Для изменения настроек обратитесь к разработчику.*"
        )
        await query.edit_message_text(message, parse_mode='Markdown')

# ========== ПРОСТОЙ HTTP СЕРВЕР ДЛЯ RENDER ==========
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    """Простой HTTP обработчик для Render"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_index_html()
            self.wfile.write(html_content.encode('utf-8'))
        
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "online",
                "bot_name": "Monopoly Telegram Bot",
                "version": "2.0.0",
                "developer": "qulms - Темный принц",
                "server_time": datetime.now().isoformat(),
                "message": Config.BOT_DOWN_MESSAGE if not Config.BOT_TOKEN else "Бот работает"
            }
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def get_index_html(self):
        """Генерация HTML страницы"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        return f'''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Monopoly Bot Status</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            max-width: 800px;
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            display: inline-block;
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            padding: 12px 30px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.2rem;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        .info {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: left;
        }}
        .info h3 {{
            color: #4ecdc4;
            margin-top: 0;
        }}
        .dev {{
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 107, 107, 0.1));
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            border: 1px solid rgba(255, 215, 0, 0.2);
        }}
        .dev-name {{
            font-size: 1.8rem;
            color: #ffd700;
            margin-bottom: 10px;
        }}
        .commands {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }}
        .command {{
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .code {{
            font-family: 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 5px 10px;
            border-radius: 5px;
            color: #fca5a5;
            display: block;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Monopoly Telegram Bot</h1>
        <div class="status">
            <span id="statusText">✅ Бот работает</span>
        </div>
        
        <div class="info">
            <h3>📊 Статус системы</h3>
            <p><strong>Время сервера:</strong> <span id="time">{current_time}</span></p>
            <p><strong>Версия бота:</strong> 2.0.0</p>
            <p><strong>Режим работы:</strong> Веб-хуки</p>
            <p><strong>Статус токена:</strong> {"✅ Установлен" if Config.BOT_TOKEN else "❌ Отсутствует"}</p>
        </div>
        
        <div class="commands">
            <div class="command">
                <h3>🤖 Команды бота</h3>
                <span class="code">/start</span>
                <span>Запуск и информация</span>
            </div>
            <div class="command">
                <h3>🎮 Игровое меню</h3>
                <span class="code">/monopoly</span>
                <span>Главное меню игры</span>
            </div>
            <div class="command">
                <h3>❓ Помощь</h3>
                <span class="code">/help</span>
                <span>Справка по командам</span>
            </div>
        </div>
        
        <div class="info">
            <h3>🛡️ Особенности</h3>
            <p>• Работает в режиме белого списка</p>
            <p>• Поддержка лобби для 2-4 игроков</p>
            <p>• Лидерборд и статистика</p>
            <p>• Скрываемое игровое меню</p>
            <p>• Разнообразные ответы (ИИ-стиль)</p>
        </div>
        
        <div class="dev">
            <div class="dev-name">👑 qulms - Темный принц</div>
            <div>Разработчик Monopoly Bot (only for Shit Daily)</div>
            <div style="margin-top: 15px; font-size: 0.9em; color: #cbd5e0;">
                {Config.BOT_DOWN_MESSAGE}
            </div>
        </div>
        
        <div style="margin-top: 30px; color: #a0aec0; font-size: 0.9rem;">
            <p>🔄 Страница обновляется автоматически</p>
            <p>📡 API статуса: <a href="/api/status" style="color: #4ecdc4;">/api/status</a></p>
        </div>
    </div>
    
    <script>
        // Обновление времени
        function updateTime() {{
            const now = new Date();
            const timeString = now.toLocaleTimeString('ru-RU');
            document.getElementById('time').textContent = timeString;
        }}
        
        // Проверка статуса
        async function checkStatus() {{
            try {{
                const response = await fetch('/api/status');
                const data = await response.json();
                if (data.status === 'online') {{
                    document.getElementById('statusText').textContent = '✅ Бот работает';
                }}
            }} catch (error) {{
                console.log('Ошибка проверки статуса:', error);
            }}
        }}
        
        // Инициализация
        updateTime();
        checkStatus();
        setInterval(updateTime, 1000);
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>
'''
    
    def log_message(self, format, *args):
        """Отключаем логирование запросов"""
        pass

def run_http_server():
    """Запуск HTTP сервера"""
    server_address = ('0.0.0.0', Config.PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    
    logger.info(f"🌐 HTTP сервер запущен на порту {Config.PORT}")
    logger.info(f"📡 Доступно по адресу: http://0.0.0.0:{Config.PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 HTTP сервер остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка HTTP сервера: {e}")

# ========== НАСТРОЙКА И ЗАПУСК ==========
def setup_handlers(app: Application):
    """Настройка обработчиков"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("monopoly", monopoly_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))

async def setup_webhook():
    """Настройка веб-хука"""
    if Config.WEBHOOK_URL and Config.BOT_TOKEN:
        webhook_url = f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}"
        
        try:
            await application.bot.set_webhook(
                url=webhook_url,
                max_connections=50,
                drop_pending_updates=True
            )
            logger.info(f"✅ Веб-хук установлен: {webhook_url[:50]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка установки веб-хука: {e}")
            return False
    else:
        logger.warning("⚠️ WEBHOOK_URL не установлен. Используется polling режим.")
        return True

async def main_async():
    """Асинхронная основная функция"""
    global application
    
    if not Config.BOT_TOKEN:
        logger.error("❌ Токен бота не найден! Установите переменную TOKEN")
        logger.error(f"📋 Текущий токен: {Config.BOT_TOKEN[:10]}...")
        sys.exit(1)
    
    # Создаем приложение
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    setup_handlers(application)
    
    # Настраиваем веб-хук
    await setup_webhook()
    
    # Инициализируем приложение
    await application.initialize()
    
    logger.info("✅ Бот успешно инициализирован!")
    logger.info(f"🔑 Токен: {Config.BOT_TOKEN[:10]}...{Config.BOT_TOKEN[-5:]}")
    logger.info(f"🌐 Порт HTTP: {Config.PORT}")
    
    # Запускаем HTTP сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    logger.info("🚀 Бот готов к работе!")
    logger.info("📱 Напишите /start в Telegram чтобы начать")
    
    # Держим бота активным
    try:
        # Для polling режима
        if not Config.WEBHOOK_URL:
            await application.start()
            await application.updater.start_polling()
            logger.info("🔄 Запущен polling режим")
        
        # Бесконечный цикл
        while True:
            import asyncio
            await asyncio.sleep(3600)
            
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота...")
        await application.stop()
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Точка входа"""
    try:
        import asyncio
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.error(f"🔥 Фатальная ошибка при запуске: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
