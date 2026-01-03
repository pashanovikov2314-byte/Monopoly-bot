"""Веб-сервер для Render.com (обязательно!)"""

import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

# ===== МАРШРУТЫ =====
@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return jsonify({
        "status": "online",
        "service": "Monopoly Telegram Bot",
        "port": os.environ.get("PORT", 10000),
        "health": "ok"
    })

@app.route('/health')
def health():
    """Health check для Render"""
    return "OK", 200

@app.route('/ping')
def ping():
    """Проверка ping"""
    return "pong", 200

@app.route('/status')
def status():
    """Статус сервиса"""
    return jsonify({
        "bot": "running",
        "web": "online",
        "timestamp": os.times().system
    })

# ===== ЗАПУСК СЕРВЕРА =====
def run_web_server():
    """Запуск веб-сервера (КРИТИЧНО ДЛЯ RENDER!)"""
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 [WEB SERVER] Запуск на порту {port}")
    print(f"🌐 [WEB SERVER] Доступен по: http://0.0.0.0:{port}")
    
    # Важно: host='0.0.0.0' для Render!
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False
    )

def start_in_thread():
    """Запуск в отдельном потоке"""
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    run_web_server()
