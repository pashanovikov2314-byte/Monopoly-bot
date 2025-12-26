"""Обработчики игровых действий"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

from game.game_engine import MonopolyGame, create_new_game, get_game, active_games
from keyboards.game_keyboards import (
    get_game_reply_keyboard, get_game_inline_keyboard,
    get_bank_keyboard, get_mortgage_keyboard,
    get_build_keyboard, get_trade_keyboard,
    get_confirm_keyboard, get_game_info_keyboard,
    remove_game_keyboard
)
from keyboards.keyboard_system import get_main_reply_keyboard

logger = logging.getLogger(__name__)

game_router = Router()

# Хранилище игровых сессий
game_sessions: Dict[int, Dict] = {}  # user_id -> {game_id, last_action}

# ========== ОБРАБОТКА REPLY КНОПОК В ИГРЕ ==========

@game_router.message(F.text == "🎲 БРОСИТЬ КУБИКИ")
async def handle_game_roll_dice(message: Message):
    """Бросок кубиков в игре"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        del game_sessions[user_id]
        return
    
    # Проверяем ход игрока
    current_player = game.get_current_player()
    if not current_player or current_player.user_id != user_id:
        await message.answer("⏳ Сейчас не ваш ход!")
        return
    
    try:
        # Бросаем кубики
        dice1, dice2, is_double = game.roll_dice(user_id)
        
        # Получаем информацию о позиции
        pos_info = game.get_current_position_info(user_id)
        
        # Формируем сообщение
        dice_text = f"🎲 *Бросок кубиков:* {dice1} + {dice2} = **{dice1 + dice2}**"
        
        if is_double:
            dice_text += "\n🎯 *ДУБЛЬ!* Вы бросаете еще раз!"
        
        position_text = f"\n\n📍 *Вы на:* {pos_info['property_name']}"
        
        # Проверяем нужно ли платить аренду
        if pos_info['owner'] and pos_info['owner'] != user_id:
            rent = pos_info['rent']
            player = game.players[user_id]
            owner = game.players[pos_info['owner']]
            
            if player.balance >= rent:
                player.balance -= rent
                owner.balance += rent
                rent_text = f"\n💸 *Аренда:* -${rent} → {owner.username}"
            else:
                rent_text = f"\n💀 *БАНКРОТСТВО!* Не можете оплатить аренду ${rent}"
        else:
            rent_text = ""
        
        # Проверяем можно ли купить
        buy_text = ""
        if pos_info['can_buy']:
            buy_text = f"\n💰 *Можно купить за:* ${pos_info['price']}"
        
        # Отправляем полное сообщение
        response = dice_text + position_text + rent_text + buy_text
        
        await message.answer(response, parse_mode="Markdown")
        
        # Обновляем клавиатуру
        await message.answer(
            "🎮 *Ваш ход продолжается...*" if is_double else "➡️ *Ход переходит к следующему игроку*",
            parse_mode="Markdown",
            reply_markup=get_game_reply_keyboard(game, user_id)
        )
        
        # Если не дубль - следующий ход
        if not is_double:
            game.next_turn()
            
            # Уведомляем следующего игрока
            next_player = game.get_current_player()
            if next_player:
                try:
                    await message.bot.send_message(
                        chat_id=next_player.user_id,
                        text=f"🎮 *Ваш ход в игре #{game.id}!*",
                        parse_mode="Markdown",
                        reply_markup=get_game_reply_keyboard(game, next_player.user_id)
                    )
                except:
                    pass  # Игрок может быть offline
        
        # Обновляем время последнего действия
        game_sessions[user_id]["last_action"] = datetime.now()
        
    except Exception as e:
        logger.error(f"Ошибка при броске кубиков: {e}")
        await message.answer("❌ Ошибка при броске кубиков!")

