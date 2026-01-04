"""
🎮 Monopoly Bot - Исправленная версия
Удаляет старый веб-хук перед настройкой
"""
import os
import logging
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TOKEN', '7957782509:AAFQ7zEe1xoKxNvjZGVMvOCdmrJTijpHGrQ')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://monopoly-bot-stnn.onrender.com').rstrip('/')

# Flask приложение
app = Flask(__name__)

# Создаем приложение Telegram
application = Application.builder().token(TOKEN).build()

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🎮 Привет {user.first_name}!\n"
        f"Я Monopoly Bot на Render!\n\n"
        f"👑 Разработчик: qulms - Темный принц\n"
        f"✅ Веб-хук: Работает\n"
        f"🌐 URL: {WEBHOOK_URL}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /help"""
    await update.message.reply_text(
        "🤖 *Monopoly Bot Help*\n\n"
        "Команды:\n"
        "• /start - Начало работы\n"
        "• /help - Эта справка\n"
        "• /status - Статус бота\n\n"
        "👑 Разработчик: @qulms\n"
        "💬 Вопросы: @qulms",
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /status"""
    await update.message.reply_text(
        f"📊 *Статус бота:*\n\n"
        f"• Веб-хук: ✅ Работает\n"
        f"• URL: {WEBHOOK_URL}\n"
        f"• Разработчик: qulms - Темный принц\n"
        f"• Режим: Веб-хук на Render",
        parse_mode='Markdown'
    )

# Регистрируем команды
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("status", status))

# ========== FLASK ENDPOINTS ==========
@app.route('/')
def home():
    """Главная страница"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎮 Monopoly Bot</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: white; 
                text-align: center; 
                padding: 50px;
                margin: 0;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                max-width: 800px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            }
            h1 { 
                color: #4ecdc4; 
                font-size: 2.8rem;
                margin-bottom: 10px;
            }
            .status { 
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: white; 
                padding: 12px 30px; 
                border-radius: 50px; 
                font-weight: bold;
                font-size: 1.2rem;
                margin: 20px auto;
                display: inline-block;
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
            <div class="status">✅ Бот работает через веб-хук</div>
            
            <div class="info">
                <h3>📊 Информация о боте</h3>
                <p><strong>Статус:</strong> Онлайн и работает</p>
                <p><strong>Веб-хук URL:</strong> ''' + WEBHOOK_URL + '''</p>
                <p><strong>Токен:</strong> Установлен и работает</p>
                <p><strong>Режим:</strong> Веб-хук на Render</p>
            </div>
            
            <div class="info">
                <h3>🤖 Команды бота</h3>
                <p><code>/start</code> - Начало работы</p>
                <p><code>/help</code> - Помощь по командам</p>
                <p><code>/status</code> - Статус бота</p>
            </div>
            
            <div class="dev">
                <div class="dev-name">👑 qulms - Темный принц</div>
                <div>Разработчик Monopoly Bot (only for Shit Daily)</div>
                <div style="margin-top: 15px; font-size: 0.9em; color: #cbd5e0;">
                    Бот работает в режиме веб-хука на Render
                </div>
            </div>
            
            <div style="margin-top: 30px; color: #a0aec0; font-size: 0.9rem;">
                <p>🔄 Страница обновляется автоматически</p>
                <p>📡 API статуса: <a href="/api/status" style="color: #4ecdc4;">/api/status</a></p>
            </div>
        </div>
        
        <script>
            // Автообновление времени
            function updateTime() {
                const now = new Date();
                const timeString = now.toLocaleTimeString('ru-RU');
                document.querySelector('.info p:nth-child(1)').innerHTML = 
                    `<strong>Статус:</strong> Онлайн (${timeString})`;
            }
            
            updateTime();
            setInterval(updateTime, 1000);
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """Health check для Render"""
    return 'OK', 200

@app.route('/api/status')
def api_status():
    """API для проверки статуса"""
    return {
        "status": "online",
        "bot_name": "Monopoly Bot",
        "webhook_url": WEBHOOK_URL,
        "mode": "webhook",
        "developer": "qulms - Темный принц"
    }

@app.route(f'/{TOKEN}', methods=['POST'])
async def telegram_webhook():
    """Endpoint для веб-хука от Telegram"""
    if request.is_json:
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        logger.info(f"✅ Веб-хук обработан")
    return Response(status=200)

# ========== НАСТРОЙКА ВЕБ-ХУКА ==========
async def setup_webhook():
    """Настройка веб-хука с удалением старого"""
    try:
        # 1. Сначала удаляем старый веб-хук
        logger.info("🗑️ Удаляю старый веб-хук...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Старый веб-хук удален")
        
        # 2. Устанавливаем новый веб-хук
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        logger.info(f"🔧 Устанавливаю новый веб-хук: {webhook_url}")
        
        await application.bot.set_webhook(
            url=webhook_url,
            max_connections=50,
            drop_pending_updates=True
        )
        
        # 3. Проверяем установку
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"✅ Веб-хук установлен: {webhook_info.url}")
        logger.info(f"📊 Информация: {webhook_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки веб-хука: {e}")
        return False

# ========== ЗАПУСК ==========
def main():
    """Запуск приложения"""
    import asyncio
    
    # Проверяем конфигурацию
    if not TOKEN:
        logger.error("❌ Токен бота не найден!")
        return
    
    if not WEBHOOK_URL:
        logger.error("❌ WEBHOOK_URL не установлен!")
        return
    
    # Инициализируем приложение
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Настраиваем веб-хук
    success = loop.run_until_complete(setup_webhook())
    
    if not success:
        logger.error("🚫 Не удалось настроить веб-хук. Бот не запущен.")
        return
    
    # Запускаем приложение
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    
    logger.info("🚀 Бот успешно запущен через веб-хук!")
    logger.info(f"🌐 Веб-страница: {WEBHOOK_URL}")
    logger.info(f"📱 Напишите /start в Telegram")
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)), debug=False, threaded=True)

if __name__ == '__main__':
    main()
