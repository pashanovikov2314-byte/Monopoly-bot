"""
Text button handlers for game controls
"""

import logging
from typing import Dict, Any
from aiogram import Dispatcher, types, F
from aiogram.types import Message
import random

from config import MAINTENANCE_MSG
from keyboards.game_keyboards import (
    get_reply_keyboard_for_text,
    game_main_kb,
    dice_roll_kb,
    build_menu_kb,
    bank_menu_kb,
    trade_menu_kb,
    assets_menu_kb,
    map_menu_kb,
    jail_menu_kb,
    stats_menu_kb
)
from database import db
from core.security import request_logger
from utils.animations import send_dice_animation

logger = logging.getLogger(__name__)

def setup_text_handlers(dp: Dispatcher, db, active_games: Dict[int, Any]):
    """Настройка обработчиков текстовых кнопок"""
    
    @dp.message(F.text == "❌ Скрыть меню")
    async def hide_menu_button(message: Message):
        """Кнопка скрытия меню"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем, есть ли активная игра
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры для скрытия меню!</b>",
                    parse_mode="HTML"
                )
                return
            
            # Скрываем меню и показываем inline меню
            from handlers.commands import show_inline_menu
            await show_inline_menu(message)
            
            await message.answer(
                "✅ <b>Меню скрыто!</b>\n\n"
                "Используйте inline кнопки для управления игрой.",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в hide_menu_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🎲 Бросить кубик")
    async def roll_dice_button(message: Message):
        """Кнопка броска кубиков"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>\n\n"
                    "Сначала начните игру через /monopoly",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем, чей ход
            current_idx = game_state.get("current_player", 0)
            player_ids = list(game_state.get("players", {}).keys())
            
            if not player_ids:
                await message.answer("❌ Ошибка: нет игроков в игре!")
                return
            
            current_player_id = player_ids[current_idx]
            if str(user_id) != current_player_id:
                # Получаем имя текущего игрока
                players = game_state.get("players", {})
                current_player = players.get(current_player_id, {})
                player_name = current_player.get("name", "Неизвестно")
                
                await message.answer(
                    f"⏳ <b>Сейчас ходит {player_name}!</b>\n"
                    f"Ждите своего хода.",
                    parse_mode="HTML"
                )
                return
            
            # Показываем меню броска
            await message.answer(
                "🎲 <b>Бросок кубиков</b>\n\n"
                "Выберите тип броска:",
                parse_mode="HTML",
                reply_markup=dice_roll_kb(user_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в roll_dice_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🎲 Бросить кубики (1-й бросок)")
    async def roll_dice_first(message: Message):
        """Первый бросок кубиков"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Отправляем анимацию кубиков (пункт 2)
            dice_result = await send_dice_animation(message, user_id, chat_id)
            
            if dice_result:
                dice1, dice2 = dice_result
                total = dice1 + dice2
                is_double = dice1 == dice2
                
                # Обновляем игру
                game_state = await db.get_game_state(chat_id)
                if game_state:
                    # Двигаем игрока
                    players = game_state.get("players", {})
                    player = players.get(str(user_id), {})
                    current_position = player.get("position", 0)
                    new_position = (current_position + total) % 40
                    
                    # Обновляем позицию
                    players[str(user_id)]["position"] = new_position
                    game_state["players"] = players
                    
                    # Если дубль - даем еще ход
                    if is_double:
                        game_state["double_count"] = game_state.get("double_count", 0) + 1
                        
                        # Если 3 дубля подряд - в тюрьму
                        if game_state.get("double_count", 0) >= 3:
                            players[str(user_id)]["is_in_jail"] = True
                            players[str(user_id)]["jail_turns"] = 0
                            await message.answer(
                                f"🎲 <b>Три дубля подряд!</b>\n\n"
                                f"Вы отправляетесь в тюрьму!",
                                parse_mode="HTML"
                            )
                        else:
                            await message.answer(
                                f"🎲 <b>Выпал дубль!</b>\n\n"
                                f"Кубики: {dice1} + {dice2} = {total}\n"
                                f"Вы ходите еще раз!",
                                parse_mode="HTML"
                            )
                    else:
                        # Сбрасываем счетчик дублей
                        game_state["double_count"] = 0
                        
                        # Передаем ход следующему игроку
                        current_idx = game_state.get("current_player", 0)
                        player_count = len(players)
                        next_idx = (current_idx + 1) % player_count
                        game_state["current_player"] = next_idx
                        
                        # Получаем имя следующего игрока
                        next_player_id = list(players.keys())[next_idx]
                        next_player = players[next_player_id]
                        
                        await message.answer(
                            f"🎲 <b>Результат броска:</b>\n\n"
                            f"Кубики: {dice1} + {dice2} = {total}\n"
                            f"Новая позиция: {new_position}\n\n"
                            f"🎯 <b>Следующий ход: {next_player['name']}</b>",
                            parse_mode="HTML"
                        )
                    
                    # Сохраняем состояние игры
                    await db.update_game_state(chat_id, game_state)
            
            # Возвращаем основное меню
            await message.answer(
                "Выберите действие:",
                reply_markup=game_main_kb()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в roll_dice_first: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🏠 Построить")
    async def build_button(message: Message):
        """Кнопка управления недвижимостью"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            # Получаем свойства игрока
            players = game_state.get("players", {})
            player = players.get(str(user_id), {})
            properties = player.get("properties", [])
            
            if not properties:
                await message.answer(
                    "🏠 <b>У вас нет недвижимости!</b>\n\n"
                    "Купите улицы, чтобы строить дома.",
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                "🏠 <b>Управление недвижимостью</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=build_menu_kb(properties, user_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в build_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "💰 Банк")
    async def bank_button(message: Message):
        """Кнопка банковских операций"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                "💰 <b>Банковские операции</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=bank_menu_kb(user_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в bank_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🤝 Торговля")
    async def trade_button(message: Message):
        """Кнопка торговли"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            # Получаем список игроков
            players = game_state.get("players", {})
            game_players = [
                {
                    "id": pid,
                    "name": p["name"],
                    "balance": p.get("balance", 0),
                    "is_bankrupt": p.get("is_bankrupt", False)
                }
                for pid, p in players.items()
                if pid != str(user_id) and not p.get("is_bankrupt", False)
            ]
            
            if not game_players:
                await message.answer(
                    "🤝 <b>Нет игроков для торговли!</b>\n\n"
                    "Дождитесь других игроков или они все банкроты.",
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                "🤝 <b>Торговля с игроками</b>\n\n"
                "Выберите действие:",
                parse_mode="HTML",
                reply_markup=trade_menu_kb(game_players, user_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в trade_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "📊 Мои активы")
    async def assets_button(message: Message):
        """Кнопка моих активов"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            # Получаем данные игрока
            players = game_state.get("players", {})
            player = players.get(str(user_id), {})
            
            properties = player.get("properties", [])
            balance = player.get("balance", 0)
            position = player.get("position", 0)
            
            properties_text = "\n".join([
                f"• {prop['name']}" + 
                (f" (🏠×{prop.get('houses', 0)})" if prop.get('houses', 0) > 0 else "") +
                (f" (🏨)" if prop.get('hotel', False) else "") +
                (f" [💸 заложено]" if prop.get('is_mortgaged', False) else "")
                for prop in properties
            ]) if properties else "Нет недвижимости"
            
            await message.answer(
                f"📊 <b>Мои активы</b>\n\n"
                f"💰 Баланс: ${balance:,}\n"
                f"📍 Позиция: {position}\n\n"
                f"<b>Недвижимость:</b>\n{properties_text}\n\n"
                f"Выберите действие:",
                parse_mode="HTML",
                reply_markup=assets_menu_kb(user_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в assets_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🗺️ Карта игры")
    async def map_button(message: Message):
        """Кнопка карты игры"""
        try:
            chat_id = message.chat.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                "🗺️ <b>Карта игры</b>\n\n"
                "Выберите тип карты:",
                parse_mode="HTML",
                reply_markup=map_menu_kb(chat_id, chat_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в map_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "🏛️ Тюрьма")
    async def jail_button(message: Message):
        """Кнопка тюрьмы"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем, в тюрьме ли игрок
            players = game_state.get("players", {})
            player = players.get(str(user_id), {})
            
            if not player.get("is_in_jail", False):
                await message.answer(
                    "🏛️ <b>Вы не в тюрьме!</b>\n\n"
                    "Эта кнопка только для игроков в тюрьме.",
                    parse_mode="HTML"
                )
                return
            
            turns_in_jail = player.get("jail_turns", 0)
            has_jail_card = player.get("has_jail_card", False)
            
            await message.answer(
                f"🏛️ <b>Тюрьма</b>\n\n"
                f"Вы в тюрьме {turns_in_jail}/3 хода\n\n"
                f"Выберите действие:",
                parse_mode="HTML",
                reply_markup=jail_menu_kb(user_id, turns_in_jail, has_jail_card)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в jail_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "📈 Статистика")
    async def stats_button(message: Message):
        """Кнопка статистики"""
        try:
            chat_id = message.chat.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await message.answer(
                    "❌ <b>Нет активной игры!</b>",
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                "📈 <b>Статистика игры</b>\n\n"
                "Выберите что показать:",
                parse_mode="HTML",
                reply_markup=stats_menu_kb(chat_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в stats_button: {e}")
            await message.answer(f"🤖 {MAINTENANCE_MSG}")
    
    @dp.message(F.text == "⬅️ Назад в меню")
    async def back_to_main_menu(message: Message):
        """Возврат в главное меню игры"""
        await message.answer(
            "Возврат в главное меню:",
            reply_markup=game_main_kb()
        )
    
    logger.info("✅ Текстовые обработчики зарегистрированы")
