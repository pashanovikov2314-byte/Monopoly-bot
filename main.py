"""
Точка входа для Render - перенаправляет в bot/main.py
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Импортируем и запускаем основной бот
    from bot.main import main
    import asyncio
    
    # Запускаем асинхронную функцию
    asyncio.run(main())
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Пути Python:", sys.path)
    print("Текущая директория:", os.getcwd())
    print("Содержимое bot/:", os.listdir('bot') if os.path.exists('bot') else "Папка bot не существует")
    sys.exit(1)
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
