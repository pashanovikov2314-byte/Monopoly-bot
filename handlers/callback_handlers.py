from aiogram import types
from aiogram.dispatcher import FSMContext
from core.beautiful_design import BeautifulDesign

async def handle_hide_menu(callback: types.CallbackQuery, state: FSMContext):
    """Скрыть меню"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Меню скрыто 👁️")

async def handle_show_menu(callback: types.CallbackQuery, state: FSMContext):
    """Показать меню"""
    keyboard = BeautifulDesign.create_main_menu()
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Меню показано ✨")

async def handle_new_game(callback: types.CallbackQuery, state: FSMContext):
    """Новая игра с красивым интерфейсом"""
    # Пример данных игры
    game_data = {
        "cells": [
            {"name": "СТАРТ", "type": "go"},
            {"name": "Балтийская", "type": "property"},
            {"name": "Казна", "type": "community"},
            {"name": "Вокзал", "type": "railroad"}
        ],
        "balance": 1500000,
        "properties": 0
    }
    
    game_text = BeautifulDesign.game_board_display(game_data, player_position=1)
    game_keyboard = BeautifulDesign.create_game_interface({})
    
    await callback.message.edit_text(
        game_text,
        reply_markup=game_keyboard,
        parse_mode="HTML"
    )
    await callback.answer("Игра началась! 🎲")

async def handle_refresh(callback: types.CallbackQuery, state: FSMContext):
    """Обновить интерфейс"""
    await callback.answer("Интерфейс обновлен! 🔄")

async def handle_compact_view(callback: types.CallbackQuery, state: FSMContext):
    """Компактный вид"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Включен компактный вид 📱")

# Регистрируем обработчики для нового дизайна
def register_beautiful_handlers(dp):
    dp.register_callback_query_handler(handle_hide_menu, text="hide_menu")
    dp.register_callback_query_handler(handle_hide_menu, text="hide_game_menu")
    dp.register_callback_query_handler(handle_show_menu, text="show_menu")
    dp.register_callback_query_handler(handle_new_game, text="new_game")
    dp.register_callback_query_handler(handle_refresh, text="refresh")
    dp.register_callback_query_handler(handle_compact_view, text="compact_view")
