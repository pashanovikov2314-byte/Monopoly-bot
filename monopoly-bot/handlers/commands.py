"""
Command handlers for /start, /monopoly, etc.
"""

import logging
from typing import Dict, Any
from aiogram import Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from config import (
    BANNER, DEV_TAG, MAINTENANCE_MSG,
    ADMIN_USER_IDS, PORT
)
from keyboards.main_keyboards import (
    main_menu_kb,
    waiting_room_kb,
    game_main_kb,
    inline_menu_kb
)
from core.security import request_logger
from database import db

logger = logging.getLogger(__name__)

def setup_commands(dp: Dispatcher, hidden_menu_users: Dict[int, int], stats: Dict[str, Any]):
    """Настройка обработчиков команд"""
    
    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        """Команда /start - ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ"""
        try:
            # Проверяем режим обслуживания
            if stats.get("maintenance_mode", False):
                await message.answer(
                    f"⚠️ {MAINTENANCE_MSG}\n\n"
                    f"👑 Темный Принц уже исправляет это ♥️♥️",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем тип чата - отвечаем ТОЛЬКО в ЛС
            if message.chat.type not in ["private"]:
                await message.answer(
                    "👋 Для управления игрой используйте команду /monopoly в этой группе",
                    parse_mode="HTML"
                )
                return
            
            # Добавляем пользователя в БД
            user = message.from_user
            await db.add_or_update_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or ""
            )
            
            # Только в личных сообщениях показываем полное меню
            user_id = message.from_user.id
            is_admin = user_id in ADMIN_USER_IDS or await db.is_admin(user_id)
            
            # Ссылка на веб-интерфейс
            domain = "your-domain.com"  # Замените на ваш домен
            web_url = f"https://{domain}" if domain != "localhost" else f"http://localhost:{PORT}"
            
            await message.answer(
                f"👋 <b>Добро пожаловать в Monopoly Premium!</b>\n\n"
                f"🎮 <b>Как начать игру:</b>\n"
                f"1. Добавьте меня в группу (кнопка ниже)\n"
                f"2. Дайте мне права администратора\n"
                f"3. Напишите /monopoly в группе\n"
                f"4. Начните сбор игроков\n\n"
                f"👑 <b>Версия Темного Принца</b>\n"
                f"✨ Premium Edition v2.5\n\n"
                f"Разработчик: {DEV_TAG}\n\n"
                f"🌐 <a href='{web_url}'>Веб-интерфейс</a>",
                parse_mode="HTML",
                reply_markup=main_menu_kb(is_group=False, user_id=user_id, is_admin=is_admin),
                disable_web_page_preview=True
            )
            
            # Логируем
            request_logger.log_request(
                user_id=user.id,
                chat_id=message.chat.id,
                message_type="command",
                text="/start"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_start: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("monopoly"))
    async def cmd_monopoly(message: Message):
        """Главная команда - РАЗНЫЕ меню для групп и ЛС"""
        try:
            if stats.get("maintenance_mode", False):
                await message.answer(
                    f"⚠️ {MAINTENANCE_MSG}\n\n"
                    f"👑 Темный Принц уже исправляет это ♥️♥️",
                    parse_mode="HTML"
                )
                return
            
            # Определяем тип чата
            is_group = message.chat.type in ["group", "supergroup"]
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # Проверяем, скрыл ли пользователь меню
            if user_id in hidden_menu_users and hidden_menu_users[user_id] == chat_id:
                # Пользователь скрыл меню - показываем inline версию
                await show_inline_menu(message, hidden_menu_users)
                return
            
            # Проверяем админские права
            is_admin = user_id in ADMIN_USER_IDS or await db.is_admin(user_id)
            
            # Проверяем состояние игры в этом чате
            waiting_game = await db.get_waiting_game(chat_id)
            game_state = await db.get_game_state(chat_id)
            
            # Разные приветствия
            if is_group:
                header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
                
                if game_state and game_state.get("game_state") == "active":
                    header += "🎮 <b>Игра уже идет!</b>\nНажмите '❌ Скрыть меню' чтобы увидеть игровые кнопки\n\n"
                elif waiting_game:
                    players_count = len(waiting_game.get("players", []))
                    header += f"👥 <b>Лобби ожидания активно</b>\nИгроков: {players_count}/8\nПрисоединяйтесь!\n\n"
                else:
                    header += "🎮 <b>Доступные действия:</b>\n"
            
            else:
                header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
                header += "👋 <b>Добро пожаловать!</b>\n\n"
                header += "Чтобы начать игру, добавьте бота в группу и используйте /monopoly там\n\n"
            
            await message.answer(
                header,
                parse_mode="HTML",
                reply_markup=main_menu_kb(
                    is_group=is_group, 
                    user_id=user_id, 
                    is_admin=is_admin
                )
            )
            
            # Логируем
            request_logger.log_request(
                user_id=user_id,
                chat_id=chat_id,
                message_type="command",
                text="/monopoly"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_monopoly: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("hide"))
    async def cmd_hide_menu(message: Message):
        """Команда /hide - скрыть меню (ТОЛЬКО для активных игр)"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем, есть ли активная игра
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры для скрытия меню!</b>\n\n"
                    "Сначала начните игру с помощью /monopoly",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем, участвует ли пользователь в игре
            players = game_state.get("players", {})
            player_exists = str(user_id) in players
            
            if not player_exists:
                await message.answer(
                    "❌ <b>Вы не участвуете в этой игре!</b>\n\n"
                    "Только игроки могут скрывать меню",
                    parse_mode="HTML"
                )
                return
            
            # Скрываем меню
            await message.answer(
                "✅ <b>Меню скрыто!</b>\n\n"
                "Теперь используйте кнопки в сообщении ниже для управления игрой.\n"
                "Эти кнопки видны только вам.\n\n"
                "Чтобы вернуть обычное меню, нажмите '📱 Вернуть меню'",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Сохраняем информацию о скрытии
            hidden_menu_users[user_id] = chat_id
            
            # Показываем inline меню (только этому пользователю)
            player = players[str(user_id)]
            is_turn = False  # TODO: Определить чей сейчас ход
            
            await message.answer(
                f"🎮 <b>Inline меню</b>\n\n"
                f"👤 Игрок: {player['name']}\n"
                f"💰 Баланс: {player.get('balance', 1500)}$\n"
                f"{'🎯 Сейчас ваш ход!' if is_turn else '⏳ Ожидайте своего хода'}\n\n"
                f"👇 <i>Используйте кнопки ниже для управления:</i>",
                parse_mode="HTML",
                reply_markup=inline_menu_kb(player['name'], player['balance'], is_turn)
            )
            
            # Логируем
            request_logger.log_request(
                user_id=user_id,
                chat_id=chat_id,
                message_type="command",
                text="/hide"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_hide: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("show"))
    async def cmd_show_menu(message: Message):
        """Команда /show - показать скрытое меню"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            if user_id in hidden_menu_users:
                del hidden_menu_users[user_id]
                
                await message.answer(
                    "✅ <b>Меню показано!</b>\n\n"
                    "Теперь вы видите обычное игровое меню.",
                    parse_mode="HTML",
                    reply_markup=game_main_kb()
                )
            else:
                await message.answer(
                    "ℹ️ <b>Меню и так показано</b>",
                    parse_mode="HTML"
                )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_show: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("stats"))
    async def cmd_stats(message: Message):
        """Команда /stats - показать статистику"""
        try:
            user_id = message.from_user.id
            
            stats = await db.get_player_stats(user_id)
            if not stats:
                await message.answer(
                    "📊 <b>Ваша статистика</b>\n\n"
                    "Вы еще не играли! Начните первую игру через /monopoly",
                    parse_mode="HTML"
                )
                return
            
            win_rate = (stats["games_won"] / stats["games_played"] * 100) if stats["games_played"] > 0 else 0
            
            await message.answer(
                f"📊 <b>Ваша статистика</b>\n\n"
                f"👤 Игрок: {stats['first_name']}\n"
                f"🎮 Сыграно игр: {stats['games_played']}\n"
                f"🏆 Побед: {stats['games_won']}\n"
                f"📈 Винрейт: {win_rate:.1f}%\n"
                f"💰 Всего заработано: ${stats['total_money']:,}\n"
                f"🏠 Построено домов: {stats['total_houses']}\n"
                f"🏨 Построено отелей: {stats['total_hotels']}\n"
                f"🤝 Сделок: {stats['total_trades']}\n"
                f"🏛️ Посещений тюрьмы: {stats['total_jail_visits']}",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_stats: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("rating"))
    async def cmd_rating(message: Message):
        """Команда /rating - показать рейтинг игроков"""
        try:
            # Получаем топ игроков
            top_players = await db.get_top_players(limit=10, by="games_won")
            
            if not top_players:
                await message.answer(
                    "🏆 <b>Рейтинг игроков</b>\n\n"
                    "Пока никто не играл! Будьте первым!",
                    parse_mode="HTML"
                )
                return
            
            # Формируем сообщение с рейтингом
            rating_text = "🏆 <b>Топ-10 игроков по победам:</b>\n\n"
            
            for i, player in enumerate(top_players, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                username = f"@{player['username']}" if player['username'] else player['first_name']
                
                rating_text += (
                    f"{medal} <b>{username}</b>\n"
                    f"   🏆 Побед: {player['score']} | 🎮 Игр: {player['games_played']}\n"
                    f"   📈 Винрейт: {(player['games_won']/player['games_played']*100):.1f}%\n\n"
                )
            
            rating_text += "\n👑 <i>Версия Темного Принца</i>"
            
            await message.answer(
                rating_text,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_rating: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("map"))
    async def cmd_map(message: Message):
        """Команда /map - показать карту игры"""
        try:
            chat_id = message.chat.id
            
            game_state = await db.get_game_state(chat_id)
            if not game_state:
                await message.answer(
                    "❌ <b>Нет активной игры!</b>\n\n"
                    "Сначала начните игру через /monopoly",
                    parse_mode="HTML"
                )
                return
            
            # Здесь будет генерация карты
            # Пока просто сообщение
            await message.answer(
                "🗺️ <b>Карта игры</b>\n\n"
                "Интерактивная карта в разработке...\n"
                "Скоро будет доступна через веб-интерфейс!",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_map: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("admin"))
    async def cmd_admin(message: Message):
        """Команда /admin - админ панель"""
        try:
            user_id = message.from_user.id
            
            if user_id not in ADMIN_USER_IDS and not await db.is_admin(user_id):
                await message.answer("❌ У вас нет прав администратора!")
                return
            
            # Получаем статистику системы
            total_games = 0  # TODO: Получить из БД
            active_games = 0  # TODO: Получить из БД
            total_players = 0  # TODO: Получить из БД
            
            await message.answer(
                "⚙️ <b>Админ панель</b>\n\n"
                f"📊 Статистика:\n"
                f"• Всего игр: {total_games}\n"
                f"• Активных игр: {active_games}\n"
                f"• Игроков всего: {total_players}\n\n"
                f"👑 Темный Принц",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_admin: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        """Команда /help - помощь"""
        try:
            help_text = """
🎮 <b>Monopoly Premium - Помощь</b>

<b>Основные команды:</b>
/monopoly - Главное меню игры
/stats - Ваша статистика
/rating - Рейтинг игроков
/map - Карта текущей игры
/hide - Скрыть меню (в активной игре)
/show - Показать скрытое меню

<b>Игровые кнопки:</b>
🎲 Бросить кубик - Сделать ход
🏠 Построить - Управление недвижимостью
💰 Банк - Финансовые операции
🤝 Торговля - Обмен с игроками
📊 Мои активы - Показать имущество
🗺️ Карта игры - Открыть карту
🏛️ Тюрьма - Действия в тюрьме
📈 Статистика - Статистика игры

<b>Администрация:</b>
/admin - Админ панель (только для админов)

👑 <i>Версия Темного Принца</i>
            """
            
            await message.answer(help_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Ошибка в cmd_help: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    async def show_inline_menu(message: Message, hidden_menu_users: Dict[int, int]):
        """Показать inline меню (вместо скрытой клавиатуры)"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем, есть ли активная игра
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                return
            
            players = game_state.get("players", {})
            
            # Находим игрока
            player = players.get(str(user_id))
            if not player:
                return
            
            # Получаем текущего игрока
            current_idx = game_state.get("current_player", 0)
            player_ids = list(players.keys())
            
            is_your_turn = False
            if player_ids and current_idx < len(player_ids):
                is_your_turn = (player_ids[current_idx] == str(user_id))
            
            turn_info = ""
            if is_your_turn:
                turn_info = "🎯 <b>Сейчас ваш ход!</b>\n"
            else:
                if player_ids and current_idx < len(player_ids):
                    current_player_id = player_ids[current_idx]
                    current_player = players.get(current_player_id, {})
                    turn_info = f"⏳ <b>Сейчас ходит: {current_player.get('name', 'Неизвестно')}</b>\n"
            
            menu_text = (
                f"🎮 <b>Monopoly Premium - Inline меню</b>\n\n"
                f"👤 Игрок: {player['name']}\n"
                f"💰 Баланс: {player.get('balance', 1500)}$\n"
                f"📍 Позиция: {player.get('position', 0)}\n"
                f"{turn_info}\n"
                f"👇 <i>Используйте кнопки ниже для управления:</i>"
            )
            
            # Отправляем inline меню
            await message.answer(
                menu_text,
                parse_mode="HTML",
                reply_markup=inline_menu_kb(
                    player['name'], 
                    player.get('balance', 1500), 
                    is_your_turn
                )
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_inline_menu: {e}")
    
    logger.info("✅ Обработчики команд зарегистрированы")
