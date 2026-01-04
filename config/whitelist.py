#!/usr/bin/env python3
"""Система белого списка для Monopoly Bot"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Уровни доступа"""
    BANNED = 0
    USER = 1
    TRUSTED = 2
    ADMIN = 3
    DEVELOPER = 4

# ===== КОНФИГУРАЦИЯ РАЗРАБОТЧИКА =====
DEVELOPER_CONFIG = {
    "id": 000000000,  # ЗАМЕНИТЕ НА ВАШ TELEGRAM ID
    "username": "qulms",
    "display_name": "Темный принц (only for Shit Daily)",
    "contact": "@qulms",
    "special_message": "Бот не работает, или сломался - Темный принц уже исправляет!"
}

class WhitelistManager:
    """Менеджер белого списка"""
    
    def __init__(self):
        self.data_file = "config/whitelist_data.json"
        self.web_users_file = "config/web_users.json"
        self.active_chats_file = "config/active_chats.json"
        
        # Данные
        self.allowed_chats: Set[int] = set()
        self.web_panel_users: Dict[int, Dict] = {}
        self.active_chats: Dict[int, Dict] = {}
        self.chat_history: Dict[int, List] = {}
        
        self.load_data()
        self.ensure_developer_access()
    
    def load_data(self):
        """Загрузка данных"""
        # Загружаем белый список чатов
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.allowed_chats = set(data.get('allowed_chats', []))
                logger.info(f"✅ Загружено {len(self.allowed_chats)} чатов из белого списка")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки белого списка: {e}")
        
        # Загружаем пользователей веб-панели
        if os.path.exists(self.web_users_file):
            try:
                with open(self.web_users_file, 'r', encoding='utf-8') as f:
                    self.web_panel_users = json.load(f)
                logger.info(f"✅ Загружено {len(self.web_panel_users)} пользователей веб-панели")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки пользователей веб-панели: {e}")
        
        # Загружаем активные чаты
        if os.path.exists(self.active_chats_file):
            try:
                with open(self.active_chats_file, 'r', encoding='utf-8') as f:
                    self.active_chats = json.load(f)
                logger.info(f"✅ Загружено {len(self.active_chats)} активных чатов")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки активных чатов: {e}")
    
    def save_data(self):
        """Сохранение данных"""
        try:
            # Сохраняем белый список
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'allowed_chats': list(self.allowed_chats),
                    'last_updated': datetime.now().isoformat(),
                    'developer': DEVELOPER_CONFIG
                }, f, ensure_ascii=False, indent=2)
            
            # Сохраняем пользователей веб-панели
            with open(self.web_users_file, 'w', encoding='utf-8') as f:
                json.dump(self.web_panel_users, f, ensure_ascii=False, indent=2)
            
            # Сохраняем активные чаты
            with open(self.active_chats_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_chats, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Данные белого списка сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных: {e}")
    
    def ensure_developer_access(self):
        """Гарантируем доступ разработчика"""
        dev_id = DEVELOPER_CONFIG["id"]
        if dev_id not in self.web_panel_users:
            self.web_panel_users[dev_id] = {
                "username": DEVELOPER_CONFIG["username"],
                "access_level": AccessLevel.DEVELOPER.value,
                "permissions": ["full_access", "manage_chats", "view_logs", "manage_users"],
                "added_date": datetime.now().isoformat(),
                "last_login": None
            }
            self.save_data()
            logger.info("✅ Добавлен доступ разработчика")
    
    # ===== ОСНОВНЫЕ МЕТОДЫ =====
    
    def is_chat_allowed(self, chat_id: int) -> bool:
        """Проверка разрешен ли чат"""
        # Личные сообщения (ID > 0) всегда разрешены
        if chat_id > 0:
            return True
        
        # Для групп/супергрупп проверяем белый список
        return abs(chat_id) in self.allowed_chats
    
    def add_chat_to_whitelist(self, chat_id: int, chat_name: str, added_by: int) -> bool:
        """Добавление чата в белый список"""
        # Только разработчик может добавлять чаты
        if not self.is_developer(added_by):
            return False
        
        chat_id_abs = abs(chat_id)
        self.allowed_chats.add(chat_id_abs)
        self.save_data()
        
        logger.info(f"✅ Чат добавлен в белый список: {chat_name} ({chat_id})")
        return True
    
    def remove_chat_from_whitelist(self, chat_id: int, removed_by: int) -> bool:
        """Удаление чата из белого списка"""
        # Только разработчик может удалять чаты
        if not self.is_developer(removed_by):
            return False
        
        chat_id_abs = abs(chat_id)
        if chat_id_abs in self.allowed_chats:
            self.allowed_chats.remove(chat_id_abs)
            self.save_data()
            logger.info(f"✅ Чат удален из белого списка: {chat_id}")
            return True
        return False
    
    def is_web_user(self, user_id: int) -> bool:
        """Проверка доступа к веб-панели"""
        return user_id in self.web_panel_users
    
    def add_web_user(self, user_id: int, username: str, added_by: int, 
                    access_level: AccessLevel = AccessLevel.USER) -> bool:
        """Добавление пользователя веб-панели"""
        # Только разработчик и админы могут добавлять пользователей
        if not (self.is_developer(added_by) or self.is_admin(added_by)):
            return False
        
        self.web_panel_users[user_id] = {
            "username": username,
            "access_level": access_level.value,
            "permissions": self._get_permissions_for_level(access_level),
            "added_by": added_by,
            "added_date": datetime.now().isoformat(),
            "last_login": None
        }
        self.save_data()
        return True
    
    def is_developer(self, user_id: int) -> bool:
        """Проверка является ли разработчиком"""
        user = self.web_panel_users.get(user_id)
        return user and user.get('access_level') == AccessLevel.DEVELOPER.value
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли администратором"""
        user = self.web_panel_users.get(user_id)
        return user and user.get('access_level') >= AccessLevel.ADMIN.value
    
    def _get_permissions_for_level(self, level: AccessLevel) -> List[str]:
        """Получение прав для уровня доступа"""
        permissions = {
            AccessLevel.USER: ["view_status"],
            AccessLevel.TRUSTED: ["view_status", "view_logs"],
            AccessLevel.ADMIN: ["view_status", "view_logs", "manage_chats"],
            AccessLevel.DEVELOPER: ["full_access"]
        }
        return permissions.get(level, [])
    
    def track_chat_activity(self, chat_id: int, chat_name: str, user_id: int):
        """Отслеживание активности чата"""
        chat_id_abs = abs(chat_id)
        self.active_chats[chat_id_abs] = {
            "name": chat_name,
            "last_activity": datetime.now().isoformat(),
            "last_user": user_id,
            "message_count": self.active_chats.get(chat_id_abs, {}).get("message_count", 0) + 1
        }
        self.save_data()
    
    def get_whitelist_info(self) -> Dict:
        """Получение информации о белом списке"""
        return {
            "total_allowed_chats": len(self.allowed_chats),
            "total_web_users": len(self.web_panel_users),
            "active_chats_count": len(self.active_chats),
            "developer": DEVELOPER_CONFIG["display_name"],
            "last_updated": datetime.now().isoformat()
        }
    
    def get_chat_info_for_web(self, chat_id: int) -> Optional[Dict]:
        """Получение информации о чате для веб-панели"""
        chat_id_abs = abs(chat_id)
        if chat_id_abs in self.allowed_chats:
            return {
                "id": chat_id,
                "in_whitelist": True,
                "activity": self.active_chats.get(chat_id_abs, {})
            }
        return None

# Глобальный экземпляр
whitelist_manager = WhitelistManager()

def get_whitelist_manager() -> WhitelistManager:
    return whitelist_manager
