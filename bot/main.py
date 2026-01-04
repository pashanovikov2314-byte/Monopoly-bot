"""
🎮 Монополия Telegram Bot - Упрощенная версия
Сначала сделаем работающую версию, потом добавим фичи
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
    ContextTypes,
    ApplicationBuilder
)
from flask import Flask, render_template_string, request, jsonify, Response

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

# ========== ПРОСТОЙ WHITELIST МЕНЕДЖЕР ==========
class WhitelistManager:
    def __init__(self):
        self.data = {
            "allowed_chats": [],
            "admin_users": [Config.ADMIN_ID]
        }
        logger.info("✅ Простой белый список инициализирован")
    
    def is_chat_allowed(self, chat_id: int) -> bool:
        """Проверка, разрешен ли чат (все разрешены для теста)"""
        return True  # Пока разрешаем всем для тестирования

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
                InlineKeyboardButton("❓ Помощь по боту", callback_data="bot_help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user = update.effective_user
    
    message = (
        f"🎮 Привет, {user.first_name}!\n"
        f"Я бот для игры в Монополию.\n\n"
        f"👤 ID: {user.id}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=Keyboards.get_start_keyboard()
    )

async def monopoly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /monopoly"""
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
    
    if data == "add_to_group":
        await query.edit_message_text(
            "🤖 *Как добавить бота в группу:*\n\n"
            "1. Создайте группу в Telegram\n"
            "2. Добавьте этого бота как участника\n"
            "3. Готово! Бот будет работать в группе.\n\n"
            "⚠️ Внимание: бот работает в режиме тестирования.",
            parse_mode='Markdown'
        )
    
    elif data == "developer_info":
        await query.edit_message_text(
            f"👑 *Информация о разработчике:*\n\n{Config.DEVELOPER_INFO}",
            parse_mode='Markdown'
        )
    
    elif data == "rules":
        await query.edit_message_text(
            "📜 *Правила игры в Монополию:*\n\n"
            "1. Игроки ходят по очереди\n"
            "2. Покупайте собственность и стройте дома\n"
            "3. Собирайте ренту с других игроков\n"
            "4. Цель - остаться единственным не обанкротившимся\n\n"
            "🎮 Полные правила скоро будут добавлены!",
            parse_mode='Markdown'
        )
    
    elif data == "whitelist_guide":
        await query.edit_message_text(
            "📝 *Гайд по White List:*\n\n"
            "Сейчас бот работает в тестовом режиме.\n"
            "Белый список будет добавлен в следующих обновлениях.",
            parse_mode='Markdown'
        )
    
    elif data == "start_lobby":
        await query.edit_message_text(
            "🎮 *Создание лобби:*\n\n"
            "Функция лобби скоро будет добавлена!\n"
            "Следите за обновлениями.",
            parse_mode='Markdown'
        )
    
    elif data == "leaderboard":
        await query.edit_message_text(
            "📊 *Лидерборд:*\n\n"
            "Таблица лидеров в разработке.\n"
            "Скоро здесь появятся лучшие игроки!",
            parse_mode='Markdown'
        )
    
    elif data == "bot_help":
        await query.edit_message_text(
            "❓ *Помощь по боту:*\n\n"
            "🎮 *Основные команды:*\n"
            "• /start - Запуск бота\n"
            "• /monopoly - Меню игры\n\n"
            "⚙️ *Бот в стадии разработки:*\n"
            "• Все функции скоро будут добавлены\n"
            "• Следите за обновлениями\n"
            "• Сообщайте об ошибках разработчику",
            parse_mode='Markdown'
        )

