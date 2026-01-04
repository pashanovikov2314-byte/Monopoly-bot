#!/usr/bin/env python3
"""Красивый дизайн для бота с анимированными ответами"""

import random
from datetime import datetime
from typing import List, Dict

class BeautifulDesign:
    """Класс для красивого оформления бота"""
    
    # Разнообразные приветствия
    GREETINGS = [
        "✨ *Добро пожаловать в мир высоких ставок!*",
        "🎮 *Приветствую, стратег!* Готов к монополии?",
        "🏰 *Ты вошел в элитный клуб!* Удачи в сделках!",
        "💎 *Доступ к Monopoly Premium получен!*",
        "🚀 *Система активирована!* Приготовься к игре!"
    ]
    
    # Разнообразные ответы на действия
    ACTION_RESPONSES = {
        "join_lobby": [
            "🎪 Отличный выбор! Добро пожаловать в лобби!",
            "👥 Прекрасно! Теперь ты в команде!",
            "🚀 Игрок присоединился! Становится интереснее!",
            "💫 Новый участник в игре! Да начнется битва!"
        ],
        "leave_lobby": [
            "👋 Будем скучать! Возвращайся скорее!",
            "🚪 Выход принят. Ждем тебя снова!",
            "🌅 Игрок покинул поле. До новых встреч!",
            "✨ Спасибо за игру! Заходи еще!"
        ],
        "ready_toggle": [
            "✅ Игрок готов к старту!",
            "🎯 Статус готовности обновлен!",
            "⚡ Игрок заряжен и ждет начала!",
            "🔥 Готовность подтверждена! Ждем остальных!"
        ]
    }
    
    # Разнообразные сообщения о разработчике
    DEVELOPER_TEXTS = [
        """
👑 *ТЕМНЫЙ ПРИНЦ (qulms)*
*only for Shit Daily*

🚀 *Роль:* Главный разработчик и архитектор системы
💎 *Статус:* Эксклюзивный доступ для Shit Daily
⚡ *Специализация:* Telegram боты, монополия, стратегии

📞 *Контакты:* @qulms
🎯 *Девиз:* "Каждая игра - это история"

⚠️ *Важно:* Все вопросы и предложения только через разработчика
""",
        
        """
⚡ *РАЗРАБОТЧИК СИСТЕМЫ*
*qulms - Темный принц*

🏆 *Достижения:*
• Создал эксклюзивную версию Monopoly
• Разработал систему white list
• Реализовал продвинутый игровой движок

🔧 *Технологии:*
• Python 3.10+
• python-telegram-bot
• Flask для веб-панели
• Собственная система лобби

🎮 *Философия:* Каждый игрок - часть истории Shit Daily
"""
    ]
    
    # Разнообразные сообщения о белом списке
    WHITELIST_GUIDES = [
        """
🔒 *ГАЙД ПО WHITE LIST СИСТЕМЕ*

*Что это?*
Система ограниченного доступа к боту только для избранных чатов.

*Как это работает?*
1. 👑 Разработчик добавляет чат в белый список
2. 🤖 Бот активируется только в разрешенных чатах
3. 🚫 В остальных чатах бот не работает

*Как добавить чат?*
1. Свяжитесь с @qulms
2. Предоставьте ID чата и его назначение
3. Дождитесь проверки и активации

*Почему такая система?*
• 🔐 Безопасность от спама
• 💎 Эксклюзивность для Shit Daily
• 🎯 Качественная поддержка
• 🚀 Стабильная работа
""",
        
        """
📋 *WHITE LIST - СИСТЕМА ДОСТУПА*

🏢 *Текущие привилегированные чаты:*
• Shit Daily Official (основной)
• Тестовые среды разработчика
• Партнерские сообщества

⚖️ *Критерии добавления:*
1. Соответствие тематике Shit Daily
2. Активное сообщество
3. Соблюдение правил
4. Рекомендация от участника

🚫 *Причины отказа:*
• Нарушения в прошлом
• Неактивный чат
• Несоответствие тематике

📞 *Для добавления:* @qulms
"""
    ]
    
    @staticmethod
    def get_random_greeting() -> str:
        """Случайное приветствие"""
        return random.choice(BeautifulDesign.GREETINGS)
    
    @staticmethod
    def get_developer_info() -> str:
        """Информация о разработчике"""
        return random.choice(BeautifulDesign.DEVELOPER_TEXTS)
    
    @staticmethod
    def get_whitelist_guide() -> str:
        """Гайд по white list"""
        return random.choice(BeautifulDesign.WHITELIST_GUIDES)
    
    @staticmethod
    def get_action_response(action: str) -> str:
        """Ответ на действие игрока"""
        responses = BeautifulDesign.ACTION_RESPONSES.get(action, ["Действие выполнено!"])
        return random.choice(responses)
    
    @staticmethod
    def create_lobby_keyboard(lobby_id: str = None) -> List[List[Dict]]:
        """Создание клавиатуры для лобби"""
        if lobby_id:
            return [
                [
                    {"text": "✅ Готов/Не готов", "callback_data": f"toggle_ready_{lobby_id}"},
                    {"text": "👥 Пригласить друзей", "callback_data": f"invite_{lobby_id}"}
                ],
                [
                    {"text": "🚪 Выйти из лобби", "callback_data": f"leave_{lobby_id}"},
                    {"text": "🚀 Начать игру", "callback_data": f"start_game_{lobby_id}"}
                ],
                [
                    {"text": "📊 Статус лобби", "callback_data": f"status_{lobby_id}"},
                    {"text": "👁️ Скрыть меню", "callback_data": "hide_menu"}
                ]
            ]
        else:
            return [
                [
                    {"text": "🎮 Создать лобби", "callback_data": "create_lobby"},
                    {"text": "👥 Присоединиться", "callback_data": "join_lobby"}
                ],
                [
                    {"text": "📖 Правила", "callback_data": "rules"},
                    {"text": "👑 Разработчик", "callback_data": "developer"}
                ]
            ]
    
    @staticmethod
    def create_game_keyboard(game_id: str = None) -> List[List[Dict]]:
        """Создание игровой клавиатуры"""
        keyboards = [
            # Вариант 1
            [
                [{"text": "🎲 Бросить кубики", "callback_data": "roll_dice"}],
                [{"text": "💵 Купить участок", "callback_data": "buy_property"}],
                [{"text": "🏗️ Строить", "callback_data": "build"}],
                [{"text": "👁️ Скрыть меню", "callback_data": "hide_game_menu"}]
            ],
            # Вариант 2
            [
                [
                    {"text": "🎲 Кубики", "callback_data": "roll_dice"},
                    {"text": "💵 Купить", "callback_data": "buy_property"}
                ],
                [
                    {"text": "🏗️ Стройка", "callback_data": "build"},
                    {"text": "💳 Торговля", "callback_data": "trade"}
                ],
                [
                    {"text": "📊 Статус", "callback_data": "game_status"},
                    {"text": "👁️ Скрыть", "callback_data": "hide_game_menu"}
                ]
            ],
            # Вариант 3
            [
                [
                    {"text": "⚡ Быстрые действия", "callback_data": "quick_actions"},
                    {"text": "🎯 Стратегия", "callback_data": "strategy"}
                ],
                [
                    {"text": "💰 Финансы", "callback_data": "finances"},
                    {"text": "🏠 Недвижимость", "callback_data": "properties"}
                ],
                [
                    {"text": "👁️ Скрыть интерфейс", "callback_data": "hide_game_menu"},
                    {"text": "❓ Помощь", "callback_data": "game_help"}
                ]
            ]
        ]
        
        return random.choice(keyboards)
    
    @staticmethod
    def format_player_info(user_id: int, username: str, first_name: str) -> str:
        """Форматирование информации об игроке"""
        avatars = ["👑", "⚡", "💎", "🚀", "🎯", "🌟", "🔥", "💫"]
        avatar = random.choice(avatars)
        
        return f"""
{avatar} *ИГРОК:*
• Имя: {first_name}
• Ник: @{username if username else 'без ника'}
• ID: `{user_id}`
• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    @staticmethod
    def create_bot_status_message(status: str = "online") -> str:
        """Создание сообщения о статусе бота"""
        status_messages = {
            "online": [
                "✅ *Бот работает нормально!* Все системы в порядке.",
                "🚀 *Система активна!* Готова к новым игрокам.",
                "💎 *Статус: ONLINE* - Monopoly Bot на связи!"
            ],
            "offline": [
                "🚫 *Бот временно не работает.* Темный принц уже исправляет!",
                "⚠️ *Система на обслуживании.* Скоро вернемся в игру!",
                "🔧 *Технические работы.* Приносим извинения за неудобства!"
            ],
            "error": [
                "❌ *Обнаружена ошибка!* Разработчик уже в курсе.",
                "⚡ *Временные неполадки.* Работаем над решением!",
                "💥 *Системный сбой.* Восстановление в процессе..."
            ]
        }
        
        messages = status_messages.get(status, status_messages["online"])
        return random.choice(messages)

# Глобальный экземпляр
design = BeautifulDesign()
