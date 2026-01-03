#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monopoly Bot - Основной файл с ВЕБ-СЕРВЕРОМ для Render"""

import asyncio
import logging
import sys
import os

# ===== RENDER PORT CONFIGURATION =====
PORT = int(os.environ.get("PORT", 10000))
print(f"🚀 RENDER PORT: {PORT}")
print(f"🌐 WEBHOOK URL: {os.environ.get('WEBHOOK_URL', 'Not set')}")

# ===== WEB SERVER IMPORTS =====
try:
    from render_webserver import run_server, is_running
    import threading
    WEB_SERVER_AVAILABLE = True
    print("✅ Web server module loaded")
except ImportError as e:
    WEB_SERVER_AVAILABLE = False
    print(f"⚠️  Web server module not available: {e}")

# ===== BOT IMPORTS =====
print("=== ЗАПУСК MONOPOLY BOT ===")
print("Python путь:", sys.path[:2])

try:
    from core.bot import setup_bot
    from handlers.commands import cmd_start, cmd_help, cmd_stats
    from handlers.callback_handlers import register_beautiful_handlers
    from aiogram import Bot, Dispatcher, types
    from aiogram.contrib.middlewares.logging import LoggingMiddleware
    from aiogram.utils import executor
    BOT_AVAILABLE = True
except ImportError as e:
    print(f"❌ Bot import error: {e}")
    BOT_AVAILABLE = False

async def main():
    """Основная функция запуска"""
    
    # 1. ЗАПУСК ВЕБ-СЕРВЕРА (КРИТИЧЕСКИ ВАЖНО ДЛЯ RENDER!)
    if WEB_SERVER_AVAILABLE:
        print("🌐 Запуск веб-сервера для Render...")
        web_thread = threading.Thread(target=run_server, daemon=True)
        web_thread.start()
        
        # Ждем немного для запуска сервера
        await asyncio.sleep(2)
        print(f"✅ Веб-сервер запущен на порту {PORT}")
    else:
        print("⚠️  Веб-сервер не запущен (модуль не найден)")
    
    # 2. ЗАПУСК ТЕЛЕГРАМ БОТА
    if BOT_AVAILABLE:
        print("🤖 Запуск Telegram бота...")
        
        # Получаем токен бота
        BOT_TOKEN = os.environ.get("BOT_TOKEN")
        if not BOT_TOKEN:
            print("❌ BOT_TOKEN не установлен!")
            return
        
        # Инициализация бота
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(bot)
        dp.middleware.setup(LoggingMiddleware())
        
        # Регистрация команд
        dp.register_message_handler(cmd_start, commands=['start'])
        dp.register_message_handler(cmd_help, commands=['help'])
        dp.register_message_handler(cmd_stats, commands=['stats'])
        
        # Регистрация обработчиков красивого дизайна
        try:
            register_beautiful_handlers(dp)
            print("✅ Beautiful handlers registered")
        except Exception as e:
            print(f"⚠️  Beautiful handlers error: {e}")
        
        # Запуск бота
        print(f"🎮 Бот запущен: @{bot.me.username}")
        await dp.start_polling()
    else:
        print("🤖 Telegram бот не запущен (ошибка импорта)")
        print("⚠️  Но веб-сервер работает! Render увидит порт.")

def start_web_only():
    """Запуск ТОЛЬКО веб-сервера (fallback)"""
    if WEB_SERVER_AVAILABLE:
        print("🌐 Запускаю ТОЛЬКО веб-сервер для Render...")
        run_server()
    else:
        print("❌ Не могу запустить веб-сервер")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Пытаемся запустить всё
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Остановка по Ctrl+C")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Пробую запустить только веб-сервер...")
        start_web_only()
