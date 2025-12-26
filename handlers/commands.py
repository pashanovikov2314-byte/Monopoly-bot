from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
import logging

logger = logging.getLogger(__name__)

router = Router()

def is_private_chat(message: Message) -> bool:
    """Проверка, что сообщение в личных сообщениях"""
    return message.chat.type == "private"

def is_group_chat(message: Message) -> bool:
    """Проверка, что сообщение в группе/супергруппе"""
    return message.chat.type in ["group", "supergroup"]

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start - ТОЛЬКО в личных сообщениях"""
    
    if not is_private_chat(message):
        await message.answer(
            "❌ *Команда /start работает только в личных сообщениях с ботом!*\n\n"
            "Для работы в группе используйте команду:\n"
            "🎮 `/monopoly` - главное меню",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "🎮 *Monopoly Premium Bot*\n"
        "👑 *Версия Темного Принца*\n\n"
        "*Приветствую!* Я бот для игры в Monopoly.\n\n"
        "📋 *Как использовать:*\n"
        "1. Добавьте меня в группу\n"
        "2. В группе напишите `/monopoly`\n"
        "3. Начните играть с друзьями!\n\n"
        "👨‍💻 *Создатель:* @Whylovely05 (Темный Принц)\n"
        "🔧 *Статус:* ✅ Активен",
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота в ЛС")

@router.message(Command("monopoly"))
async def cmd_monopoly(message: Message):
    """Главное меню Monopoly - ТОЛЬКО в группе"""
    
    if not is_group_chat(message):
        await message.answer(
            "❌ *Команда /monopoly работает только в группах!*\n\n"
            "Для личного использования:\n"
            "🚀 `/start` - запуск бота\n\n"
            "Добавьте меня в группу и используйте `/monopoly` там.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "🎮 *ГЛАВНОЕ МЕНЮ MONOPOLY*\n"
        "👑 *Премиум версия от Темного Принца*\n\n"
        "*Выберите действие:*\n"
        "🎲 /game - Начать новую игру\n"
        "👥 /join - Присоединиться к игре\n"
        "👤 /profile - Ваш профиль\n"
        "📊 /stats - Статистика\n"
        "⚙️ /settings - Настройки",
        parse_mode="Markdown"
    )
    logger.info(f"Меню Monopoly открыто в группе {message.chat.id}")

@router.message(Command("game"))
async def cmd_game(message: Message):
    """Создание новой игры"""
    await message.answer(
        "🎮 *Создание новой игры...*\n"
        "Игра будет создана через несколько секунд.\n\n"
        "👑 *Система:* Темный Принц",
        parse_mode="Markdown"
    )

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Профиль игрока"""
    user = message.from_user
    await message.answer(
        f"👤 *ПРОФИЛЬ ИГРОКА*\n"
        f"👑 *Система Темного Принца*\n\n"
        f"🏷️ *ID:* `{user.id}`\n"
        f"📛 *Имя:* {user.first_name}\n"
        f"🔗 *Ник:* @{user.username if user.username else '—'}\n\n"
        f"🎮 *Статистика:*\n"
        f"• Сыграно игр: 0\n"
        f"• Побед: 0\n"
        f"• Банк: $15,000",
        parse_mode="Markdown"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика бота"""
    await message.answer(
        "📊 *СТАТИСТИКА БОТА*\n\n"
        "🤖 *Система:*\n"
        "👑 Версия: Темный Принц\n"
        "✅ Статус: Работает\n\n"
        "🎮 *Игры:*\n"
        "• Всего игр: 0\n"
        "• Активных: 0\n"
        "• Игроков: 0\n\n"
        "_Данные обновляются..._",
        parse_mode="Markdown"
    )

def setup_commands(dp, db, hidden_menu_users, stats):
    """Настройка обработчиков команд"""
    dp.include_router(router)
    logger.info("Командные обработчики настроены с проверкой чатов")
