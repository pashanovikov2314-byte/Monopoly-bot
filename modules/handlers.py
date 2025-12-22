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
