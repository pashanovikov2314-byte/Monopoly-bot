from aiogram import BaseMiddleware
import secrets
import time
from typing import Dict, Optional

class RateLimiter(BaseMiddleware):
    async def __call__(self, handler, event, data):
        return await handler(event, data)

class LaunchAuth:
    """Аутентификация для запуска бота через веб-интерфейс"""
    
    def __init__(self):
        self.tokens: Dict[str, dict] = {}
        self.token_lifetime = 3600  # 1 час
        
    def generate_token(self, user_id: int) -> str:
        """Генерация токена для пользователя"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            'user_id': user_id,
            'created_at': time.time()
        }
        return token
    
    def verify_token(self, token: str, user_id: int) -> bool:
        """Проверка токена"""
        if token not in self.tokens:
            return False
            
        token_data = self.tokens[token]
        
        # Проверяем пользователя
        if token_data['user_id'] != user_id:
            return False
            
        # Проверяем время жизни
        if time.time() - token_data['created_at'] > self.token_lifetime:
            del self.tokens[token]
            return False
            
        return True
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Проверка, разрешен ли пользователь"""
        # Здесь можно добавить проверку по списку разрешенных пользователей
        # Пока разрешаем всем
        return True
    
    def cleanup_expired_tokens(self):
        """Очистка просроченных токенов"""
        current_time = time.time()
        expired_tokens = [
            token for token, data in self.tokens.items()
            if current_time - data['created_at'] > self.token_lifetime
        ]
        for token in expired_tokens:
            del self.tokens[token]

# Создаем экземпляр для импорта
launch_auth = LaunchAuth()
