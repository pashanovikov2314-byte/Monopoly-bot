"""
Обработчики callback-кнопок
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные из callback
    data = query.data
    
    # Обрабатываем разные типы callback
    if data.startswith('buy_'):
        property_id = data.split('_')[1]
        await query.edit_message_text(f'Покупка собственности {property_id}...')
    elif data.startswith('roll_'):
        await query.edit_message_text('Бросаем кубики...')
    else:
        await query.edit_message_text(f'Нажата кнопка: {data}')
