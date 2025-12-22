"""
GAME_LOGIC.PY - Основная игровая логика (300 строк)
👑 Создано Темным Принцем (Dark Prince) 👑
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from modules.config import (
    BOARD, CHANCE_CARDS, STARTING_BALANCE, 
    JAIL_FINE, MAX_HOUSES, logger, 
    get_property_set, get_rent
)

class MonopolyPlayer:
    """Класс игрока в Монополии"""
    
    def __init__(self, user_id: int, name: str, username: str = ""):
        self.id = user_id
        self.name = name
        self.username = username
        self.balance = STARTING_BALANCE
        self.position = 0
        self.properties: List[int] = []
        self.mortgaged_properties: List[int] = []
        self.houses: Dict[int, int] = {}
        self.in_jail = False
        self.jail_turns = 0
        self.get_out_of_jail_cards = 0
        self.color = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠"][user_id % 6]
        self.doubles_count = 0
        self.bankrupt = False
    
    def add_property(self, property_id: int) -> bool:
        if property_id not in self.properties:
            self.properties.append(property_id)
            self.houses[property_id] = 0
            return True
        return False
    
    def remove_property(self, property_id: int) -> bool:
        if property_id in self.properties:
            self.properties.remove(property_id)
            if property_id in self.houses:
                del self.houses[property_id]
            if property_id in self.mortgaged_properties:
                self.mortgaged_properties.remove(property_id)
            return True
        return False
    
    def get_property_count(self, color: str = None) -> int:
        if color is None:
            return len(self.properties)
        count = 0
        for prop_id in self.properties:
            if prop_id in BOARD and BOARD[prop_id]["color"] == color:
                count += 1
        return count
    
    def has_full_set(self, color: str) -> bool:
        full_set = get_property_set(color)
        return all(p in self.properties for p in full_set)

class MonopolyGame:
    """Класс игры в Монополию"""
    
    def __init__(self, chat_id: int, creator_id: int):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.players: List[MonopolyPlayer] = []
        self.current_player_idx = 0
        self.turn = 1
        self.started_at = datetime.now()
        self.properties: Dict[int, Dict] = {}
        self.chance_deck = CHANCE_CARDS.copy()
        self.community_chest_deck = []
        self.game_over = False
        self.winner = None
        
    def add_player(self, user_id: int, name: str, username: str = "") -> bool:
        if len(self.players) >= 8:
            return False
        if any(p.id == user_id for p in self.players):
            return False
        player = MonopolyPlayer(user_id, name, username)
        self.players.append(player)
        return True
    
    def remove_player(self, user_id: int) -> bool:
        for i, player in enumerate(self.players):
            if player.id == user_id:
                # Продаем все имущество игрока
                for prop_id in player.properties[:]:
                    self.sell_property(player, prop_id)
                self.players.pop(i)
                
                if self.current_player_idx >= len(self.players):
                    self.current_player_idx = 0
                return True
        return False
    
    def get_current_player(self) -> Optional[MonopolyPlayer]:
        if not self.players:
            return None
        return self.players[self.current_player_idx]
    
    def next_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.players[self.current_player_idx].doubles_count = 0
    
    def roll_dice(self, player: MonopolyPlayer) -> tuple:
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        if dice1 == dice2:
            player.doubles_count += 1
        else:
            player.doubles_count = 0
        
        return dice1, dice2, total
    
    def move_player(self, player: MonopolyPlayer, steps: int):
        old_pos = player.position
        new_pos = (old_pos + steps) % 40
        player.position = new_pos
        
        # Проверка прохождения через старт
        if old_pos > new_pos:
            player.balance += 200
            logger.info(f"Игрок {player.name} прошел СТАРТ и получил 200$")
        
        return new_pos
    
    def process_position(self, player: MonopolyPlayer, position: int) -> Dict[str, Any]:
        result = {
            "position": position,
            "message": "",
            "action_required": False,
            "can_buy": False,
            "rent_due": 0,
            "special_action": None
        }
        
        if position not in BOARD:
            return result
        
        cell = BOARD[position]
        result["cell_name"] = cell["name"]
        result["cell_type"] = cell["type"]
        
        # Обработка разных типов клеток
        if cell["type"] == "start":
            result["message"] = "🏁 Вы на СТАРТЕ! Получите 200$ при следующем ходе."
        
        elif cell["type"] == "property":
            if position in self.properties:
                owner_info = self.properties[position]
                if owner_info["owner"] != player.id:
                    # Вычисляем аренду
                    owner = self.get_player_by_id(owner_info["owner"])
                    if owner and position not in owner.mortgaged_properties:
                        rent = self.calculate_rent(position, owner_info["houses"])
                        result["rent_due"] = rent
                        result["message"] = f"🏠 Это собственность {owner.name}. Платите аренду: {rent}$"
                else:
                    result["message"] = "🏠 Это ваша собственность!"
            else:
                result["can_buy"] = True
                result["message"] = f"🏠 Свободная недвижимость! Цена: {cell['price']}$"
        
        elif cell["type"] == "railroad":
            if position in self.properties:
                owner_info = self.properties[position]
                if owner_info["owner"] != player.id:
                    railroads_owned = self.count_railroads_owned(owner_info["owner"])
                    rent = cell["rent"][railroads_owned - 1] if railroads_owned <= 4 else 200
                    result["rent_due"] = rent
                    result["message"] = f"🚂 Железная дорога {owner_info['owner_name']}. Платите: {rent}$"
            else:
                result["can_buy"] = True
                result["message"] = f"🚂 Свободная ж/д! Цена: {cell['price']}$"
        
        elif cell["type"] == "utility":
            if position in self.properties:
                owner_info = self.properties[position]
                if owner_info["owner"] != player.id:
                    dice_roll = random.randint(1, 6) + random.randint(1, 6)
                    utilities_owned = self.count_utilities_owned(owner_info["owner"])
                    multiplier = 4 if utilities_owned == 1 else 10
                    rent = dice_roll * multiplier
                    result["rent_due"] = rent
                    result["message"] = f"💡 Коммунальное предприятие. Платите: {rent}$"
            else:
                result["can_buy"] = True
                result["message"] = f"💡 Свободное предприятие! Цена: {cell['price']}$"
        
        elif cell["type"] == "tax":
            tax = cell["price"]
            result["rent_due"] = tax
            result["message"] = f"💸 Налог! Заплатите {tax}$"
        
        elif cell["type"] == "chance":
            result["special_action"] = "chance"
            result["message"] = "🎲 КАРТА ШАНСА! Нажмите кнопку чтобы вытянуть карту"
        
        elif cell["type"] == "jail":
            result["message"] = "🚓 Вы просто посещаете тюрьму"
        
        elif cell["type"] == "go_jail":
            result["special_action"] = "go_to_jail"
            result["message"] = "⛓️ ИДИТЕ В ТЮРЬМУ! Не проходите СТАРТ, не получайте 200$"
        
        elif cell["type"] == "free":
            result["message"] = "🅿️ Бесплатная стоянка! Отдыхайте"
        
        return result
    
    def calculate_rent(self, position: int, houses: int) -> int:
        if position not in BOARD:
            return 0
        
        cell = BOARD[position]
        if houses >= 5:  # Отель
            return cell["rent"][5] if len(cell["rent"]) > 5 else cell["rent"][-1]
        elif houses > 0:  # Дома
            return cell["rent"][houses] if len(cell["rent"]) > houses else cell["rent"][-1]
        else:  # Без домов
            # Проверяем, есть ли полный набор у владельца
            owner_id = self.properties[position]["owner"]
            owner = self.get_player_by_id(owner_id)
            if owner and owner.has_full_set(cell["color"]):
                return cell["rent"][0] * 2  # Двойная аренда
            return cell["rent"][0]
    
    def count_railroads_owned(self, owner_id: int) -> int:
        count = 0
        for prop_id, prop_info in self.properties.items():
            if prop_info["owner"] == owner_id and BOARD[prop_id]["type"] == "railroad":
                count += 1
        return count
    
    def count_utilities_owned(self, owner_id: int) -> int:
        count = 0
        for prop_id, prop_info in self.properties.items():
            if prop_info["owner"] == owner_id and BOARD[prop_id]["type"] == "utility":
                count += 1
        return count
    
    def get_player_by_id(self, user_id: int) -> Optional[MonopolyPlayer]:
        for player in self.players:
            if player.id == user_id:
                return player
        return None
    
    def buy_property(self, player: MonopolyPlayer, position: int) -> bool:
        if position not in BOARD:
            return False
        
        if position in self.properties:
            return False
        
        price = BOARD[position]["price"]
        if player.balance < price:
            return False
        
        player.balance -= price
        player.add_property(position)
        
        self.properties[position] = {
            "owner": player.id,
            "owner_name": player.name,
            "houses": 0,
            "mortgaged": False,
            "purchase_price": price,
            "purchase_turn": self.turn
        }
        
        return True
    
    def sell_property(self, player: MonopolyPlayer, position: int) -> bool:
        if position not in player.properties:
            return False
        
        # Возвращаем половину стоимости покупки
        if position in self.properties:
            purchase_price = self.properties[position].get("purchase_price", 0)
            refund = purchase_price // 2
            
            # Плюс стоимость домов/отелей
            houses = player.houses.get(position, 0)
            if houses > 0:
                house_cost = BOARD[position].get("house_cost", 50)
                hotel_cost = BOARD[position].get("hotel_cost", 50)
                
                if houses == 5:  # Отель
                    refund += hotel_cost // 2
                else:
                    refund += (houses * house_cost) // 2
            
            player.balance += refund
        
        player.remove_property(position)
        if position in self.properties:
            del self.properties[position]
        
        return True
    
    def mortgage_property(self, player: MonopolyPlayer, position: int) -> bool:
        if position not in player.properties:
            return False
        
        if position in player.mortgaged_properties:
            return False
        
        # Нельзя закладывать недвижимость с домами
        if player.houses.get(position, 0) > 0:
            return False
        
        mortgage_value = BOARD[position].get("mortgage", 0)
        if mortgage_value == 0:
            return False
        
        player.balance += mortgage_value
        player.mortgaged_properties.append(position)
        
        if position in self.properties:
            self.properties[position]["mortgaged"] = True
        
        return True
    
    def unmortgage_property(self, player: MonopolyPlayer, position: int) -> bool:
        if position not in player.mortgaged_properties:
            return False
        
        unmortgage_cost = int(BOARD[position].get("mortgage", 0) * 1.1)
        if player.balance < unmortgage_cost:
            return False
        
        player.balance -= unmortgage_cost
        player.mortgaged_properties.remove(position)
        
        if position in self.properties:
            self.properties[position]["mortgaged"] = False
        
        return True
    
    def build_house(self, player: MonopolyPlayer, position: int) -> bool:
        if position not in player.properties:
            return False
        
        if position in player.mortgaged_properties:
            return False
        
        current_houses = player.houses.get(position, 0)
        if current_houses >= 5:  # Уже отель
            return False
        
        house_cost = BOARD[position].get("house_cost", 50)
        if player.balance < house_cost:
            return False
        
        # Проверяем возможность строительства
        color = BOARD[position]["color"]
        if not player.has_full_set(color):
            return False
        
        player.balance -= house_cost
        player.houses[position] = current_houses + 1
        
        if position in self.properties:
            self.properties[position]["houses"] = player.houses[position]
        
        return True

  def sell_house(self, player: MonopolyPlayer, position: int) -> bool:
    if position not in player.properties:
        return False
    
    current_houses = player.houses.get(position, 0)
    if current_houses == 0:
        return False
    
    house_cost = BOARD[position].get("house_cost", 50)
    refund = house_cost // 2
    
    player.balance += refund
    player.houses[position] = current_houses - 1
    
    if position in self.properties:
        self.properties[position]["houses"] = player.houses[position]
    
    return True

def draw_chance_card(self, player: MonopolyPlayer) -> Dict[str, Any]:
    if not self.chance_deck:
        self.chance_deck = CHANCE_CARDS.copy()
        random.shuffle(self.chance_deck)
    
    card_text = self.chance_deck.pop()
    result = {
        "card": card_text,
        "action": None,
        "amount": 0,
        "move_to": None,
        "jail": False
    }
    
    # Парсинг карточки
    if "Пройдите на СТАРТ" in card_text:
        result["action"] = "move"
        result["move_to"] = 0
        result["amount"] = 200
    
    elif "Идите в тюрьму" in card_text:
        result["action"] = "jail"
        result["jail"] = True
    
    elif "Заплатите за ремонт" in card_text:
        result["action"] = "pay_for_houses"
        # Считаем стоимость ремонта
        total_cost = 0
        for prop_id, houses in player.houses.items():
            if houses == 5:  # Отель
                total_cost += 115
            elif houses > 0:  # Дома
                total_cost += houses * 40
        result["amount"] = total_cost
    
    elif "Освобождение из тюрьмы" in card_text:
        result["action"] = "get_out_of_jail_card"
        player.get_out_of_jail_cards += 1
    
    elif "Аванс на три хода" in card_text:
        result["action"] = "move_forward"
        result["amount"] = 3
    
    elif "Банковская ошибка" in card_text:
        result["action"] = "receive"
        result["amount"] = 200
    
    elif "Вы выиграли конкурс" in card_text:
        result["action"] = "receive"
        result["amount"] = 100
    
    elif "Заплатите штраф" in card_text:
        result["action"] = "pay"
        result["amount"] = 15
    
    elif "Заплатите каждому игроку" in card_text:
        result["action"] = "pay_each_player"
        result["amount"] = 50
    
    elif "Получите 150$" in card_text:
        result["action"] = "receive"
        result["amount"] = 150
    
    elif "Вернитесь на три шага" in card_text:
        result["action"] = "move_back"
        result["amount"] = 3
    
    elif "Отправляйтесь на ближайшую железную дорогу" in card_text:
        result["action"] = "nearest_railroad"
        # Ищем ближайшую ж/д
        railroads = [5, 15, 25, 35]
        nearest = min(railroads, key=lambda x: abs(x - player.position))
        result["move_to"] = nearest
    
    elif "Отправляйтесь на ближайшее коммунальное предприятие" in card_text:
        result["action"] = "nearest_utility"
        utilities = [12, 28]
        nearest = min(utilities, key=lambda x: abs(x - player.position))
        result["move_to"] = nearest
    
    return result

def execute_chance_card(self, player: MonopolyPlayer, card_result: Dict) -> str:
    action = card_result["action"]
    message = f"🎲 Шанс: {card_result['card']}\n\n"
    
    if action == "move" and card_result["move_to"] is not None:
        old_pos = player.position
        player.position = card_result["move_to"]
        if card_result["amount"] > 0:
            player.balance += card_result["amount"]
            message += f"💰 Получено: {card_result['amount']}$\n"
        message += f"📍 Перемещение: {old_pos} → {player.position}"
    
    elif action == "jail":
        player.in_jail = True
        player.position = 10  # Тюрьма
        message += "⛓️ Вы отправлены в тюрьму!"
    
    elif action == "pay_for_houses":
        amount = card_result["amount"]
        if player.balance >= amount:
            player.balance -= amount
            message += f"💸 Оплачено: {amount}$ за ремонт"
        else:
            message += f"❌ Недостаточно средств! Нужно {amount}$"
    
    elif action == "get_out_of_jail_card":
        message += "🎫 Вы получили карту освобождения из тюрьмы!"
    
    elif action == "move_forward":
        steps = card_result["amount"]
        new_pos = self.move_player(player, steps)
        message += f"📍 Аванс на {steps} шага: {player.position-steps if player.position>=steps else 40+(player.position-steps)} → {new_pos}"
    
    elif action == "receive":
        amount = card_result["amount"]
        player.balance += amount
        message += f"💰 Получено: {amount}$"
    
    elif action == "pay":
        amount = card_result["amount"]
        if player.balance >= amount:
            player.balance -= amount
            message += f"💸 Оплачено: {amount}$"
        else:
            message += f"❌ Недостаточно средств!"
    
    elif action == "pay_each_player":
        amount = card_result["amount"]
        total = amount * (len(self.players) - 1)
        if player.balance >= total:
            player.balance -= total
            # Раздаем другим игрокам
            for other in self.players:
                if other.id != player.id:
                    other.balance += amount
            message += f"💸 Оплачено каждому игроку по {amount}$"
        else:
            message += f"❌ Недостаточно средств! Нужно {total}$"
    
    elif action == "move_back":
        steps = card_result["amount"]
        old_pos = player.position
        player.position = (player.position - steps) % 40
        message += f"📍 Возврат на {steps} шага: {old_pos} → {player.position}"
    
    elif action == "nearest_railroad" and card_result["move_to"] is not None:
        railroad_pos = card_result["move_to"]
        # Если владелец есть - платим в 2 раза больше аренды
        if railroad_pos in self.properties:
            owner_info = self.properties[railroad_pos]
            if owner_info["owner"] != player.id:
                rent = self.calculate_rent(railroad_pos, owner_info["houses"])
                rent *= 2  # В 2 раза больше
                if player.balance >= rent:
                    player.balance -= rent
                    owner = self.get_player_by_id(owner_info["owner"])
                    if owner:
                        owner.balance += rent
                    message += f"🚂 Ближайшая ж/д! Платите {rent}$"
                else:
                    message += f"🚂 Ближайшая ж/д! Нужно {rent}$, но у вас недостаточно"
            else:
                message += f"🚂 Это ваша ж/д!"
        else:
            player.position = railroad_pos
            message += f"🚂 Перемещение на ж/д {BOARD[railroad_pos]['name']}"
    
    elif action == "nearest_utility" and card_result["move_to"] is not None:
        utility_pos = card_result["move_to"]
        # Бросаем кубики для расчета аренды
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        dice_total = dice1 + dice2
        
        if utility_pos in self.properties:
            owner_info = self.properties[utility_pos]
            if owner_info["owner"] != player.id:
                utilities_owned = self.count_utilities_owned(owner_info["owner"])
                multiplier = 10 if utilities_owned == 2 else 4
                rent = dice_total * multiplier
                
                if player.balance >= rent:
                    player.balance -= rent
                    owner = self.get_player_by_id(owner_info["owner"])
                    if owner:
                        owner.balance += rent
                    message += f"💡 Ближайшее предприятие! Кубики: {dice_total}, платите {rent}$"
                else:
                    message += f"💡 Ближайшее предприятие! Нужно {rent}$, но у вас недостаточно"
            else:
                message += f"💡 Это ваше предприятие!"
        else:
            player.position = utility_pos
            message += f"💡 Перемещение на {BOARD[utility_pos]['name']}"
    
    return message

def process_jail(self, player: MonopolyPlayer) -> Dict[str, Any]:
    result = {
        "in_jail": player.in_jail,
        "turns_left": 3 - player.jail_turns,
        "can_pay": player.balance >= JAIL_FINE,
        "has_card": player.get_out_of_jail_cards > 0,
        "message": ""
    }
    
    if not player.in_jail:
        return result
    
    player.jail_turns += 1
    
    if player.jail_turns >= 3:
        # Автоматически платит после 3 ходов
        if player.balance >= JAIL_FINE:
            player.balance -= JAIL_FINE
            player.in_jail = False
            player.jail_turns = 0
            result["message"] = "⛓️ Вы провели 3 хода в тюрьме. Автоматически оплатили 50$"
            result["in_jail"] = False
        else:
            result["message"] = "⛓️ Вы банкрот! Не можете оплатить выход из тюрьмы"
            player.bankrupt = True
    else:
        result["message"] = f"⛓️ Ход {player.jail_turns}/3 в тюрьме. Осталось ходов: {3-player.jail_turns}"
    
    return result

def attempt_jail_escape(self, player: MonopolyPlayer) -> Dict[str, Any]:
    if not player.in_jail:
        return {"success": False, "message": "Вы не в тюрьме!"}
    
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    
    result = {
        "dice1": dice1,
        "dice2": dice2,
        "doubles": dice1 == dice2,
        "success": False,
        "message": ""
    }
    
    if dice1 == dice2:
        player.in_jail = False
        player.jail_turns = 0
        result["success"] = True
        result["message"] = f"🎲 Выпал дубль! {dice1}-{dice2}. Вы свободны!"
        # Двигаемся на сумму кубиков
        total = dice1 + dice2
        self.move_player(player, total)
    else:
        result["message"] = f"🎲 Не дубль: {dice1}-{dice2}. Остаетесь в тюрьме"
    
    return result

def pay_jail_fine(self, player: MonopolyPlayer) -> bool:
    if not player.in_jail:
        return False
    
    if player.balance < JAIL_FINE:
        return False
    
    player.balance -= JAIL_FINE
    player.in_jail = False
    player.jail_turns = 0
    return True

def use_jail_card(self, player: MonopolyPlayer) -> bool:
    if not player.in_jail:
        return False
    
    if player.get_out_of_jail_cards == 0:
        return False
    
    player.get_out_of_jail_cards -= 1
    player.in_jail = False
    player.jail_turns = 0
    return True

def check_bankruptcy(self, player: MonopolyPlayer) -> bool:
    if player.balance < 0:
        # Проверяем, может ли продать дома/недвижимость
        total_assets = player.balance
        
        # Стоимость домов
        for prop_id, houses in player.houses.items():
            if houses > 0:
                house_cost = BOARD[prop_id].get("house_cost", 50)
                sell_value = (house_cost // 2) * houses
                total_assets += sell_value
        
        # Стоимость недвижимости (половина цены покупки)
        for prop_id in player.properties:
            if prop_id in BOARD:
                price = BOARD[prop_id]["price"]
                total_assets += price // 2
        
        if total_assets < 0:
            player.bankrupt = True
            return True
    
    return False

def transfer_assets(self, from_player: MonopolyPlayer, to_player: MonopolyPlayer):
    """Передача активов при банкротстве"""
    # Передаем деньги
    if from_player.balance > 0:
        to_player.balance += from_player.balance
    
    # Передаем недвижимость
    for prop_id in from_player.properties[:]:
        from_player.remove_property(prop_id)
        to_player.add_property(prop_id)
        
        # Обновляем владельца в свойствах игры
        if prop_id in self.properties:
            self.properties[prop_id]["owner"] = to_player.id
            self.properties[prop_id]["owner_name"] = to_player.name
    
    # Передаем дома
    for prop_id, houses in from_player.houses.items():
        if prop_id in to_player.properties:
            to_player.houses[prop_id] = houses
    
    # Передаем карты освобождения
    to_player.get_out_of_jail_cards += from_player.get_out_of_jail_cards

def check_game_over(self) -> bool:
    active_players = [p for p in self.players if not p.bankrupt]
    
    if len(active_players) == 1:
        self.game_over = True
        self.winner = active_players[0]
        
        # Обновляем статистику
        for player in self.players:
            win = (player.id == self.winner.id)
            money = player.balance if win else 0
            update_user_stats(
                player.id,
                player.username,
                player.name,
                win=win,
                money=money
            )
        
        return True
    
    return False

def get_game_state(self) -> Dict[str, Any]:
    """Возвращает состояние игры для отображения"""
    current_player = self.get_current_player()
    
    return {
        "chat_id": self.chat_id,
        "turn": self.turn,
        "current_player": {
            "id": current_player.id if current_player else None,
            "name": current_player.name if current_player else "",
            "position": current_player.position if current_player else 0,
            "balance": current_player.balance if current_player else 0
        },
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "balance": p.balance,
                "position": p.position,
                "in_jail": p.in_jail,
                "properties": len(p.properties),
                "color": p.color
            }
            for p in self.players
        ],
        "properties_owned": len(self.properties),
        "game_over": self.game_over,
        "winner": self.winner.name if self.winner else None
    }

def get_player_assets(self, player: MonopolyPlayer) -> Dict[str, Any]:
    """Возвращает активы игрока"""
    properties_data = []
    total_value = player.balance
    
    for prop_id in player.properties:
        if prop_id in BOARD:
            cell = BOARD[prop_id]
            houses = player.houses.get(prop_id, 0)
            mortgaged = prop_id in player.mortgaged_properties
            
            # Стоимость имущества
            prop_value = cell["price"]
            if houses > 0:
                house_cost = cell.get("house_cost", 50)
                prop_value += houses * house_cost
            
            total_value += prop_value
            
            properties_data.append({
                "id": prop_id,
                "name": cell["name"],
                "color": cell["color"],
                "price": cell["price"],
                "houses": houses,
                "hotel": houses == 5,
                "mortgaged": mortgaged,
                "value": prop_value,
                "rent": self.calculate_rent(prop_id, houses)
            })
    
    # Сортируем по цвету
    properties_data.sort(key=lambda x: x["color"])
    
    return {
        "balance": player.balance,
        "position": player.position,
        "in_jail": player.in_jail,
        "jail_turns": player.jail_turns,
        "get_out_cards": player.get_out_of_jail_cards,
        "properties": properties_data,
        "total_assets": total_value,
        "can_build": any(player.has_full_set(BOARD[p]["color"]) for p in player.properties if p in BOARD)
      }
