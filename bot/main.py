"""
🎮 ПРОСТОЙ РАБОЧИЙ Monopoly Bot
Минимальная версия для запуска на Render
"""
import os
import sys
import logging
from datetime import datetime

from flask import Flask, request, Response, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    ApplicationBuilder
)

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
class Config:
    TOKEN = os.getenv('TOKEN', '7957782509:AAFQ7zEe1xoKxNvjZGVMvOCdmrJTijpHGrQ')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://monopoly-bot-stnn.onrender.com').rstrip('/')
    PORT = int(os.getenv('PORT', 10000))

# ========== FLASK ПРИЛОЖЕНИЕ ==========
app = Flask(__name__)

# ========== TELEGRAM ПРИЛОЖЕНИЕ ==========
application = None

# ========== HTML ШАБЛОН ==========
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Monopoly Bot</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            max-width: 800px;
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            display: inline-block;
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            padding: 12px 30px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.2rem;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .info {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: left;
        }
        .dev {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 107, 107, 0.1));
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            border: 1px solid rgba(255, 215, 0, 0.2);
        }
        .dev-name {
            font-size: 1.8rem;
            color: #ffd700;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Monopoly Telegram Bot</h1>
        <div class="status" id="status">✅ Бот работает</div>
        
        <div class="info">
            <h3>📊 Статус системы</h3>
            <p><strong>Токен бота:</strong> {{ '✅ Установлен' if token else '❌ Не установлен' }}</p>
            <p><strong>Веб-хук URL:</strong> {{ webhook_url or 'Не указан' }}</p>
            <p><strong>Порт:</strong> {{ port }}</p>
            <p><strong>Время сервера:</strong> <span id="time">{{ current_time }}</span></p>
        </div>
        
        <div class="info">
            <h3>🤖 Команды бота</h3>
            <p><code>/start</code> - Начало работы</p>
            <p><code>/help</code> - Помощь</p>
            <p><code>/monopoly</code> - Игровое меню</p>
        </div>
        
        <div class="dev">
            <div class="dev-name">👑 qulms - Темный принц</div>
            <div>Разработчик Monopoly Bot (only for Shit Daily)</div>
        </div>
    </div>
    
    <script>
        // Обновление времени
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ru-RU');
            document.getElementById('time').textContent = timeString;
        }
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
'''

# ========== FLASK ROUTES ==========
@app.route('/')
def index():
    """Главная страница"""
    current_time = datetime.now().strftime('%H:%M:%S')
    return render_template_string(
        INDEX_HTML,
        token=bool(Config.TOKEN),
        webhook_url=Config.WEBHOOK_URL,
        port=Config.PORT,
        current_time=current_time
    )

@app.route('/health')
def health():
    """Health check для Render"""
    return 'OK', 200

@app.route('/api/status')
def api_status():
    """API статуса"""
    return {
        "status": "online",
        "bot_name": "Monopoly Bot",
        "webhook_url": Config.WEBHOOK_URL,
        "developer": "qulms - Темный принц",
        "server_time": datetime.now().isoformat()
    }

# ========== TELEGRAM HANDLERS ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("👑 Разработчик", callback_data="dev")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")],
        [InlineKeyboardButton("🎮 Начать игру", callback_data="play")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 Привет {user.first_name}!\n"
        f"Я Monopoly Bot на Render!\n\n"
        f"✅ Веб-хук работает\n"
        f"🌐 URL: {Config.WEBHOOK_URL}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /help"""
    await update.message.reply_text(
        "🤖 *Monopoly Bot Help*\n\n"
        "Доступные команды:\n"
        "• /start - Начало работы\n"
        "• /help - Эта справка\n"
        "• /monopoly - Игровое меню\n\n"
        "👑 Разработчик: qulms - Темный принц",
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "dev":
        await query.edit_message_text(
            "👑 *Разработчик:*\n\n"
            "qulms - Темный принц\n"
            "(only for Shit Daily)\n\n"
            "Telegram: @qulms",
            parse_mode='Markdown'
        )
    elif data == "rules":
        await query.edit_message_text(
            "📜 *Правила Монополии:*\n\n"
            "1. Бросай кубики\n"
            "2. Покупай свойства\n"
            "3. Собирай ренту\n"
            "4. Стань монополистом!",
            parse_mode='Markdown'
        )
    elif data == "play":
        await query.edit_message_text(
            "🎮 *Начать игру*\n\n"
            "Функция в разработке!\n"
            "Скоро можно будет играть.",
            parse_mode='Markdown'
        )

@app.route(f'/{Config.TOKEN}', methods=['POST'])
async def telegram_webhook():
    """Endpoint для веб-хука от Telegram"""
    if request.is_json and application:
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        logger.info("✅ Веб-хук обработан")
    return Response(status=200)

# ========== НАСТРОЙКА ВЕБ-ХУКА ==========
async def setup_webhook():
    """Настройка веб-хука"""
    try:
        global application
        
        if not Config.TOKEN:
            logger.error("❌ Токен бота не найден!")
            return False
        
        if not Config.WEBHOOK_URL:
            logger.warning("⚠️ WEBHOOK_URL не установлен")
            return False
        
        # Создаем приложение
        application = ApplicationBuilder().token(Config.TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("monopoly", start_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Удаляем старый веб-хук
        logger.info("🗑️ Удаляю старый веб-хук...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Старый веб-хук удален")
        
        # Устанавливаем новый веб-хук
        webhook_url = f"{Config.WEBHOOK_URL}/{Config.TOKEN}"
        logger.info(f"🔧 Устанавливаю веб-хук: {webhook_url}")
        
        await application.bot.set_webhook(
            url=webhook_url,
            max_connections=50,
            drop_pending_updates=True
        )
        
        logger.info("✅ Веб-хук установлен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки веб-хука: {e}")
        return False

# ========== ЗАПУСК ==========
def main():
    """Основная функция запуска"""
    import asyncio
    
    logger.info("🚀 Запуск Monopoly Bot...")
    logger.info(f"🔑 Токен: {'Есть' if Config.TOKEN else 'Нет'}")
    logger.info(f"🌐 WEBHOOK_URL: {Config.WEBHOOK_URL}")
    logger.info(f"🚪 PORT: {Config.PORT}")
    
    # Настраиваем веб-хук асинхронно
    success = asyncio.run(setup_webhook())
    
    if not success:
        logger.error("❌ Не удалось настроить веб-хук. Запускаю без него.")
    
    # Запускаем Flask
    logger.info(f"🌐 Запуск Flask на порту {Config.PORT}...")
    app.run(host='0.0.0.0', port=Config.PORT, debug=False, threaded=True)

if __name__ == '__main__':
    main()
