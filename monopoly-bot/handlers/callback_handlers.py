"""
Callback query handlers for inline keyboards
"""

import logging
import asyncio
from typing import Dict, Any
from aiogram import Dispatcher, types, F
from aiogram.types import CallbackQuery
from datetime import datetime

from config import MAINTENANCE_MSG, DEV_TAG
from keyboards.main_keyboards import (
    main_menu_kb,
    waiting_room_kb,
    inline_menu_kb,
    confirm_kb
)
from keyboards.game_keyboards import (
    properties_menu_kb,
    trade_menu_kb,
    jail_menu_kb,
    mortgage_menu_kb,
    bank_menu_kb
)
from database import db
from core.security import request_logger
from utils.animations import send_dice_animation

logger = logging.getLogger(__name__)

def setup_callbacks(
    dp: Dispatcher, 
    waiting_games: Dict[int, Any],
    active_games: Dict[int, Any],
    hidden_menu_users: Dict[int, int],
    stats: Dict[str, Any]
):
    """Настройка обработчиков callback запросов"""
    
    @dp.callback_query(F.data == "show_rules")
    async def show_rules(callback: CallbackQuery):
        """Показать правила игры"""
        try:
            rules_text = """
🎮 <b>Правила Monopoly Premium</b>

<b>Цель игры:</b>
Стать единственным необанкротившимся игроком, скупив всю недвижимость.

<b>Начало игры:</b>
• Каждый игрок получает 1500$
• Игроки ходят по очереди
• При прохождении "Старта" получают 200$

<b>Покупка недвижимости:</b>
• Если выпало на пустую улицу - можно купить
• Если не покупаете - начинается аукцион
• Можно строить дома и отели при владении всем цветом

<b>Тюрьма:</b>
• Попадаете, если выпало на поле "Тюрьма"
• Или если три дубля подряд
• Можно выйти за 50$ или карточкой

<b>Банкротство:</b>
• Если не можете оплатить долг
• Имущество переходит кредитору
• Игрок выбывает из игры

👑 <i>Версия Темного Принца</i>
            """
            
            await callback.message.edit_text(
                rules_text,
                parse_mode="HTML",
                reply_markup=confirm_kb("back", "back_to_main", "back_to_main")
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в show_rules: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data == "show_developer")
    async def show_developer(callback: CallbackQuery):
        """Показать информацию о разработчике"""
        try:
            dev_text = f"""
👑 <b>Темный Принц</b>

<b>Monopoly Premium Bot</b>
Версия 2.5 (Premium Edition)

<b>Особенности:</b>
• Полная реализация правил Монополии
• Интерактивная карта игры
• Торговля между игроками
• Система рейтинга
• Защита от DDoS атак
• Веб-интерфейс для управления

<b>Контакты:</b>
Telegram: {DEV_TAG}

<b>Поддержка:</b>
Если нашли баг или есть предложения - пишите!

❤️ Спасибо за игру!
            """
            
            await callback.message.edit_text(
                dev_text,
                parse_mode="HTML",
                reply_markup=confirm_kb("back", "back_to_main", "back_to_main")
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в show_developer: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data == "start_player_gathering")
    async def start_player_gathering(callback: CallbackQuery):
        """Начать сбор игроков"""
        try:
            if stats.get("maintenance_mode", False):
                await callback.answer(MAINTENANCE_MSG, show_alert=True)
                return
            
            chat_id = callback.message.chat.id
            user_id = callback.from_user.id
            
            # Проверяем, не идет ли уже сбор
            waiting_game = await db.get_waiting_game(chat_id)
            if waiting_game:
                await callback.answer("❌ Сбор игроков уже начат!", show_alert=True)
                return
            
            # Проверяем, нет ли активной игры
            game_state = await db.get_game_state(chat_id)
            if game_state and game_state.get("game_state") == "active":
                await callback.answer("❌ Игра уже идет!", show_alert=True)
                return
            
            # Создаем лобби
            message = await callback.message.answer(
                f"👥 <b>Сбор игроков начат!</b>\n\n"
                f"Создатель: {callback.from_user.first_name}\n"
                f"Игроков: 1/8\n"
                f"Автостарт через 3 минуты...\n\n"
                f"👇 Нажмите 'Присоединиться' чтобы войти",
                parse_mode="HTML"
            )
            
            # Сохраняем в БД
            await db.create_waiting_game(
                chat_id=chat_id,
                creator_id=user_id,
                message_id=message.message_id,
                settings={"max_players": 8, "min_players": 2}
            )
            
            # Добавляем создателя в список игроков
            await db.add_player_to_waiting_game(
                chat_id=chat_id,
                user_id=user_id,
                username=callback.from_user.username or "",
                first_name=callback.from_user.first_name
            )
            
            # Обновляем сообщение с кнопками
            await message.edit_reply_markup(
                reply_markup=waiting_room_kb(chat_id, is_creator=True)
            )
            
            await callback.answer("✅ Сбор игроков начат!")
            
            # Логируем
            request_logger.log_request(
                user_id=user_id,
                chat_id=chat_id,
                message_type="callback",
                text="start_player_gathering"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в start_player_gathering: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data.startswith("join_game_"))
    async def join_game(callback: CallbackQuery):
        """Присоединиться к игре"""
        try:
            if stats.get("maintenance_mode", False):
                await callback.answer(MAINTENANCE_MSG, show_alert=True)
                return
            
            chat_id = int(callback.data.split("_")[2])
            user_id = callback.from_user.id
            
            # Получаем лобби
            waiting_game = await db.get_waiting_game(chat_id)
            if not waiting_game:
                await callback.answer("❌ Лобби не найдено!", show_alert=True)
                return
            
            # Проверяем, не полное ли лобби
            players = waiting_game.get("players", [])
            if len(players) >= 8:
                await callback.answer("❌ Лобби заполнено!", show_alert=True)
                return
            
            # Проверяем, не присоединился ли уже
            if any(p["id"] == user_id for p in players):
                await callback.answer("❌ Вы уже в лобби!", show_alert=True)
                return
            
            # Добавляем игрока
            success = await db.add_player_to_waiting_game(
                chat_id=chat_id,
                user_id=user_id,
                username=callback.from_user.username or "",
                first_name=callback.from_user.first_name
            )
            
            if not success:
                await callback.answer("❌ Ошибка присоединения!", show_alert=True)
                return
            
            # Обновляем сообщение лобби
            players_count = len(players) + 1
            is_creator = waiting_game["creator_id"] == user_id
            
            # Получаем обновленный список игроков
            updated_game = await db.get_waiting_game(chat_id)
            updated_players = updated_game.get("players", [])
            
            # Формируем список игроков
            players_list = "\n".join([
                f"• {p['name']}" + (" 👑" if p['id'] == waiting_game["creator_id"] else "")
                for p in updated_players
            ])
            
            await callback.message.edit_text(
                f"👥 <b>Сбор игроков</b>\n\n"
                f"Создатель: {callback.from_user.first_name if is_creator else 'Неизвестно'}\n"
                f"Игроков: {len(updated_players)}/8\n"
                f"Автостарт через 3 минуты...\n\n"
                f"<b>Игроки:</b>\n{players_list}\n\n"
                f"👇 Нажмите 'Присоединиться' чтобы войти",
                parse_mode="HTML"
            )
            
            # Обновляем кнопки (кнопки не убираются - исправление пункта 6)
            await callback.message.edit_reply_markup(
                reply_markup=waiting_room_kb(chat_id, is_creator=is_creator)
            )
            
            await callback.answer(f"✅ Вы присоединились! Игроков: {players_count}/8")
            
            # Логируем
            request_logger.log_request(
                user_id=user_id,
                chat_id=chat_id,
                message_type="callback",
                text=f"join_game_{chat_id}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в join_game: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data.startswith("leave_game_"))
    async def leave_game(callback: CallbackQuery):
        """Выйти из лобби"""
        try:
            chat_id = int(callback.data.split("_")[2])
            user_id = callback.from_user.id
            
            # Удаляем игрока
            success = await db.remove_player_from_waiting_game(chat_id, user_id)
            
            if not success:
                await callback.answer("❌ Вы не в лобби!", show_alert=True)
                return
            
            # Получаем обновленное лобби
            waiting_game = await db.get_waiting_game(chat_id)
            
            if not waiting_game:
                # Если лобби пустое - удаляем
                await callback.message.delete()
                await callback.answer("✅ Вы вышли из лобби")
                return
            
            # Обновляем сообщение
            updated_players = waiting_game.get("players", [])
            is_creator = waiting_game["creator_id"] == user_id
            
            players_list = "\n".join([
                f"• {p['name']}" + (" 👑" if p['id'] == waiting_game["creator_id"] else "")
                for p in updated_players
            ]) if updated_players else "Нет игроков"
            
            await callback.message.edit_text(
                f"👥 <b>Сбор игроков</b>\n\n"
                f"Создатель: {'Вы' if is_creator else 'Неизвестно'}\n"
                f"Игроков: {len(updated_players)}/8\n"
                f"Автостарт через 3 минуты...\n\n"
                f"<b>Игроки:</b>\n{players_list}\n\n"
                f"👇 Нажмите 'Присоединиться' чтобы войти",
                parse_mode="HTML"
            )
            
            # Обновляем кнопки (кнопки остаются - исправление пункта 6)
            await callback.message.edit_reply_markup(
                reply_markup=waiting_room_kb(chat_id, is_creator=is_creator)
            )
            
            await callback.answer("✅ Вы вышли из лобби")
            
        except Exception as e:
            logger.error(f"Ошибка в leave_game: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data.startswith("start_real_game_"))
    async def start_real_game(callback: CallbackQuery):
        """Начать реальную игру из лобби"""
        try:
            if stats.get("maintenance_mode", False):
                await callback.answer(MAINTENANCE_MSG, show_alert=True)
                return
            
            chat_id = int(callback.data.split("_")[3])
            user_id = callback.from_user.id
            
            # Проверяем, является ли пользователь создателем
            waiting_game = await db.get_waiting_game(chat_id)
            if not waiting_game:
                await callback.answer("❌ Лобби не найдено!", show_alert=True)
                return
            
            if waiting_game["creator_id"] != user_id:
                await callback.answer("❌ Только создатель может начать игру!", show_alert=True)
                return
            
            # Проверяем минимальное количество игроков
            players = waiting_game.get("players", [])
            if len(players) < 2:
                await callback.answer("❌ Нужно минимум 2 игрока!", show_alert=True)
                return
            
            # Запускаем игру
            game_id = await db.start_game_from_waiting(chat_id)
            
            if not game_id:
                await callback.answer("❌ Ошибка запуска игры!", show_alert=True)
                return
            
            # Удаляем сообщение лобби
            await callback.message.delete()
            
            # Отправляем сообщение о начале игры
            players_list = "\n".join([f"• {p['name']}" for p in players])
            
            await callback.message.answer(
                f"🎮 <b>Игра началась!</b>\n\n"
                f"<b>Игроки:</b>\n{players_list}\n\n"
                f"💰 Начальный баланс: 1500$\n"
                f"🎲 Первый ход: {players[0]['name']}\n\n"
                f"👇 Используйте кнопки ниже для игры",
                parse_mode="HTML"
            )
            
            await callback.answer("✅ Игра началась!")
            
            # Логируем
            request_logger.log_request(
                user_id=user_id,
                chat_id=chat_id,
                message_type="callback",
                text=f"start_real_game_{chat_id}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в start_real_game: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data.startswith("cancel_gathering_"))
    async def cancel_gathering(callback: CallbackQuery):
        """Отменить сбор игроков"""
        try:
            chat_id = int(callback.data.split("_")[2])
            user_id = callback.from_user.id
            
            # Проверяем, является ли пользователь создателем
            waiting_game = await db.get_waiting_game(chat_id)
            if not waiting_game:
                await callback.answer("❌ Лобби не найдено!", show_alert=True)
                return
            
            if waiting_game["creator_id"] != user_id:
                await callback.answer("❌ Только создатель может отменить сбор!", show_alert=True)
                return
            
            # Удаляем лобби из БД
            await db.remove_waiting_game(chat_id)
            
            # Удаляем сообщение
            await callback.message.delete()
            
            await callback.answer("✅ Сбор игроков отменен")
            
        except Exception as e:
            logger.error(f"Ошибка в cancel_gathering: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data == "inline_roll_dice")
    async def inline_roll_dice(callback: CallbackQuery):
        """Бросок кубиков из inline меню"""
        try:
            chat_id = callback.message.chat.id
            user_id = callback.from_user.id
            
            # Проверяем активную игру
            game_state = await db.get_game_state(chat_id)
            if not game_state or game_state.get("game_state") != "active":
                await callback.answer("❌ Нет активной игры!", show_alert=True)
                return
            
            # Проверяем, чей сейчас ход
            current_idx = game_state.get("current_player", 0)
            player_ids = list(game_state.get("players", {}).keys())
            
            if not player_ids or current_idx >= len(player_ids):
                await callback.answer("❌ Ошибка определения хода!", show_alert=True)
                return
            
            current_player_id = player_ids[current_idx]
            if str(user_id) != current_player_id:
                await callback.answer("❌ Не ваш ход!", show_alert=True)
                return
            
            # Отправляем анимацию кубиков (пункт 2)
            dice_result = await send_dice_animation(
                callback.message,
                user_id,
                chat_id
            )
            
            if dice_result:
                # Обновляем игру
                # TODO: Обработка результата броска
                pass
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в inline_roll_dice: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data == "restore_menu")
    async def restore_menu(callback: CallbackQuery):
        """Вернуть скрытое меню"""
        try:
            user_id = callback.from_user.id
            
            if user_id in hidden_menu_users:
                del hidden_menu_users[user_id]
                
                await callback.message.edit_text(
                    "✅ <b>Меню восстановлено!</b>\n\n"
                    "Теперь вы видите обычное игровое меню.",
                    parse_mode="HTML"
                )
                await callback.answer("✅ Меню восстановлено")
            else:
                await callback.answer("ℹ️ Меню и так показано")
                
        except Exception as e:
            logger.error(f"Ошибка в restore_menu: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    @dp.callback_query(F.data == "back_to_main")
    async def back_to_main(callback: CallbackQuery):
        """Вернуться в главное меню"""
        try:
            user_id = callback.from_user.id
            is_admin = user_id in ADMIN_USER_IDS or await db.is_admin(user_id)
            
            await callback.message.edit_text(
                f"{BANNER}\n\n🎲 <b>Monopoly Premium Edition</b>\n👑 Версия Темного Принца",
                parse_mode="HTML",
                reply_markup=main_menu_kb(
                    is_group=callback.message.chat.type in ["group", "supergroup"],
                    user_id=user_id,
                    is_admin=is_admin
                )
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в back_to_main: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    # Добавляем обработчики для админки
    @dp.callback_query(F.data.startswith("admin_"))
    async def handle_admin_callback(callback: CallbackQuery):
        """Обработчик админских callback"""
        try:
            user_id = callback.from_user.id
            
            if user_id not in ADMIN_USER_IDS and not await db.is_admin(user_id):
                await callback.answer("❌ Нет прав!", show_alert=True)
                return
            
            action = callback.data
            
            if action == "admin_maintenance":
                # Переключение режима обслуживания
                stats["maintenance_mode"] = not stats.get("maintenance_mode", False)
                status = "включен" if stats["maintenance_mode"] else "выключен"
                
                await callback.message.edit_text(
                    f"⚙️ <b>Режим обслуживания {status}</b>\n\n"
                    f"Бот {'недоступен' if stats['maintenance_mode'] else 'доступен'} для пользователей.",
                    parse_mode="HTML"
                )
                await callback.answer(f"✅ Режим обслуживания {status}")
                
            elif action == "admin_restart":
                # Перезапуск бота
                await callback.message.edit_text(
                    "🔄 <b>Перезапуск бота...</b>\n\n"
                    "Бот будет перезапущен через 3 секунды.",
                    parse_mode="HTML"
                )
                await callback.answer("✅ Перезапуск начат")
                
                # Запускаем перезапуск
                await asyncio.sleep(3)
                # Здесь будет перезапуск бота
                
            elif action == "admin_cleanup":
                # Очистка старых игр
                await db.cleanup_old_games()
                await callback.message.edit_text(
                    "🗑️ <b>Очистка завершена</b>\n\n"
                    "Старые игры удалены.",
                    parse_mode="HTML"
                )
                await callback.answer("✅ Очистка завершена")
                
        except Exception as e:
            logger.error(f"Ошибка в handle_admin_callback: {e}")
            await callback.answer("❌ Ошибка!", show_alert=True)
    
    logger.info("✅ Callback обработчики зарегистрированы")
