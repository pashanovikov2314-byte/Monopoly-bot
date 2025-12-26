"""
Interactive map generator for the game
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MapGenerator:
    """Генератор интерактивной карты игры"""
    
    def __init__(self, board_data_path: str = "data/board.json"):
        self.board_data = self.load_board_data(board_data_path)
        self.positions = {}
        
    def load_board_data(self, path: str) -> Dict:
        """Загрузить данные игрового поля"""
        try:
            if Path(path).exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Стандартное поле Monopoly
                return self.get_default_board()
        except Exception as e:
            logger.error(f"Ошибка загрузки данных поля: {e}")
            return self.get_default_board()
    
    def get_default_board(self) -> Dict:
        """Стандартное поле Monopoly"""
        return {
            "positions": [
                {"id": 0, "name": "Старт", "type": "start", "color": None, "price": 0},
                {"id": 1, "name": "Житная", "type": "property", "color": "brown", "price": 60, "rent": [2, 10, 30, 90, 160, 250]},
                {"id": 2, "name": "Общественная казна", "type": "chest", "color": None, "price": 0},
                {"id": 3, "name": "Нагатинская", "type": "property", "color": "brown", "price": 60, "rent": [4, 20, 60, 180, 320, 450]},
                {"id": 4, "name": "Налог на доход", "type": "tax", "color": None, "price": 200},
                {"id": 5, "name": "Рижская ж/д", "type": "railroad", "color": "rail", "price": 200, "rent": [25, 50, 100, 200]},
                # ... остальные позиции
                {"id": 10, "name": "Тюрьма (просто посетить)", "type": "jail_visit", "color": None, "price": 0},
                {"id": 20, "name": "Бесплатная стоянка", "type": "free_parking", "color": None, "price": 0},
                {"id": 30, "name": "Отправляйтесь в тюрьму", "type": "go_to_jail", "color": None, "price": 0},
                {"id": 40, "name": "Шанс", "type": "chance", "color": None, "price": 0}
            ],
            "colors": {
                "brown": {"name": "Коричневый", "hex": "#8B4513"},
                "blue": {"name": "Голубой", "hex": "#87CEEB"},
                "pink": {"name": "Розовый", "hex": "#FF69B4"},
                "orange": {"name": "Оранжевый", "hex": "#FFA500"},
                "red": {"name": "Красный", "hex": "#FF0000"},
                "yellow": {"name": "Желтый", "hex": "#FFFF00"},
                "green": {"name": "Зеленый", "hex": "#00FF00"},
                "darkblue": {"name": "Темно-синий", "hex": "#00008B"},
                "rail": {"name": "Железная дорога", "hex": "#808080"},
                "utility": {"name": "Коммунальное", "hex": "#000000"}
            }
        }
    
    def generate_text_map(self, game_state: Dict) -> str:
        """Генерировать текстовую карту"""
        players = game_state.get("players", {})
        properties = game_state.get("properties", {})
        
        # Создаем матрицу поля (упрощенная версия)
        map_lines = []
        map_lines.append("=" * 50)
        map_lines.append("🗺️ КАРТА ИГРЫ")
        map_lines.append("=" * 50)
        
        for pos in self.board_data["positions"]:
            pos_id = pos["id"]
            pos_name = pos["name"]
            
            # Кто владеет этой позицией?
            owner = None
            for prop_id, prop_data in properties.items():
                if prop_data.get("position") == pos_id:
                    owner = prop_data.get("owner")
                    break
            
            # Кто стоит на этой позиции?
            players_here = []
            for player_id, player_data in players.items():
                if player_data.get("position") == pos_id:
                    players_here.append(player_data.get("name", "Игрок"))
            
            line = f"{pos_id:2d}. {pos_name:<20}"
            
            if owner:
                owner_name = players.get(str(owner), {}).get("name", "Неизвестно")
                line += f" [Владелец: {owner_name}]"
            
            if players_here:
                line += f" <-- {' '.join(players_here)}"
            
            map_lines.append(line)
        
        map_lines.append("=" * 50)
        return "\n".join(map_lines)
    
    def generate_html_map(self, game_state: Dict, game_id: str) -> str:
        """Генерировать HTML карту для веб-интерфейса"""
        players = game_state.get("players", {})
        properties = game_state.get("properties", {})
        
        # Создаем HTML с игровым полем
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Карта игры Monopoly #{game_id}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 20px;
                }
                .board-container {
                    display: grid;
                    grid-template-columns: repeat(11, 1fr);
                    grid-template-rows: repeat(11, 1fr);
                    gap: 2px;
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 10px;
                    border-radius: 10px;
                }
                .board-cell {
                    border: 1px solid #ccc;
                    padding: 5px;
                    text-align: center;
                    font-size: 10px;
                    position: relative;
                    min-height: 60px;
                }
                .property-name {
                    font-weight: bold;
                    margin-bottom: 3px;
                }
                .player-marker {
                    position: absolute;
                    bottom: 2px;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 1px solid black;
                }
                .brown { background-color: #8B4513; color: white; }
                .blue { background-color: #87CEEB; }
                .pink { background-color: #FF69B4; }
                .orange { background-color: #FFA500; }
                .red { background-color: #FF0000; color: white; }
                .yellow { background-color: #FFFF00; }
                .green { background-color: #00FF00; }
                .darkblue { background-color: #00008B; color: white; }
                .rail { background-color: #808080; color: white; }
                .utility { background-color: #000000; color: white; }
                .special { background-color: #f0f0f0; color: black; }
            </style>
        </head>
        <body>
            <h1>🗺️ Карта игры Monopoly #{game_id}</h1>
            <div class="board-container">
        """
        
        # Генерируем клетки поля
        positions = self.board_data["positions"]
        for pos in positions:
            pos_id = pos["id"]
            pos_name = pos["name"]
            pos_type = pos["type"]
            pos_color = pos.get("color")
            
            # Определяем класс цвета
            color_class = pos_color if pos_color else "special"
            
            # Кто владеет?
            owner_info = ""
            for prop_id, prop_data in properties.items():
                if prop_data.get("position") == pos_id:
                    owner_id = prop_data.get("owner")
                    if owner_id:
                        owner_name = players.get(str(owner_id), {}).get("name", "Игрок")
                        owner_info = f"<div style='font-size:8px;'>👑 {owner_name}</div>"
                    break
            
            # Кто стоит?
            players_here = []
            for player_id, player_data in players.items():
                if player_data.get("position") == pos_id:
                    players_here.append(player_data)
            
            player_markers = ""
            for i, player in enumerate(players_here):
                player_color = self.get_player_color(player.get("id", 0))
                player_markers += f"""
                <div class="player-marker" style="background-color: {player_color}; left: {i * 15 + 5}px;"></div>
                """
            
            html += f"""
            <div class="board-cell {color_class}" data-position="{pos_id}">
                <div class="property-name">{pos_name}</div>
                {owner_info}
                {player_markers}
            </div>
            """
        
        html += """
            </div>
            <div style="margin-top: 20px; text-align: center;">
                <button onclick="refreshMap()">🔄 Обновить</button>
                <button onclick="zoomIn()">➕ Увеличить</button>
                <button onclick="zoomOut()">➖ Уменьшить</button>
            </div>
            <script>
                async function refreshMap() {
                    location.reload();
                }
                
                function zoomIn() {
                    document.querySelector('.board-container').style.transform = 'scale(1.2)';
                }
                
                function zoomOut() {
                    document.querySelector('.board-container').style.transform = 'scale(1)';
                }
            </script>
        </body>
        </html>
        """.format(game_id=game_id)
        
        return html
    
    def get_player_color(self, player_id: int) -> str:
        """Получить цвет для маркера игрока"""
        colors = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
            "#FF00FF", "#00FFFF", "#FFA500", "#800080"
        ]
        return colors[player_id % len(colors)]
    
    def get_position_info(self, position_id: int) -> Dict:
        """Получить информацию о позиции"""
        for pos in self.board_data["positions"]:
            if pos["id"] == position_id:
                return pos
        return {}


def generate_map(game_state: Dict, map_type: str = "text", game_id: str = "") -> str:
    """Генерировать карту игры"""
    generator = MapGenerator()
    
    if map_type == "html":
        return generator.generate_html_map(game_state, game_id)
    else:
        return generator.generate_text_map(game_state)
