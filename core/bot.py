from aiogram import Bot, Dispatcher

async def setup_bot():
    """Инициализация бота"""
    import os
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не установлен")
    
    bot = Bot(token=token)
    dp = Dispatcher()
    return bot, dp
