#!/usr/bin/env python3
"""Красивый веб-сервер мониторинга для Monopoly Bot"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from config.whitelist import get_whitelist_manager, DEVELOPER_CONFIG

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'monopoly-bot-secret-key-2024')
CORS(app)

# ===== СИСТЕМА МОНИТОРИНГА =====
class BotMonitor:
    """Мониторинг состояния бота"""
    
    def __init__(self):
        self.start_time = time.time()
        self.bot_status = "online"
        self.last_check = datetime.now()
        self.error_log = []
        self.performance_metrics = {
            "response_time": [],
            "memory_usage": [],
            "active_users": 0,
            "active_games": 0
        }
        self.system_messages = {
            "online": "✅ Бот работает нормально",
            "offline": "🚫 Бот отключен",
            "error": "⚠️ Временные проблемы",
            "maintenance": "🔧 Техническое обслуживание"
        }
    
    def update_status(self, status: str, message: str = None):
        """Обновление статуса бота"""
        self.bot_status = status
        self.last_check = datetime.now()
        
        if message:
            self.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "message": message
            })
            # Храним только последние 100 ошибок
            if len(self.error_log) > 100:
                self.error_log = self.error_log[-100:]
    
    def get_uptime(self) -> dict:
        """Получение времени работы"""
        uptime_seconds = int(time.time() - self.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": uptime_seconds
        }
    
    def get_status_info(self) -> dict:
        """Получение полной информации о статусе"""
        whitelist = get_whitelist_manager()
        whitelist_info = whitelist.get_whitelist_info()
        
        return {
            "status": self.bot_status,
            "status_message": self.system_messages.get(self.bot_status, "Неизвестный статус"),
            "last_check": self.last_check.isoformat(),
            "uptime": self.get_uptime(),
            "whitelist_stats": whitelist_info,
            "active_chats": len(whitelist.active_chats),
            "performance": self.performance_metrics,
            "developer": DEVELOPER_CONFIG,
            "timestamp": datetime.now().isoformat()
        }

# Глобальный экземпляр мониторинга
bot_monitor = BotMonitor()

# ===== ДЕКОРАТОРЫ ДОСТУПА =====
def require_web_auth(f):
    """Декоратор для проверки авторизации"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем сессию
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Проверяем белый список
        whitelist = get_whitelist_manager()
        user_id = session['user_id']
        
        if not whitelist.is_web_user(user_id):
            session.clear()
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

# ===== МАРШРУТЫ =====
@app.route('/')
def index():
    """Главная страница - редирект на логин"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            return render_template('login.html', 
                                 error="❌ ID должен быть числом!",
                                 developer=DEVELOPER_CONFIG)
        
        # Проверяем белый список
        whitelist = get_whitelist_manager()
        
        if whitelist.is_web_user(user_id_int):
            # Сохраняем в сессии
            session['user_id'] = user_id_int
            user_info = whitelist.web_panel_users.get(user_id_int, {})
            session['username'] = user_info.get('username', 'Пользователь')
            session['access_level'] = user_info.get('access_level', 1)
            
            # Обновляем последний вход
            if user_id_int in whitelist.web_panel_users:
                whitelist.web_panel_users[user_id_int]['last_login'] = datetime.now().isoformat()
                whitelist.save_data()
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html',
                                 error="🚫 Доступ запрещен! Ваш ID не в белом списке.",
                                 developer=DEVELOPER_CONFIG,
                                 special_message=DEVELOPER_CONFIG['special_message'])
    
    return render_template('login.html', developer=DEVELOPER_CONFIG)

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_web_auth
def dashboard():
    """Панель управления"""
    whitelist = get_whitelist_manager()
    status_info = bot_monitor.get_status_info()
    user_info = whitelist.web_panel_users.get(session['user_id'], {})
    
    return render_template('dashboard.html',
                         status=status_info,
                         user=user_info,
                         developer=DEVELOPER_CONFIG,
                         active_chats=whitelist.active_chats)

@app.route('/api/status')
@require_web_auth
def api_status():
    """API статуса бота"""
    status_info = bot_monitor.get_status_info()
    return jsonify(status_info)

@app.route('/api/chats')
@require_web_auth
def api_chats():
    """API списка чатов"""
    whitelist = get_whitelist_manager()
    chats_info = []
    
    for chat_id, chat_data in whitelist.active_chats.items():
        chats_info.append({
            "id": chat_id,
            "name": chat_data.get("name", "Неизвестный чат"),
            "last_activity": chat_data.get("last_activity"),
            "message_count": chat_data.get("message_count", 0),
            "in_whitelist": chat_id in whitelist.allowed_chats
        })
    
    return jsonify({
        "chats": sorted(chats_info, key=lambda x: x.get("last_activity", ""), reverse=True),
        "total": len(chats_info)
    })

@app.route('/api/errors')
@require_web_auth
def api_errors():
    """API ошибок"""
    return jsonify({
        "errors": bot_monitor.error_log[-20:],  # Последние 20 ошибок
        "total": len(bot_monitor.error_log)
    })

@app.route('/health')
def health():
    """Health check для Render"""
    return "OK", 200

@app.route('/status/public')
def public_status():
    """Публичный статус (без авторизации)"""
    status_info = bot_monitor.get_status_info()
    
    # Показываем только базовую информацию
    public_info = {
        "status": status_info["status"],
        "status_message": status_info["status_message"],
        "last_check": status_info["last_check"],
        "developer": DEVELOPER_CONFIG["display_name"],
        "special_message": DEVELOPER_CONFIG["special_message"]
    }
    
    return jsonify(public_info)

# ===== ЗАПУСК СЕРВЕРА =====
def run_web_server():
    """Запуск веб-сервера"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Запуск веб-сервера на порту {port}")
    logger.info(f"🌐 Панель мониторинга: http://0.0.0.0:{port}/login")
    
    # Обновляем статус
    bot_monitor.update_status("online", "Веб-сервер запущен")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

def start_in_thread():
    """Запуск в отдельном потоке"""
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()
    logger.info("✅ Веб-сервер запущен в отдельном потоке")
    return thread

if __name__ == '__main__':
    run_web_server()
