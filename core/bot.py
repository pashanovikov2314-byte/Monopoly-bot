"""Модуль для настройки бота"""
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import os
import logging

logger = logging.getLogger(__name__)

async def setup_bot():
    """
    Инициализация бота и диспетчера
    
    Возвращает:
        tuple: (Bot, Dispatcher)
    """
    try:
        # Получаем токен бота из переменных окружения
        BOT_TOKEN = os.environ.get('BOT_TOKEN')
        if not BOT_TOKEN:
            raise ValueError('ОШИБКА: Переменная окружения BOT_TOKEN не установлена!')
        
        logger.info(f'Бот инициализируется с токеном: {BOT_TOKEN[:10]}...')
        
        # Создаем экземпляр бота
        bot = Bot(token=BOT_TOKEN)
        
        # Создаем диспетчер с хранилищем в памяти
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        logger.info('Бот и диспетчер успешно инициализированы')
        return bot, dp
        
    except Exception as e:
        logger.error(f'Не удалось настроить бота: {e}')
        raise

# Для тестирования
if __name__ == '__main__':
    import asyncio
    try:
        bot, dp = asyncio.run(setup_bot())
        print(f'Бот создан: {bot}')
        print(f'Диспетчер создан: {dp}')
    except Exception as e:
        print(f'Ошибка: {e}')
