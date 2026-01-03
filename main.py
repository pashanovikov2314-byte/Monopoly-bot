#!/usr/bin/env python3
"""Корневой файл запуска для Render.com"""

import os
import sys

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем основной бот из папки bot
try:
    from bot.main import main
    print("🚀 Запуск Monopoly Bot...")
    main()
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📋 Проверьте структуру проекта и зависимости")
    sys.exit(1)
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    sys.exit(1)
