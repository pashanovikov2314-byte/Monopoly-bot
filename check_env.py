#!/usr/bin/env python3
"""
Скрипт для проверки переменных окружения
Запустите его на Render через Console
"""
import os
import sys

print("=== ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ НА RENDER ===")
print()

# Проверяем все переменные
variables = {
    'TOKEN': 'Токен Telegram бота',
    'MONGODB_URI': 'Строка подключения к MongoDB',
    'WEBHOOK_URL': 'URL веб-хука',
    'PORT': 'Порт приложения'
}

all_good = True

for var, description in variables.items():
    value = os.getenv(var)
    if value:
        if var == 'TOKEN':
            # Скрываем токен для безопасности
            display = f"{value[:10]}... (скрыто)"
        elif var == 'MONGODB_URI':
            # Скрываем пароль от MongoDB
            if '@' in value:
                # Маскируем пароль в URI
                parts = value.split('@')
                if '://' in parts[0]:
                    protocol, credentials = parts[0].split('://')
                    if ':' in credentials:
                        user, password = credentials.split(':')
                        masked = f"{protocol}://{user}:****@{parts[1]}"
                        display = masked
                    else:
                        display = value
                else:
                    display = value
            else:
                display = value
        else:
            display = value
        
        print(f"✅ {var}: {display}")
        print(f"   Описание: {description}")
    else:
        print(f"❌ {var}: НЕ УСТАНОВЛЕН")
        print(f"   Описание: {description}")
        all_good = False
    print()

# Дополнительная информация
print("=== ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===")
print(f"Текущая директория: {os.getcwd()}")
print(f"Содержимое директории: {os.listdir('.')}")
print()

if all_good:
    print("🎉 ВСЕ ПЕРЕМЕННЫЕ УСТАНОВЛЕНЫ КОРРЕКТНО!")
    print("Бот должен работать без проблем.")
else:
    print("⚠️  НЕКОТОРЫЕ ПЕРЕМЕННЫЕ НЕ УСТАНОВЛЕНЫ!")
    print("Смотрите инструкцию в RENDER_SETUP.md")
    sys.exit(1)
