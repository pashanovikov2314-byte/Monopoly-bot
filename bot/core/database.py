"""
Модуль для работы с базой данных MongoDB
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с MongoDB"""
    
    def __init__(self):
        self.uri = os.getenv('MONGODB_URI')
        if not self.uri:
            raise ValueError("MONGODB_URI не установлен в переменных окружения")
        
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Подключение к MongoDB"""
        try:
            self.client = MongoClient(self.uri)
            # Проверяем подключение
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            logger.info("✅ Успешное подключение к MongoDB")
        except ConnectionFailure as e:
            logger.error(f"❌ Ошибка подключения к MongoDB: {e}")
            raise
    
    def get_collection(self, name):
        """Получение коллекции"""
        if not self.db:
            self.connect()
        return self.db[name]
    
    def close(self):
        """Закрытие подключения"""
        if self.client:
            self.client.close()
            logger.info("🔌 Подключение к MongoDB закрыто")

# Глобальный экземпляр базы данных
db_instance = None

def get_database():
    """Получение глобального экземпляра базы данных"""
    global db_instance
    if db_instance is None:
        db_instance = Database()
    return db_instance

def init_database():
    """Инициализация базы данных при старте приложения"""
    try:
        get_database()
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return False
