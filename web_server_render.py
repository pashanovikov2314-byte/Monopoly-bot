"""
Минимальный веб-сервер для Render.com
Просто слушает порт и отвечает 200 OK
"""

from flask import Flask, jsonify
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Monopoly Telegram Bot",
        "health": "ok"
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    # Для будущих вебхуков Telegram
    return jsonify({"status": "webhook_received"}), 200

def run_web_server():
    """Запуск веб-сервера на порту из переменных окружения"""
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting web server on port {port}")
    # Важно: host='0.0.0.0' для Render
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_web_server()
