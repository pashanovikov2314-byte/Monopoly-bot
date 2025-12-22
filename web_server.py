"""
Monopoly Premium Bot - Веб-сервер (Flask)
👑 Создано Темным Принцем (Dark Prince) 👑
Веб-панель управления, API, мониторинг
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys

# ==================== КОНФИГУРАЦИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Логотип Темного Принца
PRINCE_BANNER = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   🎮 MONOPOLY PREMIUM BOT v2.5                       ║
║                                                       ║
║   👑 Создано Темным Принцем (Dark Prince)            ║
║   ✨ Premium Edition - Исключительное качество        ║
║   🏆 Для истинных ценителей настольных игр            ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""

print(PRINCE_BANNER)

# Порт из переменных окружения
PORT = int(os.environ.get('PORT', 8080))

# ==================== FLASK ПРИЛОЖЕНИЕ ====================
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
# Общие переменные между Flask и ботом (в продакшене - Redis/БД)
WAITING_GAMES = {}
ACTIVE_GAMES = {}
game_history = []

# Статистика системы
STATS = {
    'status': 'online',
    'version': 'Premium v2.5 👑',
    'started_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'total_players': 0,
    'developer': '@Whylovely05',
    'prince_title': 'Темный Принц',
    'signature': 'Создано с ❤️ Темным Принцем',
    'maintenance_mode': False,
    'maintenance_msg': 'Бот обновляется, Темный принц уже исправляет это ♥️♥️'
}

# Игровое поле (полная версия из вашего начального кода)
BOARD = {
    1: ["Житная", 60, 4, "BROWN"],
    3: ["Нагатинская", 60, 4, "BROWN"],
    5: ["Рижская ж/д", 200, 25, "RAIL"],
    6: ["Варшавское ш.", 100, 6, "BLUE"],
    8: ["Огородный пр.", 100, 6, "BLUE"],
    9: ["Рижская", 120, 8, "BLUE"],
    11: ["Курская", 140, 10, "PINK"],
    12: ["Электросеть", 150, 10, "UTIL"],
    13: ["Абрамцево", 140, 10, "PINK"],
    14: ["Пантелеевская", 160, 12, "PINK"],
    15: ["Казанская ж/д", 200, 25, "RAIL"],
    16: ["Вавилова", 180, 14, "ORANGE"],
    18: ["Тимирязевская", 180, 14, "ORANGE"],
    19: ["Лихоборы", 200, 16, "ORANGE"],
    21: ["Арбат", 220, 18, "RED"],
    23: ["Полянка", 220, 18, "RED"],
    24: ["Сретенка", 240, 20, "RED"],
    25: ["Курская ж/д", 200, 25, "RAIL"],
    26: ["Ростовская", 260, 22, "YELLOW"],
    27: ["Рязанский пр.", 260, 22, "YELLOW"],
    28: ["Водопровод", 150, 10, "UTIL"],
    29: ["Новинский б-р", 280, 24, "YELLOW"],
    31: ["Пушкинская", 300, 26, "GREEN"],
    32: ["Тверская", 300, 26, "GREEN"],
    34: ["Маяковского", 320, 28, "GREEN"],
    35: ["Ленинградская ж/д", 200, 25, "RAIL"],
    37: ["Кутузовский", 350, 35, "DARKBLUE"],
    39: ["Бродвей", 400, 50, "DARKBLUE"]
}

# Специальные клетки
SPECIAL_CELLS = {
    0: ["СТАРТ", "Получите 200$ при прохождении"],
    2: ["КАЗНА", "Вытяните карту казны"],
    4: ["ПОДОХОДНЫЙ НАЛОГ", "Заплатите 200$"],
    7: ["ШАНС", "Вытяните карту шанса"],
    10: ["ТЮРЬМА", "Просто посещение"],
    17: ["КАЗНА", "Вытяните карту казны"],
    20: ["БЕСПЛАТНАЯ ПАРКОВКА", "Бесплатный отдых"],
    22: ["ШАНС", "Вытяните карту шанса"],
    30: ["ОТПРАВЛЯЙТЕСЬ В ТЮРЬМУ", "Прямо в тюрьму!"],
    33: ["КАЗНА", "Вытяните карту казны"],
    36: ["ШАНС", "Вытяните карту шанса"],
    38: ["СУПЕРНАЛОГ", "Заплатите 100$"]
}

# Карточки шанса и казны (из вашего кода)
CHANCE_CARDS = [
    "Пройдите на СТАРТ. Получите 200$",
    "Отправляйтесь на Бродвей. Если проходите СТАРТ, получите 200$",
    "Отправляйтесь на Варшавское шоссе",
    "Отправляйтесь на ближайшую железную дорогу. Заплатите владельцу вдвое",
    "Банк выплачивает вам дивиденды 50$",
    "Освобождение из тюрьмы. Карту можно продать",
    "Вернитесь на 3 клетки назад",
    "Отправляйтесь в тюрьму. Не проходите СТАРТ",
    "Ремонт улиц. За каждый дом заплатите 25$, за каждый отель 100$",
    "Вы выиграли конкурс красоты. Получите 20$",
    "Сбор на день рождения. Получите 10$ от каждого игрока",
    "Оплатите штраф за превышение скорости 15$",
    "Ваш займ одобрен. Получите 150$",
    "Оплатите больничный счет 100$",
    "Вы получили наследство 100$"
]

CHEST_CARDS = [
    "Ошибка банка в вашу пользу. Получите 200$",
    "Вторая премия за красоту. Получите 10$",
    "Оплата страхования жизни 100$",
    "Доход от акций 50$",
    "Вернитесь на СТАРТ",
    "Выгодная продажа акций. Получите 45$",
    "Оплата обучения 150$",
    "Сбор за咨询 25$",
    "Рождественский фонд выплачивает вам 100$",
    "Вы заняли второе место на конкурсе. Получите 10$",
    "Оплатите налог на недвижимость 40$",
    "Получите гонорар 25$",
    "Банковская ошибка. Заплатите 50$",
    "Освобождение из тюрьмы. Карту можно продать",
    "Оплата доктору 50$"
]

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def calculate_uptime():
    """Рассчитать время работы системы"""
    started = datetime.strptime(STATS['started_at'], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    diff = now - started
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    return f"{days} дней {hours} часов {minutes} минут"

def update_stats():
    """Обновить статистику"""
    STATS.update({
        'uptime': calculate_uptime(),
        'active_games': len(ACTIVE_GAMES),
        'waiting_games': len(WAITING_GAMES),
        'total_players': sum(len(g.get('players', [])) for g in list(ACTIVE_GAMES.values()) + list(WAITING_GAMES.values()))
    })

# ==================== HTML ШАБЛОН ====================
def create_html_template():
    """Создать HTML шаблон"""
    html_template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>МОНОПОЛИЯ ПРЕМИУМ - Статус</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: rgba(25, 25, 40, 0.9); border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); border: 1px solid #2a2a4a; }
        .header { text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid #00ff88; }
        .header h1 { font-size: 2.8rem; background: linear-gradient(90deg, #00ff88, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; }
        .header h2 { color: #a0a0ff; font-weight: 300; font-size: 1.2rem; }
        .prince-banner { 
            background: linear-gradient(90deg, #8B0000, #4B0082); 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            text-align: center;
            border: 2px solid #FFD700;
        }
        .prince-banner h3 { color: #FFD700; font-size: 1.4rem; margin-bottom: 5px; }
        .prince-banner p { color: #fff; font-size: 0.9rem; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .status-card { background: rgba(40, 40, 60, 0.7); border-radius: 15px; padding: 25px; border-left: 5px solid #00ff88; transition: transform 0.3s, box-shadow 0.3s; }
        .status-card:hover { transform: translateY(-5px); box-shadow: 0 5px 20px rgba(0, 255, 136, 0.2); }
        .card-title { color: #00ff88; font-size: 1.1rem; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        .info-line { display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        .label { color: #a0a0ff; font-weight: 500; }
        .value { color: #fff; font-weight: 600; }
        .value.online { color: #00ff88; }
        .value.offline { color: #ff4444; }
        .maintenance-warning { 
            background: linear-gradient(90deg, #ff4444, #ff8800); 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0;
            text-align: center;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .instructions { background: rgba(30, 30, 50, 0.8); border-radius: 15px; padding: 25px; margin-top: 30px; border: 1px solid #3a3a6a; }
        .instructions h3 { color: #00ccff; margin-bottom: 20px; font-size: 1.4rem; }
        .steps { list-style-type: none; counter-reset: step; }
        .steps li { margin: 15px 0; padding-left: 30px; position: relative; line-height: 1.6; }
        .steps li:before { content: counter(step); counter-increment: step; position: absolute; left: 0; top: 0; background: #00ff88; color: #000; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-weight: bold; }
        .log-button { display: inline-block; background: linear-gradient(90deg, #ff0088, #ff5500); color: white; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 15px; transition: all 0.3s; border: none; cursor: pointer; }
        .log-button:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(255, 0, 136, 0.3); }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); color: #888; font-size: 0.9rem; }
        .uptime { display: inline-block; background: rgba(0, 255, 136, 0.1); padding: 5px 15px; border-radius: 20px; margin-top: 10px; color: #00ff88; font-weight: 500; }
        @media (max-width: 768px) { .container { padding: 15px; } .header h1 { font-size: 2rem; } .status-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👑 МОНОПОЛИЯ ПРЕМИУМ</h1>
            <h2>Telegram Bot для игры в группах</h2>
        </div>
        
        {% if stats.maintenance_mode %}
        <div class="maintenance-warning">
            <h3>⚠️ Техническое обслуживание</h3>
            <p>{{ stats.maintenance_msg }}</p>
            <p>👑 Темный Принц уже исправляет это ♥️♥️</p>
        </div>
        {% endif %}
        
        <div class="prince-banner">
            <h3>👑 Версия Темного Принца</h3>
            <p>Premium Edition v2.5 • Создано с любовью для истинных ценителей</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="card-title">📊 Статус системы</div>
                <div class="info-line">
                    <span class="label">Бот:</span>
                    <span class="value {{ 'online' if not stats.maintenance_mode else 'offline' }}">
                        {{ '🟢 Онлайн' if not stats.maintenance_mode else '🔴 На обслуживании' }}
                    </span>
                </div>
                <div class="info-line"><span class="label">Активных игр:</span><span class="value">{{ stats.active_games }}</span></div>
                <div class="info-line"><span class="label">Ожидающих игр:</span><span class="value">{{ stats.waiting_games }}</span></div>
                <div class="info-line"><span class="label">Всего игроков:</span><span class="value">{{ stats.total_players }}</span></div>
                <div class="info-line"><span class="label">Версия:</span><span class="value">{{ stats.version }}</span></div>
            </div>
            
            <div class="status-card">
                <div class="card-title">⚙️ Стандарт</div>
                <div class="info-line"><span class="label">Запущен:</span><span class="value">{{ stats.started_at }}</span></div>
                <div class="info-line"><span class="label">Время работы:</span><span class="value">{{ stats.uptime }}</span></div>
                <div class="info-line"><span class="label">Порт:</span><span class="value">{{ port }}</span></div>
                <div class="info-line"><span class="label">Домен:</span><span class="value">{{ domain }}</span></div>
            </div>
            
            <div class="status-card">
                <div class="card-title">👥 Проектор</div>
                <div class="info-line"><span class="label">Разработчик:</span><span class="value">{{ stats.developer }}</span></div>
                <div class="info-line"><span class="label">Титул:</span><span class="value">{{ stats.prince_title }}</span></div>
                <div class="info-line"><span class="label">Подпись:</span><span class="value">{{ stats.signature }}</span></div>
            </div>
        </div>
        
        <div class="instructions">
            <h3>📋 Инструкция по использованию</h3>
            <ol class="steps">
                <li>Добавьте бота <strong>{{ bot_name }}</strong> в Telegram группу как администратора</li>
                <li>Напишите в группе команду <code>/monopoly</code></li>
                <li>Нажмите "Начать сбор игроков" и дождитесь участников</li>
                <li>Когда все готовы, создатель игры нажимает "Начать игру"</li>
                <li>Используйте кнопки "🎲 Бросить кубик" для хода</li>
                <li>Купите недвижимость, стройте дома и отели</li>
                <li>Торгуйтесь с другими игроками</li>
                <li>В любой момент можно скрыть меню командой <code>/hide</code></li>
            </ol>
            
            <button class="log-button" onclick="location.reload()">🔄 Обновить статус</button>
            <a href="/stats" class="log-button" style="margin-left: 10px;">📊 API Статистики</a>
            <a href="/health" class="log-button" style="margin-left: 10px;">❤️ Health Check</a>
            <a href="/games" class="log-button" style="margin-left: 10px;">🎮 Список игр</a>
        </div>
        
        <div class="footer">
            <p>{{ stats.signature }}</p>
            <div class="uptime">⏱ Uptime: {{ stats.uptime }}</div>
            <p style="margin-top: 15px;">🔧 При возникновении проблем используйте команду /hide для сброса меню</p>
            <p>👑 {{ stats.prince_title }} всегда на страже вашего комфорта</p>
        </div>
    </div>
    
    <script>
        // Автоматическое обновление каждые 30 секунд
        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.querySelectorAll('.status-card')[0].querySelectorAll('.value')[1].textContent = data.system.active_games;
                    document.querySelectorAll('.status-card')[0].querySelectorAll('.value')[2].textContent = data.system.waiting_games;
                    document.querySelectorAll('.status-card')[0].querySelectorAll('.value')[3].textContent = data.system.total_players;
                })
                .catch(err => console.log('Ошибка обновления:', err));
        }
        
        // Проверка здоровья
        setInterval(() => {
            fetch('/health').then(response => response.json()).then(data => {
                if (data.status === 'ok') {
                    console.log('✅ Bot is healthy at', new Date().toLocaleTimeString());
                }
            }).catch(err => console.log('Health check failed:', err));
        }, 30000);
        
        // Анимация при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.status-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'opacity 0.5s, transform 0.5s';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
            
            // Первое обновление
            setTimeout(updateStats, 1000);
            // Автообновление каждую минуту
            setInterval(updateStats, 60000);
        });
    </script>
</body>
</html>'''
    
    return html_template

# Создаем папку templates если её нет
os.makedirs('templates', exist_ok=True)

# Сохраняем HTML шаблон
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(create_html_template())

# ==================== API МАРШРУТЫ ====================
@app.route('/')
def index():
    """Главная страница статуса"""
    update_stats()
    
    # Получаем домен
    external_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if external_hostname:
        domain = f"https://{external_hostname}"
    else:
        domain = f"http://localhost:{PORT}"
    
    return render_template('index.html',
                         stats=STATS,
                         bot_name="Monopoly Premium",
                         domain=domain,
                         port=PORT)

@app.route('/health')
def health():
    """Проверка здоровья"""
    update_stats()
    return {
        "status": "ok" if not STATS['maintenance_mode'] else "maintenance",
        "bot": "running",
        "active_games": len(ACTIVE_GAMES),
        "waiting_games": len(WAITING_GAMES),
        "maintenance_mode": STATS['maintenance_mode'],
        "maintenance_message": STATS['maintenance_msg'] if STATS['maintenance_mode'] else None,
        "timestamp": datetime.now().isoformat(),
        "prince_version": STATS['version']
    }, 200

@app.route('/stats')
def stats():
    """Полная статистика"""
    update_stats()
    
    # Информация об активных играх
    active_games_info = {}
    for chat_id, game in ACTIVE_GAMES.items():
        active_games_info[str(chat_id)] = {
            "started": game.get("started_at", datetime.now().isoformat()),
            "players": len(game.get("players", [])),
            "current_player": game.get("current_player", 0),
            "creator": game.get("creator_name", "Unknown")
        }
    
    # Информация об ожидающих играх
    waiting_games_info = {}
    for chat_id, game in WAITING_GAMES.items():
        waiting_games_info[str(chat_id)] = {
            "created": game.get("created_at", datetime.now().isoformat()),
            "players": len(game.get("players", [])),
            "creator": game.get("creator_name", "Unknown")
        }
    
    return {
        "system": STATS,
        "games": {
            "active": active_games_info,
            "waiting": waiting_games_info,
            "total_active": len(ACTIVE_GAMES),
            "total_waiting": len(WAITING_GAMES)
        },
        "board": {
            "total_properties": len(BOARD),
            "special_cells": len(SPECIAL_CELLS),
            "chance_cards": len(CHANCE_CARDS),
            "chest_cards": len(CHEST_CARDS)
        }
    }

@app.route('/games')
def games():
    """Список всех игр"""
    return {
        "active_games": ACTIVE_GAMES,
        "waiting_games": WAITING_GAMES,
        "counts": {
            "active": len(ACTIVE_GAMES),
            "waiting": len(WAITING_GAMES)
        }
    }

@app.route('/board')
def get_board():
    """Информация об игровом поле"""
    return {
        "properties": BOARD,
        "special_cells": SPECIAL_CELLS,
        "chance_cards_count": len(CHANCE_CARDS),
        "chest_cards_count": len(CHEST_CARDS)
    }

@app.route('/maintenance', methods=['POST'])
def toggle_maintenance():
    """Включить/выключить режим обслуживания"""
    data = request.get_
