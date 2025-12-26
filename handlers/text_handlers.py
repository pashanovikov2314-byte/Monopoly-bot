from aiogram import Router, F
from aiogram.types import Message
import logging
import re

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text)
async def handle_text(message: Message):
    """Обработка ЛЮБОГО текстового сообщения"""
    text = message.text.lower().strip()
    
    # Приветствия
    if any(word in text for word in ['привет', 'хай', 'здравствуй', 'hello', 'hi']):
        await message.answer('👋 Привет! Рад тебя видеть!')
    
    # Вопросы о боте
    elif any(word in text for word in ['кто ты', 'что ты', 'твое имя', 'твой создатель']):
        await message.answer('🤖 Я Monopoly Premium Bot!\n👑 Создан Темным Принцем (@Whylovely05)')
    
    # Монополия
    elif any(word in text for word in ['монополи', 'monopoly', 'игра', 'game']):
        await message.answer('🎮 Хотите сыграть в Monopoly? Используйте /game')
    
    # Помощь
    elif any(word in text for word in ['помощь', 'help', 'что делать', 'как играть']):
        await message.answer('📚 Используйте /help для списка команд')
    
    # Спасибо
    elif any(word in text for word in ['спасибо', 'thanks', 'thank you', 'благодарю']):
        await message.answer('🙏 Всегда рад помочь!')
    
    # Как дела
    elif any(word in text for word in ['как дела', 'как ты', 'how are you']):
        await message.answer('✨ Отлично! Готов играть в Monopoly!')
    
    # ID игры
    elif re.match(r'^\d+$', text) and len(text) > 3:
        await message.answer(f'🎯 Вы ввели ID игры: {text}\nИщу игру...')
    
    # Непонятное сообщение - предлагаем помощь
    else:
        await message.answer(
            '🤔 Я не совсем понимаю. Возможно:\n'
            '1. Вы хотите начать игру - /game\n'
            '2. Посмотреть профиль - /profile\n'
            '3. Получить помощь - /help\n'
            '4. Узнать статистику - /stats'
        )
    
    logger.info(f'Обработано текстовое сообщение от {message.from_user.id}: {text[:50]}')

def setup_text_handlers(dp, db, active_games):
    """Настройка текстовых обработчиков"""
    dp.include_router(router)
    logger.info('Текстовые обработчики зарегистрированы')
