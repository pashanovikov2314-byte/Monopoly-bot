"""
🎮 Точка входа для Monopoly Bot на Render
"""
print("🚀 Запуск Monopoly Bot...")
print("📁 Текущая директория:", __file__)

import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Пытаемся импортировать и запустить бота
    from bot.main import main
    
    if __name__ == '__main__':
        print("✅ Импорт успешен, запускаем бота...")
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Пробую альтернативный запуск...")
    
    # Альтернативный запуск если bot/main не работает
    try:
        # Прямой запуск Flask приложения
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>🎮 Monopoly Bot</title></head>
            <body>
                <h1>🎮 Monopoly Bot</h1>
                <p>Бот запускается...</p>
            </body>
            </html>
            '''
        
        port = int(os.getenv('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e2:
        print(f"❌ Альтернативный запуск также не удался: {e2}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Общая ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
