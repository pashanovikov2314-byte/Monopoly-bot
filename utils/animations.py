"""
Dice roll animations and other animations
"""

import random
import asyncio
from typing import Tuple, Optional
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)

async def send_dice_animation(message: Message, user_id: int, chat_id: int) -> Optional[Tuple[int, int]]:
    """
    Отправка анимации броска кубиков (пункт 2)
    Возвращает результат броска (dice1, dice2)
    """
    try:
        # Отправляем начальное сообщение
        msg = await message.answer(
            "🎲 <b>Бросаю кубики...</b>",
            parse_mode="HTML"
        )
        
        # Имитация анимации
        dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        
        for _ in range(3):  # 3 кадра анимации
            await asyncio.sleep(0.3)
            random_faces = random.sample(dice_faces, 2)
            await msg.edit_text(
                f"🎲 <b>Бросаю кубики...</b>\n\n"
                f"{random_faces[0]} {random_faces[1]}",
                parse_mode="HTML"
            )
        
        # Финальный бросок
        await asyncio.sleep(0.5)
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        dice_emojis = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }
        
        # Отправляем результат
        await msg.edit_text(
            f"🎲 <b>Результат броска:</b>\n\n"
            f"{dice_emojis[dice1]} {dice_emojis[dice2]}\n"
            f"Кубики: {dice1} + {dice2} = {dice1 + dice2}\n\n"
            f"{'🎯 Дубль!' if dice1 == dice2 else '➡️ Продолжаем игру'}",
            parse_mode="HTML"
        )
        
        # Логируем бросок
        logger.info(f"Игрок {user_id} бросил кубики: {dice1}+{dice2}={dice1+dice2}")
        
        return dice1, dice2
        
    except Exception as e:
        logger.error(f"Ошибка в анимации кубиков: {e}")
        
        # Отправляем обычный результат без анимации
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        await message.answer(
            f"🎲 <b>Результат броска:</b>\n\n"
            f"Кубики: {dice1} + {dice2} = {dice1 + dice2}",
            parse_mode="HTML"
        )
        
        return dice1, dice2


async def send_loading_animation(message: Message, text: str = "Загрузка..."):
    """Анимация загрузки"""
    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    msg = await message.answer(f"{dots[0]} {text}")
    
    for i in range(10):
        await asyncio.sleep(0.1)
        await msg.edit_text(f"{dots[i % len(dots)]} {text}")
    
    return msg


async def send_countdown(message: Message, seconds: int = 3, text: str = "Начинаем через"):
    """Обратный отсчет"""
    msg = await message.answer(f"{text} {seconds}...")
    
    for i in range(seconds, 0, -1):
        await asyncio.sleep(1)
        await msg.edit_text(f"{text} {i}...")
    
    await msg.edit_text("🎮 Начинаем!")
    return msg


async def send_progress_bar(message: Message, current: int, total: int, 
                           text: str = "Прогресс", bar_length: int = 10):
    """Прогресс бар"""
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    percentage = int(100 * current / total)
    
    await message.answer(
        f"{text}\n"
        f"[{bar}] {percentage}% ({current}/{total})"
    )
