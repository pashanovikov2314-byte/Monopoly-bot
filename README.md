# 🎮 Monopoly Telegram Bot

Telegram бот для игры в Монополию с веб-интерфейсом.

## 📁 Структура проекта
\\\
monopoly-bot/
├── bot/                    # Код бота
│   ├── main.py            # Точка входа
│   ├── core/              # Ядро бота
│   └── handlers/          # Обработчики
├── web/                   # Веб-сервер
│   └── server.py          # Flask сервер
├── config/                # Конфигурация
├── Procfile              # Конфигурация Render
├── render.yaml           # Деплой-конфигурация
└── runtime.txt           # Версия Python
\\\

## 🚀 Быстрый старт
\\\ash
git clone https://github.com/pashanovikov2314-byte/Monopoly-bot.git
cd Monopoly-bot
cp config/.env.example .env
pip install -r config/requirements.txt
python bot/main.py
\\\

## 🌐 Развертывание на Render
1. Подключите GitHub репозиторий
2. Добавьте переменные окружения:
   - \BOT_TOKEN\ - токен от @BotFather
   - \PORT\ - 10000
3. Render автоматически развернет приложение

## 🔧 Технологии
- **Python 3.10**
- **python-telegram-bot 20.7**
- **Flask 2.3.3**
- **Render.com**
