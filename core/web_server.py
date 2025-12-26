"""
Web server for bot launch link and game map
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from aiohttp import web
import json
import secrets
from pathlib import Path

from config import (
    WEB_HOST, 
    WEB_PORT, 
    LAUNCH_SECRET,
    ALLOWED_LAUNCH_USERS,
    PORT
)
from core.security import launch_auth

logger = logging.getLogger(__name__)

class WebServer:
    """Web server for bot management and game features"""
    
    def __init__(self):
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.bot = None
        self.setup_routes()
        
        # Статус сервера
        self.is_running = False
        self.start_time = None
        
        # Для управления играми через веб
        self.active_games: Dict[str, Dict] = {}
        
        # Статические файлы
        self.static_path = Path("web/static")
        self.templates_path = Path("web/templates")
    
    def setup_routes(self):
        """Настройка маршрутов"""
        # Основные маршруты
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/status', self.handle_status)
        self.app.router.add_get('/launch', self.handle_launch)
        self.app.router.add_post('/launch', self.handle_launch_post)
        self.app.router.add_get('/map/{game_id}', self.handle_map)
        self.app.router.add_get('/game/{game_id}/status', self.handle_game_status)
        self.app.router.add_post('/game/{game_id}/action', self.handle_game_action)
        self.app.router.add_get('/admin', self.handle_admin)
        
        # Статические файлы
        if self.static_path.exists():
            self.app.router.add_static('/static/', self.static_path)
    
    async def start(self, bot):
        """Запуск веб-сервера"""
        self.bot = bot
        self.start_time = datetime.now()
        
        try:
            # Создаем runner и site
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner, 
                WEB_HOST, 
                WEB_PORT
            )
            
            await self.site.start()
            
            self.is_running = True
            logger.info(f"🌐 Web сервер запущен на http://{WEB_HOST}:{WEB_PORT}")
            
            # Запускаем фоновую задачу для обновления статуса
            asyncio.create_task(self.update_status_task())
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска web сервера: {e}")
            raise
    
    async def stop(self):
        """Остановка веб-сервера"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.cleanup()
        self.is_running = False
        logger.info("🌐 Web сервер остановлен")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        await self.runner.cleanup()
    
    async def update_status_task(self):
        """Фоновая задача для обновления статуса"""
        while self.is_running:
            await asyncio.sleep(60)  # Обновляем каждую минуту
            # Здесь можно обновлять статус игр и т.д.
    
    # ==================== HANDLERS ====================
    
    async def handle_index(self, request):
        """Главная страница"""
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Monopoly Premium Bot</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .status {
                    background: rgba(255, 255, 255, 0.2);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .btn {
                    display: inline-block;
                    background: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 5px;
                    transition: background 0.3s;
                }
                .btn:hover {
                    background: #45a049;
                }
                .btn-launch {
                    background: #ff6b6b;
                }
                .btn-launch:hover {
                    background: #ff5252;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Monopoly Premium Bot</h1>
                <div class="status">
                    <h2>📊 Статус системы</h2>
                    <p><strong>Время работы:</strong> {uptime}</p>
                    <p><strong>Активных игр:</strong> {active_games}</p>
                    <p><strong>Версия:</strong> 2.5 (Dark Prince Edition)</p>
                </div>
                <div>
                    <a href="/launch" class="btn btn-launch">🚀 Запуск бота</a>
                    <a href="/status" class="btn">📈 Детальный статус</a>
                    <a href="/admin" class="btn">⚙️ Админ панель</a>
                </div>
                <div style="margin-top: 30px; text-align: center;">
                    <p>👑 Создано Темным Принцем</p>
                    <p>Telegram: @Whylovely05</p>
                </div>
            </div>
        </body>
        </html>
        """.format(
            uptime=self.get_uptime(),
            active_games=len(self.active_games)
        )
        
        return web.Response(text=html, content_type='text/html')
    
    async def handle_status(self, request):
        """Страница статуса"""
        data = {
            "status": "running",
            "uptime": self.get_uptime(),
            "active_games": len(self.active_games),
            "server_time": datetime.now().isoformat(),
            "version": "2.5.0",
            "author": "Dark Prince (@Whylovely05)"
        }
        
        # Если запрос JSON
        if request.headers.get('Accept') == 'application/json':
            return web.json_response(data)
        
        # HTML версия
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Статус бота</title>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                .card {{ background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 10px; }}
                .online {{ color: green; }}
                .offline {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>📊 Статус Monopoly Premium Bot</h1>
            <div class="card">
                <h2 class="online">✅ Бот онлайн</h2>
                <p><strong>Время работы:</strong> {data['uptime']}</p>
                <p><strong>Активных игр:</strong> {data['active_games']}</p>
                <p><strong>Версия:</strong> {data['version']}</p>
                <p><strong>Автор:</strong> {data['author']}</p>
            </div>
            <a href="/">⬅️ Назад</a>
        </body>
        </html>
        """
        
        return web.Response(text=html, content_type='text/html')
    
    async def handle_launch(self, request):
        """Страница запуска бота"""
        # Проверяем наличие токена
        token = request.query.get('token')
        user_id = request.query.get('user_id')
        
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Запуск бота</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .container {
                    max-width: 500px;
                    margin: 50px auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                }
                input {
                    width: 100%;
                    padding: 10px;
                    border-radius: 5px;
                    border: none;
                    font-size: 16px;
                }
                button {
                    width: 100%;
                    padding: 12px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                }
                button:hover {
                    background: #45a049;
                }
                .error {
                    background: #ff6b6b;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .success {
                    background: #4CAF50;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Запуск Monopoly Premium Bot</h1>
        """
        
        # Если есть токен, проверяем его
        if token and user_id:
            try:
                user_id_int = int(user_id)
                if launch_auth.verify_token(token, user_id_int):
                    html += """
                    <div class="success">
                        ✅ Токен действителен! Бот запущен.
                    </div>
                    <p>Бот успешно запущен и готов к работе.</p>
                    <p><a href="https://t.me/MonopolyPremiumBot" style="color: white; text-decoration: underline;">
                        Перейти в бота
                    </a></p>
                    """
                else:
                    html += """
                    <div class="error">
                        ❌ Неверный или просроченный токен.
                    </div>
                    """
            except (ValueError, TypeError):
                html += """
                <div class="error">
                    ❌ Неверный формат данных.
                </div>
                """
        
        html += """
                <form method="POST" action="/launch">
                    <div class="form-group">
                        <label for="user_id">Ваш ID в Telegram:</label>
                        <input type="number" id="user_id" name="user_id" required>
                    </div>
                    <div class="form-group">
                        <label for="secret">Секретный код:</label>
                        <input type="password" id="secret" name="secret" required>
                    </div>
                    <button type="submit">🚀 Запустить бота</button>
                </form>
                <p style="margin-top: 20px; font-size: 14px;">
                    🔒 Только авторизованные пользователи могут запускать бота.
                </p>
            </div>
        </body>
        </html>
        """
        
        return web.Response(text=html, content_type='text/html')
    
    async def handle_launch_post(self, request):
        """Обработка POST запроса для запуска"""
        data = await request.post()
        user_id = data.get('user_id')
        secret = data.get('secret')
        
        try:
            user_id_int = int(user_id)
            
            # Проверяем секретный код
            if secret != LAUNCH_SECRET:
                return web.Response(
                    text="❌ Неверный секретный код!",
                    content_type='text/plain'
                )
            
            # Проверяем, разрешен ли пользователь
            if not launch_auth.is_user_allowed(user_id_int):
                return web.Response(
                    text="❌ У вас нет прав для запуска бота!",
                    content_type='text/plain'
                )
            
            # Генерируем токен
            token = launch_auth.generate_token(user_id_int)
            
            # Перенаправляем с токеном
            return web.HTTPFound(
                f"/launch?token={token}&user_id={user_id_int}"
            )
            
        except (ValueError, TypeError):
            return web.Response(
                text="❌ Неверный формат ID пользователя",
                content_type='text/plain'
            )
        except PermissionError as e:
            return web.Response(
                text=f"❌ {str(e)}",
                content_type='text/plain'
            )
    
    async def handle_map(self, request):
        """Интерактивная карта игры"""
        game_id = request.match_info.get('game_id')
        
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Карта игры Monopoly</title>
            <link rel="stylesheet" href="/static/css/map.css">
        </head>
        <body>
            <div class="map-container">
                <h1>🗺️ Карта игры #{game_id}</h1>
                <div id="monopoly-board">
                    <!-- Карта будет генерироваться JavaScript -->
                </div>
                <div id="player-info"></div>
                <div class="controls">
                    <button onclick="refreshMap()">🔄 Обновить</button>
                    <button onclick="zoomIn()">➕ Увеличить</button>
                    <button onclick="zoomOut()">➖ Уменьшить</button>
                </div>
            </div>
            <script src="/static/js/map.js"></script>
            <script>
                // Загружаем данные игры
                async function loadGameData() {
                    try {
                        const response = await fetch('/game/{game_id}/status');
                        const data = await response.json();
                        renderMap(data);
                    } catch (error) {
                        console.error('Ошибка загрузки данных:', error);
                    }
                }
                
                // Загружаем данные при старте
                loadGameData();
            </script>
        </body>
        </html>
        """.format(game_id=game_id)
        
        return web.Response(text=html, content_type='text/html')
    
    async def handle_game_status(self, request):
        """API статуса игры"""
        game_id = request.match_info.get('game_id')
        
        # Здесь будет получение данных игры из базы данных
        game_data = self.active_games.get(game_id, {
            "status": "not_found",
            "message": "Игра не найдена"
        })
        
        return web.json_response(game_data)
    
    async def handle_game_action(self, request):
        """API для игровых действий"""
        try:
            data = await request.json()
            game_id = request.match_info.get('game_id')
            action = data.get('action')
            
            # Обработка действий
            if action == 'roll_dice':
                # Симуляция броска кубиков
                dice1 = secrets.randbelow(6) + 1
                dice2 = secrets.randbelow(6) + 1
                
                response = {
                    "success": True,
                    "dice": [dice1, dice2],
                    "total": dice1 + dice2,
                    "is_double": dice1 == dice2
                }
            else:
                response = {
                    "success": False,
                    "error": "Неизвестное действие"
                }
            
            return web.json_response(response)
            
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "Неверный JSON"},
                status=400
            )
    
    async def handle_admin(self, request):
        """Админ панель"""
        # Проверяем доступ
        token = request.query.get('token')
        
        if token != LAUNCH_SECRET:
            return web.Response(
                text="❌ Доступ запрещен",
                content_type='text/plain'
            )
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Админ панель</title>
            <style>
                body { font-family: Arial; padding: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>⚙️ Админ панель</h1>
            <h2>Активные игры</h2>
            <table>
                <tr>
                    <th>ID игры</th>
                    <th>Статус</th>
                    <th>Игроков</th>
                    <th>Действия</th>
                </tr>
                <!-- Данные будут добавлены через JS -->
            </table>
            
            <h2>Система</h2>
            <div>
                <button onclick="restartBot()">🔄 Перезапустить бота</button>
                <button onclick="clearCache()">🗑️ Очистить кэш</button>
            </div>
            
            <script>
                async function loadGames() {
                    // Загрузка списка игр
                }
                
                function restartBot() {
                    if (confirm('Перезапустить бота?')) {
                        // Отправка команды перезапуска
                    }
                }
                
                function clearCache() {
                    if (confirm('Очистить кэш?')) {
                        // Очистка кэша
                    }
                }
            </script>
        </body>
        </html>
        """
        
        return web.Response(text=html, content_type='text/html')
    
    def get_uptime(self) -> str:
        """Получить время работы в читаемом формате"""
        if not self.start_time:
            return "0 секунд"
        
        delta = datetime.now() - self.start_time
        seconds = delta.total_seconds()
        
        # Форматируем время
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
    
    def register_game(self, game_id: str, game_data: Dict):
        """Зарегистрировать игру для веб-доступа"""
        self.active_games[game_id] = {
            **game_data,
            "registered_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    
    def unregister_game(self, game_id: str):
        """Удалить игру из веб-доступа"""
        if game_id in self.active_games:
            del self.active_games[game_id]


# Синглтон экземпляр
web_server = WebServer()

async def start_web_server(bot):
    """Запустить веб-сервер"""
    await web_server.start(bot)
    return web_server
