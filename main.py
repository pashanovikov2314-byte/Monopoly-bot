import os
import logging
from flask import Flask, request  # ДОБАВЛЕНО: Flask для веб-сервера на Render
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database as db
from game_logic import *

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv('TOKEN')

# ИСПРАВЛЕНИЕ: Получаем URL для веб-хука из переменных окружения
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8080))  # ДОБАВЛЕНО: PORT для Render

# ИСПРАВЛЕНИЕ: Создаем Flask приложение для обработки веб-хуков
app = Flask(__name__)

# Создание приложения Telegram
application = ApplicationBuilder().token(TOKEN).build()

# Регистрация обработчиков команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f'Привет {user.first_name}! Я бот для игры в Монополию. Используй /new_game чтобы начать новую игру.')

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Проверяем, есть ли уже активная игра
    active_game = db.get_active_game(chat_id)
    if active_game:
        await update.message.reply_text('В этом чате уже есть активная игра!')
        return
    
    # Создаем новую игру
    game_id = db.create_game(chat_id, user.id)
    await update.message.reply_text(f'Игра создана! ID: {game_id}\nИспользуй /join чтобы присоединиться.')

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Находим активную игру в чате
    game = db.get_active_game(chat_id)
    if not game:
        await update.message.reply_text('Нет активной игры в этом чате. Создайте новую с помощью /new_game')
        return
    
    # Проверяем, присоединился ли уже пользователь
    if db.is_player_in_game(game['_id'], user.id):
        await update.message.reply_text('Вы уже присоединились к игре!')
        return
    
    # Добавляем игрока в игру
    db.add_player_to_game(game['_id'], user.id, user.first_name)
    await update.message.reply_text(f'{user.first_name} присоединился к игре!')

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("new_game", new_game))
application.add_handler(CommandHandler("join", join_game))

# ИСПРАВЛЕНИЕ: Добавляем Flask роуты для обработки веб-хуков
@app.route('/')
def home():
    # Health check для Render
    return "✅ Bot is running!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    # Обработка входящих обновлений от Telegram
    json_str = request.get_data().decode('UTF-8')
    update = Update.de_json(json.loads(json_str), application.bot)
    application.process_update(update)
    return 'ok'

# ИСПРАВЛЕНИЕ: Функция запуска веб-сервера
def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

# ИСПРАВЛЕНИЕ: Асинхронная функция для настройки веб-хука
async def setup_webhook():
    webhook_url = f'{WEBHOOK_URL}/{TOKEN}'
    
    # Устанавливаем веб-хук
    await application.bot.set_webhook(webhook_url)
    logger.info(f'Webhook установлен на: {webhook_url}')
    
    # Запускаем Flask
    run_flask()

# ИСПРАВЛЕНИЕ: Основная функция запуска
async def main():
    if WEBHOOK_URL:
        # Режим веб-хука для production (Render)
        logger.info("Запуск в режиме веб-хука...")
        await setup_webhook()
    else:
        # Режим polling для локальной разработки
        logger.info("Запуск в режиме polling...")
        await application.run_polling()

# ИСПРАВЛЕНИЕ: Точка входа для Render
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