@game_router.message(F.text == "🏠 КУПИТЬ НЕДВИЖИМОСТЬ")
async def handle_buy_property(message: Message):
    """Покупка недвижимости"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    # Проверяем ход игрока
    current_player = game.get_current_player()
    if not current_player or current_player.user_id != user_id:
        await message.answer("⏳ Сейчас не ваш ход!")
        return
    
    # Получаем информацию о позиции
    pos_info = game.get_current_position_info(user_id)
    
    if not pos_info["can_buy"]:
        await message.answer("❌ Эту недвижимость нельзя купить!")
        return
    
    # Пытаемся купить
    if game.buy_property(user_id):
        player = game.players[user_id]
        
        await message.answer(
            f"✅ *Покупка успешна!*\n"
            f"🏠 *Недвижимость:* {pos_info['property_name']}\n"
            f"💰 *Цена:* ${pos_info['price']}\n"
            f"💵 *Новый баланс:* ${player.balance}",
            parse_mode="Markdown"
        )
        
        # Обновляем клавиатуру
        await message.answer(
            "🎮 *Продолжайте ваш ход...*",
            parse_mode="Markdown",
            reply_markup=get_game_reply_keyboard(game, user_id)
        )
    else:
        await message.answer("❌ Недостаточно средств для покупки!")

@game_router.message(F.text == "🏦 ОТКРЫТЬ БАНК")
async def handle_open_bank(message: Message):
    """Открыть банк"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    
    await message.answer(
        "🏦 *БАНК MONOPOLY*\n\n"
        "💰 *Операции:*\n"
        "• Получить $200 за проход через Старт\n"
        "• Взять кредит под 10%\n"
        "• Внести деньги на депозит\n"
        "• Проверить баланс\n\n"
        "*Используйте кнопки ниже для операций:*",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "💳 УПРАВЛЕНИЕ ЗАЛОГОМ")
async def handle_mortgage_menu(message: Message):
    """Меню залога"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    player = game.players.get(user_id)
    if not player:
        await message.answer("❌ Вы не в этой игре!")
        return
    
    # Получаем недвижимость игрока
    player_props = []
    for i, prop in enumerate(game.board):
        if prop.owner == user_id:
            player_props.append({
                "id": i,
                "name": prop.name,
                "price": prop.price,
                "mortgage_value": prop.price // 2,
                "is_mortgaged": prop.is_mortgaged
            })
    
    if not player_props:
        await message.answer("❌ У вас нет недвижимости для залога!")
        return
    
    prop_list = "\n".join([
        f"• {p['name']}: ${p['price']} (залог: ${p['mortgage_value']})"
        for p in player_props[:5]
    ])
    
    await message.answer(
        f"💳 *ВАША НЕДВИЖИМОСТЬ*\n\n{prop_list}\n\n"
        f"*Выберите недвижимость для залога или выкупа:*",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "🔄 ПРЕДЛОЖИТЬ СДЕЛКУ")
async def handle_trade_offer(message: Message):
    """Предложение сделки"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    # Получаем других игроков
    other_players = []
    for pid, player in game.players.items():
        if pid != user_id and not player.is_bankrupt:
            other_players.append({
                "id": pid,
                "name": player.username,
                "balance": player.balance
            })
    
    if not other_players:
        await message.answer("❌ Нет других игроков для торговли!")
        return
    
    players_list = "\n".join([
        f"• {p['name']} (${p['balance']})"
        for p in other_players[:3]
    ])
    
    await message.answer(
        f"🔄 *ТОРГОВЛЯ С ИГРОКАМИ*\n\n{players_list}\n\n"
        f"*Выберите игрока для сделки:*",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "🏗️ ПОСТРОИТЬ ДОМ")
