"""
Core game logic
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import random

from .player import Player
from .property import Property
from .dice import Dice
from .jail import JailSystem
from .trade import TradeSystem
from .mortgage import MortgageSystem
from .cards import CardSystem
from .auction import Auction
from .bank import Bank

logger = logging.getLogger(__name__)

class MonopolyGame:
    """Основной класс игры Монополия"""
    
    def __init__(self, game_id: str, chat_id: int, settings: Dict = None):
        self.game_id = game_id
        self.chat_id = chat_id
        self.settings = settings or {}
        
        # Игровые компоненты
        self.players: Dict[str, Player] = {}
        self.properties: Dict[int, Property] = {}
        self.board = self._create_board()
        self.dice = Dice()
        self.jail_system = JailSystem()
        self.trade_system = TradeSystem()
        self.mortgage_system = MortgageSystem()
        self.card_system = CardSystem()
        self.auction = Auction()
        self.bank = Bank()
        
        # Состояние игры
        self.current_player_index = 0
        self.turn_number = 0
        self.game_state = "waiting"  # waiting, active, finished
        self.winner: Optional[Player] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # История игры
        self.history: List[Dict] = []
        
        logger.info(f"Игра {game_id} создана в чате {chat_id}")
    
    def _create_board(self) -> List[Dict]:
        """Создать игровое поле"""
        # Стандартное поле Монополии (Московская версия)
        board = [
            # 0-9
            {"position": 0, "name": "Старт", "type": "start", "action": "collect_200"},
            {"position": 1, "name": "Житная", "type": "property", "group": "brown", "price": 60, "rent": [2, 10, 30, 90, 160, 250]},
            {"position": 2, "name": "Общественная казна", "type": "chest", "action": "draw_chest_card"},
            {"position": 3, "name": "Нагатинская", "type": "property", "group": "brown", "price": 60, "rent": [4, 20, 60, 180, 320, 450]},
            {"position": 4, "name": "Налог на доход", "type": "tax", "amount": 200},
            {"position": 5, "name": "Рижская ж/д", "type": "railroad", "price": 200, "rent": [25, 50, 100, 200]},
            {"position": 6, "name": "Варшавское шоссе", "type": "property", "group": "lightblue", "price": 100, "rent": [6, 30, 90, 270, 400, 550]},
            {"position": 7, "name": "Шанс", "type": "chance", "action": "draw_chance_card"},
            {"position": 8, "name": "Огородный проспект", "type": "property", "group": "lightblue", "price": 100, "rent": [6, 30, 90, 270, 400, 550]},
            {"position": 9, "name": "Рижская", "type": "property", "group": "lightblue", "price": 120, "rent": [8, 40, 100, 300, 450, 600]},
            
            # 10-19
            {"position": 10, "name": "Тюрьма (просто посетить)", "type": "jail_visit"},
            {"position": 11, "name": "Курская", "type": "property", "group": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750]},
            {"position": 12, "name": "Электросеть", "type": "utility", "price": 150, "multiplier": [4, 10]},
            {"position": 13, "name": "Абрамцево", "type": "property", "group": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750]},
            {"position": 14, "name": "Пантелеевская", "type": "property", "group": "pink", "price": 160, "rent": [12, 60, 180, 500, 700, 900]},
            {"position": 15, "name": "Казанская ж/д", "type": "railroad", "price": 200, "rent": [25, 50, 100, 200]},
            {"position": 16, "name": "Вавилова", "type": "property", "group": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950]},
            {"position": 17, "name": "Общественная казна", "type": "chest", "action": "draw_chest_card"},
            {"position": 18, "name": "Тимирязевская", "type": "property", "group": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950]},
            {"position": 19, "name": "Лихоборы", "type": "property", "group": "orange", "price": 200, "rent": [16, 80, 220, 600, 800, 1000]},
            
            # 20-29
            {"position": 20, "name": "Бесплатная стоянка", "type": "free_parking"},
            {"position": 21, "name": "Арбат", "type": "property", "group": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050]},
            {"position": 22, "name": "Шанс", "type": "chance", "action": "draw_chance_card"},
            {"position": 23, "name": "Полянка", "type": "property", "group": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050]},
            {"position": 24, "name": "Сретенка", "type": "property", "group": "red", "price": 240, "rent": [20, 100, 300, 750, 925, 1100]},
            {"position": 25, "name": "Курская ж/д", "type": "railroad", "price": 200, "rent": [25, 50, 100, 200]},
            {"position": 26, "name": "Ростовская", "type": "property", "group": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150]},
            {"position": 27, "name": "Рязанский проспект", "type": "property", "group": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150]},
            {"position": 28, "name": "Водопровод", "type": "utility", "price": 150, "multiplier": [4, 10]},
            {"position": 29, "name": "Новинский бульвар", "type": "property", "group": "yellow", "price": 280, "rent": [24, 120, 360, 850, 1025, 1200]},
            
            # 30-39
            {"position": 30, "name": "Отправляйтесь в тюрьму", "type": "go_to_jail", "action": "go_to_jail"},
            {"position": 31, "name": "Пушкинская", "type": "property", "group": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275]},
            {"position": 32, "name": "Тверская", "type": "property", "group": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275]},
            {"position": 33, "name": "Общественная казна", "type": "chest", "action": "draw_chest_card"},
            {"position": 34, "name": "Маяковского", "type": "property", "group": "green", "price": 320, "rent": [28, 150, 450, 1000, 1200, 1400]},
            {"position": 35, "name": "Ленинградская ж/д", "type": "railroad", "price": 200, "rent": [25, 50, 100, 200]},
            {"position": 36, "name": "Шанс", "type": "chance", "action": "draw_chance_card"},
            {"position": 37, "name": "Кутузовский проспект", "type": "property", "group": "darkblue", "price": 350, "rent": [35, 175, 500, 1100, 1300, 1500]},
            {"position": 38, "name": "Налог на роскошь", "type": "tax", "amount": 100},
            {"position": 39, "name": "Бродвей", "type": "property", "group": "darkblue", "price": 400, "rent": [50, 200, 600, 1400, 1700, 2000]},
        ]
        
        return board
    
    def add_player(self, user_id: int, username: str, name: str) -> bool:
        """Добавить игрока в игру"""
        if self.game_state != "waiting":
            logger.warning(f"Нельзя добавить игрока: игра уже началась")
            return False
        
        player_id = str(user_id)
        if player_id in self.players:
            logger.warning(f"Игрок {player_id} уже в игре")
            return False
        
        # Создаем игрока
        player = Player(user_id, username, name)
        self.players[player_id] = player
        
        logger.info(f"Игрок {name} ({user_id}) добавлен в игру {self.game_id}")
        return True
    
    def remove_player(self, user_id: int) -> bool:
        """Удалить игрока из игры"""
        player_id = str(user_id)
        if player_id not in self.players:
            return False
        
        # Если игра активна, помечаем игрока как банкрота
        if self.game_state == "active":
            player = self.players[player_id]
            player.is_bankrupt = True
            
            # Освобождаем собственность
            for prop in player.properties.values():
                prop.owner = None
                prop.is_mortgaged = False
            
            logger.info(f"Игрок {player.name} вышел из активной игры")
        else:
            del self.players[player_id]
            logger.info(f"Игрок удален из лобби")
        
        return True
    
    def start_game(self) -> bool:
        """Начать игру"""
        if self.game_state != "waiting":
            return False
        
        if len(self.players) < 2:
            logger.warning(f"Недостаточно игроков для начала игры: {len(self.players)}")
            return False
        
        # Инициализируем игровое поле
        self._initialize_properties()
        
        # Устанавливаем начальные параметры
        self.game_state = "active"
        self.start_time = datetime.now()
        self.current_player_index = 0
        
        # Определяем порядок ходов (случайный)
        player_ids = list(self.players.keys())
        random.shuffle(player_ids)
        
        # Переупорядочиваем игроков
        reordered_players = {}
        for i, player_id in enumerate(player_ids):
            player = self.players[player_id]
            player.player_index = i
            reordered_players[player_id] = player
        
        self.players = reordered_players
        
        logger.info(f"Игра {self.game_id} началась с {len(self.players)} игроками")
        
        # Записываем в историю
        self.add_to_history("game_start", {
            "players": [p.name for p in self.players.values()],
            "start_time": self.start_time.isoformat()
        })
        
        return True
    
    def _initialize_properties(self):
        """Инициализировать свойства на поле"""
        for cell in self.board:
            if cell["type"] in ["property", "railroad", "utility"]:
                prop = Property(
                    position=cell["position"],
                    name=cell["name"],
                    price=cell["price"],
                    group=cell.get("group"),
                    rent=cell.get("rent"),
                    multiplier=cell.get("multiplier")
                )
                self.properties[cell["position"]] = prop
    
    def get_current_player(self) -> Optional[Player]:
        """Получить текущего игрока"""
        player_ids = list(self.players.keys())
        if not player_ids:
            return None
        
        if self.current_player_index >= len(player_ids):
            self.current_player_index = 0
        
        player_id = player_ids[self.current_player_index]
        return self.players.get(player_id)
    
    async def process_turn(self, player_id: int, dice_roll: Tuple[int, int] = None) -> Dict:
        """Обработать ход игрока"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        if player.is_bankrupt:
            return {"success": False, "error": "Игрок банкрот"}
        
        if player.is_in_jail:
            return await self._process_jail_turn(player)
        
        # Бросаем кубики, если не предоставлен результат
        if dice_roll is None:
            dice_roll = self.dice.roll()
        
        dice1, dice2 = dice_roll
        total = dice1 + dice2
        is_double = dice1 == dice2
        
        # Обновляем счетчик дублей
        if is_double:
            player.double_count += 1
            if player.double_count >= 3:
                # 3 дубля подряд - в тюрьму
                await self._send_to_jail(player, "Три дубля подряд")
                return {
                    "success": True,
                    "dice": dice_roll,
                    "action": "go_to_jail",
                    "reason": "three_doubles"
                }
        else:
            player.double_count = 0
        
        # Двигаем игрока
        old_position = player.position
        new_position = (old_position + total) % 40
        player.position = new_position
        
        # Обрабатываем клетку
        cell_result = await self._process_cell(player, new_position)
        
        # Если дубль и игрок не в тюрьме - дает еще ход
        next_player_id = None
        if not is_double or player.is_in_jail:
            next_player_id = self._get_next_player_id()
        
        result = {
            "success": True,
            "player": player.name,
            "dice": dice_roll,
            "old_position": old_position,
            "new_position": new_position,
            "cell_result": cell_result,
            "is_double": is_double,
            "extra_turn": is_double and not player.is_in_jail,
            "next_player": next_player_id
        }
        
        # Записываем в историю
        self.add_to_history("turn", {
            "player": player.name,
            "dice": dice_roll,
            "position": new_position,
            "action": cell_result.get("action", "move")
        })
        
        return result
    
    async def _process_jail_turn(self, player: Player) -> Dict:
        """Обработать ход игрока в тюрьме"""
        # Игрок может попытаться выйти
        result = await self.jail_system.process_turn(player)
        
        if result.get("released", False):
            # Игрок вышел из тюрьмы
            player.is_in_jail = False
            player.jail_turns = 0
            
            # Теперь он может сделать обычный ход
            return await self.process_turn(player.user_id)
        
        # Игрок остался в тюрьме
        player.jail_turns += 1
        
        # Если 3 хода в тюрьме - автоматически выходит
        if player.jail_turns >= 3:
            fine = 50
            if player.balance >= fine:
                player.balance -= fine
                player.is_in_jail = False
                player.jail_turns = 0
                
                # Записываем в историю
                self.add_to_history("jail_release", {
                    "player": player.name,
                    "method": "forced_payment",
                    "fine": fine
                })
                
                return {
                    "success": True,
                    "action": "jail_release_forced",
                    "fine": fine,
                    "next_player": self._get_next_player_id()
                }
        
        # Передаем ход следующему игроку
        return {
            "success": True,
            "action": "jail_wait",
            "turns_in_jail": player.jail_turns,
            "next_player": self._get_next_player_id()
        }
    
    async def _process_cell(self, player: Player, position: int) -> Dict:
        """Обработать клетку, на которую попал игрок"""
        cell = self.board[position]
        cell_type = cell["type"]
        
        result = {"cell": cell["name"], "type": cell_type}
        
        if cell_type == "property":
            return await self._process_property_cell(player, cell)
        elif cell_type == "railroad":
            return await self._process_railroad_cell(player, cell)
        elif cell_type == "utility":
            return await self._process_utility_cell(player, cell)
        elif cell_type == "tax":
            return await self._process_tax_cell(player, cell)
        elif cell_type == "chest":
            return await self._process_chest_cell(player)
        elif cell_type == "chance":
            return await self._process_chance_cell(player)
        elif cell_type == "go_to_jail":
            return await self._send_to_jail(player, "Попал на 'Отправляйтесь в тюрьму'")
        elif cell_type == "start":
            return await self._process_start_cell(player)
        elif cell_type == "free_parking":
            return await self._process_free_parking_cell(player)
        
        return result
    
    async def _process_property_cell(self, player: Player, cell: Dict) -> Dict:
        """Обработать клетку с недвижимостью"""
        position = cell["position"]
        property_obj = self.properties.get(position)
        
        if not property_obj:
            return {"action": "error", "error": "Property not found"}
        
        if property_obj.owner is None:
            # Собственность не куплена
            return {
                "action": "property_available",
                "property": property_obj.name,
                "price": property_obj.price,
                "position": position
            }
        elif property_obj.owner == player.user_id:
            # Игрок владеет этой собственностью
            return {
                "action": "own_property",
                "property": property_obj.name
            }
        else:
            # Кто-то другой владеет - платим ренту
            owner = self.players.get(str(property_obj.owner))
            if not owner or owner.is_bankrupt:
                return {"action": "no_rent", "reason": "owner_bankrupt"}
            
            rent_amount = property_obj.calculate_rent()
            
            # Проверяем, может ли игрок заплатить
            if player.balance >= rent_amount:
                player.balance -= rent_amount
                owner.balance += rent_amount
                
                # Записываем в историю
                self.add_to_history("pay_rent", {
                    "payer": player.name,
                    "receiver": owner.name,
                    "property": property_obj.name,
                    "amount": rent_amount
                })
                
                return {
                    "action": "pay_rent",
                    "property": property_obj.name,
                    "owner": owner.name,
                    "amount": rent_amount,
                    "payer_balance": player.balance,
                    "owner_balance": owner.balance
                }
            else:
                # Игрок не может заплатить - банкротство
                return await self._process_bankruptcy(player, owner, rent_amount)
    
    async def _process_railroad_cell(self, player: Player, cell: Dict) -> Dict:
        """Обработать клетку с железной дорогой"""
        position = cell["position"]
        railroad = self.properties.get(position)
        
        if not railroad:
            return {"action": "error", "error": "Railroad not found"}
        
        if railroad.owner is None:
            # Железная дорога не куплена
            return {
                "action": "railroad_available",
                "name": railroad.name,
                "price": railroad.price,
                "position": position
            }
        elif railroad.owner == player.user_id:
            # Игрок владеет этой железной дорогой
            return {
                "action": "own_railroad",
                "name": railroad.name
            }
        else:
            # Кто-то другой владеет - платим ренту
            owner = self.players.get(str(railroad.owner))
            if not owner or owner.is_bankrupt:
                return {"action": "no_rent", "reason": "owner_bankrupt"}
            
            # Считаем количество железных дорог у владельца
            owned_railroads = sum(1 for p in self.properties.values() 
                                if p.type == "railroad" and p.owner == owner.user_id)
            
            rent_amount = railroad.calculate_railroad_rent(owned_railroads)
            
            if player.balance >= rent_amount:
                player.balance -= rent_amount
                owner.balance += rent_amount
                
                return {
                    "action": "pay_railroad_rent",
                    "name": railroad.name,
                    "owner": owner.name,
                    "owned_railroads": owned_railroads,
                    "amount": rent_amount
                }
            else:
                # Банкротство
                return await self._process_bankruptcy(player, owner, rent_amount)
    
    async def _process_utility_cell(self, player: Player, cell: Dict) -> Dict:
        """Обработать клетку с коммунальным предприятием"""
        position = cell["position"]
        utility = self.properties.get(position)
        
        if not utility:
            return {"action": "error", "error": "Utility not found"}
        
        if utility.owner is None:
            # Коммунальное предприятие не куплено
            return {
                "action": "utility_available",
                "name": utility.name,
                "price": utility.price,
                "position": position
            }
        elif utility.owner == player.user_id:
            # Игрок владеет
            return {
                "action": "own_utility",
                "name": utility.name
            }
        else:
            # Кто-то другой владеет
            owner = self.players.get(str(utility.owner))
            if not owner or owner.is_bankrupt:
                return {"action": "no_rent", "reason": "owner_bankrupt"}
            
            # Считаем количество коммунальных предприятий у владельца
            owned_utilities = sum(1 for p in self.properties.values() 
                                 if p.type == "utility" and p.owner == owner.user_id)
            
            # Получаем последний бросок кубиков
            dice_roll = self.dice.get_last_roll()
            if not dice_roll:
                dice_roll = (1, 1)  # По умолчанию
            
            rent_amount = utility.calculate_utility_rent(owned_utilities, sum(dice_roll))
            
            if player.balance >= rent_amount:
                player.balance -= rent_amount
                owner.balance += rent_amount
                
                return {
                    "action": "pay_utility_rent",
                    "name": utility.name,
                    "owner": owner.name,
                    "owned_utilities": owned_utilities,
                    "dice_roll": sum(dice_roll),
                    "amount": rent_amount
                }
            else:
                # Банкротство
                return await self._process_bankruptcy(player, owner, rent_amount)
    
    async def _process_tax_cell(self, player: Player, cell: Dict) -> Dict:
        """Обработать клетку с налогом"""
        tax_amount = cell.get("amount", 0)
        
        if player.balance >= tax_amount:
            player.balance -= tax_amount
            # Налог идет в банк бесплатной парковки или сгорает
            # В классической версии - в банк
            
            return {
                "action": "pay_tax",
                "amount": tax_amount,
                "balance": player.balance
            }
        else:
            return {
                "action": "tax_bankruptcy",
                "amount": tax_amount,
                "balance": player.balance
            }
    
    async def _process_chest_cell(self, player: Player) -> Dict:
        """Обработать клетку 'Общественная казна'"""
        card = self.card_system.draw_chest_card()
        return await self._execute_card(player, card, "chest")
    
    async def _process_chance_cell(self, player: Player) -> Dict:
        """Обработать клетку 'Шанс'"""
        card = self.card_system.draw_chance_card()
        return await self._execute_card(player, card, "chance")
    
    async def _process_start_cell(self, player: Player) -> Dict:
        """Обработать клетку 'Старт'"""
        salary = 200
        player.balance += salary
        
        return {
            "action": "collect_salary",
            "amount": salary,
            "balance": player.balance
        }
    
    async def _process_free_parking_cell(self, player: Player) -> Dict:
        """Обработать клетку 'Бесплатная парковка'"""
        # В некоторых версиях здесь лежат деньги
        parking_money = self.bank.free_parking
        if parking_money > 0:
            player.balance += parking_money
            self.bank.free_parking = 0
            
            return {
                "action": "collect_free_parking",
                "amount": parking_money,
                "balance": player.balance
            }
        
        return {
            "action": "free_parking",
            "message": "Бесплатная стоянка"
        }
    
    async def _send_to_jail(self, player: Player, reason: str) -> Dict:
        """Отправить игрока в тюрьму"""
        player.is_in_jail = True
        player.position = 10  # Позиция тюрьмы
        player.jail_turns = 0
        
        # Записываем в историю
        self.add_to_history("go_to_jail", {
            "player": player.name,
            "reason": reason
        })
        
        return {
            "action": "go_to_jail",
            "reason": reason,
            "position": 10
        }
    
    async def _execute_card(self, player: Player, card: Dict, deck_type: str) -> Dict:
        """Выполнить действие карточки"""
        action = card.get("action", "")
        result = {"action": "card", "card_type": deck_type, "card_text": card.get("text", "")}
        
        if action == "collect_money":
            amount = card.get("amount", 0)
            player.balance += amount
            
            result.update({
                "sub_action": "collect",
                "amount": amount,
                "balance": player.balance
            })
            
        elif action == "pay_money":
            amount = card.get("amount", 0)
            if player.balance >= amount:
                player.balance -= amount
                # Деньги идут в банк
                
                result.update({
                    "sub_action": "pay",
                    "amount": amount,
                    "balance": player.balance
                })
            else:
                result.update({
                    "sub_action": "pay_bankruptcy",
                    "amount": amount,
                    "balance": player.balance
                })
                
        elif action == "move_to":
            position = card.get("position", 0)
            player.position = position
            
            # Если прошел через старт
            if position < player.position:
                player.balance += 200
            
            result.update({
                "sub_action": "move",
                "position": position
            })
            
        elif action == "go_to_jail":
            await self._send_to_jail(player, "Карточка 'Отправляйтесь в тюрьму'")
            result["sub_action"] = "go_to_jail"
            
        elif action == "get_out_of_jail_free":
            player.has_jail_card = True
            result["sub_action"] = "get_jail_card"
            
        elif action == "repairs":
            # Ремонт домов/отелей
            house_cost = card.get("house_cost", 0)
            hotel_cost = card.get("hotel_cost", 0)
            
            total_cost = 0
            for prop in player.properties.values():
                if prop.houses > 0:
                    total_cost += prop.houses * house_cost
                if prop.has_hotel:
                    total_cost += hotel_cost
            
            if player.balance >= total_cost:
                player.balance -= total_cost
                result.update({
                    "sub_action": "repairs",
                    "house_cost": house_cost,
                    "hotel_cost": hotel_cost,
                    "total_cost": total_cost,
                    "balance": player.balance
                })
            else:
                result.update({
                    "sub_action": "repairs_bankruptcy",
                    "total_cost": total_cost,
                    "balance": player.balance
                })
        
        return result
    
    async def _process_bankruptcy(self, player: Player, creditor, debt: int) -> Dict:
        """Обработать банкротство игрока"""
        # Пытаемся продать имущество
        can_pay = await self._try_raise_money(player, debt)
        
        if can_pay:
            player.balance -= debt
            if isinstance(creditor, Player):
                creditor.balance += debt
            
            return {
                "action": "paid_debt",
                "debt": debt,
                "balance": player.balance
            }
        else:
            # Объявляем банкротство
            player.is_bankrupt = True
            
            # Передаем имущество кредитору
            if isinstance(creditor, Player):
                for prop in player.properties.values():
                    prop.owner = creditor.user_id
                    # Сбрасываем залог
                    if prop.is_mortgaged:
                        prop.is_mortgaged = False
            
            # Записываем в историю
            self.add_to_history("bankruptcy", {
                "player": player.name,
                "creditor": creditor.name if isinstance(creditor, Player) else "bank",
                "debt": debt
            })
            
            # Проверяем, остался ли победитель
            active_players = [p for p in self.players.values() if not p.is_bankrupt]
            if len(active_players) == 1:
                self.winner = active_players[0]
                self.game_state = "finished"
                self.end_time = datetime.now()
            
            return {
                "action": "bankruptcy",
                "debt": debt,
                "winner": self.winner.name if self.winner else None
            }
    
    async def _try_raise_money(self, player: Player, amount: int) -> bool:
        """Попытаться собрать деньги (продажа имущества, залог)"""
        # Сначала пытаемся продать дома/отели
        total_raised = 0
        
        for prop in player.properties.values():
            if prop.has_hotel:
                # Продажа отеля дает половину стоимости
                total_raised += prop.hotel_price // 2
                prop.has_hotel = False
                prop.houses = 4
                
                if total_raised >= amount:
                    return True
            
            if prop.houses > 0:
                # Продажа дома дает половину стоимости
                house_value = prop.house_price // 2
                while prop.houses > 0 and total_raised < amount:
                    total_raised += house_value
                    prop.houses -= 1
                
                if total_raised >= amount:
                    return True
        
        # Затем пытаемся заложить недвижимость
        for prop in player.properties.values():
            if not prop.is_mortgaged and prop.houses == 0 and not prop.has_hotel:
                mortgage_value = prop.price // 2
                total_raised += mortgage_value
                prop.is_mortgaged = True
                
                if total_raised >= amount:
                    return True
        
        # Проверяем баланс после всех операций
        player.balance += total_raised
        return player.balance >= amount
    
    def _get_next_player_id(self) -> Optional[int]:
        """Получить ID следующего игрока"""
        player_ids = [pid for pid, p in self.players.items() if not p.is_bankrupt]
        if not player_ids:
            return None
        
        current_id = list(self.players.keys())[self.current_player_index]
        current_idx = player_ids.index(current_id) if current_id in player_ids else 0
        
        next_idx = (current_idx + 1) % len(player_ids)
        next_player_id = player_ids[next_idx]
        
        # Обновляем индекс текущего игрока
        self.current_player_index = list(self.players.keys()).index(next_player_id)
        
        return int(next_player_id)
    
    def add_to_history(self, event_type: str, data: Dict):
        """Добавить событие в историю"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "turn": self.turn_number
        }
        self.history.append(event)
    
    def buy_property(self, player_id: int, position: int) -> Dict:
        """Купить недвижимость"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        property_obj = self.properties.get(position)
        if not property_obj:
            return {"success": False, "error": "Недвижимость не найдена"}
        
        if property_obj.owner is not None:
            return {"success": False, "error": "Недвижимость уже куплена"}
        
        if player.balance < property_obj.price:
            return {"success": False, "error": "Недостаточно денег"}
        
        # Покупка
        player.balance -= property_obj.price
        property_obj.owner = player.user_id
        player.add_property(property_obj)
        
        # Записываем в историю
        self.add_to_history("buy_property", {
            "player": player.name,
            "property": property_obj.name,
            "price": property_obj.price,
            "balance": player.balance
        })
        
        return {
            "success": True,
            "property": property_obj.name,
            "price": property_obj.price,
            "balance": player.balance
        }
    
    def build_house(self, player_id: int, position: int) -> Dict:
        """Построить дом"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        property_obj = self.properties.get(position)
        if not property_obj:
            return {"success": False, "error": "Недвижимость не найдена"}
        
        # Проверяем владение
        if property_obj.owner != player.user_id:
            return {"success": False, "error": "Вы не владеете этой недвижимостью"}
        
        # Проверяем, что это свойство, а не ж/д или коммунальное
        if property_obj.type != "property":
            return {"success": False, "error": "Здесь нельзя строить"}
        
        # Проверяем, что владеем всем цветом
        group_properties = [p for p in self.properties.values() 
                           if p.group == property_obj.group and p.type == "property"]
        
        owns_all = all(p.owner == player.user_id for p in group_properties)
        if not owns_all:
            return {"success": False, "error": "Владейте всеми улицами этого цвета"}
        
        # Проверяем равномерность застройки
        houses_in_group = [p.houses for p in group_properties]
        min_houses = min(houses_in_group)
        max_houses = max(houses_in_group)
        
        if property_obj.houses > min_houses:
            return {"success": False, "error": "Сначала постройте на других улицах"}
        
        if property_obj.houses >= 4:
            return {"success": False, "error": "Максимум 4 дома"}
        
        # Проверяем деньги
        house_price = property_obj.house_price
        if player.balance < house_price:
            return {"success": False, "error": "Недостаточно денег"}
        
        # Строим
        player.balance -= house_price
        property_obj.houses += 1
        
        # Записываем в историю
        self.add_to_history("build_house", {
            "player": player.name,
            "property": property_obj.name,
            "house_price": house_price,
            "houses": property_obj.houses,
            "balance": player.balance
        })
        
        return {
            "success": True,
            "property": property_obj.name,
            "house_price": house_price,
            "houses": property_obj.houses,
            "balance": player.balance
        }
    
    def build_hotel(self, player_id: int, position: int) -> Dict:
        """Построить отель"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        property_obj = self.properties.get(position)
        if not property_obj:
            return {"success": False, "error": "Недвижимость не найдена"}
        
        # Проверяем владение
        if property_obj.owner != player.user_id:
            return {"success": False, "error": "Вы не владеете этой недвижимостью"}
        
        # Проверяем, что есть 4 дома
        if property_obj.houses != 4:
            return {"success": False, "error": "Нужно 4 дома для постройки отеля"}
        
        if property_obj.has_hotel:
            return {"success": False, "error": "Отель уже построен"}
        
        # Проверяем деньги
        hotel_price = property_obj.hotel_price
        if player.balance < hotel_price:
            return {"success": False, "error": "Недостаточно денег"}
        
        # Строим отель
        player.balance -= hotel_price
        property_obj.houses = 0
        property_obj.has_hotel = True
        
        # Записываем в историю
        self.add_to_history("build_hotel", {
            "player": player.name,
            "property": property_obj.name,
            "hotel_price": hotel_price,
            "balance": player.balance
        })
        
        return {
            "success": True,
            "property": property_obj.name,
            "hotel_price": hotel_price,
            "balance": player.balance
        }
    
    def mortgage_property(self, player_id: int, position: int) -> Dict:
        """Заложить недвижимость"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        property_obj = self.properties.get(position)
        if not property_obj:
            return {"success": False, "error": "Недвижимость не найдена"}
        
        # Проверяем владение
        if property_obj.owner != player.user_id:
            return {"success": False, "error": "Вы не владеете этой недвижимостью"}
        
        # Проверяем, не заложена ли уже
        if property_obj.is_mortgaged:
            return {"success": False, "error": "Недвижимость уже заложена"}
        
        # Проверяем, нет ли домов/отелей
        if property_obj.houses > 0 or property_obj.has_hotel:
            return {"success": False, "error": "Сначала продайте постройки"}
        
        # Залогаем
        mortgage_value = property_obj.price // 2
        player.balance += mortgage_value
        property_obj.is_mortgaged = True
        
        # Записываем в историю
        self.add_to_history("mortgage", {
            "player": player.name,
            "property": property_obj.name,
            "mortgage_value": mortgage_value,
            "balance": player.balance
        })
        
        return {
            "success": True,
            "property": property_obj.name,
            "mortgage_value": mortgage_value,
            "balance": player.balance
        }
    
    def unmortgage_property(self, player_id: int, position: int) -> Dict:
        """Выкупить недвижимость из залога"""
        player = self.players.get(str(player_id))
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        property_obj = self.properties.get(position)
        if not property_obj:
            return {"success": False, "error": "Недвижимость не найдена"}
        
        # Проверяем владение
        if property_obj.owner != player.user_id:
            return {"success": False, "error": "Вы не владеете этой недвижимостью"}
        
        # Проверяем, заложена ли
        if not property_obj.is_mortgaged:
            return {"success": False, "error": "Недвижимость не заложена"}
        
        # Стоимость выкупа = залог + 10%
        unmortgage_cost = (property_obj.price // 2) * 1.1
        unmortgage_cost = int(unmortgage_cost)
        
        if player.balance < unmortgage_cost:
            return {"success": False, "error": "Недостаточно денег"}
        
        # Выкупаем
        player.balance -= unmortgage_cost
        property_obj.is_mortgaged = False
        
        # Записываем в историю
        self.add_to_history("unmortgage", {
            "player": player.name,
            "property": property_obj.name,
            "cost": unmortgage_cost,
            "balance": player.balance
        })
        
        return {
            "success": True,
            "property": property_obj.name,
            "cost": unmortgage_cost,
            "balance": player.balance
        }
    
    def get_game_state_summary(self) -> Dict:
        """Получить сводку состояния игры"""
        active_players = [p for p in self.players.values() if not p.is_bankrupt]
        
        return {
            "game_id": self.game_id,
            "state": self.game_state,
            "players": len(self.players),
            "active_players": len(active_players),
            "current_player": self.get_current_player().name if self.get_current_player() else None,
            "turn": self.turn_number,
            "winner": self.winner.name if self.winner else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration": self._get_game_duration()
        }
    
    def _get_game_duration(self) -> str:
        """Получить продолжительность игры"""
        if not self.start_time:
            return "0:00"
        
        end_time = self.end_time or datetime.now()
        duration = end_time - self.start_time
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}"
        else:
            return f"{minutes}:{total_seconds % 60:02d}"