# ========== ВЕБ-СЕРВЕР (ПРОСТОЙ) ==========
# Создаем простой HTML шаблон прямо в коде
SIMPLE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Monopoly Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #a0aec0;
            font-size: 1.2rem;
            margin-bottom: 20px;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            padding: 12px 30px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.1rem;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .info-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .info-card:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-5px);
        }
        
        .info-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .info-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: #e2e8f0;
        }
        
        .info-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #4ecdc4;
        }
        
        .developer {
            margin-top: 40px;
            padding: 30px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        .dev-name {
            font-size: 1.8rem;
            margin-bottom: 10px;
            color: #ffd700;
        }
        
        .dev-title {
            color: #cbd5e0;
            font-size: 1.1rem;
        }
        
        .commands {
            margin-top: 30px;
            text-align: left;
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 12px;
        }
        
        .commands h3 {
            margin-bottom: 15px;
            color: #4ecdc4;
        }
        
        .commands ul {
            list-style: none;
        }
        
        .commands li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
        }
        
        .commands li:last-child {
            border-bottom: none;
        }
        
        .code {
            font-family: 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            color: #fca5a5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Monopoly Bot</h1>
            <div class="subtitle">Телеграм бот для игры в Монополию</div>
            <div class="status-badge">
                <i class="fas fa-circle"></i>
                <span>Бот онлайн и работает</span>
            </div>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <div class="info-icon">🤖</div>
                <div class="info-title">Статус бота</div>
                <div class="info-value">Онлайн</div>
            </div>
            
            <div class="info-card">
                <div class="info-icon">🕐</div>
                <div class="info-title">Время сервера</div>
                <div class="info-value" id="serverTime">00:00:00</div>
            </div>
            
            <div class="info-card">
                <div class="info-icon">📊</div>
                <div class="info-title">Версия</div>
                <div class="info-value">2.0.0</div>
            </div>
            
            <div class="info-card">
                <div class="info-icon">⚡</div>
                <div class="info-title">Режим</div>
                <div class="info-value">Веб-хук</div>
            </div>
        </div>
        
        <div class="commands">
            <h3>📋 Доступные команды:</h3>
            <ul>
                <li><span class="code">/start</span> - Запуск бота и информация</li>
                <li><span class="code">/monopoly</span> - Главное меню игры</li>
                <li><span class="code">/help</span> - Помощь по командам</li>
            </ul>
        </div>
        
        <div class="developer">
            <div class="dev-name">👑 qulms - Темный принц</div>
            <div class="dev-title">Разработчик Monopoly Bot (only for Shit Daily)</div>
        </div>
        
        <div style="margin-top: 30px; color: #a0aec0; font-size: 0.9rem;">
            <p>📡 Статус API: <span id="apiStatus">Загрузка...</span></p>
            <p>🔄 Последнее обновление: <span id="lastUpdate">Сейчас</span></p>
        </div>
    </div>
    
    <script>
        // Обновление времени
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ru-RU');
            document.getElementById('serverTime').textContent = timeString;
            
            const updateElement = document.getElementById('lastUpdate');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            updateElement.textContent = `${now.getHours()}:${minutes}`;
        }
        
        // Проверка API
        async function checkAPI() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('apiStatus').textContent = data.status === 'online' ? '✅ Работает' : '⚠️ Ошибка';
            } catch (error) {
                document.getElementById('apiStatus').textContent = '❌ Не доступен';
            }
        }
        
        // Инициализация
        updateTime();
        checkAPI();
        setInterval(updateTime, 1000);
        setInterval(checkAPI, 30000);
    </script>
</body>
</html>
'''

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница - простой HTML"""
    return render_template_string(SIMPLE_HTML)

@app.route('/api/status')
def api_status():
    """API статуса бота"""
    try:
        status = {
            "status": "online",
            "bot_name": "Monopoly Bot",
            "version": "2.0.0",
            "server_time": datetime.now().isoformat(),
            "developer": "qulms - Темный принц",
            "bot_token_set": bool(Config.BOT_TOKEN),
            "webhook_enabled": bool(Config.WEBHOOK_URL)
        }
        return jsonify(status)
    except Exception as e:
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

# ========== ИНИЦИАЛИЗАЦИЯ ==========
def setup_handlers(app: Application):
    """Настройка обработчиков"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("monopoly", monopoly_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CallbackQueryHandler(button_callback))

async def setup_webhook():
    """Настройка веб-хука"""
    if Config.WEBHOOK_URL:
        webhook_url = f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}"
        
        try:
            await application.bot.set_webhook(
                url=webhook_url,
                max_connections=50,
                drop_pending_updates=True
            )
            logger.info(f"✅ Веб-хук установлен: {webhook_url}")
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
        sys.exit(1)
    
    # Создаем приложение
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    setup_handlers(application)
    
    # Настраиваем веб-хук
    await setup_webhook()
    
    # Инициализируем приложение
    await application.initialize()
    
    logger.info("✅ Бот успешно запущен!")
    logger.info(f"🌐 Веб-панель доступна на порту: {Config.PORT}")
    logger.info(f"🤖 Токен бота: {'✅ Установлен' if Config.BOT_TOKEN else '❌ Не установлен'}")
    
    # Запускаем Flask в главном потоке
    # На Render Flask должен быть в основном потоке
    app.run(host='0.0.0.0', port=Config.PORT, debug=False)

def main():
    """Точка входа"""
    try:
        import asyncio
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
