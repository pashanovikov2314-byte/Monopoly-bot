"""
Middleware for message processing
"""

import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from core.security import request_logger, rate_limiter
from database import db

logger = logging.getLogger(__name__)

class UserUpdateMiddleware(BaseMiddleware):
    """Middleware для обновления информации о пользователе"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Обновляем информацию о пользователе в БД
        user = event.from_user
        if user:
            await db.add_or_update_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                language_code=user.language_code or "ru"
            )
        
        # Логируем запрос
        request_logger.log_request(
            user_id=user.id if user else 0,
            chat_id=event.chat.id,
            message_type="message",
            text=event.text or ""
        )
        
        return await handler(event, data)


class CallbackQueryMiddleware(BaseMiddleware):
    """Middleware для обработки callback запросов"""
    
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Логируем callback запрос
        user = event.from_user
        request_logger.log_request(
            user_id=user.id if user else 0,
            chat_id=event.message.chat.id if event.message else 0,
            message_type="callback",
            text=event.data or ""
        )
        
        return await handler(event, data)


class GameStateMiddleware(BaseMiddleware):
    """Middleware для проверки состояния игры"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chat_id = event.chat.id
        
        # Если это команда /start или /monopoly, пропускаем без проверки
        if event.text and event.text.startswith(('/', '🎲', '🏠', '💰', '🤝', '📊', '🗺️', '🏛️', '📈')):
            return await handler(event, data)
        
        # Проверяем, есть ли активная игра в этом чате
        game_data = await db.get_game_state(chat_id)
        if game_data:
            # Добавляем данные игры в context
            data['game_state'] = game_data
        
        return await handler(event, data)


class MaintenanceMiddleware(BaseMiddleware):
    """Middleware для режима обслуживания"""
    
    def __init__(self, maintenance_mode: bool = False):
        super().__init__()
        self.maintenance_mode = maintenance_mode
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if self.maintenance_mode:
            # Пропускаем только админов
            user_id = event.from_user.id
            if not await db.is_admin(user_id):
                await event.answer(
                    "⚠️ Бот находится в режиме обслуживания. "
                    "Попробуйте позже. 👑 Темный Принц уже исправляет это ♥️♥️"
                )
                return
        return await handler(event, data)


class TimingMiddleware(BaseMiddleware):
    """Middleware для замера времени обработки"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.time()
        
        try:
            result = await handler(event, data)
            return result
        finally:
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # в миллисекундах
            
            # Логируем медленные запросы
            if processing_time > 1000:  # больше 1 секунды
                logger.warning(
                    f"Медленный запрос от {event.from_user.id}: "
                    f"{processing_time:.0f}ms - {event.text}"
                )
            
            # Можно добавить в статистику
            data['processing_time'] = processing_time


# Функция для настройки всех middleware
def setup_middleware(dp, maintenance_mode: bool = False):
    """Настроить все middleware"""
    # User Update Middleware
    dp.message.middleware(UserUpdateMiddleware())
    dp.callback_query.middleware(CallbackQueryMiddleware())
    
    # Game State Middleware
    dp.message.middleware(GameStateMiddleware())
    
    # Maintenance Middleware
    dp.message.middleware(MaintenanceMiddleware(maintenance_mode))
    dp.callback_query.middleware(MaintenanceMiddleware(maintenance_mode))
    
    # Timing Middleware
    dp.message.middleware(TimingMiddleware())
    
    # Rate Limiter (уже добавлен в main.py)
    # dp.message.middleware(rate_limiter)
    
    logger.info("✅ Middleware настроены")
