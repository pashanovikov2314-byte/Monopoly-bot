"""
Manager for pinned messages in games
"""

import logging
from typing import Dict, Optional
from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)

class PinManager:
    """Менеджер закрепленных сообщений для игр"""
    
    def __init__(self):
        self.pinned_messages: Dict[int, int] = {}  # chat_id -> message_id
        self.game_messages: Dict[int, Dict] = {}   # chat_id -> game_data
        
    async def pin_game_message(self, bot: Bot, chat_id: int, 
                              message_text: str, game_data: Dict) -> Optional[int]:
        """Закрепить игровое сообщение"""
        try:
            # Отправляем сообщение
            message = await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode="HTML"
            )
            
            # Пытаемся закрепить
            try:
                await bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message.message_id,
                    disable_notification=True
                )
                
                # Сохраняем информацию
                self.pinned_messages[chat_id] = message.message_id
                self.game_messages[chat_id] = game_data
                
                logger.info(f"Сообщение закреплено в чате {chat_id}")
                return message.message_id
                
            except Exception as e:
                logger.warning(f"Не удалось закрепить сообщение в чате {chat_id}: {e}")
                # Бот должен быть админом для закрепления
                return None
                
        except Exception as e:
            logger.error(f"Ошибка отправки/закрепления сообщения: {e}")
            return None
    
    async def update_pinned_message(self, bot: Bot, chat_id: int, 
                                   new_text: str) -> bool:
        """Обновить закрепленное сообщение"""
        if chat_id not in self.pinned_messages:
            return False
        
        try:
            message_id = self.pinned_messages[chat_id]
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=new_text,
                parse_mode="HTML"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления закрепленного сообщения: {e}")
            return False
    
    async def unpin_game_message(self, bot: Bot, chat_id: int) -> bool:
        """Открепить игровое сообщение (пункт 1 - после автостарта через 3 минуты)"""
        if chat_id not in self.pinned_messages:
            return False
        
        try:
            await bot.unpin_chat_message(
                chat_id=chat_id,
                message_id=self.pinned_messages[chat_id]
            )
            
            # Удаляем из кэша
            del self.pinned_messages[chat_id]
            if chat_id in self.game_messages:
                del self.game_messages[chat_id]
            
            logger.info(f"Сообщение откреплено в чате {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка открепления сообщения: {e}")
            return False
    
    def get_pinned_message_info(self, chat_id: int) -> Optional[Dict]:
        """Получить информацию о закрепленном сообщении"""
        if chat_id in self.pinned_messages:
            return {
                "message_id": self.pinned_messages[chat_id],
                "game_data": self.game_messages.get(chat_id, {})
            }
        return None
    
    def cleanup_old_pins(self, chat_ids_to_remove: list):
        """Очистить старые закрепления"""
        for chat_id in chat_ids_to_remove:
            if chat_id in self.pinned_messages:
                del self.pinned_messages[chat_id]
            if chat_id in self.game_messages:
                del self.game_messages[chat_id]


# Синглтон экземпляр
pin_manager = PinManager()
