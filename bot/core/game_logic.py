"""Основная логика игры Монополия"""

import json
import random
from typing import Dict, List, Optional

class MonopolyGame:
    """Класс управления игрой"""
    
    def __init__(self):
        self.board = self.load_board()
        self.chance_cards = self.load_chance_cards()
        self.players = []
        self.current_player = 0
        self.game_state = "waiting"  # waiting, active, finished
    
    def load_board(self) -> List[Dict]:
        """Загрузка игрового поля"""
        try:
            with open('bot/data/board.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_board()
    
    def load_chance_cards(self) -> List[Dict]:
        """Загрузка карточек шанса"""
        try:
            with open('bot/data/chance_cards.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_cards()
    
    def _create_default_board(self) -> List[Dict]:
        """Создание поля по умолчанию"""
        return [
            {"id": 0, "name": "СТАРТ", "type": "go", "price": 0, "rent": 0},
            {"id": 1, "name": "Улица 1", "type": "property", "price": 60, "rent": 2},
            {"id": 2, "name": "Казна", "type": "community", "price": 0, "rent": 0}
        ]
    
    def _create_default_cards(self) -> List[Dict]:
        """Создание карточек по умолчанию"""
        return [
            {"id": 1, "type": "chance", "description": "Получите $50", "action": "receive_money", "value": 50}
        ]
    
    def add_player(self, player_id: int, name: str):
        """Добавление игрока"""
        player = {
            "id": player_id,
            "name": name,
            "position": 0,
            "balance": 1500,
            "properties": [],
            "in_jail": False,
            "jail_turns": 0
        }
        self.players.append(player)
        return player
    
    def roll_dice(self) -> tuple:
        """Бросок кубиков"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1, dice2, dice1 + dice2
    
    def move_player(self, player_index: int, steps: int):
        """Перемещение игрока"""
        player = self.players[player_index]
        old_position = player["position"]
        new_position = (old_position + steps) % len(self.board)
        
        player["position"] = new_position
        
        # Проверяем прохождение старта
        if new_position < old_position:
            player["balance"] += 200
            return {"passed_go": True, "bonus": 200}
        
        return {"passed_go": False}
    
    def buy_property(self, player_index: int, property_id: int) -> bool:
        """Покупка недвижимости"""
        player = self.players[player_index]
        property_data = next((p for p in self.board if p["id"] == property_id), None)
        
        if not property_data or property_data["type"] != "property":
            return False
        
        if player["balance"] >= property_data["price"]:
            player["balance"] -= property_data["price"]
            player["properties"].append(property_id)
            return True
        
        return False
    
    def pay_rent(self, payer_index: int, owner_index: int, property_id: int) -> bool:
        """Оплата аренды"""
        payer = self.players[payer_index]
        owner = self.players[owner_index]
        property_data = next((p for p in self.board if p["id"] == property_id), None)
        
        if not property_data:
            return False
        
        rent = property_data["rent"]
        
        if payer["balance"] >= rent:
            payer["balance"] -= rent
            owner["balance"] += rent
            return True
        
        return False
    
    def draw_chance_card(self):
        """Взятие карточки шанса"""
        if not self.chance_cards:
            return None
        
        card = random.choice(self.chance_cards)
        return card
    
    def get_player_info(self, player_index: int) -> Dict:
        """Информация об игроке"""
        player = self.players[player_index]
        
        return {
            "name": player["name"],
            "position": player["position"],
            "balance": player["balance"],
            "properties_count": len(player["properties"]),
            "in_jail": player["in_jail"]
        }
    
    def get_board_info(self) -> List[Dict]:
        """Информация о текущем состоянии поля"""
        board_info = []
        
        for cell in self.board:
            cell_info = {
                "id": cell["id"],
                "name": cell["name"],
                "type": cell["type"],
                "owner": None
            }
            
            # Находим владельца
            for player in self.players:
                if cell["id"] in player["properties"]:
                    cell_info["owner"] = player["name"]
                    break
            
            board_info.append(cell_info)
        
        return board_info

# Создаем глобальный экземпляр игры
game_instance = MonopolyGame()

def get_game() -> MonopolyGame:
    """Получить экземпляр игры"""
    return game_instance
