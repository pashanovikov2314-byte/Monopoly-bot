"""Веб-сервер для бота"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from aiohttp import web
import json
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)

class WebServer:
    """Веб-сервер для управления ботом и игрой"""

    def __init__(self):
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPsite] = None
        self.bot = None
        
        # Инициализируем static_path перед setup_routes
        self.static_path = Path("web/static")
        self.templates_path = Path("web/templates")
        
        self.setup_routes()

        # Статус сервера
        self.is_running = False
        self.start_time = None

        # Для управления играми через веб
        self.active_games: Dict[str, Dict] = {}

    def setup_routes(self):
        """Настройка маршрутов"""
        # Основные маршруты
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/status', self.handle_status)
        self.app.router.add_get('/health', self.handle_health)

        # Статические файлы (если папка существует)
        if self.static_path.exists():
            self.app.router.add_static('/static/', self.static_path)

    async def handle_index(self, request):
        """Главная страница"""
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Monopoly Bot</title></head>
        <body>
            <h1>🎮 Monopoly Premium Bot</h1>
            <p>Бот запущен и работает!</p>
            <p><a href="/status">Статус</a> | <a href="/health">Health Check</a></p>
        </body>
        </html>
        '''
        return web.Response(text=html, content_type='text/html')

    async def handle_status(self, request):
        """Страница статуса"""
        data = {
            "status": "running",
            "uptime": self.get_uptime(),
            "active_games": len(self.active_games),
            "server_time": datetime.now().isoformat()
        }
        return web.json_response(data)

    async def handle_health(self, request):
        """Health check для Render"""
        return web.Response(text="OK")

    async def start(self, bot):
        """Запуск веб-сервера"""
        self.bot = bot
        self.start_time = datetime.now()

        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Используем порт из переменной окружения Render
            import os
            port = int(os.environ.get('PORT', 8080))
            
            self.site = web.TCPsite(
                self.runner, 
                '0.0.0.0', 
                port
            )

            await self.site.start()

            self.is_running = True
            logger.info(f"Веб-сервер запущен на порту {port}")

        except Exception as e:
            logger.error(f"Ошибка запуска веб-сервера: {e}")
            # Не прерываем работу бота из-за ошибки веб-сервера

    async def stop(self):
        """Остановка веб-сервера"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        self.is_running = False
        logger.info("Веб-сервер остановлен")

    def get_uptime(self) -> str:
        """Получить время работы"""
        if not self.start_time:
            return "0 секунд"

        delta = datetime.now() - self.start_time
        seconds = delta.total_seconds()

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if days > 0:
            parts.append(f"{days} д")
        if hours > 0:
            parts.append(f"{hours} ч")
        if minutes > 0:
            parts.append(f"{minutes} м")
        if secs > 0 or not parts:
            parts.append(f"{secs} с")

        return " ".join(parts)

# Создаем экземпляр
web_server = WebServer()

async def start_web_server(bot):
    """Запустить веб-сервер"""
    await web_server.start(bot)
    return web_server
