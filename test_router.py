from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import logging

logger = logging.getLogger(__name__)

test_router = Router()

@test_router.message(Command('test'))
async def cmd_test(message: Message):
    """Тестовая команда"""
    await message.answer('✅ Тест пройден! Бот работает!')
    logger.info(f'Тест от пользователя {message.from_user.id}')

@test_router.message(F.text)
async def echo_test(message: Message):
    """Эхо-тест"""
    await message.answer(f'Вы написали: {message.text[:100]}')
    logger.info(f'Эхо от {message.from_user.id}: {message.text[:50]}')

def setup_test_handlers(dp):
    """Настройка тестовых обработчиков"""
    dp.include_router(test_router)
    logger.info('Тестовые обработчики зарегистрированы')