async def handle_build_house(message: Message):
    """Построить дом"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    player = game.players.get(user_id)
    if not player:
        await message.answer("❌ Вы не в этой игре!")
        return
    
    # Получаем улицы где можно строить
    buildable_props = []
    for i, prop in enumerate(game.board):
        if prop.owner == user_id and not prop.is_mortgaged:
            # Проверяем что игрок владеет всей группой
            group_props = [p for p in game.board if p.group == prop.group]
            if all(p.owner == user_id for p in group_props):
                build_price = prop.price // 2
                buildable_props.append({
                    "id": i,
                    "name": prop.name,
                    "price": prop.price,
                    "build_price": build_price,
                    "houses": prop.houses,
                    "max_houses": 5
                })
    
    if not buildable_props:
        await message.answer("❌ У вас нет улиц для строительства!")
        return
    
    houses_list = "\n".join([
        f"• {p['name']}: {p['houses']}/5 домов (${p['build_price']} за дом)"
        for p in buildable_props[:4]
    ])
    
    await message.answer(
        f"🏗️ *СТРОИТЕЛЬСТВО ДОМОВ*\n\n{houses_list}\n\n"
        f"*Выберите улицу для строительства:*",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "⏭️ ЗАКОНЧИТЬ ХОД")
async def handle_end_turn(message: Message):
    """Завершить ход"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    # Проверяем ход игрока
    current_player = game.get_current_player()
    if not current_player or current_player.user_id != user_id:
        await message.answer("⏳ Сейчас не ваш ход!")
        return
    
    # Переходим к следующему ходу
    game.next_turn()
    
    await message.answer(
        "✅ *Ход завершен!*\n➡️ *Ход переходит к следующему игроку*",
        parse_mode="Markdown"
    )
    
    # Уведомляем следующего игрока
    next_player = game.get_current_player()
    if next_player:
        try:
            await message.bot.send_message(
                chat_id=next_player.user_id,
                text=f"🎮 *Ваш ход в игре #{game.id}!*",
                parse_mode="Markdown",
                reply_markup=get_game_reply_keyboard(game, next_player.user_id)
            )
        except:
            pass  # Игрок может быть offline

@game_router.message(F.text == "👀 НАБЛЮДАТЬ ЗА ИГРОЙ")
async def handle_spectate_game(message: Message):
    """Наблюдать за игрой"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    # Получаем информацию об игре
    game_state = game.get_game_state()
    current_player = game.get_current_player()
    
    player_list = "\n".join([
        f"• {player.username}: ${player.balance}"
        for player in game.players.values() if not player.is_bankrupt
    ])
    
    await message.answer(
        f"👀 *НАБЛЮДЕНИЕ ЗА ИГРОЙ #{game.id}*\n\n"
        f"🎮 *Текущий ход:* {current_player.username if current_player else 'Нет'}\n"
        f"📊 *Ход номер:* {game_state['turn_number']}\n"
        f"⏱️ *Длительность:* {game_state['duration']} сек\n\n"
        f"👥 *Игроки:*\n{player_list}",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "📊 СТАТИСТИКА ИГРЫ")
async def handle_game_stats(message: Message):
    """Статистика игры"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    game_state = game.get_game_state()
    
    # Сортируем игроков по балансу
    sorted_players = sorted(
        [p for p in game.players.values() if not p.is_bankrupt],
        key=lambda x: x.balance,
        reverse=True
    )
    
    leaderboard = "\n".join([
        f"{i+1}. {player.username}: ${player.balance}"
        for i, player in enumerate(sorted_players[:5])
    ])
    
    # Подсчитываем недвижимость
    property_stats = {}
    for prop in game.board:
        if prop.owner and prop.price > 0:
            owner_name = game.players[prop.owner].username
            if owner_name not in property_stats:
                property_stats[owner_name] = 0
            property_stats[owner_name] += 1
    
    property_text = "\n".join([
        f"• {name}: {count} объектов"
        for name, count in list(property_stats.items())[:3]
    ]) if property_stats else "• Недвижимость не куплена"
    
    await message.answer(
        f"📊 *СТАТИСТИКА ИГРЫ #{game.id}*\n\n"
        f"🏆 *Лидеры:*\n{leaderboard}\n\n"
        f"🏠 *Недвижимость:*\n{property_text}\n\n"
        f"🎮 *Активных игроков:* {game_state['active_players']}\n"
        f"⏱️ *Время игры:* {game_state['duration']} сек",
        parse_mode="Markdown"
    )

