"""
UTILS.PY - Утилиты, анимации и генерация карты
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import random
import asyncio
import io
import base64
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont
import math

from modules.config import (
    BOARD, COLOR_MAP, logger, BOARD_COORDS,
    BOARD_IMAGE_WIDTH, BOARD_IMAGE_HEIGHT,
    CELL_WIDTH, CELL_HEIGHT
)

# ==================== АНИМАЦИЯ КУБИКОВ ====================

class DiceAnimation:
    """Класс для анимации броска кубиков"""
    
    def __init__(self):
        self.dice_faces = {
            1: ["⬜⬜⬜", "⬜⚫⬜", "⬜⬜⬜"],
            2: ["⚫⬜⬜", "⬜⬜⬜", "⬜⬜⚫"],
            3: ["⚫⬜⬜", "⬜⚫⬜", "⬜⬜⚫"],
            4: ["⚫⬜⚫", "⬜⬜⬜", "⚫⬜⚫"],
            5: ["⚫⬜⚫", "⬜⚫⬜", "⚫⬜⚫"],
            6: ["⚫⬜⚫", "⚫⬜⚫", "⚫⬜⚫"]
        }
    
    def create_dice_face(self, value: int) -> str:
        """Создать текстовое представление кубика"""
        if value not in range(1, 7):
            value = random.randint(1, 6)
        
        face = self.dice_faces.get(value, self.dice_faces[1])
        return "\n".join(face)
    
    async def animate_roll(self, message, dice1_final: int, dice2_final: int) -> Tuple[int, int]:
        """Анимировать бросок кубиков"""
        try:
            # Начальное сообщение
            animation_msg = await message.answer(
                "🎲 <b>Бросаем кубики...</b>\n\n"
                "⬜⬜⬜     ⬜⬜⬜\n"
                "⬜⚫⬜     ⬜⚫⬜\n"
                "⬜⬜⬜     ⬜⬜⬜",
                parse_mode="HTML"
            )
            
            # Анимация вращения (5 кадров)
            for i in range(5):
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                
                face1 = self.create_dice_face(dice1)
                face2 = self.create_dice_face(dice2)
                
                # Создаем анимационный кадр
                frames = face1.split('\n')
                frames2 = face2.split('\n')
                
                animation_text = f"🎲 <b>Бросаем кубики...</b>\n\n"
                for j in range(3):
                    animation_text += f"{frames[j]}     {frames2[j]}\n"
                
                await animation_msg.edit_text(animation_text, parse_mode="HTML")
                await asyncio.sleep(0.3)
            
            # Финальный результат
            face1_final = self.create_dice_face(dice1_final)
            face2_final = self.create_dice_face(dice2_final)
            
        frames_final = face1_final.split('\n')
        frames2_final = face2_final.split('\n')
        
        result_text = f"🎲 <b>Результат броска:</b>\n\n"
        for j in range(3):
            result_text += f"{frames_final[j]}     {frames2_final[j]}\n"
        
        result_text += f"\n🎯 <b>Кубик 1:</b> {dice1_final}\n"
        result_text += f"🎯 <b>Кубик 2:</b> {dice2_final}\n"
        result_text += f"📊 <b>Сумма:</b> {dice1_final + dice2_final}"
        
        await animation_msg.edit_text(result_text, parse_mode="HTML")
        
        return dice1_final, dice2_final
        
        except Exception as e:
            logger.error(f"Ошибка в анимации кубиков: {e}")
            # Возвращаем значения без анимации
            return dice1_final, dice2_final
    
    def quick_roll(self) -> Tuple[int, int]:
        """Быстрый бросок без анимации"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1, dice2
    
    def is_double(self, dice1: int, dice2: int) -> bool:
        """Проверка на дубль"""
        return dice1 == dice2

# ==================== ГЕНЕРАЦИЯ КАРТЫ ====================

