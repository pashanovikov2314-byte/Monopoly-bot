import sqlite3
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='data/monopoly.db'):
        self.db_path = db_path
        self.connection = None
        
    async def init_database(self):
        """Инициализация базы данных"""
        Path('data').mkdir(exist_ok=True)
        self.connection = await aiosqlite.connect(self.db_path)
        logger.info(f'База данных инициализирована: {self.db_path}')
        
    async def cleanup_old_games(self):
        """Очистка старых игр"""
        logger.info('Очистка старых игр...')
        
    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            await self.connection.close()
            logger.info('Соединение с базой данных закрыто')
