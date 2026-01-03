"""
🚀 РАБОЧИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER.COM
Минимальный, но обязательный для работы на Render
"""

from flask import Flask, jsonify, request
import os
import threading
import time

app = Flask(__name__)

# Глобальная переменная для проверки работы
server_started = False

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Monopoly Telegram Bot",
        "timestamp": time.time(),
        "port": os.environ.get("PORT", "unknown")
    })

@app.route('/health')
def health():
    """Для health checks от Render"""
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Для будущих Telegram вебхуков"""
    return jsonify({"status": "ready"}), 200

@app.route('/ping')
def ping():
    return "pong", 200

def run_server():
    """Запуск сервера на правильном порту"""
    global server_started
    try:
        port = int(os.environ.get("PORT", 10000))
        print(f"🚀 [WEB SERVER] Starting Flask on port {port}")
        print(f"🌐 [WEB SERVER] Access URL: http://0.0.0.0:{port}")
        server_started = True
        # КРИТИЧЕСКОЕ: host='0.0.0.0' обязательно для Render!
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ [WEB SERVER] Error: {e}")
        server_started = False

# Функция для проверки запуска
def is_running():
    return server_started

if __name__ == '__main__':
    run_server()
