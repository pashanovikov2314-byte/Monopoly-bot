"""
Security module for DDoS protection and user authentication
"""

import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import logging
from collections import defaultdict

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from config import (
    MAX_REQUESTS_PER_MINUTE,
    MAX_MESSAGES_PER_SECOND,
    BAN_DURATION_MINUTES,
    ALLOWED_LAUNCH_USERS
)

logger = logging.getLogger(__name__)

class RateLimiter(BaseMiddleware):
    """Middleware для защиты от DDoS и ограничения запросов"""
    
    def __init__(self):
        super().__init__()
        # Хранилище запросов по пользователям
        self.user_requests: Dict[int, List[float]] = defaultdict(list)
        # Хранилище запросов по чатам
        self.chat_requests: Dict[int, List[float]] = defaultdict(list)
        # Бан-лист пользователей
        self.banned_users: Dict[int, datetime] = {}
        # Список подозрительных пользователей
        self.suspicious_users: Dict[int, Dict] = {}
        # Белый список (админы и доверенные пользователи)
        self.whitelist: Set[int] = set(ALLOWED_LAUNCH_USERS)
        
        # Настройки лимитов
        self.user_limit_per_minute = MAX_REQUESTS_PER_MINUTE
        self.user_limit_per_second = MAX_MESSAGES_PER_SECOND
        self.ban_duration = timedelta(minutes=BAN_DURATION_MINUTES)
        
        # Время последней очистки
        self.last_cleanup = time.time()
    
    async def __call__(self, handler, event: types.Message, data: dict):
        """Обработка входящего сообщения"""
        try:
            user_id = event.from_user.id
            chat_id = event.chat.id
            current_time = time.time()
            
            # Очистка старых записей каждую минуту
            if current_time - self.last_cleanup > 60:
                self._cleanup_old_requests(current_time)
                self.last_cleanup = current_time
            
            # Проверка на бан
            if user_id in self.banned_users:
                if datetime.now() < self.banned_users[user_id]:
                    # Пользователь забанен, игнорируем сообщение
                    logger.warning(f"Заблокированный пользователь {user_id} пытался отправить сообщение")
                    return
                else:
                    # Бан истек
                    del self.banned_users[user_id]
                    if user_id in self.suspicious_users:
                        del self.suspicious_users[user_id]
            
            # Проверяем белый список (админы не ограничены)
            if user_id in self.whitelist:
                return await handler(event, data)
            
            # Проверка лимита в секунду
            if not self._check_second_limit(user_id, current_time):
                await self._handle_rate_limit_exceeded(event, user_id, "second")
                return
            
            # Проверка лимита в минуту
            if not self._check_minute_limit(user_id, current_time):
                await self._handle_rate_limit_exceeded(event, user_id, "minute")
                return
            
            # Проверка подозрительной активности
            self._check_suspicious_activity(user_id, current_time)
            
            # Все проверки пройдены, пропускаем сообщение
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Ошибка в RateLimiter: {e}")
            return await handler(event, data)
    
    def _check_second_limit(self, user_id: int, current_time: float) -> bool:
        """Проверка лимита сообщений в секунду"""
        user_reqs = self.user_requests[user_id]
        
        # Удаляем запросы старше 1 секунды
        user_reqs[:] = [req_time for req_time in user_reqs 
                       if current_time - req_time < 1]
        
        # Проверяем количество запросов
        if len(user_reqs) >= self.user_limit_per_second:
            return False
        
        # Добавляем текущий запрос
        user_reqs.append(current_time)
        return True
    
    def _check_minute_limit(self, user_id: int, current_time: float) -> bool:
        """Проверка лимита сообщений в минуту"""
        user_reqs = self.user_requests[user_id]
        
        # Удаляем запросы старше 60 секунд
        user_reqs[:] = [req_time for req_time in user_reqs 
                       if current_time - req_time < 60]
        
        # Проверяем количество запросов
        if len(user_reqs) >= self.user_limit_per_minute:
            return False
        
        return True
    
    def _check_suspicious_activity(self, user_id: int, current_time: float):
        """Проверка на подозрительную активность"""
        if user_id not in self.suspicious_users:
            self.suspicious_users[user_id] = {
                'warning_count': 0,
                'first_warning': current_time,
                'last_warning': current_time
            }
        
        user_data = self.suspicious_users[user_id]
        
        # Проверяем частоту предупреждений
        if current_time - user_data['last_warning'] < 30:  # 30 секунд
            user_data['warning_count'] += 1
            user_data['last_warning'] = current_time
            
            # Если много предупреждений за короткое время - бан
            if user_data['warning_count'] >= 5:
                self._ban_user(user_id, "Слишком много нарушений за короткое время")
        else:
            # Сбрасываем счетчик если прошло больше 30 секунд
            user_data['warning_count'] = 1
            user_data['last_warning'] = current_time
    
    async def _handle_rate_limit_exceeded(self, event: types.Message, user_id: int, limit_type: str):
        """Обработка превышения лимита"""
        if limit_type == "second":
            warning_msg = "⚠️ Слишком много сообщений в секунду! Подождите 1 секунду."
            logger.warning(f"Пользователь {user_id} превысил лимит в секунду")
        else:
            warning_msg = "⚠️ Слишком много сообщений! Подождите немного."
            logger.warning(f"Пользователь {user_id} превысил лимит в минуту")
        
        # Отправляем предупреждение
        try:
            await event.answer(warning_msg)
        except:
            pass
        
        # Добавляем в список подозрительных
        self._check_suspicious_activity(user_id, time.time())
    
    def _ban_user(self, user_id: int, reason: str):
        """Забанить пользователя"""
        ban_until = datetime.now() + self.ban_duration
        self.banned_users[user_id] = ban_until
        
        # Логируем бан
        logger.warning(f"Пользователь {user_id} забанен до {ban_until}. Причина: {reason}")
        
        # Уведомляем в лог-канал если есть
        self._notify_admin_about_ban(user_id, reason, ban_until)
    
    def _notify_admin_about_ban(self, user_id: int, reason: str, ban_until: datetime):
        """Уведомить админа о бане"""
        # Можно добавить отправку уведомления в админский чат
        pass
    
    def _cleanup_old_requests(self, current_time: float):
        """Очистка старых записей"""
        # Очищаем записи старше 2 минут
        cutoff_time = current_time - 120
        
        for user_id in list(self.user_requests.keys()):
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > cutoff_time
            ]
            if not self.user_requests[user_id]:
                del self.user_requests[user_id]
        
        # Очищаем старые баны
        current_datetime = datetime.now()
        for user_id in list(self.banned_users.keys()):
            if current_datetime > self.banned_users[user_id]:
                del self.banned_users[user_id]
    
    def add_to_whitelist(self, user_id: int):
        """Добавить пользователя в белый список"""
        self.whitelist.add(user_id)
        logger.info(f"Пользователь {user_id} добавлен в белый список")
    
    def remove_from_whitelist(self, user_id: int):
        """Удалить пользователя из белого списка"""
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            logger.info(f"Пользователь {user_id} удален из белого списка")
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        current_time = time.time()
        user_reqs = self.user_requests.get(user_id, [])
        
        # Фильтруем запросы за последнюю минуту
        recent_reqs = [req for req in user_reqs if current_time - req < 60]
        
        return {
            'requests_last_minute': len(recent_reqs),
            'is_banned': user_id in self.banned_users,
            'ban_until': self.banned_users.get(user_id),
            'is_whitelisted': user_id in self.whitelist,
            'suspicious_warnings': self.suspicious_users.get(user_id, {}).get('warning_count', 0)
        }


