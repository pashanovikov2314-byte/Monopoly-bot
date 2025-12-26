from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Глобальные переменные как в оригинальном коде
WAITING_GAMES = {}
ACTIVE_GAMES = {}
HIDDEN_MENU_USERS = {}
STATS = {
    \"maintenance_mode\": True,  # По умолчанию включен режим техработ
    \"total_games\": 0,
    \"active_games\": 0,
    \"total_players\": 0
}

ADMINS = [571902217, 123456789]  # ID админов (замени на реальные)
ADMIN_USERNAMES = [\"@Whylovely05\", \"@admin2\"]  # Юзернеймы админов

router = Router()

def is_private_chat(message: Message) -> bool:
    \"\"\"Проверка, что сообщение в личных сообщениях\"\"\"
    return message.chat.type == \"private\"

def is_group_chat(message: Message) -> bool:
    \"\"\"Проверка, что сообщение в группе/супергруппе\"\"\"
    return message.chat.type in [\"group\", \"supergroup\"]

def get_maintenance_message() -> str:
    \"\"\"Сообщение о технических работах\"\"\"
    admins_text = \"\\n\".join([f\"• {admin}\" for admin in ADMIN_USERNAMES])
    return (
        '🔧 *ВЕДУТСЯ ТЕХНИЧЕСКИЕ РАБОТЫ*\\n\\n'
        '👑 *Темный Принц* обновляет бота!\\n\\n'
        '📅 *Примерное время работ:*\\n'
        '• 10-15 минут\\n\\n'
        '👨‍💻 *Администраторы:*\\n'
        f'{admins_text}\\n\\n'
        '_Спасибо за понимание!_'
    )

def get_admin_mention_text() -> str:
    \"\"\"Текст с упоминанием админов\"\"\"
    mentions = \" \".join([f\"{admin}\" for admin in ADMIN_USERNAMES])
    return (
        f'Напишите этим админам, либо же упомяните их в группе '
        f'(если они у вас в группе):\\n{mentions}'
    )

@router.message(CommandStart())
async def cmd_start(message: Message):
    \"\"\"Обработчик команды /start - ТОЛЬКО в личных сообщениях\"\"\"
    
    # Проверяем режим техработ
    if STATS[\"maintenance_mode\"]:
        await message.answer(get_maintenance_message(), parse_mode='Markdown')
        return
    
    # Проверяем что это личные сообщения
    if not is_private_chat(message):
        await message.answer(
            '❌ *Команда /start работает только в личных сообщениях с ботом!*\\n\\n'
            'Для работы в группе используйте команду:\\n'
            '🎮 /monopoly - главное меню',
            parse_mode='Markdown'
        )
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Сохраняем как в оригинальном коде
    HIDDEN_MENU_USERS[user_id] = chat_id
    
    await message.answer(
        '🎮 *Monopoly Premium Bot*\\n'
        '👑 *Версия Темного Принца*\\n\\n'
        '*Приветствую!* Я бот для игры в Monopoly.\\n\\n'
        '📋 *Как использовать:*\\n'
        '1. Добавьте меня в группу\\n'
        '2. В группе напишите /monopoly\\n'
        '3. Начните играть с друзьями!\\n\\n'
        '👨‍💻 *Создатель:* @Whylovely05 (Темный Принц)\\n'
        '🔧 *Статус:* ✅ Активен',
        parse_mode='Markdown'
    )
    logger.info(f'Пользователь {user_id} запустил бота в ЛС {chat_id}')

@router.message(Command('monopoly'))
async def cmd_monopoly(message: Message):
    \"\"\"Главное меню Monopoly - ТОЛЬКО в группе\"\"\"
    
    # Проверяем режим техработ
    if STATS[\"maintenance_mode\"]:
        await message.answer(get_maintenance_message(), parse_mode='Markdown')
        
        # Добавляем текст про админов
        await message.answer(get_admin_mention_text())
        return
    
    # Проверяем что это группа
    if not is_group_chat(message):
        await message.answer(
            '❌ *Команда /monopoly работает только в группах!*\\n\\n'
            'Для личного использования:\\n'
            '🚀 /start - запуск бота\\n\\n'
            'Добавьте меня в группу и используйте /monopoly там.',
            parse_mode='Markdown'
        )
        return
    
    from keyboards.main_keyboards import get_main_menu
    
    await message.answer(
        '🎮 *ГЛАВНОЕ МЕНЮ MONOPOLY*\\n'
        '👑 *Премиум версия от Темного Принца*\\n\\n'
        '*Выберите действие:*',
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )
    logger.info(f'Меню Monopoly открыто в группе {message.chat.id}')

@router.message(Command('game'))
async def cmd_game(message: Message):
    \"\"\"Создание новой игры - работает везде\"\"\"
    
    if STATS[\"maintenance_mode\"]:
        await message.answer(get_maintenance_message(), parse_mode='Markdown')
        await message.answer(get_admin_mention_text())
        return
    
    user_id = message.from_user.id
    
    if user_id in WAITING_GAMES:
        await message.answer('⚠️ Вы уже в очереди на игру!')
        return
    
    # Создаем новую игру
    game_id = len(ACTIVE_GAMES) + 1
    WAITING_GAMES[user_id] = {
        'game_id': game_id,
        'players': [user_id],
        'created_at': message.date,
        'status': 'waiting',
        'chat_id': message.chat.id
    }
    
    await message.answer(
        f'🎮 *Игра #{game_id} создана!*\\n'
        f'👑 *Организатор:* Темный Принц\\n\\n'
        f'👥 *Ожидание игроков...* (1/4)\\n'
        f'🆔 *ID игры:* {game_id}\\n'
        f'💬 *Чат:* {message.chat.title if hasattr(message.chat, \"title\") else \"ЛС\"}',
        parse_mode='Markdown'
    )
    
    STATS['total_games'] += 1
    logger.info(f'Создана игра #{game_id} пользователем {user_id}')

@router.message(Command('profile'))
async def cmd_profile(message: Message):
    \"\"\"Профиль игрока\"\"\"
    
    if STATS[\"maintenance_mode\"]:
        await message.answer(get_maintenance_message(), parse_mode='Markdown')
        return
    
    user = message.from_user
    
    await message.answer(
        f'👤 *ПРОФИЛЬ ИГРОКА*\\n'
        f'👑 *Система Темного Принца*\\n\\n'
        f'🏷️ *ID:* {user.id}\\n'
        f'📛 *Имя:* {user.first_name}\\n'
        f'🔗 *Ник:* @{user.username if user.username else \"—\"}\\n\\n'
        f'🎮 *Статистика:*\\n'
        f'• Сыграно игр: 0\\n'
        f'• Побед: 0\\n'
        f'• Банк: ,000\\n\\n'
        f'_Данные обновляются..._',
        parse_mode='Markdown'
    )

@router.message(Command('status'))
async def cmd_status(message: Message):
    \"\"\"Проверка статуса бота\"\"\"
    status_text = \"🔧 *ВЕДУТСЯ ТЕХНИЧЕСКИЕ РАБОТЫ*\" if STATS[\"maintenance_mode\"] else \"✅ *БОТ АКТИВЕН*\" 
    
    await message.answer(
        f'{status_text}\\n\\n'
        f'👑 *Система:* Темный Принц\\n'
        f'🎮 *Всего игр:* {STATS[\"total_games\"]}\\n'
        f'⚡ *Активных игр:* {len(ACTIVE_GAMES)}\\n'
        f'👥 *Игроков онлайн:* {STATS[\"total_players\"]}\\n\\n'
        f'💬 *Чат ID:* {message.chat.id}\\n'
        f'👤 *Ваш ID:* {message.from_user.id}',
        parse_mode='Markdown'
    )
    
    if STATS[\"maintenance_mode\"]:
        await message.answer(get_admin_mention_text())

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    \"\"\"Информация об админах\"\"\"
    if message.from_user.id not in ADMINS:
        await message.answer('❌ У вас нет прав для этой команды!')
        return
    
    # Команды для админов
    if len(message.text.split()) > 1:
        action = message.text.split()[1]
        if action == 'toggle_maintenance':
            STATS[\"maintenance_mode\"] = not STATS[\"maintenance_mode\"]
            status = \"ВКЛЮЧЕН\" if STATS[\"maintenance_mode\"] else \"ВЫКЛЮЧЕН\"
            await message.answer(f'🔧 Режим техработ: *{status}*', parse_mode='Markdown')
            logger.info(f'Админ {message.from_user.id} изменил режим техработ на {status}')
    
    await message.answer(
        f'👑 *ПАНЕЛЬ АДМИНИСТРАТОРА*\\n\\n'
        f'*Доступные команды:*\\n'
        f'• /admin toggle_maintenance - переключить режим техработ\\n\\n'
        f'*Текущий статус:*\\n'
        f'• Техработы: {\"ВКЛ\" if STATS[\"maintenance_mode\"] else \"ВЫКЛ\"}\\n'
        f'• Активных игр: {len(ACTIVE_GAMES)}\\n'
        f'• Всего игр: {STATS[\"total_games\"]}',
        parse_mode='Markdown'
    )

def setup_commands(dp, db, hidden_menu_users, stats):
    \"\"\"Настройка обработчиков команд\"\"\"
    # Обновляем глобальные переменные
    global HIDDEN_MENU_USERS, STATS
    HIDDEN_MENU_USERS = hidden_menu_users
    STATS = stats
    
    dp.include_router(router)
    logger.info('Командные обработчики настроены с проверкой чатов')
