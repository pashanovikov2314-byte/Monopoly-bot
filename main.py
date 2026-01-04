"""
Точка входа для Render
Просто запускает бота из bot/main.py
"""
print("🚀 Запуск Monopoly Bot...")
print("📁 Текущая директория:", __file__)

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Импортируем и запускаем бота
    from bot.main import main
    
    if __name__ == '__main__':
        print("✅ Импорт бота успешен, запускаем...")
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Пути Python:", sys.path)
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