class LaunchAuth:
    """Аутентификация для запуска бота через веб-ссылку"""
    
    def __init__(self, allowed_users: List[int] = None):
        self.allowed_users = set(allowed_users or [])
        self.tokens: Dict[str, Dict] = {}  # token -> {user_id, expires}
        self.token_secret = secrets.token_hex(32)
    
    def generate_token(self, user_id: int, valid_minutes: int = 5) -> str:
        """Сгенерировать токен для запуска"""
        if user_id not in self.allowed_users:
            raise PermissionError("User not allowed to launch bot")
        
        # Создаем уникальный токен
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}:{self.token_secret}"
        token = hashlib.sha256(data.encode()).hexdigest()[:16]
        
        # Сохраняем токен
        expires = datetime.now() + timedelta(minutes=valid_minutes)
        self.tokens[token] = {
            'user_id': user_id,
            'expires': expires,
            'created_at': datetime.now()
        }
        
        # Очищаем просроченные токены
        self._cleanup_expired_tokens()
        
        return token
    
    def verify_token(self, token: str, user_id: int = None) -> bool:
        """Проверить валидность токена"""
        # Очищаем просроченные токены
        self._cleanup_expired_tokens()
        
        if token not in self.tokens:
            return False
        
        token_data = self.tokens[token]
        
        # Проверяем срок действия
        if datetime.now() > token_data['expires']:
            del self.tokens[token]
            return False
        
        # Если указан user_id, проверяем соответствие
        if user_id is not None and token_data['user_id'] != user_id:
            return False
        
        return True
    
    def _cleanup_expired_tokens(self):
        """Очистить просроченные токены"""
        current_time = datetime.now()
        expired_tokens = [
            token for token, data in self.tokens.items()
            if current_time > data['expires']
        ]
        
        for token in expired_tokens:
            del self.tokens[token]
    
    def add_allowed_user(self, user_id: int):
        """Добавить пользователя в список разрешенных"""
        self.allowed_users.add(user_id)
    
    def remove_allowed_user(self, user_id: int):
        """Удалить пользователя из списка разрешенных"""
        if user_id in self.allowed_users:
            self.allowed_users.remove(user_id)
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Проверить, разрешен ли пользователь"""
        return user_id in self.allowed_users


class RequestLogger:
    """Логирование всех запросов для анализа"""
    
    def __init__(self, log_file: str = "logs/requests.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("request_logger")
        
        # Настройка файлового обработчика
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, user_id: int, chat_id: int, 
                   message_type: str, text: str = ""):
        """Записать запрос в лог"""
        # Ограничиваем длину текста
        if len(text) > 100:
            text = text[:97] + "..."
        
        # Маскируем конфиденциальные данные
        text = self._mask_sensitive_data(text)
        
        log_message = (
            f"USER:{user_id} | "
            f"CHAT:{chat_id} | "
            f"TYPE:{message_type} | "
            f"TEXT:{text}"
        )
        
        self.logger.info(log_message)
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Маскировка конфиденциальных данных"""
        # Маскируем токены (пример)
        if "token" in text.lower():
            return "[TOKEN_MASKED]"
        return text


# Синглтон экземпляры
rate_limiter = RateLimiter()
launch_auth = LaunchAuth(ALLOWED_LAUNCH_USERS)
request_logger = RequestLogger()

def setup_security():
    """Настройка системы безопасности"""
    logger.info("🔒 Система безопасности инициализирована")
    return rate_limiter
