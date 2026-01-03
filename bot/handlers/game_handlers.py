"""Обработчики игровых действий"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.core.game_logic import get_game

logger = logging.getLogger(__name__)

# ===== КОМАНДЫ ДЛЯ ИГРЫ =====
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новую игру"""
    query = update.callback_query
    await query.answer()
    
    game = get_game()
    user = update.effective_user
    
    # Добавляем игрока
    player = game.add_player(user.id, user.first_name)
    
    keyboard = [
        [InlineKeyboardButton("🎲 Бросить кубики", callback_data='roll_dice')],
        [InlineKeyboardButton("📊 Статус игры", callback_data='game_status')],
        [InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
🎮 *ИГРА НАЧАТА!*

👤 Игрок: {user.first_name}
💰 Баланс: ${player['balance']}
🎯 Позиция: Старт

*Доступные действия:*
• 🎲 Бросить кубики - сделать ход
• 💵 Купить участок - если на свободной клетке
• 🏗️ Строить - при наличии комплекта

👇 *Ваш ход!*"""
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def roll_dice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Бросок кубиков"""
    query = update.callback_query
    await query.answer()
    
    game = get_game()
    dice1, dice2, total = game.roll_dice()
    
    # Двигаем игрока
    result = game.move_player(0, total)
    
    current_player = game.players[0]
    current_cell = game.board[current_player["position"]]
    
    message = f"""
🎲 *БРОСОК КУБИКОВ*

🎯 Результат: {dice1} + {dice2} = {total}
📍 Новая позиция: {current_cell['name']}

💰 Баланс: ${current_player['balance']}"""
    
    if result["passed_go"]:
        message += f"\n✨ Прошли СТАРТ! +${result['bonus']}"
    
    # Проверяем что на клетке
    if current_cell["type"] == "property" and current_cell["id"] not in current_player["properties"]:
        message += f"\n\n🏠 *СВОБОДНЫЙ УЧАСТОК!*\nЦена: ${current_cell['price']}"
        
        keyboard = [
            [InlineKeyboardButton("💵 Купить", callback_data=f'buy_{current_cell["id"]}')],
            [InlineKeyboardButton("❌ Отказаться", callback_data='skip_buy')],
            [InlineKeyboardButton("🎲 Бросить еще раз", callback_data='roll_dice')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎲 Следующий ход", callback_data='next_turn')],
            [InlineKeyboardButton("📊 Статус", callback_data='game_status')],
            [InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_menu')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def buy_property_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка недвижимости"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем ID собственности из callback_data (например: 'buy_1')
    property_id = int(query.data.split('_')[1])
    
    game = get_game()
    success = game.buy_property(0, property_id)
    
    if success:
        player = game.players[0]
        property_data = next((p for p in game.board if p["id"] == property_id), None)
        
        message = f"""
✅ *УЧАСТОК КУПЛЕН!*

🏠 {property_data['name']}
💰 Стоимость: ${property_data['price']}
📊 Ваш баланс: ${player['balance']}

🎉 Поздравляем с приобретением!"""
    else:
        message = "❌ *Не удалось купить участок*\nНедостаточно средств!"
    
    keyboard = [
        [InlineKeyboardButton("🎲 Продолжить игру", callback_data='roll_dice')],
        [InlineKeyboardButton("📊 Статус игры", callback_data='game_status')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def game_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус игры"""
    query = update.callback_query
    await query.answer()
    
    game = get_game()
    player = game.players[0] if game.players else None
    
    if not player:
        message = "❌ *Игра не начата*\nНажмите /start чтобы начать!"
    else:
        # Получаем информацию об игроке
        player_info = game.get_player_info(0)
        
        message = f"""
📊 *СТАТУС ИГРЫ*

👤 Игрок: {player_info['name']}
💰 Баланс: ${player_info['balance']}
📍 Позиция: клетка {player_info['position']}
🏠 Владений: {player_info['properties_count']}
{"🚓 В тюрьме" if player_info['in_jail'] else "✅ Свободен"}

🎯 *Ваши владения:*"""
        
        # Показываем собственность игрока
        for prop_id in player["properties"]:
            prop = next((p for p in game.board if p["id"] == prop_id), None)
            if prop:
                message += f"\n• {prop['name']} (${prop['price']})"
    
    keyboard = [
        [InlineKeyboardButton("🎲 Продолжить игру", callback_data='roll_dice')],
        [InlineKeyboardButton("🏁 Завершить игру", callback_data='end_game')],
        [InlineKeyboardButton("👁️ Скрыть меню", callback_data='hide_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===== РЕГИСТРАЦИЯ ИГРОВЫХ ОБРАБОТЧИКОВ =====
def register_game_handlers(application):
    """Регистрация игровых обработчиков"""
    application.add_handler(CallbackQueryHandler(start_game, pattern='^single$'))
    application.add_handler(CallbackQueryHandler(start_game, pattern='^multi$'))
    application.add_handler(CallbackQueryHandler(start_game, pattern='^fast$'))
    application.add_handler(CallbackQueryHandler(roll_dice_handler, pattern='^roll_dice$'))
    application.add_handler(CallbackQueryHandler(buy_property_handler, pattern='^buy_\d+$'))
    application.add_handler(CallbackQueryHandler(game_status_handler, pattern='^game_status$'))
    
    logger.info("✅ Игровые обработчики зарегистрированы")