@game_router.message(F.text == "📋 ИНФОРМАЦИЯ ОБ ИГРЕ")
async def handle_game_info(message: Message):
    """Информация об игре"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        return
    
    current_player = game.get_current_player()
    pos_info = game.get_current_position_info(user_id) if user_id in game.players else {}
    
    info_text = (
        f"🎮 *ИГРА #{game.id}*\n\n"
        f"👑 *Создатель:* {game.players[game.creator_id].username}\n"
        f"🎯 *Текущий ход:* {current_player.username if current_player else 'Нет'}\n"
        f"👥 *Игроков:* {len(game.players)}\n"
        f"📅 *Начата:* {game.start_time.strftime('%H:%M') if game.start_time else 'Не начата'}\n"
    )
    
    # Если игрок в игре - добавляем его информацию
    if user_id in game.players:
        player = game.players[user_id]
        info_text += (
            f"\n👤 *ВАША ИНФОРМАЦИЯ:*\n"
            f"💰 *Баланс:* ${player.balance}\n"
            f"📍 *Позиция:* {pos_info.get('property_name', 'Неизвестно')}\n"
            f"🏠 *Недвижимость:* {len(player.properties)} объектов\n"
            f"🎯 *Ваш порядок хода:* {player.order + 1}\n"
        )
    
    await message.answer(info_text, parse_mode="Markdown")

@game_router.message(F.text == "🚪 ВЫЙТИ ИЗ ИГРЫ")
async def handle_leave_game(message: Message):
    """Выйти из игры"""
    user_id = message.from_user.id
    
    if user_id not in game_sessions:
        await message.answer("❌ Вы не в игре!")
        return
    
    game_id = game_sessions[user_id]["game_id"]
    game = get_game(game_id)
    
    if not game:
        await message.answer("❌ Игра не найдена!")
        del game_sessions[user_id]
        return
    
    # Удаляем игрока из игры
    if user_id in game.players:
        player_name = game.players[user_id].username
        game.remove_player(user_id)
        
        # Уведомляем других игроков
        for pid in game.players:
            if pid != user_id:
                try:
                    await message.bot.send_message(
                        chat_id=pid,
                        text=f"⚠️ *Игрок {player_name} вышел из игры!*",
                        parse_mode="Markdown"
                    )
                except:
                    pass
    
    # Удаляем сессию
    del game_sessions[user_id]
    
    await message.answer(
        "🚪 *Вы вышли из игры!*\n\n"
        "⬅️ *Возвращаемся в главное меню...*",
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard()
    )
    
    # Проверяем остались ли игроки в игре
    if len(game.players) < 2:
        # Завершаем игру если остался 1 игрок или меньше
        winner_id = next(iter(game.players.keys())) if game.players else None
        if winner_id:
            winner_name = game.players[winner_id].username
            for pid in game.players:
                try:
                    await message.bot.send_message(
                        chat_id=pid,
                        text=f"🏆 *Игра завершена! Победитель: {winner_name}!*",
                        parse_mode="Markdown",
                        reply_markup=get_main_reply_keyboard()
                    )
                except:
                    pass
        
        # Удаляем игру
        if game_id in active_games:
            del active_games[game_id]

# ========== ОБРАБОТКА CALLBACK КНОПОК ИГРЫ ==========

@game_router.callback_query(F.data.startswith("game:"))
async def handle_game_callback(callback: CallbackQuery):
    """Обработка игровых callback кнопок"""
    data_parts = callback.data.split(":")
    
    if len(data_parts) < 3:
        await callback.answer("❌ Ошибка в данных кнопки")
        return
    
    action = data_parts[2]
    game_id = int(data_parts[1])
    
    # Всегда отвечаем на callback (100% отклик)
    await callback.answer(f"⏳ Обрабатываем: {action}...")
    
    game = get_game(game_id)
    if not game:
        await callback.message.answer("❌ Игра не найдена!")
        return
    
    user_id = callback.from_user.id
    
    # Проверяем что пользователь в этой игре
    if user_id not in game.players:
        await callback.message.answer("❌ Вы не участник этой игры!")
        return
    
    if action == "roll_dice":
        await handle_game_roll_dice_callback(callback, game, user_id)
    elif action == "buy_property":
        await handle_buy_property_callback(callback, game, user_id)
    elif action == "bank":
        await handle_bank_callback(callback, game, user_id)
    elif action == "end_turn":
        await handle_end_turn_callback(callback, game, user_id)
    elif action == "leave":
        await handle_leave_callback(callback, game, user_id)
    elif action == "info":
        await handle_game_info_callback(callback, game)
    elif action == "players":
        await handle_players_list_callback(callback, game)
    elif action == "spectate":
        await handle_spectate_callback(callback, game, user_id)
    elif action == "stats":
        await handle_stats_callback(callback, game)
    elif action == "back_to_game":
        await handle_back_to_game(callback, game, user_id)

async def handle_game_roll_dice_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для броска кубиков"""
    try:
        dice1, dice2, is_double = game.roll_dice(user_id)
        pos_info = game.get_current_position_info(user_id)
        
        response = (
            f"🎲 *Бросок кубиков:* {dice1} + {dice2} = **{dice1 + dice2}**\n"
            f"📍 *Позиция:* {pos_info['property_name']}\n"
        )
        
        if is_double:
            response += "🎯 *ДУБЛЬ!* Бросайте еще раз!"
        
        await callback.message.answer(response, parse_mode="Markdown")
        
        if not is_double:
            game.next_turn()
            
    except Exception as e:
        logger.error(f"Ошибка в callback броска кубиков: {e}")
        await callback.message.answer("❌ Ошибка при броске кубиков!")

