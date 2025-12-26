from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging
from keyboards.main_keyboards import get_game_keyboard
import secrets

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == 'start_game')
async def start_game_callback(callback: CallbackQuery):
    """Обработка кнопки 'Начать игру'"""
    from handlers.commands import WAITING_GAMES, ACTIVE_GAMES, STATS
    
    user_id = callback.from_user.id
    
    if user_id in WAITING_GAMES:
        await callback.answer('⚠️ Вы уже в очереди на игру!', show_alert=True)
        return
    
    game_id = len(ACTIVE_GAMES) + 1
    WAITING_GAMES[user_id] = {
        'game_id': game_id,
        'players': [user_id],
        'created_at': callback.message.date,
        'status': 'waiting'
    }
    
    await callback.answer('🎮 Игра создана!', show_alert=False)
    await callback.message.answer(
        f'🎮 *Игра #{game_id} создана!*\n'
        f'👥 Ожидание игроков... (1/4)\n\n'
        f'ID игры: {game_id}',
        parse_mode='Markdown',
        reply_markup=get_game_keyboard()
    )
    
    STATS['total_games'] += 1
    logger.info(f'Callback: игра #{game_id} создана пользователем {user_id}')

@router.callback_query(F.data == 'roll_dice')
async def roll_dice_callback(callback: CallbackQuery):
    """Бросить кубики"""
    dice1 = secrets.randbelow(6) + 1
    dice2 = secrets.randbelow(6) + 1
    total = dice1 + dice2
    
    await callback.answer(f'🎲 Выпало: {dice1} + {dice2} = {total}', show_alert=True)
    await callback.message.answer(
        f'🎲 *Бросок кубиков:*\n'
        f'• Первый кубик: {dice1}\n'
        f'• Второй кубик: {dice2}\n'
        f'• Сумма: *{total}*\n\n'
        f'{"🎯 ДУБЛЬ!" if dice1 == dice2 else "➡️ Продолжайте"}',
        parse_mode='Markdown'
    )

@router.callback_query(F.data == 'show_profile')
async def show_profile_callback(callback: CallbackQuery):
    """Показать профиль"""
    user = callback.from_user
    
    await callback.answer('👤 Профиль загружен', show_alert=False)
    await callback.message.answer(
        f'👤 *ПРОФИЛЬ*\n\n'
        f'🏷️ ID: {user.id}\n'
        f'📛 Имя: {user.first_name}\n'
        f'🔗 Ник: @{user.username if user.username else "—"}\n\n'
        f'💰 Начальный капитал: ,000\n'
        f'🎮 Активных игр: 0\n'
        f'🏆 Рейтинг: Новичок',
        parse_mode='Markdown'
    )

@router.callback_query(F.data == 'show_stats')
async def show_stats_callback(callback: CallbackQuery):
    """Показать статистику"""
    from handlers.commands import STATS, ACTIVE_GAMES, WAITING_GAMES
    
    await callback.answer('📊 Статистика', show_alert=False)
    await callback.message.answer(
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'🤖 *Система:*\n'
        f'🎮 Всего игр: {STATS["total_games"]}\n'
        f'⚡ Активных игр: {len(ACTIVE_GAMES)}\n'
        f'⏳ В ожидании: {len(WAITING_GAMES)}\n'
        f'👥 Игроков: {STATS["total_players"]}\n\n'
        f'👑 *Версия:* Темный Принц\n'
        f'✅ *Статус:* Работает',
        parse_mode='Markdown'
    )

@router.callback_query()
async def generic_callback(callback: CallbackQuery):
    """Обработка остальных callback"""
    actions = {
        'join_game': '👥 Присоединиться к игре',
        'open_settings': '⚙️ Настройки',
        'show_help': '❓ Помощь',
        'buy_property': '🏠 Купить собственность',
        'open_bank': '🏦 Банк',
        'trade': '🔄 Обмен',
        'skip_turn': '⏭ Пропуск хода',
        'leave_game': '🚪 Выход из игры'
    }
    
    action_text = actions.get(callback.data, 'Действие')
    await callback.answer(f'{action_text}...', show_alert=False)
    await callback.message.answer(f'🔄 {action_text}')

def setup_callbacks(dp, db, waiting_games, active_games, hidden_menu_users, stats):
    """Настройка callback обработчиков"""
    from handlers.commands import WAITING_GAMES, ACTIVE_GAMES, STATS, HIDDEN_MENU_USERS
    
    # Обновляем глобальные переменные
    WAITING_GAMES.update(waiting_games)
    ACTIVE_GAMES.update(active_games)
    STATS.update(stats)
    HIDDEN_MENU_USERS.update(hidden_menu_users)
    
    dp.include_router(router)
    logger.info('Callback обработчики настроены (оригинальная структура)')
