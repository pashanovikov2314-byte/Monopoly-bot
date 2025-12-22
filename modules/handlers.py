"""
HANDLERS.PY - Обработчики команд и кнопок (300 строк)
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.config import (
    logger, WAITING_GAMES, ACTIVE_GAMES, HIDDEN_MENU_USERS,
    STATS, USER_STATS, ADMINS, BANNER, MAINTENANCE_MSG,
    DEV_TAG, PORT, API_TOKEN, ALLOWED_USERS,
    get_top_players, update_user_stats, load_user_stats, save_user_stats
)
from modules.keyboards import (
    main_menu_kb, waiting_room_kb, game_main_kb, inline_menu_kb,
    board_map_kb, trade_menu_kb, build_menu_kb, mortgage_menu_kb,
    jail_menu_kb, rating_menu_kb, admin_panel_kb,
    back_button_kb, yes_no_kb, dice_animation_kb,
    update_waiting_room
)
from modules.game_logic import MonopolyGame, MonopolyPlayer

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def cmd_start(message: types.Message, bot: Bot):
    """Команда /start - ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ"""
    try:
        if message.chat.type not in ["private"]:
            await message.answer(
                "👋 Для управления игрой используйте команду /monopoly в этой группе",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            f"👋 <b>Добро пожаловать в Monopoly Premium!</b>\n\n"
            f"🎮 <b>Как начать игру:</b>\n"
            f"1. Добавьте меня в группу (кнопка ниже)\n"
            f"2. Дайте мне права администратора\n"
            f"3. Напишите /monopoly в группе\n"
            f"4. Начните сбор игроков\n\n"
            f"👑 <b>Версия Темного Принца</b>\n"
            f"✨ Premium Edition v3.0\n\n"
            f"Разработчик: {DEV_TAG}",
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=False, user_id=message.from_user.id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def cmd_monopoly(message: types.Message):
    """Главная команда - РАЗНЫЕ меню для групп и ЛС"""
    try:
        if STATS.get("maintenance_mode", False):
            await message.answer(
                f"⚠️ {MAINTENANCE_MSG}\n\n"
                f"👑 Темный Принц уже исправляет это ♥️",
                parse_mode="HTML"
            )
            return
        
        is_group = message.chat.type in ["group", "supergroup"]
        user_id = message.from_user.id
        
        # Проверяем, скрыл ли пользователь меню
        if user_id in HIDDEN_MENU_USERS and HIDDEN_MENU_USERS[user_id] == message.chat.id:
            await show_inline_menu(message, user_id)
            return
        
        # Разные приветствия
        if is_group:
            header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
            header += "🎮 <b>Доступные действия:</b>"
        else:
            header = f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца\n\n"
            header += "👋 <b>Добро пожаловать!</b>"
        
        await message.answer(
            header,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_group=is_group, user_id=user_id)
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_monopoly: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def cmd_hide(message: types.Message):
    """Команда /hide - скрыть меню"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer(
                "❌ <b>Нет активной игры для скрытия меню!</b>\n\n"
                "Сначала начните игру с помощью /monopoly",
                parse_mode="HTML"
            )
            return
        
        game = ACTIVE_GAMES[chat_id]
        player_exists = any(p.id == user_id for p in game.players)
        
        if not player_exists:
            await message.answer(
                "❌ <b>Вы не участвуете в этой игре!</b>",
                parse_mode="HTML"
            )
            return
        
        # Скрываем меню
        await message.answer(
            "✅ <b>Меню скрыто!</b>\n\n"
            "Теперь используйте кнопки в сообщении ниже для управления игрой.\n"
            "Эти кнопки видны только вам.\n\n"
            "Чтобы вернуть меню, нажмите '📱 Вернуть меню'",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        HIDDEN_MENU_USERS[user_id] = chat_id
        await show_inline_menu(message, user_id)
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_hide: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def cmd_show(message: types.Message):
    """Команда /show - показать меню"""
    try:
        user_id = message.from_user.id
        
        if user_id in HIDDEN_MENU_USERS:
            chat_id = HIDDEN_MENU_USERS[user_id]
            
            if chat_id in ACTIVE_GAMES:
                await message.answer(
                    "✅ <b>Меню восстановлено!</b>",
                    parse_mode="HTML",
                    reply_markup=game_main_kb()
                )
                del HIDDEN_MENU_USERS[user_id]
            else:
                await message.answer(
                    "✅ <b>Меню восстановлено!</b>",
                    parse_mode="HTML"
                )
                del HIDDEN_MENU_USERS[user_id]
        else:
            await message.answer(
                "ℹ️ <b>Меню уже отображается!</b>",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в cmd_show: {e}")

async def cmd_stats(message: types.Message):
    """Команда /stats - моя статистика"""
    try:
        user_id = message.from_user.id
        
        if user_id not in USER_STATS:
            await message.answer(
                "📊 <b>Ваша статистика</b>\n\n"
                "🎮 Игр сыграно: <b>0</b>\n"
                "🏆 Побед: <b>0</b>\n"
                "📈 Процент побед: <b>0%</b>\n"
                "💰 Общий выигрыш: <b>0$</b>\n\n"
                "🎯 <b>Ранг: Новичок</b>\n\n"
                "Сыграйте свою первую игру!",
                parse_mode="HTML"
            )
            return
        
        stats = USER_STATS[user_id]
        games = stats.get("games", 0)
        wins = stats.get("wins", 0)
        total_money = stats.get("total_money", 0)
        
        win_rate = (wins / games * 100) if games > 0 else 0
        
        # Определяем ранг
        if games == 0:
            rank = "Новичок"
        elif win_rate >= 60:
            rank = "👑 Чемпион"
        elif win_rate >= 40:
            rank = "🏆 Профи"
        elif win_rate >= 20:
            rank = "⭐ Игрок"
        else:
            rank = "🎮 Новичок"
        
        await message.answer(
            f"📊 <b>Ваша статистика</b>\n\n"
            f"👤 Игрок: <b>{stats.get('first_name', '')}</b>\n"
            f"🎮 Игр сыграно: <b>{games}</b>\n"
            f"🏆 Побед: <b>{wins}</b>\n"
            f"📈 Процент побед: <b>{win_rate:.1f}%</b>\n"
            f"💰 Общий выигрыш: <b>{total_money}$</b>\n"
            f"📅 Последняя игра: <b>{stats.get('last_played', 'никогда')}</b>\n\n"
            f"🎯 <b>Ранг: {rank}</b>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_stats: {e}")
        await message.answer("❌ Ошибка загрузки статистики")

async def cmd_rating(message: types.Message):
    """Команда /rating - рейтинг игроков"""
    try:
        top_players = get_top_players(10)
        
        if not top_players:
            await message.answer(
                "🏆 <b>Рейтинг игроков</b>\n\n"
                "📊 Еще никто не играл. Будьте первым!",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        rating_text = "🏆 <b>Топ-10 игроков</b>\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            name = player["first_name"]
            if player["username"]:
                name = f"@{player['username']}"
            
            games = player["games"]
            wins = player["wins"]
            win_rate = player["win_rate"]
            
            rating_text += (
                f"{medal} <b>{name}</b>\n"
                f"   🎮 Игр: {games} | 🏆 Побед: {wins}\n"
                f"   📈 Винрейт: {win_rate:.1f}%\n"
            )
        
        await message.answer(
            rating_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_rating: {e}")
        await message.answer("❌ Ошибка загрузки рейтинга")

async def cmd_admin(message: types.Message):
    """Команда /admin - админ панель"""
    try:
        user_id = message.from_user.id
        
        if user_id not in ADMINS:
            await message.answer(
                "⛔ <b>Доступ запрещен!</b>\n\n"
                "Эта команда только для администраторов бота.",
                parse_mode="HTML"
            )
            return
        
        admin_text = (
            f"⚙️ <b>Админ панель</b>\n\n"
            f"👑 Администратор: {message.from_user.first_name}\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"
            f"📊 <b>Статистика бота:</b>\n"
            f"• Активных игр: {len(ACTIVE_GAMES)}\n"
            f"• Ожидающих игр: {len(WAITING_GAMES)}\n"
            f"• Всего игроков: {len(USER_STATS)}\n"
            f"• Режим обслуживания: {'✅ ВКЛ' if STATS.get('maintenance_mode') else '❌ ВЫКЛ'}\n\n"
            f"👇 <b>Выберите действие:</b>"
        )
        
        await message.answer(
            admin_text,
            parse_mode="HTML",
            reply_markup=admin_panel_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin: {e}")
        await message.answer("❌ Ошибка админ панели")

# ==================== ОБРАБОТЧИКИ CALLBACK ДЛЯ ЛОББИ ====================

async def start_gathering(callback: CallbackQuery, bot: Bot):
    """Начать сбор игроков"""
    try:
        if STATS.get("maintenance_mode", False):
            await callback.answer(MAINTENANCE_MSG, show_alert=True)
            return
        
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id in WAITING_GAMES:
            await callback.answer("⚠️ В этой группе уже идет сбор игроков!", show_alert=True)
            return
        
        WAITING_GAMES[chat_id] = {
            "creator_id": user_id,
            "creator_name": callback.from_user.first_name,
            "players": [{
                "id": user_id,
                "name": callback.from_user.first_name,
                "username": callback.from_user.username,
                "joined_at": datetime.now().isoformat()
            }],
            "message_id": callback.message.message_id,
            "created_at": datetime.now(),
            "timer_task": None
        }
        
        # Запускаем таймер на 3 минуты
        WAITING_GAMES[chat_id]["timer_task"] = asyncio.create_task(
            lobby_timer(chat_id, bot)
        )
        
        await update_waiting_room(
            bot, chat_id, callback.message.message_id,
            WAITING_GAMES[chat_id], user_id
        )
        
        await callback.answer("🎮 Сбор игроков начат!")
        
    except Exception as e:
        logger.error(f"Ошибка в start_gathering: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def join_game(callback: CallbackQuery, bot: Bot):
    """Присоединиться к игре"""
    try:
        chat_id = int(callback.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await callback.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        user_id = callback.from_user.id
        
        # Проверяем, не в игре ли уже
        for player in game["players"]:
            if player["id"] == user_id:
                await callback.answer("✅ Вы уже в игре!")
                return
        
        # Добавляем игрока
        game["players"].append({
            "id": user_id,
            "name": callback.from_user.first_name,
            "username": callback.from_user.username,
            "joined_at": datetime.now().isoformat()
        })
        
        await update_waiting_room(
            bot, chat_id, callback.message.message_id,
            game, callback.from_user.id
        )
        
        await callback.answer(f"🎮 Вы присоединились! Игроков: {len(game['players'])}")
        
    except Exception as e:
        logger.error(f"Ошибка в join_game: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def leave_game(callback: CallbackQuery, bot: Bot):
    """Выйти из игры"""
    try:
        chat_id = int(callback.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await callback.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game = WAITING_GAMES[chat_id]
        user_id = callback.from_user.id
        original_count = len(game["players"])
        
        # Удаляем игрока
        game["players"] = [p for p in game["players"] if p["id"] != user_id]
        
        # Если игроков не осталось
        if not game["players"]:
            if game.get("timer_task"):
                game["timer_task"].cancel()
            del WAITING_GAMES[chat_id]
            await callback.message.edit_text("❌ Игра отменена - все игроки вышли")
            await callback.answer("Игра отменена")
            return
        
        # Если вышел создатель, назначаем нового
        if user_id == game["creator_id"]:
            new_creator = game["players"][0]
            game["creator_id"] = new_creator["id"]
            game["creator_name"] = new_creator["name"]
        
        await update_waiting_room(
            bot, chat_id, callback.message.message_id,
            game, callback.from_user.id
        )
        
        await callback.answer(f"🚪 Вы вышли. Игроков: {len(game['players'])}")
        
    except Exception as e:
        logger.error(f"Ошибка в leave_game: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def start_game(callback: CallbackQuery, bot: Bot):
    """Начать игру"""
    try:
        chat_id = int(callback.data.split("_")[2])
        
        if chat_id not in WAITING_GAMES:
            await callback.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game_data = WAITING_GAMES[chat_id]
        
        # Проверяем права создателя
        if callback.from_user.id != game_data["creator_id"]:
            await callback.answer("⚠️ Только создатель игры может её начать!", show_alert=True)
            return
        
        # Проверяем количество игроков
        if len(game_data["players"]) < 2:
            await callback.answer("⚠️ Нужно минимум 2 игрока!", show_alert=True)
            return
        
        # Отменяем таймер
        if game_data.get("timer_task"):
            game_data["timer_task"].cancel()
        
        # Создаем игру
        game = MonopolyGame(chat_id, game_data["creator_id"])
        
        # Добавляем игроков
        for player_data in game_data["players"]:
            game.add_player(
                player_data["id"],
                player_data["name"],
                player_data.get("username", "")
            )
        
        # Сохраняем игру
        ACTIVE_GAMES[chat_id] = game
        
        # Удаляем из ожидающих
        del WAITING_GAMES[chat_id]
        
        # Формируем список игроков
        players_list = "\n".join([f"• {p.name}" for p in game.players])
        
        # Отправляем сообщение о начале игры
        await callback.message.edit_text(
            f"🎉 <b>Игра началась!</b>\n\n"
            f"<b>Участники:</b>\n{players_list}\n\n"
            f"💰 Стартовый баланс: <b>1500$</b>\n"
            f"🎲 Первым ходит: <b>{game.players[0].name}</b>\n"
            f"🔄 Ход: <b>1</b>\n\n"
            f"<i>Используйте меню ниже для управления игрой</i>",
            parse_mode="HTML"
        )
        
        # Отправляем игровое меню
        first_player = game.players[0]
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎮 <b>Игра началась!</b>\n\n"
                 f"📢 <b>{first_player.name}</b>, ваш ход первый!\n"
                 f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
            parse_mode="HTML",
            reply_markup=game_main_kb()
        )
        
        await callback.answer("🎮 Игра началась!")
        
    except Exception as e:
        logger.error(f"Ошибка в start_game: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

  async def stop_gathering(callback: CallbackQuery, bot: Bot):
    """Прекратить набор игроков"""
    try:
        chat_id = int(callback.data.split("_")[3])
        
        if chat_id not in WAITING_GAMES:
            await callback.answer("⚠️ Игра не найдена!", show_alert=True)
            return
        
        game_data = WAITING_GAMES[chat_id]
        
        # Проверяем права создателя
        if callback.from_user.id != game_data["creator_id"]:
            await callback.answer("⚠️ Только создатель может прекратить набор!", show_alert=True)
            return
        
        # Отменяем таймер
        if game_data.get("timer_task"):
            game_data["timer_task"].cancel()
        
        # Удаляем игру
        del WAITING_GAMES[chat_id]
        
        await callback.message.edit_text(
            "❌ <b>Сбор игроков прекращен создателем</b>\n\n"
            "Для начала новой игры используйте /monopoly",
            parse_mode="HTML"
        )
        
        await callback.answer("⏹️ Набор игроков прекращен")
        
    except Exception as e:
        logger.error(f"Ошибка в stop_gathering: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def lobby_timer(chat_id: int, bot: Bot):
    """Таймер лобби (3 минуты)"""
    try:
        await asyncio.sleep(180)  # 3 минуты
        
        if chat_id not in WAITING_GAMES:
            return
        
        game_data = WAITING_GAMES[chat_id]
        
        # Проверяем количество игроков
        if len(game_data["players"]) >= 2:
            # Автоматически начинаем игру
            game = MonopolyGame(chat_id, game_data["creator_id"])
            
            # Добавляем игроков
            for player_data in game_data["players"]:
                game.add_player(
                    player_data["id"],
                    player_data["name"],
                    player_data.get("username", "")
                )
            
            # Сохраняем игру
            ACTIVE_GAMES[chat_id] = game
            
            # Удаляем из ожидающих
            del WAITING_GAMES[chat_id]
            
            # Формируем список игроков
            players_list = "\n".join([f"• {p.name}" for p in game.players])
            
            # Отправляем сообщение о начале игры
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=game_data["message_id"],
                text=f"⏰ <b>Игра начата автоматически!</b>\n\n"
                     f"<b>Участники:</b>\n{players_list}\n\n"
                     f"💰 Стартовый баланс: <b>1500$</b>\n"
                     f"🎲 Первым ходит: <b>{game.players[0].name}</b>\n"
                     f"🔄 Ход: <b>1</b>\n\n"
                     f"<i>Используйте меню ниже для управления игрой</i>",
                parse_mode="HTML"
            )
            
            # Отправляем игровое меню
            first_player = game.players[0]
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎮 <b>Игра начата автоматически!</b>\n\n"
                     f"📢 <b>{first_player.name}</b>, ваш ход первый!\n"
                     f"Нажмите '🎲 Бросить кубик' чтобы сделать ход",
                parse_mode="HTML",
                reply_markup=game_main_kb()
            )
            
            logger.info(f"Игра в чате {chat_id} начата автоматически")
        else:
            # Недостаточно игроков - отменяем
            del WAITING_GAMES[chat_id]
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=game_data["message_id"],
                text="❌ <b>Сбор игроков отменен</b>\n\n"
                     "Не удалось набрать минимум 2 игроков за 3 минуты\n\n"
                     "Для новой попытки используйте /monopoly",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в lobby_timer: {e}")

# ==================== ОБРАБОТЧИКИ КНОПОК ИГРЫ ====================

async def roll_dice_button(message: types.Message, bot: Bot):
    """Кнопка броска кубика"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        current_player = game.get_current_player()
        
        # Проверяем очередь
        if not current_player or current_player.id != user_id:
            if current_player:
                await message.answer(f"⏳ Сейчас ходит {current_player.name}!")
            return
        
        # Проверяем, не в тюрьме ли игрок
        if current_player.in_jail:
            await message.answer(
                "⛓️ <b>Вы в тюрьме!</b>\n\n"
                "Используйте специальное меню для выхода из тюрьмы",
                parse_mode="HTML",
                reply_markup=jail_menu_kb()
            )
            return
        
        # Бросаем кубик
        dice1, dice2, total = game.roll_dice(current_player)
        
        # Анимация броска
        await message.answer_dice(emoji="🎲")
        await asyncio.sleep(1)
        await message.answer_dice(emoji="🎲")
        await asyncio.sleep(2)
        
        # Двигаем игрока
        old_pos = current_player.position
        new_pos = game.move_player(current_player, total)
        
        # Формируем сообщение
        dice_text = f"🎲 <b>{current_player.name} бросает кубики:</b>\n"
        dice_text += f"🎯 Кубик 1: <b>{dice1}</b>\n"
        dice_text += f"🎯 Кубик 2: <b>{dice2}</b>\n"
        dice_text += f"📊 Сумма: <b>{total}</b>\n\n"
        
        if dice1 == dice2:
            dice_text += "✨ <b>Выпал дубль!</b> Ходите еще раз\n\n"
        
        dice_text += f"📍 Позиция: {old_pos} → <b>{new_pos}</b>\n"
        
        # Обрабатываем клетку
        cell_result = game.process_position(current_player, new_pos)
        
        if cell_result["cell_name"]:
            dice_text += f"🏠 Клетка: <b>{cell_result['cell_name']}</b>\n"
        
        # Обработка специальных действий
        if cell_result["special_action"] == "go_to_jail":
            current_player.in_jail = True
            current_player.position = 10  # Тюрьма
            dice_text += "\n⛓️ <b>ИДИТЕ В ТЮРЬМУ!</b>\n"
        
        elif cell_result["special_action"] == "chance":
            dice_text += "\n🎲 <b>ВЫПАЛ ШАНС!</b>\n"
            dice_text += "Нажмите '🎲 Бросить кубик' еще раз чтобы вытянуть карту\n"
        
        # Показываем сообщение
        await message.answer(dice_text, parse_mode="HTML")
        
        # Обработка аренды
        if cell_result["rent_due"] > 0:
            rent = cell_result["rent_due"]
            if current_player.balance >= rent:
                current_player.balance -= rent
                
                # Находим владельца
                if new_pos in game.properties:
                    owner_id = game.properties[new_pos]["owner"]
                    owner = game.get_player_by_id(owner_id)
                    if owner:
                        owner.balance += rent
                        await message.answer(
                            f"💸 <b>Оплата аренды</b>\n\n"
                            f"🏠 Недвижимость: {cell_result['cell_name']}\n"
                            f"👤 Владелец: {owner.name}\n"
                            f"💰 Сумма: {rent}$\n"
                            f"💵 Ваш баланс: {current_player.balance}$",
                            parse_mode="HTML"
                        )
            else:
                await message.answer(
                    f"❌ <b>Недостаточно средств для оплаты аренды!</b>\n\n"
                    f"Нужно: {rent}$\n"
                    f"У вас: {current_player.balance}$\n\n"
                    f"Продайте недвижимость или заложите имущество",
                    parse_mode="HTML"
                )
        
        # Предложение покупки
        elif cell_result["can_buy"]:
            price = BOARD[new_pos]["price"]
            await message.answer(
                f"🛒 <b>Свободная недвижимость!</b>\n\n"
                f"🏠 {cell_result['cell_name']}\n"
                f"💰 Цена: {price}$\n"
                f"💵 Ваш баланс: {current_player.balance}$\n\n"
                f"Хотите купить?",
                parse_mode="HTML",
                reply_markup=yes_no_kb(
                    f"buy_{new_pos}",
                    f"skip_{new_pos}"
                )
            )
            return
        
        # Проверяем банкротство
        if game.check_bankruptcy(current_player):
            await message.answer(
                f"💀 <b>БАНКРОТСТВО!</b>\n\n"
                f"{current_player.name} обанкротился!\n"
                f"Игра продолжается...",
                parse_mode="HTML"
            )
        
        # Проверяем окончание игры
        if game.check_game_over():
            winner = game.winner
            await message.answer(
                f"🏆 <b>ИГРА ОКОНЧЕНА!</b>\n\n"
                f"👑 <b>ПОБЕДИТЕЛЬ: {winner.name}</b>\n\n"
                f"💰 Финальный баланс: {winner.balance}$\n"
                f"🎮 Поздравляем победителя!",
                parse_mode="HTML"
            )
            del ACTIVE_GAMES[chat_id]
            return
        
        # Передаем ход, если не было дубля
        if dice1 != dice2:
            game.next_player()
            game.turn += 1
            
            next_player = game.get_current_player()
            await message.answer(
                f"➡️ <b>Следующий ход: {next_player.name}</b>\n"
                f"🔄 Ход: {game.turn}",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в roll_dice_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def build_button(message: types.Message):
    """Кнопка строительства"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Проверяем, есть ли что строить
        can_build = False
        for prop_id in player.properties:
            color = BOARD[prop_id]["color"]
            if player.has_full_set(color):
                can_build = True
                break
        
        if not can_build:
            await message.answer(
                "❌ <b>Нельзя строить дома!</b>\n\n"
                "Для строительства необходимо:\n"
                "1. Иметь все улицы одного цвета\n"
                "2. Не иметь заложенной недвижимости\n"
                "3. Иметь достаточно денег\n\n"
                "Сначала соберите полный набор одного цвета",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            "🏗️ <b>Строительство домов и отелей</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=build_menu_kb(player.properties)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в build_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def mortgage_button(message: types.Message):
    """Кнопка залога"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        if not player.properties:
            await message.answer(
                "❌ <b>Нет недвижимости для залога!</b>\n\n"
                "Сначала купите недвижимость",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            "💸 <b>Залог недвижимости</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=mortgage_menu_kb(
                player.properties,
                player.mortgaged_properties
            )
        )
        
    except Exception as e:
        logger.error(f"Ошибка в mortgage_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def assets_button(message: types.Message):
    """Кнопка активов"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        assets = game.get_player_assets(player)
        
        assets_text = f"💰 <b>Активы {player.name}</b>\n\n"
        assets_text += f"💵 Баланс: <b>{assets['balance']}$</b>\n"
        assets_text += f"📍 Позиция: <b>{assets['position']}</b>\n"
        
        if assets["in_jail"]:
            assets_text += f"⛓️ В тюрьме: ход {assets['jail_turns']}/3\n"
            if assets["get_out_cards"] > 0:
                assets_text += f"🎫 Карт освобождения: {assets['get_out_cards']}\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(assets['properties'])} объектов</b>\n"
        assets_text += f"💰 Общая стоимость: <b>{assets['total_assets']}$</b>\n\n"
        
        if assets["properties"]:
            assets_text += "📋 <b>Ваша недвижимость:</b>\n"
            
            # Группируем по цвету
            by_color = {}
            for prop in assets["properties"]:
                color = prop["color"]
                if color not in by_color:
                    by_color[color] = []
                by_color[color].append(prop)
            
            for color, props in by_color.items():
                color_name = color.replace("_", " ").title()
                assets_text += f"\n🎨 <b>{color_name}:</b>\n"
                
                for prop in props:
                    status = ""
                    if prop["mortgaged"]:
                        status = " 💸 (заложена)"
                    elif prop["hotel"]:
                        status = " 🏨"
                    elif prop["houses"] > 0:
                        status = f" 🏠×{prop['houses']}"
                    
                    assets_text += f"• {prop['name']}{status}\n"
                    assets_text += f"  💰 Стоимость: {prop['value']}$"
                    
                    if not prop["mortgaged"]:
                        assets_text += f" | 🏠 Аренда: {prop['rent']}$"
                    
                    assets_text += "\n"
        
        await message.answer(assets_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в assets_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def trade_button(message: types.Message):
    """Кнопка торговли"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        if len(game.players) < 2:
            await message.answer(
                "❌ <b>Недостаточно игроков для торговли!</b>\n\n"
                "Нужно минимум 2 игрока",
                parse_mode="HTML"
            )
            return
        
        await message.answer(
            "🤝 <b>Торговля с другими игроками</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=trade_menu_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в trade_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def map_button(message: types.Message):
    """Кнопка карты"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("⚠️ Активная игра не найдена!")
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await message.answer("⚠️ Вы не участвуете в этой игре!")
            return
        
        # Получаем позиции всех игроков
        players_positions = {}
        for p in game.players:
            players_positions[p.id] = p.position
        
        await message.answer(
            "🗺️ <b>Карта игрового поля</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=board_map_kb(player.position, players_positions)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в map_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

async def hide_menu_button(message: types.Message):
    """Кнопка скрытия меню"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await message.answer("❌ Нет активной игры!")
            return
        
        # Скрываем меню
        await message.answer(
            "✅ <b>Меню скрыто!</b>\n\n"
            "Теперь используйте кнопки в сообщении ниже.\n"
            "Эти кнопки видны только вам.\n\n"
            "Чтобы вернуть меню, нажмите '📱 Вернуть меню'",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        
        HIDDEN_MENU_USERS[user_id] = chat_id
        await show_inline_menu(message, user_id)
        
    except Exception as e:
        logger.error(f"Ошибка в hide_menu_button: {e}")
        await message.answer(f"🤖 {MAINTENANCE_MSG}")

# ==================== INLINE ОБРАБОТЧИКИ ====================

async def show_inline_menu(message: types.Message, user_id: int):
    """Показать inline меню"""
    try:
        chat_id = message.chat.id
        
        if chat_id not in ACTIVE_GAMES:
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            return
        
        current_player = game.get_current_player()
        is_your_turn = current_player and current_player.id == user_id
        
        turn_info = ""
        if is_your_turn:
            turn_info = "🎯 <b>Сейчас ваш ход!</b>\n"
        else:
            turn_info = f"⏳ <b>Сейчас ходит: {current_player.name}</b>\n"
        
        menu_text = (
            f"🎮 <b>Monopoly Premium - Inline меню</b>\n\n"
            f"👤 Игрок: {player.name}\n"
            f"💰 Баланс: {player.balance}$\n"
            f"{turn_info}\n"
            f"👇 <i>Используйте кнопки ниже:</i>"
        )
        
        await message.answer(
            menu_text,
            parse_mode="HTML",
            reply_markup=inline_menu_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_inline_menu: {e}")

async def inline_roll_dice(callback: CallbackQuery, bot: Bot):
    """Inline бросок кубика"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        current_player = game.get_current_player()
        
        if not current_player or current_player.id != user_id:
            if current_player:
                await callback.answer(f"⏳ Сейчас ходит {current_player.name}!", show_alert=True)
            return
        
        # Имитируем нажатие кнопки броска
        await roll_dice_button(callback.message, bot)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_roll_dice: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def inline_build_menu(callback: CallbackQuery):
    """Inline меню строительства"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.properties:
            await callback.answer("❌ Нет недвижимости!", show_alert=True)
            return
        
        await callback.message.edit_text(
            "🏗️ <b>Строительство домов и отелей</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=build_menu_kb(player.properties)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_build_menu: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def inline_mortgage_menu(callback: CallbackQuery):
    """Inline меню залога"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        await callback.message.edit_text(
            "💸 <b>Залог недвижимости</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=mortgage_menu_kb(
                player.properties,
                player.mortgaged_properties
            )
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_mortgage_menu: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def inline_assets(callback: CallbackQuery):
    """Inline просмотр активов"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        assets = game.get_player_assets(player)
        
        assets_text = f"💰 <b>Активы {player.name}</b>\n\n"
        assets_text += f"💵 Баланс: <b>{assets['balance']}$</b>\n"
        assets_text += f"📍 Позиция: <b>{assets['position']}</b>\n"
        
        if assets["in_jail"]:
            assets_text += f"⛓️ В тюрьме: ход {assets['jail_turns']}/3\n"
        
        assets_text += f"🏠 Недвижимость: <b>{len(assets['properties'])} объектов</b>\n\n"
        
        if assets["properties"]:
            assets_text += "📋 <b>Ваша недвижимость:</b>\n"
            for prop in assets["properties"][:5]:  # Ограничиваем
                status = ""
                if prop["mortgaged"]:
                    status = " 💸"
                elif prop["hotel"]:
                    status = " 🏨"
                elif prop["houses"] > 0:
                    status = f" 🏠×{prop['houses']}"
                
                assets_text += f"• {prop['name']}{status}\n"
        
        if len(assets["properties"]) > 5:
            assets_text += f"• ... и еще {len(assets['properties']) - 5}\n"
        
        assets_text += f"\n💰 <b>Общая стоимость: {assets['total_assets']}$</b>"
        
        await callback.message.edit_text(
            assets_text,
            parse_mode="HTML",
            reply_markup=inline_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_assets: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def inline_trade_menu(callback: CallbackQuery):
    """Inline меню торговли"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        
        if len(game.players) < 2:
            await callback.answer("❌ Недостаточно игроков!", show_alert=True)
            return
        
        await callback.message.edit_text(
            "🤝 <b>Торговля с другими игроками</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=trade_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_trade_menu: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def inline_board_map(callback: CallbackQuery):
    """Inline карта доски"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        players_positions = {}
        for p in game.players:
            players_positions[p.id] = p.position
        
        await callback.message.edit_text(
            "🗺️ <b>Карта игрового поля</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=board_map_kb(player.position, players_positions)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в inline_board_map: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def restore_menu_callback(callback: CallbackQuery, bot: Bot):
    """Вернуть обычное меню"""
    try:
        user_id = callback.from_user.id
        
        if user_id in HIDDEN_MENU_USERS:
            chat_id = HIDDEN_MENU_USERS[user_id]
            
            if chat_id in ACTIVE_GAMES:
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ <b>Обычное меню восстановлено!</b>",
                    parse_mode="HTML",
                    reply_markup=game_main_kb()
                )
            
            del HIDDEN_MENU_USERS[user_id]
            await callback.message.delete()
            await callback.answer("✅ Меню восстановлено")
        else:
            await callback.answer("✅ Меню уже отображается")
        
    except Exception as e:
        logger.error(f"Ошибка в restore_menu_callback: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ ДЛЯ СТРОИТЕЛЬСТВА ====================

async def build_color_menu(callback: CallbackQuery):
    """Строительство на свойствах определенного цвета"""
    try:
        color = callback.data.split("_")[2]
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        # Находим свойства этого цвета
        color_props = [p for p in player.properties 
                      if p in BOARD and BOARD[p]["color"] == color]
        
        if not color_props:
            await callback.answer("❌ Нет свойств этого цвета!", show_alert=True)
            return
        
        kb = InlineKeyboardBuilder()
        
        for prop_id in color_props:
            prop_info = BOARD[prop_id]
            houses = player.houses.get(prop_id, 0)
            
            text = f"{prop_info['name']}"
            if houses == 5:
                text += " 🏨"
            elif houses > 0:
                text += f" 🏠×{houses}"
            
            kb.button(text=text, callback_data=f"build_on_{prop_id}")
        
        kb.button(text="◀️ Назад", callback_data="build_menu")
        kb.adjust(1)
        
        await callback.message.edit_text(
            f"🏗️ <b>Строительство на {color.lower()} свойствах</b>\n\n"
            f"Выберите недвижимость для строительства:",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в build_color_menu: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def build_on_property(callback: CallbackQuery):
    """Строительство на конкретной недвижимости"""
    try:
        prop_id = int(callback.data.split("_")[2])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player or prop_id not in player.properties:
            await callback.answer("❌ Это не ваша недвижимость!", show_alert=True)
            return
        
        if prop_id in player.mortgaged_properties:
            await callback.answer("❌ Недвижимость в залоге!", show_alert=True)
            return
        
        prop_info = BOARD[prop_id]
        current_houses = player.houses.get(prop_id, 0)
        
        text = f"🏗️ <b>Строительство на {prop_info['name']}</b>\n\n"
        text += f"🎨 Цвет: {prop_info['color']}\n"
        text += f"🏠 Текущие дома: {current_houses}/4\n"
        
        if current_houses == 4:
            text += f"🏨 Можно построить отель\n"
            text += f"💰 Стоимость отеля: {prop_info.get('hotel_cost', 50)}$\n"
        elif current_houses < 4:
            text += f"🏠 Можно построить дом\n"
            text += f"💰 Стоимость дома: {prop_info.get('house_cost', 50)}$\n"
        
        text += f"\n💵 Ваш баланс: {player.balance}$"
        
        kb = InlineKeyboardBuilder()
        
        if current_houses < 4:
            kb.button(
                text=f"🏠 Построить дом (+{prop_info.get('house_cost', 50)}$)",
                callback_data=f"do_build_house_{prop_id}"
            )
        
        if current_houses == 4:
            kb.button(
                text=f"🏨 Построить отель (+{prop_info.get('hotel_cost', 50)}$)",
                callback_data=f"do_build_hotel_{prop_id}"
            )
        
        if current_houses > 0:
            sell_price = prop_info.get('house_cost', 50) // 2
            if current_houses == 5:
                sell_price = prop_info.get('hotel_cost', 50) // 2
                kb.button(
                    text=f"🏨 Продать отель (+{sell_price}$)",
                    callback_data=f"sell_hotel_{prop_id}"
                )
            else:
                kb.button(
                    text=f"🏠 Продать дом (+{sell_price}$)",
                    callback_data=f"sell_house_{prop_id}"
                )
        
        kb.button(text="◀️ Назад", callback_data=f"build_color_{prop_info['color']}")
        kb.adjust(1)
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в build_on_property: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def do_build_house(callback: CallbackQuery):
    """Построить дом"""
    try:
        prop_id = int(callback.data.split("_")[3])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        success = game.build_house(player, prop_id)
        
        if success:
            prop_info = BOARD[prop_id]
            new_houses = player.houses.get(prop_id, 0)
            
            await callback.message.edit_text(
                f"✅ <b>Дом построен!</b>\n\n"
                f"🏠 {prop_info['name']}\n"
                f"🏠 Дома: {new_houses}/4\n"
                f"💰 Потрачено: {prop_info.get('house_cost', 50)}$\n"
                f"💵 Новый баланс: {player.balance}$",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось построить дом!</b>\n\n"
                f"Возможные причины:\n"
                f"• Недостаточно денег\n"
                f"• Недвижимость в залоге\n"
                f"• Уже есть отель\n"
                f"• Не все улицы цвета куплены",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в do_build_house: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def sell_house(callback: CallbackQuery):
    """Продать дом"""
    try:
        prop_id = int(callback.data.split("_")[2])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        success = game.sell_house(player, prop_id)
        
        if success:
            prop_info = BOARD[prop_id]
            new_houses = player.houses.get(prop_id, 0)
            refund = prop_info.get('house_cost', 50) // 2
            
            await callback.message.edit_text(
                f"✅ <b>Дом продан!</b>\n\n"
                f"🏠 {prop_info['name']}\n"
                f"🏠 Дома: {new_houses}/4\n"
                f"💰 Получено: {refund}$\n"
                f"💵 Новый баланс: {player.balance}$",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось продать дом!</b>\n\n"
                f"Возможные причины:\n"
                f"• Нет домов на этой недвижимости\n"
                f"• Недвижимость в залоге",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в sell_house: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ ДЛЯ ЗАЛОГА ====================

async def mortgage_properties(callback: CallbackQuery):
    """Выбор недвижимости для залога"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        # Только свободная недвижимость без домов
        free_props = []
        for prop_id in player.properties:
            if (prop_id not in player.mortgaged_properties and 
                player.houses.get(prop_id, 0) == 0):
                free_props.append(prop_id)
        
        if not free_props:
            await callback.message.edit_text(
                "❌ <b>Нет доступной недвижимости для залога!</b>\n\n"
                "Для залога недвижимость должна быть:\n"
                "• Свободной (не в залоге)\n"
                "• Без домов/отелей",
                parse_mode="HTML",
                reply_markup=back_button_kb("mortgage_menu")
            )
            return
        
        kb = InlineKeyboardBuilder()
        
        for prop_id in free_props:
            prop_info = BOARD[prop_id]
            mortgage_value = prop_info.get("mortgage", 0)
            
            kb.button(
                text=f"💸 {prop_info['name']} (+{mortgage_value}$)",
                callback_data=f"do_mortgage_{prop_id}"
            )
        
        kb.button(text="✅ Заложить всё", callback_data="mortgage_all")
        kb.button(text="◀️ Назад", callback_data="mortgage_menu")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "💸 <b>Выберите недвижимость для залога</b>\n\n"
            "При залоге вы получаете половину стоимости недвижимости.\n"
            "Заложенную недвижимость нельзя продавать и строить на ней.",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в mortgage_properties: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def do_mortgage(callback: CallbackQuery):
    """Заложить недвижимость"""
    try:
        prop_id = int(callback.data.split("_")[2])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        success = game.mortgage_property(player, prop_id)
        
        if success:
            prop_info = BOARD[prop_id]
            mortgage_value = prop_info.get("mortgage", 0)
            
            await callback.message.edit_text(
                f"✅ <b>Недвижимость заложена!</b>\n\n"
                f"🏠 {prop_info['name']}\n"
                f"💰 Получено: {mortgage_value}$\n"
                f"💵 Новый баланс: {player.balance}$\n\n"
                f"⚠️ <i>Недвижимость теперь нельзя продавать или строить на ней.</i>",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось заложить недвижимость!</b>\n\n"
                f"Возможные причины:\n"
                f"• Недвижимость уже в залоге\n"
                f"• Есть дома/отели на недвижимости\n"
                f"• Это не ваша недвижимость",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в do_mortgage: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def unmortgage_properties(callback: CallbackQuery):
    """Выбор недвижимости для выкупа"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.mortgaged_properties:
            await callback.message.edit_text(
                "ℹ️ <b>У вас нет заложенной недвижимости</b>",
                parse_mode="HTML",
                reply_markup=back_button_kb("mortgage_menu")
            )
            return
        
        kb = InlineKeyboardBuilder()
        
        for prop_id in player.mortgaged_properties:
            prop_info = BOARD[prop_id]
            mortgage_value = prop_info.get("mortgage", 0)
            unmortgage_cost = int(mortgage_value * 1.1)
            
            kb.button(
                text=f"💰 {prop_info['name']} (-{unmortgage_cost}$)",
                callback_data=f"do_unmortgage_{prop_id}"
            )
        
        kb.button(text="✅ Выкупить всё", callback_data="unmortgage_all")
        kb.button(text="◀️ Назад", callback_data="mortgage_menu")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "💰 <b>Выберите недвижимость для выкупа</b>\n\n"
            "Для выкупа нужно заплатить на 10% больше суммы залога.",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в unmortgage_properties: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def do_unmortgage(callback: CallbackQuery):
    """Выкупить недвижимость из залога"""
    try:
        prop_id = int(callback.data.split("_")[2])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        success = game.unmortgage_property(player, prop_id)
        
        if success:
            prop_info = BOARD[prop_id]
            mortgage_value = prop_info.get("mortgage", 0)
            unmortgage_cost = int(mortgage_value * 1.1)
            
            await callback.message.edit_text(
                f"✅ <b>Недвижимость выкуплена!</b>\n\n"
                f"🏠 {prop_info['name']}\n"
                f"💰 Потрачено: {unmortgage_cost}$\n"
                f"💵 Новый баланс: {player.balance}$\n\n"
                f"✅ <i>Недвижимость теперь можно продавать и строить на ней.</i>",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось выкупить недвижимость!</b>\n\n"
                f"Возможные причины:\n"
                f"• Недостаточно денег\n"
                f"• Недвижимость не в залоге\n"
                f"• Это не ваша недвижимость",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в do_unmortgage: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ ДЛЯ КАРТЫ ====================

async def map_top_row(callback: CallbackQuery):
    """Верхний ряд карты"""
    try:
        top_row = list(range(0, 10))
        
        kb = InlineKeyboardBuilder()
        for pos in top_row:
            if pos in BOARD:
                cell = BOARD[pos]
                emoji = "🏁" if pos == 0 else "🏠" if cell["type"] == "property" else "🎲"
                kb.button(
                    text=f"{emoji} {cell['name'][:12]}",
                    callback_data=f"map_cell_{pos}"
                )
        
        kb.button(text="◀️ Назад к карте", callback_data="board_map")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "⬆️ <b>Верхний ряд (0-9):</b>\n\n"
            "0 - СТАРТ\n1-3 - Коричневые\n4 - Налог\n5 - Ж/д\n6-9 - Голубые",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_top_row: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def map_right_row(callback: CallbackQuery):
    """Правый ряд карты"""
    try:
        right_row = list(range(10, 20))
        
        kb = InlineKeyboardBuilder()
        for pos in right_row:
            if pos in BOARD:
                cell = BOARD[pos]
                emoji = "🚓" if pos == 10 else "🏠" if cell["type"] == "property" else "💡"
                kb.button(
                    text=f"{emoji} {cell['name'][:12]}",
                    callback_data=f"map_cell_{pos}"
                )
        
        kb.button(text="◀️ Назад к карте", callback_data="board_map")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "➡️ <b>Правый ряд (10-19):</b>\n\n"
            "10 - Тюрьма\n11-14 - Розовые\n15 - Ж/д\n16-19 - Оранжевые",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_right_row: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def map_bottom_row(callback: CallbackQuery):
    """Нижний ряд карты"""
    try:
        bottom_row = list(range(20, 30))
        
        kb = InlineKeyboardBuilder()
        for pos in bottom_row:
            if pos in BOARD:
                cell = BOARD[pos]
                emoji = "🅿️" if pos == 20 else "🏠" if cell["type"] == "property" else "💸"
                kb.button(
                    text=f"{emoji} {cell['name'][:12]}",
                    callback_data=f"map_cell_{pos}"
                )
        
        kb.button(text="◀️ Назад к карте", callback_data="board_map")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "⬇️ <b>Нижний ряд (20-29):</b>\n\n"
            "20 - Бесплатная стоянка\n21-24 - Красные\n25 - Ж/д\n26-29 - Желтые",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_bottom_row: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def map_left_row(callback: CallbackQuery):
    """Левый ряд карты"""
    try:
        left_row = list(range(30, 40))
        
        kb = InlineKeyboardBuilder()
        for pos in left_row:
            if pos in BOARD:
                cell = BOARD[pos]
                emoji = "⛓️" if pos == 30 else "🏠" if cell["type"] == "property" else "🎲"
                kb.button(
                    text=f"{emoji} {cell['name'][:12]}",
                    callback_data=f"map_cell_{pos}"
                )
        
        kb.button(text="◀️ Назад к карте", callback_data="board_map")
        kb.adjust(1)
        
        await callback.message.edit_text(
            "⬅️ <b>Левый ряд (30-39):</b>\n\n"
            "30 - В тюрьму\n31-34 - Зеленые\n35 - Ж/д\n37-39 - Темно-синие",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_left_row: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def map_cell_info(callback: CallbackQuery):
    """Информация о клетке"""
    try:
        pos = int(callback.data.split("_")[2])
        
        if pos not in BOARD:
            await callback.answer("❌ Клетка не найдена!", show_alert=True)
            return
        
        cell = BOARD[pos]
        
        info_text = f"🏠 <b>{cell['name']}</b>\n\n"
        info_text += f"📍 Позиция: <b>{pos}</b>\n"
        info_text += f"🎨 Тип: <b>{cell['type']}</b>\n"
        
        if cell["type"] == "property":
            info_text += f"💰 Цена: <b>{cell['price']}$</b>\n"
            info_text += f"🎨 Цвет: <b>{cell['color']}</b>\n"
            info_text += f"🏠 Стоимость дома: <b>{cell.get('house_cost', 50)}$</b>\n"
            info_text += f"🏨 Стоимость отеля: <b>{cell.get('hotel_cost', 50)}$</b>\n"
            info_text += f"💸 Залог: <b>{cell.get('mortgage', 0)}$</b>\n\n"
            
            info_text += "🏠 <b>Арендная плата:</b>\n"
            rents = cell["rent"]
            info_text += f"• Без домов: {rents[0]}$\n"
            info_text += f"• 1 дом: {rents[1]}$\n"
            info_text += f"• 2 дома: {rents[2]}$\n"
            info_text += f"• 3 дома: {rents[3]}$\n"
            info_text += f"• 4 дома: {rents[4]}$\n"
            if len(rents) > 5:
                info_text += f"• Отель: {rents[5]}$\n"
        
        elif cell["type"] == "railroad":
            info_text += f"💰 Цена: <b>{cell['price']}$</b>\n"
            info_text += f"💸 Залог: <b>{cell.get('mortgage', 100)}$</b>\n\n"
            info_text += "🚂 <b>Арендная плата:</b>\n"
            rents = cell["rent"]
            info_text += f"• 1 ж/д: {rents[0]}$\n"
            info_text += f"• 2 ж/д: {rents[1]}$\n"
            info_text += f"• 3 ж/д: {rents[2]}$\n"
            info_text += f"• 4 ж/д: {rents[3]}$\n"
        
        elif cell["type"] == "utility":
            info_text += f"💰 Цена: <b>{cell['price']}$</b>\n"
            info_text += f"💸 Залог: <b>{cell.get('mortgage', 75)}$</b>\n\n"
            info_text += "💡 <b>Арендная плата:</b>\n"
            info_text += "• 1 предприятие: 4×сумма кубиков\n"
            info_text += "• 2 предприятия: 10×сумма кубиков\n"
        
        elif cell["type"] == "tax":
            info_text += f"💸 Сумма налога: <b>{cell['price']}$</b>\n"
        
        elif cell["type"] == "chance":
            info_text += "🎲 <b>Карточка Шанса</b>\n"
            info_text += "При попадании вытягиваете случайную карту\n"
        
        elif cell["type"] == "jail":
            info_text += "🚓 <b>Тюрьма/Посещение</b>\n"
            info_text += "Просто посещаете тюрьму\n"
        
        elif cell["type"] == "go_jail":
            info_text += "⛓️ <b>Идите в тюрьму</b>\n"
            info_text += "Немедленно отправляетесь в тюрьму\n"
        
        elif cell["type"] == "free":
            info_text += "🅿️ <b>Бесплатная стоянка</b>\n"
            info_text += "Отдыхаете, ничего не происходит\n"
        
        elif cell["type"] == "start":
            info_text += "🏁 <b>СТАРТ</b>\n"
            info_text += "Получаете 200$ при прохождении\n"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🗺️ Показать на карте", callback_data=f"map_show_{pos}")
        kb.button(text="◀️ Назад к карте", callback_data="board_map")
        kb.adjust(1)
        
        await callback.message.edit_text(
            info_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_cell_info: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def map_show_position(callback: CallbackQuery):
    """Показать позицию на карте"""
    try:
        pos = int(callback.data.split("_")[2])
        
        if pos not in BOARD:
            await callback.answer("❌ Позиция не найдена!", show_alert=True)
            return
        
        cell = BOARD[pos]
        
        # Создаем простую текстовую карту
        map_text = "🗺️ <b>Позиция на карте</b>\n\n"
        
        # Простая визуализация
        if pos < 10:  # Верхний ряд
            row = ["⬜"] * 10
            row[pos] = "📍"
            map_text += "⬆️ Верхний ряд:\n"
            map_text += " ".join(row) + "\n"
            map_text += f"📍 Вы здесь: {cell['name']} (позиция {pos})"
        
        elif pos < 20:  # Правый ряд
            map_text += "➡️ Правый ряд:\n"
            map_text += f"📍 {cell['name']} (позиция {pos})\n"
            map_text += f"↕️ Между {BOARD[10]['name']} и {BOARD[19]['name']}"
        
        elif pos < 30:  # Нижний ряд
            idx = pos - 20
            row = ["⬜"] * 10
            row[9 - idx] = "📍"  # Инвертируем для правильного отображения
            map_text += "⬇️ Нижний ряд:\n"
            map_text += " ".join(row) + "\n"
            map_text += f"📍 Вы здесь: {cell['name']} (позиция {pos})"
        
        else:  # Левый ряд
            map_text += "⬅️ Левый ряд:\n"
            map_text += f"📍 {cell['name']} (позиция {pos})\n"
            map_text += f"↕️ Между {BOARD[30]['name']} и {BOARD[39]['name']}"
        
        map_text += f"\n\n🎲 <b>Следующий бросок кубиков переместит вас дальше по часовой стрелке</b>"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад", callback_data=f"map_cell_{pos}")
        kb.adjust(1)
        
        await callback.message.edit_text(
            map_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в map_show_position: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ ДЛЯ ТЮРЬМЫ ====================

async def jail_roll_dice(callback: CallbackQuery):
    """Попытка выйти из тюрьмы через дубль"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.in_jail:
            await callback.answer("✅ Вы не в тюрьме!", show_alert=True)
            return
        
        result = game.attempt_jail_escape(player)
        
        if result["success"]:
            await callback.message.edit_text(
                f"✅ <b>Успешный побег!</b>\n\n"
                f"🎲 Кубики: {result['dice1']}-{result['dice2']}\n"
                f"✨ Выпал дубль!\n"
                f"📍 Вы свободны и двигаетесь на {result['dice1']+result['dice2']} клеток",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Неудачная попытка</b>\n\n"
                f"🎲 Кубики: {result['dice1']}-{result['dice2']}\n"
                f"😞 Не дубль\n"
                f"⛓️ Остаетесь в тюрьме",
                parse_mode="HTML",
                reply_markup=jail_menu_kb(
                    player.in_jail,
                    player.get_out_of_jail_cards > 0
                )
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в jail_roll_dice: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def jail_pay_fine(callback: CallbackQuery):
    """Заплатить штраф за выход из тюрьмы"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.in_jail:
            await callback.answer("✅ Вы не в тюрьме!", show_alert=True)
            return
        
        success = game.pay_jail_fine(player)
        
        if success:
            await callback.message.edit_text(
                f"✅ <b>Штраф оплачен!</b>\n\n"
                f"💰 Потрачено: 50$\n"
                f"💵 Новый баланс: {player.balance}$\n"
                f"✅ Вы свободны!",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось оплатить штраф!</b>\n\n"
                f"💰 Нужно: 50$\n"
                f"💵 У вас: {player.balance}$\n\n"
                f"Попробуйте:\n"
                f"• Продать дома\n"
                f"• Заложить недвижимость\n"
                f"• Подождать дубля",
                parse_mode="HTML",
                reply_markup=jail_menu_kb(
                    player.in_jail,
                    player.get_out_of_jail_cards > 0
                )
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в jail_pay_fine: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def jail_use_card(callback: CallbackQuery):
    """Использовать карту освобождения"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.in_jail:
            await callback.answer("✅ Вы не в тюрьме!", show_alert=True)
            return
        
        success = game.use_jail_card(player)
        
        if success:
            await callback.message.edit_text(
                f"✅ <b>Карта использована!</b>\n\n"
                f"🎫 Карт осталось: {player.get_out_of_jail_cards}\n"
                f"✅ Вы свободны!",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Нет карт освобождения!</b>\n\n"
                f"У вас нет карт 'Освобождение из тюрьмы'",
                parse_mode="HTML",
                reply_markup=jail_menu_kb(
                    player.in_jail,
                    player.get_out_of_jail_cards > 0
                )
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в jail_use_card: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def jail_skip_turn(callback: CallbackQuery):
    """Пропустить ход в тюрьме"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_player_by_id(user_id)
        
        if not player:
            await callback.answer("❌ Вы не в игре!", show_alert=True)
            return
        
        if not player.in_jail:
            await callback.answer("✅ Вы не в тюрьме!", show_alert=True)
            return
        
        # Увеличиваем счетчик ходов
        player.jail_turns += 1
        
        if player.jail_turns >= 3:
            # Автоматически платим после 3 ходов
            if player.balance >= 50:
                player.balance -= 50
                player.in_jail = False
                player.jail_turns = 0
                
                await callback.message.edit_text(
                    f"⏰ <b>Третий ход в тюрьме!</b>\n\n"
                    f"💰 Автоматически оплачено: 50$\n"
                    f"💵 Новый баланс: {player.balance}$\n"
                    f"✅ Вы свободны!",
                    parse_mode="HTML",
                    reply_markup=back_button_kb("game")
                )
            else:
                await callback.message.edit_text(
                    f"💀 <b>БАНКРОТСТВО!</b>\n\n"
                    f"⛓️ Три хода в тюрьме\n"
                    f"💰 Нужно 50$, но у вас {player.balance}$\n"
                    f"😞 Вы банкрот",
                    parse_mode="HTML"
                )
                player.bankrupt = True
        else:
            await callback.message.edit_text(
                f"⏳ <b>Ход пропущен</b>\n\n"
                f"⛓️ Ход {player.jail_turns}/3 в тюрьме\n"
                f"➡️ Передаем ход следующему игроку",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
            
            # Передаем ход
            game.next_player()
            game.turn += 1
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в jail_skip_turn: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def jail_rules(callback: CallbackQuery):
    """Правила тюрьмы"""
    try:
        rules_text = (
            "⛓️ <b>Правила тюрьмы в Монополии</b>\n\n"
            "1. <b>Как попасть в тюрьму:</b>\n"
            "• Карточка 'Идите в тюрьму'\n"
            "• Три дубля подряд\n"
            "• Поле 'Идите в тюрьму'\n\n"
            "2. <b>Как выйти из тюрьмы:</b>\n"
            "• <b>Дубль на кубиках</b> (бесплатно)\n"
            "• <b>Заплатить 50$</b> в любой ход\n"
            "• <b>Карта 'Освобождение'</b> (бесплатно)\n"
            "• <b>После 3 ходов</b> платите 50$ и выходите\n\n"
            "3. <b>В тюрьме нельзя:</b>\n"
            "• Получать аренду за свою недвижимость\n"
            "• Строить дома/отели\n"
            "• Торговать недвижимостью\n\n"
            "4. <b>В тюрьме можно:</b>\n"
            "• Получать деньги от других игроков\n"
            "• Участвовать в торгах\n"
            "• Продавать/закладывать имущество"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад", callback_data="jail_menu")
        kb.adjust(1)
        
        await callback.message.edit_text(
            rules_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в jail_rules: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ ПОКУПКИ НЕДВИЖИМОСТИ ====================

async def buy_property(callback: CallbackQuery):
    """Купить недвижимость"""
    try:
        prop_id = int(callback.data.split("_")[1])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_current_player()
        
        if not player or player.id != user_id:
            await callback.answer("❌ Не ваш ход!", show_alert=True)
            return
        
        if prop_id not in BOARD:
            await callback.answer("❌ Недвижимость не найдена!", show_alert=True)
            return
        
        success = game.buy_property(player, prop_id)
        
        if success:
            prop_info = BOARD[prop_id]
            
            await callback.message.edit_text(
                f"✅ <b>Недвижимость куплена!</b>\n\n"
                f"🏠 {prop_info['name']}\n"
                f"💰 Потрачено: {prop_info['price']}$\n"
                f"💵 Новый баланс: {player.balance}$\n\n"
                f"🎨 Цвет: {prop_info['color']}",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
            
            # Проверяем, есть ли полный набор
            color = prop_info["color"]
            if player.has_full_set(color):
                await callback.message.answer(
                    f"🎉 <b>ПОЛНЫЙ НАБОР!</b>\n\n"
                    f"🎨 Вы собрали все {color.lower()} улицы!\n"
                    f"🏗️ Теперь можно строить дома\n"
                    f"💰 Аренда удваивается",
                    parse_mode="HTML"
                )
        else:
            await callback.message.edit_text(
                f"❌ <b>Не удалось купить недвижимость!</b>\n\n"
                f"Возможные причины:\n"
                f"• Недостаточно денег\n"
                f"• Уже куплена другим игроком\n"
                f"• Не ваш ход",
                parse_mode="HTML",
                reply_markup=back_button_kb("game")
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в buy_property: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def skip_property(callback: CallbackQuery):
    """Пропустить покупку недвижимости"""
    try:
        prop_id = int(callback.data.split("_")[1])
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        if chat_id not in ACTIVE_GAMES:
            await callback.answer("❌ Нет активной игры!", show_alert=True)
            return
        
        game = ACTIVE_GAMES[chat_id]
        player = game.get_current_player()
        
        if not player or player.id != user_id:
            await callback.answer("❌ Не ваш ход!", show_alert=True)
            return
        
        prop_info = BOARD.get(prop_id, {})
        
        await callback.message.edit_text(
            f"⏭️ <b>Покупка пропущена</b>\n\n"
            f"🏠 {prop_info.get('name', 'Недвижимость')}\n"
            f"💰 Цена: {prop_info.get('price', 0)}$\n"
            f"💵 Ваш баланс сохранен: {player.balance}$\n\n"
            f"<i>Недвижимость остается в банке для аукциона</i>",
            parse_mode="HTML",
            reply_markup=back_button_kb("game")
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в skip_property: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ РЕЙТИНГА ====================

async async def rating_top_10(callback: CallbackQuery):
    """Топ-10 игроков"""
    try:
        top_players = get_top_players(10)
        
        if not top_players:
            await callback.message.edit_text(
                "🏆 <b>Рейтинг игроков</b>\n\n"
                "📊 Еще никто не играл. Будьте первым!",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        rating_text = "🏆 <b>Топ-10 игроков (все время)</b>\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            
            # Форматируем имя
            name = player["first_name"]
            if len(name) > 15:
                name = name[:12] + "..."
            
            if player["username"]:
                name_display = f"@{player['username']}"
            else:
                name_display = name
            
            games = player["games"]
            wins = player["wins"]
            win_rate = player["win_rate"]
            
            rating_text += (
                f"{medal} <b>{name_display}</b>\n"
                f"   🎮 {games} игр | 🏆 {wins} побед\n"
                f"   📈 Винрейт: {win_rate:.1f}%\n"
            )
        
        await callback.message.edit_text(
            rating_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в rating_top_10: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def rating_my_stats(callback: CallbackQuery):
    """Моя статистика"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in USER_STATS:
            await callback.message.edit_text(
                "📊 <b>Ваша статистика</b>\n\n"
                "🎮 Игр сыграно: <b>0</b>\n"
                "🏆 Побед: <b>0</b>\n"
                "📈 Процент побед: <b>0%</b>\n"
                "💰 Общий выигрыш: <b>0$</b>\n\n"
                "🎯 <b>Ранг: Новичок</b>\n\n"
                "Сыграйте свою первую игру!",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        stats = USER_STATS[user_id]
        games = stats.get("games", 0)
        wins = stats.get("wins", 0)
        total_money = stats.get("total_money", 0)
        
        win_rate = (wins / games * 100) if games > 0 else 0
        
        # Определяем ранг
        if games == 0:
            rank = "Новичок"
            rank_emoji = "🎮"
        elif win_rate >= 60:
            rank = "Чемпион"
            rank_emoji = "👑"
        elif win_rate >= 40:
            rank = "Профи"
            rank_emoji = "🏆"
        elif win_rate >= 20:
            rank = "Игрок"
            rank_emoji = "⭐"
        else:
            rank = "Новичок"
            rank_emoji = "🎮"
        
        # Форматируем дату последней игры
        last_played = stats.get("last_played", "")
        if last_played:
            try:
                from datetime import datetime
                last_dt = datetime.fromisoformat(last_played)
                last_str = last_dt.strftime("%d.%m.%Y %H:%M")
            except:
                last_str = "неизвестно"
        else:
            last_str = "никогда"
        
        stats_text = (
            f"📊 <b>Ваша статистика</b>\n\n"
            f"👤 Игрок: <b>{stats.get('first_name', '')}</b>\n"
            f"🎮 Игр сыграно: <b>{games}</b>\n"
            f"🏆 Побед: <b>{wins}</b>\n"
            f"📈 Процент побед: <b>{win_rate:.1f}%</b>\n"
            f"💰 Общий выигрыш: <b>{total_money}$</b>\n"
            f"📅 Последняя игра: <b>{last_str}</b>\n\n"
            f"{rank_emoji} <b>Ранг: {rank}</b>"
        )
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в rating_my_stats: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def rating_top_wins(callback: CallbackQuery):
    """Топ по победам"""
    try:
        top_players = get_top_players(20)  # Берем больше для сортировки по победам
        
        # Сортируем по победам
        top_players.sort(key=lambda x: x["wins"], reverse=True)
        top_players = top_players[:10]
        
        if not top_players:
            await callback.message.edit_text(
                "🏆 <b>Топ по победам</b>\n\n"
                "📊 Еще никто не выигрывал",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        rating_text = "👑 <b>Топ-10 по победам</b>\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            
            name = player["first_name"]
            if len(name) > 15:
                name = name[:12] + "..."
            
            if player["username"]:
                name_display = f"@{player['username']}"
            else:
                name_display = name
            
            wins = player["wins"]
            games = player["games"]
            
            rating_text += (
                f"{medal} <b>{name_display}</b>\n"
                f"   👑 {wins} побед | 🎮 {games} игр\n"
            )
        
        await callback.message.edit_text(
            rating_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в rating_top_wins: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def rating_top_money(callback: CallbackQuery):
    """Топ по деньгам"""
    try:
        if not USER_STATS:
            await callback.message.edit_text(
                "💰 <b>Топ по деньгам</b>\n\n"
                "📊 Еще никто не играл",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        # Сортируем по total_money
        players_list = []
        for user_id, stats in USER_STATS.items():
            players_list.append({
                "user_id": user_id,
                "username": stats.get("username", ""),
                "first_name": stats.get("first_name", ""),
                "games": stats.get("games", 0),
                "wins": stats.get("wins", 0),
                "total_money": stats.get("total_money", 0)
            })
        
        players_list.sort(key=lambda x: x["total_money"], reverse=True)
        top_players = players_list[:10]
        
        rating_text = "💰 <b>Топ-10 по деньгам</b>\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            
            name = player["first_name"]
            if len(name) > 15:
                name = name[:12] + "..."
            
            if player["username"]:
                name_display = f"@{player['username']}"
            else:
                name_display = name
            
            money = player["total_money"]
            
            rating_text += (
                f"{medal} <b>{name_display}</b>\n"
                f"   💰 {money}$\n"
            )
        
        await callback.message.edit_text(
            rating_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в rating_top_money: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def rating_progress(callback: CallbackQuery):
    """Прогресс игрока"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in USER_STATS:
            await callback.message.edit_text(
                "📈 <b>Прогресс</b>\n\n"
                "У вас еще нет статистики.\n"
                "Сыграйте первую игру!",
                parse_mode="HTML",
                reply_markup=rating_menu_kb()
            )
            return
        
        stats = USER_STATS[user_id]
        games = stats.get("games", 0)
        wins = stats.get("wins", 0)
        
        if games == 0:
            win_rate = 0
        else:
            win_rate = (wins / games) * 100
        
        progress_text = f"📈 <b>Ваш прогресс</b>\n\n"
        progress_text += f"👤 Игрок: <b>{stats.get('first_name', '')}</b>\n"
        progress_text += f"🎮 Сыграно игр: <b>{games}</b>\n"
        progress_text += f"🏆 Побед: <b>{wins}</b>\n"
        progress_text += f"📈 Винрейт: <b>{win_rate:.1f}%</b>\n\n"
        
        # Прогресс до следующего ранга
        if games < 5:
            next_rank = "🎮 Игрок"
            need = f"{5 - games} игр"
            progress_text += f"🎯 <b>До звания 'Игрок':</b> {need}\n"
        elif win_rate < 20:
            next_rank = "⭐ Игрок"
            progress = (win_rate / 20) * 100
            progress_text += f"⭐ <b>До звания 'Игрок':</b> {progress:.1f}%\n"
        elif win_rate < 40:
            next_rank = "🏆 Профи"
            progress = ((win_rate - 20) / 20) * 100
            progress_text += f"🏆 <b>До звания 'Профи':</b> {progress:.1f}%\n"
        elif win_rate < 60:
            next_rank = "👑 Чемпион"
            progress = ((win_rate - 40) / 20) * 100
            progress_text += f"👑 <b>До звания 'Чемпион':</b> {progress:.1f}%\n"
        else:
            next_rank = "👑 Чемпион"
            progress_text += f"👑 <b>Вы достигли максимального звания!</b>\n"
        
        # Визуализация прогресса
        if win_rate < 20:
            bar = "⬜⬜⬜⬜⬜"
        elif win_rate < 40:
            bar = "🟩⬜⬜⬜⬜"
        elif win_rate < 60:
            bar = "🟩🟩⬜⬜⬜"
        else:
            bar = "🟩🟩🟩🟩🟩"
        
        progress_text += f"\n{bar} {win_rate:.1f}%\n\n"
        progress_text += "⬜ Новичок (<20%)\n"
        progress_text += "🟩 Игрок (20-40%)\n"
        progress_text += "🟩🟩 Профи (40-60%)\n"
        progress_text += "🟩🟩🟩 Чемпион (60%+)\n"
        
        await callback.message.edit_text(
            progress_text,
            parse_mode="HTML",
            reply_markup=rating_menu_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в rating_progress: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

# ==================== ОБРАБОТЧИКИ АДМИН ПАНЕЛИ ====================

async def admin_stats(callback: CallbackQuery):
    """Статистика бота"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ADMINS:
            await callback.answer("⛔ Доступ запрещен!", show_alert=True)
            return
        
        # Собираем статистику
        active_games = len(ACTIVE_GAMES)
        waiting_games = len(WAITING_GAMES)
        total_players = len(USER_STATS)
        
        # Считаем активных игроков
        active_players = 0
        for game in ACTIVE_GAMES.values():
            active_players += len(game.players)
        
        for game in WAITING_GAMES.values():
            active_players += len(game["players"])
        
        # Собираем топ игр
        game_stats = []
        for chat_id, game in ACTIVE_GAMES.items():
            game_stats.append({
                "chat_id": chat_id,
                "players": len(game.players),
                "turn": game.turn
            })
        
        stats_text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👑 Администратор: {callback.from_user.first_name}\n\n"
            f"🎮 <b>Игры:</b>\n"
            f"• Активных: {active_games}\n"
            f"• В ожидании: {waiting_games}\n"
            f"• Всего игроков онлайн: {active_players}\n\n"
            f"👥 <b>База данных:</b>\n"
            f"• Зарегистрировано игроков: {total_players}\n"
            f"• Режим обслуживания: {'✅ ВКЛ' if STATS.get('maintenance_mode') else '❌ ВЫКЛ'}\n\n"
        )
        
        if game_stats:
            stats_text += f"🎲 <b>Активные игры:</b>\n"
            for i, game in enumerate(game_stats[:5], 1):
                stats_text += f"{i}. Чат {game['chat_id']}: {game['players']} игроков, ход {game['turn']}\n"
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=admin_panel_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в admin_stats: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def admin_active_games(callback: CallbackQuery):
    """Активные игры"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ADMINS:
            await callback.answer("⛔ Доступ запрещен!", show_alert=True)
            return
        
        if not ACTIVE_GAMES:
            await callback.message.edit_text(
                "🎮 <b>Активные игры</b>\n\n"
                "Нет активных игр",
                parse_mode="HTML",
                reply_markup=admin_panel_kb()
            )
            return
        
        games_text = "🎮 <b>Активные игры</b>\n\n"
        
        for i, (chat_id, game) in enumerate(ACTIVE_GAMES.items(), 1):
            current_player = game.get_current_player()
            cp_name = current_player.name if current_player else "Нет"
            
            games_text += (
                f"<b>Игра {i}:</b>\n"
                f"• Чат ID: <code>{chat_id}</code>\n"
                f"• Игроков: {len(game.players)}\n"
                f"• Ход: {game.turn}\n"
                f"• Текущий игрок: {cp_name}\n"
                f"• Создатель: {game.creator_id}\n"
            )
            
            # Кнопки управления
            kb = InlineKeyboardBuilder()
            kb.button(text="🔄 Обновить", callback_data="admin_active_games")
            kb.button(text="⏹️ Завершить игру", callback_data=f"admin_end_game_{chat_id}")
            kb.button(text="◀️ Назад", callback_data="admin_panel")
            kb.adjust(2, 1)
            
            if i < len(ACTIVE_GAMES):
                games_text += "\n" + "─" * 20 + "\n\n"
        
        await callback.message.edit_text(
            games_text,
            parse_mode="HTML",
            reply_markup=kb.as_markup() if 'kb' in locals() else admin_panel_kb()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в admin_active_games: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def admin_reload_config(callback: CallbackQuery):
    """Перезагрузить конфиг"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ADMINS:
            await callback.answer("⛔ Доступ запрещен!", show_alert=True)
            return
        
        # Перезагружаем конфиг
        from modules.config import load_user_stats
        load_user_stats()
        
        await callback.message.edit_text(
            "🔄 <b>Конфигурация перезагружена!</b>\n\n"
            f"• Статистика игроков: {len(USER_STATS)}\n"
            f"• Активных игр: {len(ACTIVE_GAMES)}\n"
            f"• Ожидающих игр: {len(WAITING_GAMES)}\n\n"
            f"✅ Все данные обновлены",
            parse_mode="HTML",
            reply_markup=admin_panel_kb()
        )
        
        await callback.answer("✅ Конфиг перезагружен")
        
    except Exception as e:
        logger.error(f"Ошибка в admin_reload_config: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

async def admin_toggle_maintenance(callback: CallbackQuery):
    """Переключить режим обслуживания"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ADMINS:
            await callback.answer("⛔ Доступ запрещен!", show_alert=True)
            return
        
        # Переключаем режим
        STATS["maintenance_mode"] = not STATS.get("maintenance_mode", False)
        
        status = "✅ ВКЛЮЧЕН" if STATS["maintenance_mode"] else "❌ ВЫКЛЮЧЕН"
        
        await callback.message.edit_text(
            f"🔧 <b>Режим обслуживания {status}</b>\n\n"
            f"Теперь бот {'не отвечает на команды' if STATS['maintenance_mode'] else 'работает в обычном режиме'}.\n\n"
            f"👑 Изменения вступают в силу немедленно.",
            parse_mode="HTML",
            reply_markup=admin_panel_kb()
        )
        
        await callback.answer(f"Режим обслуживания {status.lower()}")
        
    except Exception as e:
        logger.error(f"Ошибка в admin_toggle_maintenance: {e}")
        await callback.answer(f"🤖 {MAINTENANCE_MSG}", show_alert=True)

