"""
Веб-сервер для бота
"""
import os
from flask import Flask, render_template, jsonify

# Создаем Flask приложение
app = Flask(__name__)

# ИСПРАВЛЕНИЕ: Убираем CORS если не используется
# Если все же нужен CORS, раскомментируй строки ниже:
# from flask_cors import CORS
# CORS(app)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API endpoint для проверки статуса"""
    return jsonify({
        'status': 'online',
        'service': 'Monopoly Bot',
        'version': '1.0.0'
    })

def run_server(port=8080):
    """Запуск Flask сервера"""
    print(f"🚀 Запуск Flask сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