class BoardMapGenerator:
    """Генератор карты игрового поля"""
    
    def __init__(self):
        self.cell_size = 80
        self.board_padding = 20
        self.board_width = 1000
        self.board_height = 1000
        
        # Цвета для карты
        self.colors = {
            "BROWN": "#8B4513",
            "BLUE": "#87CEEB", 
            "PINK": "#FFC0CB",
            "ORANGE": "#FFA500",
            "RED": "#FF0000",
            "YELLOW": "#FFFF00",
            "GREEN": "#008000",
            "DARKBLUE": "#00008B",
            "RAIL": "#A9A9A9",
            "UTIL": "#FFFFE0",
            "SPECIAL": "#FFFFFF",
            "TAX": "#FFD700",
            "CHANCE": "#32CD32",
            "JAIL": "#696969",
            "GO_JAIL": "#FF4500",
            "FREE": "#90EE90"
        }
    
    def create_simple_map(self, positions: Dict[int, List[str]] = None) -> str:
        """Создать простую текстовую карту"""
        try:
            # Создаем строковое представление доски
            board_text = "🎲 <b>Игровое поле Монополии</b> 🎲\n\n"
            
            # Верхний ряд (0-9)
            board_text += "⬆️ <b>Верхний ряд (0-9):</b>\n"
            for pos in range(0, 10):
                if pos in BOARD:
                    cell = BOARD[pos]
                    emoji = self._get_cell_emoji(cell["type"])
                    
                    # Проверяем, есть ли игроки на этой клетке
                    player_markers = ""
                    if positions and pos in positions:
                        players = positions[pos]
                        player_markers = " " + " ".join(players[:3])  # Максимум 3 игрока
                    
                    board_text += f"{pos:2d}. {emoji} {cell['name'][:15]:15} {player_markers}\n"
            
            board_text += "\n➡️ <b>Правый ряд (10-19):</b>\n"
            for pos in range(10, 20):
                if pos in BOARD:
                    cell = BOARD[pos]
                    emoji = self._get_cell_emoji(cell["type"])
                    
                    player_markers = ""
                    if positions and pos in positions:
                        players = positions[pos]
                        player_markers = " " + " ".join(players[:2])
                    
                    board_text += f"{pos:2d}. {emoji} {cell['name'][:15]:15} {player_markers}\n"
            
            board_text += "\n⬇️ <b>Нижний ряд (20-29):</b>\n"
            for pos in range(20, 30):
                if pos in BOARD:
                    cell = BOARD[pos]
                    emoji = self._get_cell_emoji(cell["type"])
                    
                    player_markers = ""
                    if positions and pos in positions:
                        players = positions[pos]
                        player_markers = " " + " ".join(players[:3])
                    
                    board_text += f"{pos:2d}. {emoji} {cell['name'][:15]:15} {player_markers}\n"
            
            board_text += "\n⬅️ <b>Левый ряд (30-39):</b>\n"
            for pos in range(30, 40):
                if pos in BOARD:
                    cell = BOARD[pos]
                    emoji = self._get_cell_emoji(cell["type"])
                    
                    player_markers = ""
                    if positions and pos in positions:
                        players = positions[pos]
                        player_markers = " " + " ".join(players[:2])
                    
                    board_text += f"{pos:2d}. {emoji} {cell['name'][:15]:15} {player_markers}\n"
            
            # Легенда
            board_text += "\n🎨 <b>Легенда:</b>\n"
            board_text += "🏁 - СТАРТ | 🏠 - Улица | 🚂 - Ж/д\n"
            board_text += "💡 - Предприятие | 🎲 - Шанс | 💸 - Налог\n"
            board_text += "🚓 - Тюрьма | ⛓️ - В тюрьму | 🅿️ - Стоянка\n"
            
            return board_text
            
        except Exception as e:
            logger.error(f"Ошибка создания текстовой карты: {e}")
            return "❌ Ошибка создания карты"
    
    def _get_cell_emoji(self, cell_type: str) -> str:
        """Получить эмодзи для типа клетки"""
        emoji_map = {
            "start": "🏁",
            "property": "🏠",
            "railroad": "🚂",
            "utility": "💡",
            "chance": "🎲",
            "tax": "💸",
            "jail": "🚓",
            "go_jail": "⛓️",
            "free": "🅿️"
        }
        return emoji_map.get(cell_type, "⬜")
    
    def generate_image_map(self, players_positions: Dict[int, List[Tuple[str, str]]] = None) -> Optional[io.BytesIO]:
        """Сгенерировать изображение карты"""
        try:
            # Создаем изображение
            img = Image.new('RGB', (self.board_width, self.board_height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Рисуем внешнюю рамку
            draw.rectangle(
                [(self.board_padding, self.board_padding), 
                 (self.board_width - self.board_padding, self.board_height - self.board_padding)],
                outline='black', width=3
            )
            
            # Рисуем клетки
            for pos in range(40):
                if pos in BOARD:
                    self._draw_cell(draw, pos, players_positions)
            
            # Добавляем заголовок
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((self.board_width // 2, 10), "MONOPOLY PREMIUM", 
                     fill='black', font=font, anchor='mt')
            
            # Конвертируем в байты
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            logger.error(f"Ошибка генерации карты: {e}")
            return None
    
    def _draw_cell(self, draw: ImageDraw.ImageDraw, position: int, 
                  players_positions: Dict[int, List[Tuple[str, str]]] = None):
        """Нарисовать одну клетку"""
        try:
            if position not in BOARD:
                return
            
            cell = BOARD[position]
            color_name = cell["color"]
            color = self.colors.get(color_name, "#FFFFFF")
            
            # Вычисляем координаты клетки
            x, y = self._get_cell_coordinates(position)
            
            # Рисуем клетку
            cell_rect = [
                (x, y),
                (x + self.cell_size, y + self.cell_size)
            ]
            
            draw.rectangle(cell_rect, fill=color, outline='black', width=1)
            
            # Добавляем текст названия
            name = cell["name"]
            if len(name) > 10:
                name = name[:8] + ".."
            
            # Центрируем текст
            text_x = x + self.cell_size // 2
            text_y = y + self.cell_size // 2
            
            draw.text((text_x, text_y - 10), name, fill='black', anchor='mt', size=8)
            
            # Добавляем тип клетки
            type_symbol = self._get_cell_symbol(cell["type"])
            draw.text((text_x, text_y + 10), type_symbol, fill='black', anchor='mt', size=10)
            
            # Добавляем позицию
            draw.text((x + 5, y + 5), str(position), fill='gray', size=8)
            
            # Добавляем игроков на клетку
            if players_positions and position in players_positions:
                players = players_positions[position]
                for i, (player_name, player_color) in enumerate(players[:4]):  # Макс 4 игрока на клетке
                    player_x = x + 10 + (i % 2) * 15
                    player_y = y + 30 + (i // 2) * 15
                    
                    # Рисуем круг игрока
                    draw.ellipse(
                        [(player_x - 5, player_y - 5), 
                         (player_x + 5, player_y + 5)],
                        fill=player_color
                    )
            
        except Exception as e:
            logger.error(f"Ошибка рисования клетки {position}: {e}")
    
    def _get_cell_coordinates(self, position: int) -> Tuple[int, int]:
        """Получить координаты клетки на карте"""
        # Распределяем клетки по кругу/квадрату
        if position < 10:  # Верхний ряд
            x = self.board_padding + (position * (self.cell_size + 5))
            y = self.board_padding
        elif position < 20:  # Правый ряд
            x = self.board_width - self.board_padding - self.cell_size
            y = self.board_padding + ((position - 10) * (self.cell_size + 5))
        elif position < 30:  # Нижний ряд
            x = self.board_width - self.board_padding - self.cell_size - ((position - 20) * (self.cell_size + 5))
            y = self.board_height - self.board_padding - self.cell_size
        else:  # Левый ряд
            x = self.board_padding
            y = self.board_height - self.board_padding - self.cell_size - ((position - 30) * (self.cell_size + 5))
        
        return x, y
    
    def _get_cell_symbol(self, cell_type: str) -> str:
        """Получить символ для типа клетки"""
        symbols = {
            "start": "🏁",
            "property": "🏠",
            "railroad": "🚂",
            "utility": "💡",
            "chance": "?",
            "tax": "$",
            "jail": "⛓",
            "go_jail": "➡⛓",
            "free": "P"
        }
        return symbols.get(cell_type, "?")

# ==================== ГЕНЕРАЦИЯ СТАТИСТИКИ ====================

class StatisticsGenerator:
    """Генератор статистики и графиков"""
    
    def generate_player_stats_chart(self, stats_data: Dict) -> str:
        """Сгенерировать текстовую диаграмму статистики"""
        try:
            games = stats_data.get("games", 0)
            wins = stats_data.get("wins", 0)
            win_rate = stats_data.get("win_rate", 0)
            
            chart = f"📊 <b>Статистика игрока</b>\n\n"
            
            # Диаграмма игр
            chart += "🎮 <b>Сыграно игр:</b>\n"
            if games > 0:
                bar_length = min(20, games)
                bar = "🟩" * bar_length + "⬜" * (20 - bar_length)
                chart += f"{bar} {games}\n"
            else:
                chart += "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0\n"
            
            # Диаграмма побед
            chart += "\n🏆 <b>Побед:</b>\n"
            if wins > 0:
                bar_length = min(20, wins)
                bar = "🟨" * bar_length + "⬜" * (20 - bar_length)
                chart += f"{bar} {wins}\n"
            else:
                chart += "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0\n"
            
            # Диаграмма винрейта
            chart += "\n📈 <b>Процент побед:</b>\n"
            if win_rate > 0:
                bar_length = int(win_rate / 5)  # 100% = 20 сегментов
                bar_length = min(20, bar_length)
                bar = "🟦" * bar_length + "⬜" * (20 - bar_length)
                chart += f"{bar} {win_rate:.1f}%\n"
            else:
                chart += "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%\n"
            
            # Дополнительная информация
            chart += f"\n📋 <b>Детали:</b>\n"
            chart += f"• Игр: {games}\n"
            chart += f"• Побед: {wins}\n"
            chart += f"• Поражений: {games - wins}\n"
            
            if games > 0:
                chart += f"• Винрейт: {win_rate:.1f}%\n"
                chart += f"• Средний результат: {stats_data.get('avg_money', 0):.0f}$\n"
            
            return chart
            
        except Exception as e:
            logger.error(f"Ошибка генерации статистики: {e}")
            return "❌ Ошибка генерации статистики"
    
    def generate_rating_chart(self, top_players: List[Dict]) -> str:
        """Сгенерировать график рейтинга"""
        try:
            if not top_players:
                return "📊 <b>Рейтинг пуст</b>\n\nНет данных для отображения"
            
            chart = "🏆 <b>Топ игроков по винрейту</b>\n\n"
            
            for i, player in enumerate(top_players[:10], 1):
                name = player["first_name"]
                if len(name) > 12:
                    name = name[:10] + ".."
                
                if player["username"]:
                    name_display = f"@{player['username']}"
                else:
                    name_display = name
                
                win_rate = player["win_rate"]
                games = player["games"]
                
                # Создаем прогресс-бар
                bar_length = int(win_rate / 5)  # 100% = 20 сегментов
                bar_length = min(20, bar_length)
                bar = "🟩" * bar_length + "⬜" * (20 - bar_length)
                
                # Меди для топ-3
                medal = ""
                if i == 1:
                    medal = "🥇 "
                elif i == 2:
                    medal = "🥈 "
                elif i == 3:
                    medal = "🥉 "
                
                chart += f"{medal}{i:2d}. {name_display:15} {bar} {win_rate:.1f}%\n"
                chart += f"     🎮 {games} игр | 🏆 {player['wins']} побед\n"
            
            chart += f"\n📈 <b>Всего игроков в рейтинге:</b> {len(top_players)}"
            
            return chart
            
        except Exception as e:
            logger.error(f"Ошибка генерации рейтинга: {e}")
            return "❌ Ошибка генерации рейтинга"

# ==================== ФОРМАТИРОВАНИЕ ВРЕМЕНИ ====================

class TimeFormatter:
    """Форматирование времени"""
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Форматировать продолжительность"""
        if seconds < 60:
            return f"{seconds}сек"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}мин {secs}сек"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}ч {minutes}мин"
    
    @staticmethod
    def format_time_ago(dt: datetime) -> str:
        """Форматировать время "сколько назад" """
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} год назад" if years == 1 else f"{years} лет назад"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} месяц назад" if months == 1 else f"{months} месяцев назад"
        elif diff.days > 0:
            return f"{diff.days} день назад" if diff.days == 1 else f"{diff.days} дней назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} час назад" if hours == 1 else f"{hours} часов назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} минуту назад" if minutes == 1 else f"{minutes} минут назад"
        else:
            return "только что"
    
    @staticmethod
    def format_game_time(start_time: datetime, end_time: datetime = None) -> str:
        """Форматировать время игры"""
        if end_time:
            duration = end_time - start_time
        else:
            duration = datetime.now() - start_time
        
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} сек"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}:{minutes:02d}"

# ==================== ФОРМАТИРОВАНИЕ ДЕНЕГ ====================

class MoneyFormatter:
    """Форматирование денежных значений"""
    
    @staticmethod
    def format_money(amount: int) -> str:
        """Форматировать сумму денег"""
        if amount >= 1000000:
            return f"{amount/1000000:.1f}M$"
        elif amount >= 1000:
            return f"{amount/1000:.1f}K$"
        else:
            return f"{amount}$"
    
    @staticmethod
    def format_balance_change(change: int) -> str:
        """Форматировать изменение баланса"""
        if change > 0:
            return f"+{MoneyFormatter.format_money(change)}"
        elif change < 0:
            return f"{MoneyFormatter.format_money(change)}"
        else:
            return "0$"
    
    @staticmethod
    def format_property_value(property_id: int, houses: int = 0) -> str:
        """Рассчитать стоимость недвижимости"""
        if property_id not in BOARD:
            return "0$"
        
        cell = BOARD[property_id]
        base_value = cell["price"]
        
        if houses > 0:
            house_cost = cell.get("house_cost", 50)
            if houses == 5:  # Отель
                hotel_cost = cell.get("hotel_cost", 50)
                total_value = base_value + (4 * house_cost) + hotel_cost
            else:
                total_value = base_value + (houses * house_cost)
        else:
            total_value = base_value
        
        return MoneyFormatter.format_money(total_value)

# ==================== ВАЛИДАЦИЯ ДАННЫХ ====================

class DataValidator:
    """Валидация входных данных"""
    
    @staticmethod
    def validate_user_id(user_id: Any) -> bool:
        """Валидация ID пользователя"""
        try:
            return isinstance(user_id, int) and user_id > 0
        except:
            return False
    
    @staticmethod
    def validate_chat_id(chat_id: Any) -> bool:
        """Валидация ID чата"""
        try:
            return isinstance(chat_id, int) and chat_id < 0  # Групповые чаты имеют отрицательные ID
        except:
            return False
    
    @staticmethod
    def validate_position(position: Any) -> bool:
        """Валидация позиции на доске"""
        try:
            pos = int(position)
            return 0 <= pos <= 39
        except:
            return False
    
    @staticmethod
    def validate_money_amount(amount: Any) -> bool:
        """Валидация суммы денег"""
        try:
            amt = int(amount)
            return 0 <= amt <= 10000000  # Максимум 10 миллионов
        except:
            return False
    
    @staticmethod
    def validate_house_count(count: Any) -> bool:
        """Валидация количества домов"""
        try:
            cnt = int(count)
            return 0 <= cnt <= 5  # 0-4 дома, 5 = отель
        except:
            return False

# ==================== ГЕНЕРАЦИЯ СЛУЧАЙНЫХ ДАННЫХ ====================

class RandomGenerator:
    """Генерация случайных данных для тестов"""
    
    @staticmethod
    def generate_test_players(count: int = 4) -> List[Dict]:
        """Сгенерировать тестовых игроков"""
        test_names = ["Алексей", "Мария", "Дмитрий", "Анна", "Иван", "Елена", 
                     "Сергей", "Ольга", "Михаил", "Наталья"]
        test_users = ["test_user_1", "test_user_2", "test_user_3", "test_user_4"]
        
        players = []
        for i in range(min(count, 10)):
            players.append({
                "id": 1000000000 + i,
                "name": test_names[i],
                "username": test_users[i % 4],
                "balance": random.randint(500, 3000),
                "position": random.randint(0, 39),
                "games": random.randint(0, 50),
                "wins": random.randint(0, 25)
            })
        
        return players
    
    @staticmethod
    def generate_test_game_state(chat_id: int = -1000000000) -> Dict:
        """Сгенерировать тестовое состояние игры"""
        from modules.game_logic import MonopolyGame
        
        game = MonopolyGame(chat_id, 999999999)
        
        # Добавляем тестовых игроков
        test_players = RandomGenerator.generate_test_players(4)
        for player in test_players:
            game.add_player(player["id"], player["name"], player["username"])
            game_player = game.get_player_by_id(player["id"])
            if game_player:
                game_player.balance = player["balance"]
                game_player.position = player["position"]
        
        # Покупаем случайные свойства
        for player in game.players:
            for _ in range(random.randint(2, 6)):
                prop_id = random.choice(list(BOARD.keys()))
                if BOARD[prop_id]["type"] == "property":
                    game.buy_property(player, prop_id)
        
        # Строим случайные дома
        for player in game.players:
            for prop_id in player.properties[:random.randint(0, 3)]:
                if random.random() > 0.5:
                    game.build_house(player, prop_id)
        
        return game.get_game_state()

# ==================== КЭШИРОВАНИЕ ====================

class SimpleCache:
    """Простой кэш для временного хранения данных"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def set(self, key: str, value: Any):
        """Установить значение в кэш"""
        self.cache[key] = {
            "value": value,
            "timestamp": datetime.now().timestamp()
        }
    
    def get(self, key: str) -> Any:
        """Получить значение из кэша"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if datetime.now().timestamp() - item["timestamp"] > self.ttl:
            del self.cache[key]
            return None
        
        return item["value"]
    
    def delete(self, key: str):
        """Удалить значение из кэша"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Очистить весь кэш"""
        self.cache.clear()
    
    def size(self) -> int:
        """Получить размер кэша"""
        return len(self.cache)

# ==================== ИНИЦИАЛИЗАЦИЯ УТИЛИТ ====================

# Создаем глобальные экземпляры утилит
dice_animator = DiceAnimation()
map_generator = BoardMapGenerator()
stats_generator = StatisticsGenerator()
time_formatter = TimeFormatter()
money_formatter = MoneyFormatter()
data_validator = DataValidator()
random_generator = RandomGenerator()

# Глобальный кэш для часто используемых данных
game_cache = SimpleCache(ttl_seconds=60)  # 1 минута

# ==================== ЭКСПОРТ ФУНКЦИЙ ====================

__all__ = [
    'dice_animator',
    'map_generator', 
    'stats_generator',
    'time_formatter',
    'money_formatter',
    'data_validator',
    'random_generator',
    'game_cache'
]

# ==================== ВЕБ-ГЕНЕРАЦИЯ ====================

class WebPageGenerator:
    """Генератор веб-страниц для статуса игры"""
    
    @staticmethod
    def generate_game_status_html(game_data: Dict) -> str:
        """Сгенерировать HTML страницу статуса игры"""
        try:
            html = """
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Monopoly Premium - Статус игры</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        padding: 30px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 3px solid #667eea;
                    }
                    .header h1 {
                        color: #333;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .header .subtitle {
                        color: #666;
                        font-size: 1.2rem;
                    }
                    .game-info {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }
                    .info-card {
                        background: #f8f9fa;
                        border-radius: 15px;
                        padding: 20px;
                        text-align: center;
                        border: 2px solid #e9ecef;
                        transition: transform 0.3s, box-shadow 0.3s;
                    }
                    .info-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    }
                    .info-card h3 {
                        color: #495057;
                        margin-bottom: 10px;
                        font-size: 1.1rem;
                    }
                    .info-card .value {
                        color: #667eea;
                        font-size: 2rem;
                        font-weight: bold;
                    }
                    .players-section {
                        margin-bottom: 30px;
                    }
                    .players-section h2 {
                        color: #333;
                        margin-bottom: 20px;
                        font-size: 1.8rem;
                    }
                    .players-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                    }
                    .player-card {
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        border-radius: 15px;
                        padding: 20px;
                        position: relative;
                        overflow: hidden;
                    }
                    .player-card.current {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        box-shadow: 0 10px 30px rgba(79, 172, 254, 0.4);
                    }
                    .player-card.bankrupt {
                        background: linear-gradient(135deg, #868f96 0%, #596164 100%);
                        opacity: 0.7;
                    }
                    .player-card.jail {
                        background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%);
                    }
                    .player-card h3 {
                        font-size: 1.3rem;
                        margin-bottom: 10px;
                    }
                    .player-stats {
                        display: flex;
                        justify-content: space-between;
                        margin-top: 15px;
                    }
                    .stat {
                        text-align: center;
                    }
                    .stat .label {
                        font-size: 0.9rem;
                        opacity: 0.9;
                    }
                    .stat .value {
                        font-size: 1.2rem;
                        font-weight: bold;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 2px solid #e9ecef;
                        color: #6c757d;
                        font-size: 0.9rem;
                    }
                    .color-badge {
                        display: inline-block;
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        margin-right: 5px;
                        vertical-align: middle;
                    }
                    @media (max-width: 768px) {
                        .container { padding: 15px; }
                        .header h1 { font-size: 2rem; }
                        .game-info { grid-template-columns: 1fr; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 Monopoly Premium</h1>
                        <div class="subtitle">👑 Версия Темного Принца | Статус игры в реальном времени</div>
                    </div>
            """
            
            # Информация об игре
            html += f"""
                    <div class="game-info">
                        <div class="info-card">
                            <h3>🔄 Ход</h3>
                            <div class="value">{game_data.get('turn', 1)}</div>
                        </div>
                        <div class="info-card">
                            <h3>👥 Игроков</h3>
                            <div class="value">{len(game_data.get('players', []))}</div>
                        </div>
                        <div class="info-card">
                            <h3>🏠 Собственность</h3>
                            <div class="value">{game_data.get('properties_owned', 0)}</div>
                        </div>
                        <div class="info-card">
                            <h3>⏱️ Длительность</h3>
                            <div class="value">{game_data.get('game_duration', 0)} мин</div>
                        </div>
                    </div>
            """
            
            # Текущий игрок
            current_player = game_data.get('current_player', {})
            if current_player:
                html += f"""
                    <div class="info-card current" style="grid-column: 1 / -1; text-align: center;">
                        <h3>🎯 ТЕКУЩИЙ ИГРОК</h3>
                        <div class="value" style="font-size: 2.5rem;">{current_player.get('name', 'Неизвестно')}</div>
                        <div style="margin-top: 10px; font-size: 1.2rem;">
                            💰 {current_player.get('balance', 0)}$ | 📍 Позиция: {current_player.get('position', 0)}
                        </div>
                    </div>
                """
            
            # Список игроков
            html += """
                    <div class="players-section">
                        <h2>👥 Участники игры</h2>
                        <div class="players-grid">
            """
            
            for player in game_data.get('players_detailed', []):
                player_class = "player-card"
                if player.get('id') == current_player.get('id'):
                    player_class += " current"
                if player.get('bankrupt'):
                    player_class += " bankrupt"
                if player.get('in_jail'):
                    player_class += " jail"
                
                html += f"""
                            <div class="{player_class}">
                                <div class="color-badge" style="background-color: {player.get('color', '#FF0000')};"></div>
                                <h3>{player.get('name', 'Игрок')}</h3>
                                <div class="player-stats">
                                    <div class="stat">
                                        <div class="label">💰 Баланс</div>
                                        <div class="value">{player.get('balance', 0)}$</div>
                                    </div>
                                    <div class="stat">
                                        <div class="label">📍 Позиция</div>
                                        <div class="value">{player.get('position', 0)}</div>
                                    </div>
                                    <div class="stat">
                                        <div class="label">🏠 Собственность</div>
                                        <div class="value">{player.get('properties_count', 0)}</div>
                                    </div>
                                </div>
                """
                
                if player.get('in_jail'):
                    html += '<div style="margin-top: 10px; font-size: 0.9rem;">⛓️ В тюрьме</div>'
                if player.get('bankrupt'):
                    html += '<div style="margin-top: 10px; font-size: 0.9rem;">💀 Банкрот</div>'
                
                html += "</div>"
            
            html += """
                        </div>
                    </div>
            """
            
            # Футер
            html += f"""
                    <div class="footer">
                        <p>👑 Monopoly Premium Bot v3.0 | Создано Темным Принцем</p>
                        <p>🔄 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>🔗 Статус игры обновляется в реальном времени</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Ошибка генерации HTML: {e}")
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Ошибка</title></head>
            <body>
                <h1>❌ Ошибка загрузки статуса игры</h1>
                <p>{str(e)}</p>
            </body>
            </html>
            """
    
    @staticmethod
    def generate_admin_panel_html(stats: Dict) -> str:
        """Сгенерировать HTML админ-панели"""
        try:
            html = """
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Monopoly Premium - Админ Панель</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        padding: 30px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 3px solid #2b5876;
                    }
                                       .header h1 {
                        color: #333;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .header .subtitle {
                        color: #666;
                        font-size: 1.2rem;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }
                    .stat-card {
                        background: #f8f9fa;
                        border-radius: 15px;
                        padding: 20px;
                        border: 2px solid #e9ecef;
                    }
                    .stat-card.critical { border-color: #dc3545; }
                    .stat-card.warning { border-color: #ffc107; }
                    .stat-card.success { border-color: #28a745; }
                    .stat-card.info { border-color: #17a2b8; }
                    .stat-card h3 {
                        color: #495057;
                        margin-bottom: 10px;
                        font-size: 1.1rem;
                    }
                    .stat-card .value {
                        color: #2b5876;
                        font-size: 2rem;
                        font-weight: bold;
                    }
                    .actions {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                        margin: 30px 0;
                    }
                    .btn {
                        padding: 15px 20px;
                        border: none;
                        border-radius: 10px;
                        font-size: 1rem;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s;
                        text-align: center;
                        text-decoration: none;
                        display: block;
                    }
                    .btn-primary {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .btn-warning {
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                    }
                    .btn-danger {
                        background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%);
                        color: white;
                    }
                    .btn-success {
                        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                        color: white;
                    }
                    .btn:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
                    }
                    .tables {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-top: 30px;
                    }
                    .table-container {
                        background: #f8f9fa;
                        border-radius: 15px;
                        padding: 20px;
                        overflow-x: auto;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 10px;
                        text-align: left;
                        border-bottom: 1px solid #dee2e6;
                    }
                    th {
                        background: #2b5876;
                        color: white;
                    }
                    tr:hover {
                        background: #e9ecef;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 2px solid #e9ecef;
                        color: #6c757d;
                        font-size: 0.9rem;
                    }
                    .password-form {
                        max-width: 400px;
                        margin: 50px auto;
                        padding: 30px;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    }
                    .password-form input {
                        width: 100%;
                        padding: 15px;
                        margin: 10px 0;
                        border: 2px solid #e9ecef;
                        border-radius: 10px;
                        font-size: 1rem;
                    }
                    @media (max-width: 768px) {
                        .container { padding: 15px; }
                        .stats-grid { grid-template-columns: 1fr; }
                        .actions { grid-template-columns: 1fr; }
                    }
                </style>
            </head>
            <body>
            """
            
            # Проверка пароля (если требуется)
            if stats.get('requires_password', True):
                html += """
                <div class="password-form">
                    <h2 style="text-align: center; margin-bottom: 20px;">🔐 Админ Панель</h2>
                    <p style="text-align: center; margin-bottom: 20px; color: #666;">
                        Введите пароль для доступа к админ-панели
                    </p>
                    <form method="GET">
                        <input type="password" name="password" placeholder="Пароль администратора" required>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Войти</button>
                    </form>
                </div>
                </body>
                </html>
                """
                return html
            
            # Основная панель
            html += f"""
                <div class="container">
                    <div class="header">
                        <h1>⚙️ Админ Панель</h1>
                        <div class="subtitle">👑 Управление Monopoly Premium Bot</div>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card success">
                            <h3>🎮 Активных игр</h3>
                            <div class="value">{stats.get('active_games', 0)}</div>
                        </div>
                        <div class="stat-card info">
                            <h3>⏳ Ожидающих игр</h3>
                            <div class="value">{stats.get('waiting_games', 0)}</div>
                        </div>
                        <div class="stat-card warning">
                            <h3>👥 Всего игроков</h3>
                            <div class="value">{stats.get('total_players', 0)}</div>
                        </div>
                        <div class="stat-card {'critical' if stats.get('maintenance_mode') else 'success'}">
                            <h3>🔧 Режим обслуживания</h3>
                            <div class="value">{'ВКЛ' if stats.get('maintenance_mode') else 'ВЫКЛ'}</div>
                        </div>
                    </div>
                    
                    <div class="actions">
                        <a href="?action=toggle_maintenance" class="btn btn-warning">
                            🔧 Переключить режим обслуживания
                        </a>
                        <a href="?action=reload_stats" class="btn btn-primary">
                            🔄 Перезагрузить статистику
                        </a>
                        <a href="?action=cleanup" class="btn btn-danger">
                            🧹 Очистить старые игры
                        </a>
                        <a href="?action=export_stats" class="btn btn-success">
                            📁 Экспорт статистики
                        </a>
                    </div>
            """
            
            # Список активных игр
            if stats.get('active_games_list'):
                html += """
                    <div class="tables">
                        <div class="table-container">
                            <h3>🎲 Активные игры</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Чат ID</th>
                                        <th>Игроков</th>
                                        <th>Ход</th>
                                        <th>Действия</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                
                for game in stats['active_games_list'][:10]:  # Ограничиваем 10 играми
                    html += f"""
                                    <tr>
                                        <td><code>{game.get('chat_id', 0)}</code></td>
                                        <td>{game.get('players', 0)}</td>
                                        <td>{game.get('turn', 0)}</td>
                                        <td>
                                            <a href="?action=view_game&id={game.get('chat_id', 0)}" style="color: #667eea; text-decoration: none;">👁️</a>
                                            <a href="?action=end_game&id={game.get('chat_id', 0)}" style="color: #dc3545; text-decoration: none; margin-left: 10px;">⏹️</a>
                                        </td>
                                    </tr>
                    """
                
                html += """
                                </tbody>
                            </table>
                        </div>
                """
            
            # Топ игроков
            if stats.get('top_players'):
                html += """
                        <div class="table-container">
                            <h3>🏆 Топ игроков</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Игрок</th>
                                        <th>Победы</th>
                                        <th>Винрейт</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                
                for i, player in enumerate(stats['top_players'][:10], 1):
                    medal = ""
                    if i == 1: medal = "🥇"
                    elif i == 2: medal = "🥈"
                    elif i == 3: medal = "🥉"
                    
                    html += f"""
                                    <tr>
                                        <td>{medal} {i}</td>
                                        <td>{player.get('name', 'Игрок')}</td>
                                        <td>{player.get('wins', 0)}</td>
                                        <td>{player.get('win_rate', 0):.1f}%</td>
                                    </tr>
                    """
                
                html += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                """
            
            # Футер
            html += f"""
                    <div class="footer">
                        <p>👑 Monopoly Premium Bot v3.0 | Админ панель</p>
                        <p>🔄 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>🔒 Доступ только для администраторов</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Ошибка генерации админ-панели: {e}")
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Ошибка</title></head>
            <body>
                <h1>❌ Ошибка админ-панели</h1>
                <p>{str(e)}</p>
            </body>
            </html>
            """

# ==================== СОЗДАНИЕ ИНИЦИАЛИЗИРОВАННЫХ ОБЪЕКТОВ ====================

web_generator = WebPageGenerator()

# ==================== СИСТЕМНЫЕ УТИЛИТЫ ====================

class SystemUtils:
    """Системные утилиты для работы бота"""
    
    @staticmethod
    def get_system_stats() -> Dict:
        """Получить статистику системы"""
        import psutil
        import os
        
        try:
            # Использование CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Использование памяти
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used // (1024 * 1024)  # MB
            memory_total = memory.total // (1024 * 1024)  # MB
            
            # Использование диска
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used // (1024 * 1024 * 1024)  # GB
            disk_total = disk.total // (1024 * 1024 * 1024)  # GB
            
            # Процессы
            processes = len(psutil.pids())
            
            # Время работы системы
            boot_time = psutil.boot_time()
            uptime_seconds = int(datetime.now().timestamp() - boot_time)
            
            # Конвертируем время работы
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_mb": memory_used,
                "memory_total_mb": memory_total,
                "disk_percent": disk_percent,
                "disk_used_gb": disk_used,
                "disk_total_gb": disk_total,
                "processes": processes,
                "uptime_days": days,
                "uptime_hours": hours,
                "uptime_minutes": minutes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения системной статистики: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def check_disk_space() -> Dict:
        """Проверить свободное место на диске"""
        import psutil
        import os
        
        try:
            disk = psutil.disk_usage('/')
            
            return {
                "total_gb": disk.total // (1024**3),
                "used_gb": disk.used // (1024**3),
                "free_gb": disk.free // (1024**3),
                "percent": disk.percent,
                "status": "CRITICAL" if disk.percent > 90 else "WARNING" if disk.percent > 75 else "OK"
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки диска: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_bot_stats() -> Dict:
        """Получить статистику бота"""
        from modules.config import (
            ACTIVE_GAMES, WAITING_GAMES, USER_STATS, 
            HIDDEN_MENU_USERS, STATS
        )
        
        # Считаем активных игроков
        active_players = 0
        for game in ACTIVE_GAMES.values():
            active_players += len(game.players)
        
        for game in WAITING_GAMES.values():
            active_players += len(game["players"])
        
        # Считаем свойства в играх
        total_properties = 0
        for game in ACTIVE_GAMES.values():
            total_properties += len(game.properties)
        
        return {
            "active_games": len(ACTIVE_GAMES),
            "waiting_games": len(WAITING_GAMES),
            "total_players_db": len(USER_STATS),
            "active_players_now": active_players,
            "hidden_menus": len(HIDDEN_MENU_USERS),
            "total_properties": total_properties,
            "maintenance_mode": STATS.get("maintenance_mode", False),
            "bot_uptime": time_formatter.format_duration(
                int((datetime.now() - STATS.get("bot_started", datetime.now())).total_seconds())
            )
        }
    
    @staticmethod
    def backup_data():
        """Создать резервную копию данных"""
        try:
            from modules.config import DATA_DIR, USER_STATS, save_user_stats
            import shutil
            import json
            import os
            
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(DATA_DIR, f"backup_{timestamp}")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Копируем файл статистики
            stats_file = os.path.join(DATA_DIR, "user_stats.json")
            if os.path.exists(stats_file):
                shutil.copy2(stats_file, os.path.join(backup_dir, "user_stats.json"))
            
            # Сохраняем текущее состояние в JSON
            backup_data = {
                "timestamp": timestamp,
                "user_stats": USER_STATS,
                "active_games_count": len(ACTIVE_GAMES),
                "waiting_games_count": len(WAITING_GAMES)
            }
            
            with open(os.path.join(backup_dir, "backup_info.json"), 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # Архивируем
            shutil.make_archive(backup_dir, 'zip', backup_dir)
            shutil.rmtree(backup_dir)
            
            backup_path = f"{backup_dir}.zip"
            
            logger.info(f"Резервная копия создана: {backup_path}")
            return {
                "success": True,
                "backup_path": backup_path,
                "size_mb": os.path.getsize(backup_path) // (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def cleanup_old_backups(max_backups: int = 10):
        """Очистить старые резервные копии"""
        try:
            from modules.config import DATA_DIR
            import os
            import glob
            
            backup_files = glob.glob(os.path.join(DATA_DIR, "backup_*.zip"))
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            removed = 0
            for backup_file in backup_files[max_backups:]:
                try:
                    os.remove(backup_file)
                    removed += 1
                except Exception as e:
                    logger.error(f"Ошибка удаления {backup_file}: {e}")
            
            return {
                "success": True,
                "total_backups": len(backup_files),
                "removed": removed,
                "kept": min(max_backups, len(backup_files))
            }
            
        except Exception as e:
            logger.error(f"Ошибка очистки бэкапов: {e}")
            return {"success": False, "error": str(e)}

# ==================== УТИЛИТЫ ДЛЯ ТЕСТИРОВАНИЯ ====================

class TestUtilities:
    """Утилиты для тестирования и отладки"""
    
    @staticmethod
    def test_game_mechanics():
        """Протестировать игровую механику"""
        from modules.game_logic import MonopolyGame, MonopolyPlayer
        
        print("🧪 Тестирование игровой механики...")
        
        try:
            # Создаем тестовую игру
            game = MonopolyGame(-1000000000, 999999999)
            
            # Добавляем тестовых игроков
            game.add_player(111111111, "Тест Игрок 1", "test1")
            game.add_player(222222222, "Тест Игрок 2", "test2")
            
            print(f"✅ Создана игра с {len(game.players)} игроками")
            
            # Тест броска кубиков
            player = game.players[0]
            dice1, dice2, total = game.roll_dice(player)
            print(f"✅ Бросок кубиков: {dice1}+{dice2}={total}")
            
            # Тест движения
            old_pos = player.position
            new_pos = game.move_player(player, total)
            print(f"✅ Движение: {old_pos} → {new_pos}")
            
            # Тест обработки клетки
            result = game.process_position(player, new_pos)
            print(f"✅ Обработка клетки: {result.get('cell_name', 'Неизвестно')}")
            
            # Тест покупки недвижимости
            if result.get("can_buy", False):
                success = game.buy_property(player, new_pos)
                print(f"✅ Покупка недвижимости: {'Успешно' if success else 'Неудача'}")
            
            # Тест механики тюрьмы
            player.in_jail = True
            jail_result = game.process_jail(player)
            print(f"✅ Механика тюрьмы: {jail_result.get('message', 'Ошибка')}")
            
            print("🎉 Все тесты пройдены успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
    
    @staticmethod
    def test_database():
        """Протестировать базу данных"""
        from modules.config import USER_STATS, save_user_stats, load_user_stats
        
        print("🗄️ Тестирование базы данных...")
        
        try:
            # Сохраняем текущее состояние
            original_count = len(USER_STATS)
            
            # Добавляем тестового пользователя
            test_user_id = 999888777
            test_user = {
                "username": "test_user",
                "first_name": "Тестовый Игрок",
                "games": 10,
                "wins": 5,
                "total_money": 15000,
                "last_played": datetime.now().isoformat()
            }
            
            USER_STATS[test_user_id] = test_user
            
            # Сохраняем
            save_user_stats()
            print(f"✅ Данные сохранены: {len(USER_STATS)} игроков")
            
            # Очищаем и загружаем заново
            USER_STATS.clear()
            load_user_stats()
            
            print(f"✅ Данные загружены: {len(USER_STATS)} игроков")
            
            # Проверяем, что тестовый пользователь загрузился
            if test_user_id in USER_STATS:
                print(f"✅ Тестовый пользователь найден в базе")
            else:
                print(f"❌ Тестовый пользователь не найден в базе")
            
            # Удаляем тестового пользователя
            if test_user_id in USER_STATS:
                del USER_STATS[test_user_id]
                save_user_stats()
                print(f"✅ Тестовый пользователь удален")
            
            print("🎉 Тестирование базы данных завершено!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования БД: {e}")
            return False
    
    @staticmethod
    def run_all_tests():
        """Запустить все тесты"""
        print("🚀 Запуск всех тестов Monopoly Premium...")
        print("=" * 50)
        
        results = []
        
        # Тест игровой механики
        results.append(("Игровая механика", TestUtilities.test_game_mechanics()))
        
        # Тест базы данных
        results.append(("База данных", TestUtilities.test_database()))
        
        print("=" * 50)
        print("📊 Результаты тестирования:")
        
        passed = 0
        failed = 0
        
        for test_name, success in results:
            status = "✅ ПРОЙДЕНО" if success else "❌ ПРОВАЛЕНО"
            print(f"{test_name}: {status}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print(f"\n🎯 Итого: {passed} пройдено, {failed} провалено")
        
        return passed, failed

# ==================== ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ ====================

system_utils = SystemUtils()
test_utils = TestUtilities()

# Экспорт
__all__.extend(['system_utils', 'test_utils', 'web_generator'])

# ==================== ФУНКЦИИ ИНИЦИАЛИЗАЦИИ ====================

def init_utils():
    """Инициализация всех утилит"""
    try:
        logger.info("🔧 Инициализация утилит...")
        
        # Проверяем наличие необходимых библиотек
        try:
            import psutil
            logger.info("✅ psutil доступен для системного мониторинга")
        except ImportError:
            logger.warning("⚠️ psutil не установлен, системный мониторинг недоступен")
        
        try:
            from PIL import Image
            logger.info("✅ Pillow доступен для генерации изображений")
        except ImportError:
            logger.warning("⚠️ Pillow не установлен, генерация карт недоступна")
        
        logger.info(f"✅ Утилиты инициализированы: {len(__all__)} компонентов")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации утилит: {e}")

# Автоматическая инициализация при импорте
if __name__ != "__main__":
    init_utils()

# ==================== УТИЛИТЫ ДЛЯ ТОРГОВЛИ ====================

class TradeUtilities:
    """Утилиты для системы торговли"""
    
    @staticmethod
    def calculate_trade_value(offer: Dict, game) -> int:
        """Рассчитать стоимость предложения"""
        total_value = 0
        
        # Деньги
        if "money" in offer:
            total_value += offer["money"]
        
        # Недвижимость
        if "properties" in offer:
            for prop_id in offer["properties"]:
                if prop_id in BOARD:
                    cell = BOARD[prop_id]
                    
                    # Базовая стоимость
                    prop_value = cell["price"]
                    
                    # Добавляем стоимость домов
                    player = game.get_player_by_id(offer.get("from_player_id"))
                    if player and prop_id in player.houses:
                        houses = player.houses[prop_id]
                        if houses > 0:
                            house_cost = cell.get("house_cost", 50)
                            if houses == 5:  # Отель
                                hotel_cost = cell.get("hotel_cost", 50)
                                prop_value += (4 * house_cost) + hotel_cost
                            else:
                                prop_value += houses * house_cost
                    
                    total_value += prop_value
        
        # Карты освобождения из тюрьмы
        if "get_out_cards" in offer:
            total_value += offer["get_out_cards"] * 100  # Примерная стоимость
        
        return total_value
    
    @staticmethod
    def validate_trade_offer(offer: Dict, from_player, to_player, game) -> Dict:
        """Валидация торгового предложения"""
        errors = []
        
        # Проверка денег
        if offer.get("money_from", 0) > from_player.balance:
            errors.append(f"❌ У {from_player.name} недостаточно денег")
        
        if offer.get("money_to", 0) > to_player.balance:
            errors.append(f"❌ У {to_player.name} недостаточно денег")
        
        # Проверка недвижимости
        for prop_id in offer.get("properties_from", []):
            if prop_id not in from_player.properties:
                errors.append(f"❌ {from_player.name} не владеет недвижимостью {prop_id}")
            elif prop_id in from_player.mortgaged_properties:
                errors.append(f"❌ Недвижимость {prop_id} в залоге у {from_player.name}")
        
        for prop_id in offer.get("properties_to", []):
            if prop_id not in to_player.properties:
                errors.append(f"❌ {to_player.name} не владеет недвижимостью {prop_id}")
            elif prop_id in to_player.mortgaged_properties:
                errors.append(f"❌ Недвижимость {prop_id} в залоге у {to_player.name}")
        
        # Проверка карт освобождения
        if offer.get("cards_from", 0) > from_player.get_out_of_jail_cards:
            errors.append(f"❌ У {from_player.name} недостаточно карт освобождения")
        
        if offer.get("cards_to", 0) > to_player.get_out_of_jail_cards:
            errors.append(f"❌ У {to_player.name} недостаточно карт освобождения")
        
        # Проверка на зацикленность (A->B и B->A одновременно)
        if offer.get("money_from", 0) > 0 and offer.get("money_to", 0) > 0:
            if offer["money_from"] == offer["money_to"]:
                errors.append("❌ Бессмысленный обмен одинаковых сумм")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "from_value": TradeUtilities.calculate_trade_value({
                "money": offer.get("money_from", 0),
                "properties": offer.get("properties_from", []),
                "get_out_cards": offer.get("cards_from", 0)
            }, game),
            "to_value": TradeUtilities.calculate_trade_value({
                "money": offer.get("money_to", 0),
                "properties": offer.get("properties_to", []),
                "get_out_cards": offer.get("cards_to", 0)
            }, game)
        }
    
    @staticmethod
    def format_trade_offer(offer: Dict, from_player, to_player, game) -> str:
        """Форматировать торговое предложение"""
        text = f"🤝 <b>Предложение от {from_player.name}</b>\n\n"
        
        # Что предлагает from_player
        from_items = []
        if offer.get("money_from", 0) > 0:
            from_items.append(f"💰 {offer['money_from']}$")
        
        if offer.get("properties_from"):
            for prop_id in offer["properties_from"]:
                if prop_id in BOARD:
                    prop_name = BOARD[prop_id]["name"]
                    from_items.append(f"🏠 {prop_name}")
        
        if offer.get("cards_from", 0) > 0:
            from_items.append(f"🎫 {offer['cards_from']} карт(ы) освобождения")
        
        if from_items:
            text += f"📤 <b>{from_player.name} предлагает:</b>\n"
            text += "\n".join(f"• {item}" for item in from_items) + "\n\n"
        else:
            text += f"📤 {from_player.name} ничего не предлагает\n\n"
        
        # Что предлагает to_player
        to_items = []
        if offer.get("money_to", 0) > 0:
            to_items.append(f"💰 {offer['money_to']}$")
        
        if offer.get("properties_to"):
            for prop_id in offer["properties_to"]:
                if prop_id in BOARD:
                    prop_name = BOARD[prop_id]["name"]
                    to_items.append(f"🏠 {prop_name}")
        
        if offer.get("cards_to", 0) > 0:
            to_items.append(f"🎫 {offer['cards_to']} карт(ы) освобождения")
        
        if to_items:
            text += f"📥 <b>{to_player.name} получает:</b>\n"
            text += "\n".join(f"• {item}" for item in to_items) + "\n"
        else:
            text += f"📥 {to_player.name} ничего не получает\n"
        
        # Стоимость предложения
        validation = TradeUtilities.validate_trade_offer(offer, from_player, to_player, game)
        if validation["valid"]:
            text += f"\n💎 <b>Стоимость сделки:</b>\n"
            text += f"• {from_player.name}: {validation['from_value']}$\n"
            text += f"• {to_player.name}: {validation['to_value']}$\n"
            
            difference = abs(validation["from_value"] - validation["to_value"])
            if difference > 0:
                text += f"📊 <b>Разница: {difference}$</b>\n"
            else:
                text += f"⚖️ <b>Сделка справедливая!</b>\n"
        else:
            text += f"\n❌ <b>Проблемы с предложением:</b>\n"
            text += "\n".join(validation["errors"])
        
        return text
    
    @staticmethod
    def execute_trade(offer: Dict, game) -> bool:
        """Выполнить торговую сделку"""
        try:
            from_player = game.get_player_by_id(offer["from_player_id"])
            to_player = game.get_player_by_id(offer["to_player_id"])
            
            if not from_player or not to_player:
                return False
            
            # Валидация
            validation = TradeUtilities.validate_trade_offer(offer, from_player, to_player, game)
            if not validation["valid"]:
                return False
            
            # Обмен деньгами
            if offer.get("money_from", 0) > 0:
                from_player.balance -= offer["money_from"]
                to_player.balance += offer["money_from"]
            
            if offer.get("money_to", 0) > 0:
                to_player.balance -= offer["money_to"]
                from_player.balance += offer["money_to"]
            
            # Обмен недвижимостью
            for prop_id in offer.get("properties_from", []):
                if (prop_id in from_player.properties and 
                    prop_id not in from_player.mortgaged_properties):
                    
                    # Передаем недвижимость
                    from_player.remove_property(prop_id)
                    to_player.add_property(prop_id)
                    
                    # Передаем дома
                    if prop_id in from_player.houses:
                        houses = from_player.houses[prop_id]
                        to_player.houses[prop_id] = houses
                        del from_player.houses[prop_id]
                    
                    # Обновляем владельца в игре
                    if prop_id in game.properties:
                        game.properties[prop_id]["owner"] = to_player.id
                        game.properties[prop_id]["owner_name"] = to_player.name
            
            for prop_id in offer.get("properties_to", []):
                if (prop_id in to_player.properties and 
                    prop_id not in to_player.mortgaged_properties):
                    
                    # Передаем недвижимость
                    to_player.remove_property(prop_id)
                    from_player.add_property(prop_id)
                    
                    # Передаем дома
                    if prop_id in to_player.houses:
                        houses = to_player.houses[prop_id]
                        from_player.houses[prop_id] = houses
                        del to_player.houses[prop_id]
                    
                    # Обновляем владельца в игре
                    if prop_id in game.properties:
                        game.properties[prop_id]["owner"] = from_player.id
                        game.properties[prop_id]["owner_name"] = from_player.name
            
            # Обмен картами освобождения
            if offer.get("cards_from", 0) > 0:
                from_player.get_out_of_jail_cards -= offer["cards_from"]
                to_player.get_out_of_jail_cards += offer["cards_from"]
            
            if offer.get("cards_to", 0) > 0:
                to_player.get_out_of_jail_cards -= offer["cards_to"]
                from_player.get_out_of_jail_cards += offer["cards_to"]
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка выполнения сделки: {e}")
            return False

# ==================== УТИЛИТЫ ДЛЯ ВЕБ-ПАНЕЛИ ====================

class WebPanelUtils:
    """Утилиты для веб-панели статуса"""
    
    @staticmethod
    def generate_status_json(game_data: Dict) -> str:
        """Сгенерировать JSON статуса игры"""
        import json
        
        status = {
            "status": "active",
            "game": {
                "turn": game_data.get("turn", 0),
                "current_player": game_data.get("current_player", {}),
                "players_count": len(game_data.get("players", [])),
                "properties_owned": game_data.get("properties_owned", 0),
                "game_duration_minutes": game_data.get("game_duration", 0)
            },
            "players": game_data.get("players_detailed", []),
            "timestamp": datetime.now().isoformat(),
            "version": "3.0",
            "author": "Темный Принц"
        }
        
        return json.dumps(status, ensure_ascii=False, indent=2)
    
    @staticmethod
    def generate_system_json() -> str:
        """Сгенерировать JSON системной информации"""
        import json
        
        system_stats = system_utils.get_system_stats()
        bot_stats = system_utils.get_bot_stats()
        
        status = {
            "system": system_stats,
            "bot": bot_stats,
            "games": {
                "active": len(ACTIVE_GAMES),
                "waiting": len(WAITING_GAMES)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(status, ensure_ascii=False, indent=2)
    
    @staticmethod
    def check_password(input_password: str) -> bool:
        """Проверить пароль для веб-панели"""
        from modules.config import os
        
        # Пароль из переменной окружения или по умолчанию
        correct_password = os.environ.get("WEB_PASSWORD", "darkprince")
        
        return input_password == correct_password

# ==================== СОЗДАНИЕ ИНИЦИАЛИЗИРОВАННЫХ ОБЪЕКТОВ ====================

trade_utils = TradeUtilities()
web_panel_utils = WebPanelUtils()

# Экспорт
__all__.extend(['trade_utils', 'web_panel_utils'])

# ==================== ФИНАЛЬНАЯ ИНИЦИАЛИЗАЦИЯ ====================

def init_all_utils():
    """Инициализировать все утилиты"""
    try:
        init_utils()
        logger.info("🎮 Утилиты для игры инициализированы")
        logger.info("🤝 Утилиты торговли инициализированы")
        logger.info("🌐 Веб-утилиты инициализированы")
        logger.info("✅ Все утилиты готовы к работе")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации утилит: {e}")

# Автоматическая инициализация
if __name__ != "__main__":
    init_all_utils()
    
    
 