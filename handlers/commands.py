from aiogram import types
from aiogram.dispatcher import FSMContext
from core.beautiful_design import BeautifulDesign

async def cmd_start(message: types.Message, state: FSMContext):
    """Красивая команда старта"""
    await state.finish()
    
    # Используем новый дизайн
    welcome_text = BeautifulDesign.welcome_message(message.from_user)
    keyboard = BeautifulDesign.create_main_menu()
    
    # Отправляем стилизованное сообщение
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def cmd_help(message: types.Message):
    """Красивая справка"""
    help_text = BeautifulDesign.notification("info", 
        """Для начала игры нажмите "Новая игра"
        
Управление в игре:
• 🎲 Бросить кубики - сделать ход
• 💵 Купить участок - приобрести клетку
• 🏗️ Строить - строить дома/отели
• 💳 Торговать - обмен с другими игроками

Специальные команды:
• 👁️ Скрыть меню - убрать кнопки
• ✨ Показать меню - вернуть кнопки
• 📱 Компактный вид - минималистичный интерфейс

По всем вопросам: @support""")
    
    await message.answer(help_text, parse_mode="HTML")

async def cmd_stats(message: types.Message):
    """Красивая статистика"""
    # Пример данных статистики
    stats = {
        "total_games": 15,
        "wins": 8,
        "max_balance": 2500000,
        "avg_time": 25,
        "trades": 12,
        "houses": 7,
        "hotels": 2,
        "achievements": ["Первый миллион", "Владелец 5 участков", "Торговый магнат"],
        "rank": 42
    }
    
    stats_text = BeautifulDesign.create_stats_display(stats)
    await message.answer(stats_text, parse_mode="HTML")
