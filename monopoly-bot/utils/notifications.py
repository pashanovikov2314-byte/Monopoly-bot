"""
Notification system for game events
"""

import logging
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)

async def send_notification(bot: Bot, chat_id: int, message: str, 
                           player_ids: Optional[List[int]] = None):
    """Отправить уведомление в чат"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

async def notify_player_turn(bot: Bot, chat_id: int, player_name: str, 
                            player_id: int, is_your_turn: bool = True):
    """Уведомить о ходе игрока"""
    if is_your_turn:
        message = f"🎯 <b>{player_name}, ваш ход!</b>\n\nБросьте кубики!"
    else:
        message = f"⏳ <b>Сейчас ходит {player_name}</b>\n\nОжидайте своего хода."
    
    await send_notification(bot, chat_id, message)

async def notify_game_start(bot: Bot, chat_id: int, players: List[Dict]):
    """Уведомить о начале игры"""
    players_list = "\n".join([f"• {p['name']}" for p in players])
    
    message = (
        f"🎮 <b>Игра началась!</b>\n\n"
        f"<b>Игроки:</b>\n{players_list}\n\n"
        f"💰 Начальный баланс: 1500$\n"
        f"🎲 Первый ход: {players[0]['name'] if players else 'Неизвестно'}"
    )
    
    await send_notification(bot, chat_id, message)

async def notify_trade_offer(bot: Bot, chat_id: int, from_player: str, 
                           to_player: str, offer_details: str):
    """Уведомить о предложении торговли"""
    message = (
        f"🤝 <b>Предложение обмена</b>\n\n"
        f"От: {from_player}\n"
        f"Кому: {to_player}\n\n"
        f"Предложение:\n{offer_details}"
    )
    
    await send_notification(bot, chat_id, message)

async def notify_auction_start(bot: Bot, chat_id: int, property_name: str, 
                              starting_bid: int):
    """Уведомить о начале аукциона"""
    message = (
        f"🔨 <b>Начат аукцион!</b>\n\n"
        f"Собственность: {property_name}\n"
        f"Начальная ставка: ${starting_bid}\n\n"
        f"Делайте ставки!"
    )
    
    await send_notification(bot, chat_id, message)