async def handle_buy_property_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для покупки недвижимости"""
    pos_info = game.get_current_position_info(user_id)
    
    if game.buy_property(user_id):
        player = game.players[user_id]
        await callback.message.answer(
            f"✅ *Куплено:* {pos_info['property_name']}\n"
            f"💰 *За:* ${pos_info['price']}\n"
            f"💵 *Баланс:* ${player.balance}",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer("❌ Не удалось купить недвижимость!")

async def handle_bank_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для банка"""
    await callback.message.answer(
        "🏦 *Выберите операцию:*",
        parse_mode="Markdown"
    )

async def handle_end_turn_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для завершения хода"""
    game.next_turn()
    await callback.message.answer("✅ *Ход завершен!*", parse_mode="Markdown")

async def handle_leave_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для выхода из игры"""
    game.remove_player(user_id)
    await callback.message.answer(
        "🚪 *Вы вышли из игры!*",
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard()
    )

async def handle_game_info_callback(callback: CallbackQuery, game: MonopolyGame):
    """Callback для информации об игре"""
    game_state = game.get_game_state()
    await callback.message.answer(
        f"🎮 *Игра #{game.id}*\n"
        f"👥 Игроков: {game_state['players_count']}\n"
        f"📊 Ход: {game_state['turn_number']}",
        parse_mode="Markdown"
    )

async def handle_players_list_callback(callback: CallbackQuery, game: MonopolyGame):
    """Callback для списка игроков"""
    players_list = "\n".join([
        f"• {player.username}: ${player.balance}"
        for player in game.players.values()
    ])
    
    await callback.message.answer(
        f"👥 *Игроки:*\n{players_list}",
        parse_mode="Markdown"
    )

async def handle_spectate_callback(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Callback для наблюдения"""
    current_player = game.get_current_player()
    await callback.message.answer(
        f"👀 *Наблюдение*\n"
        f"🎯 Сейчас ходит: {current_player.username if current_player else 'Нет'}",
        parse_mode="Markdown"
    )

async def handle_stats_callback(callback: CallbackQuery, game: MonopolyGame):
    """Callback для статистики"""
    game_state = game.get_game_state()
    await callback.message.answer(
        f"📊 *Статистика игры*\n"
        f"⏱️ Длительность: {game_state['duration']}с\n"
        f"👥 Активных: {game_state['active_players']}",
        parse_mode="Markdown"
    )

async def handle_back_to_game(callback: CallbackQuery, game: MonopolyGame, user_id: int):
    """Вернуться к игре"""
    await callback.message.answer(
        "🎮 *Возврат к игре...*",
        parse_mode="Markdown",
        reply_markup=get_game_reply_keyboard(game, user_id)
    )
