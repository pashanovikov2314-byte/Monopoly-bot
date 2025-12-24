"""
Card system for Chance and Community Chest cards
"""

import random
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Card:
    """Класс карточки шанса или общественной казны"""
    
    def __init__(self, card_id: str, deck: str, text: str, action: str, **kwargs):
        self.card_id = card_id
        self.deck = deck  # "chance" или "chest"
        self.text = text
        self.action = action
        self.data = kwargs
        
        # Типы действий:
        # - move_to: переместиться на позицию
        # - move_steps: переместиться на N шагов
        # - collect_money: получить деньги
        # - pay_money: заплатить деньги
        # - go_to_jail: отправиться в тюрьму
        # - get_out_of_jail_free: получить карточку выхода из тюрьмы
        # - repairs: оплатить ремонт домов/отелей
        # - collect_from_players: получить деньги от всех игроков
        # - pay_to_players: заплатить всем игрокам
    
    def execute(self, game, player) -> Dict:
        """Выполнить действие карточки"""
        result = {
            "card_id": self.card_id,
            "deck": self.deck,
            "text": self.text,
            "action": self.action
        }
        
        if self.action == "move_to":
            old_position = player.position
            new_position = self.data.get("position", 0)
            player.position = new_position
            
            # Если прошел через старт
            if new_position < old_position:
                result["passed_start"] = True
                result["salary_collected"] = 200
                player.balance += 200
            
            result.update({
                "old_position": old_position,
                "new_position": new_position,
                "position_name": self.data.get("position_name", f"Позиция {new_position}")
            })
        
        elif self.action == "move_steps":
            steps = self.data.get("steps", 0)
            old_position = player.position
            new_position = (old_position + steps) % 40
            player.position = new_position
            
            result.update({
                "steps": steps,
                "old_position": old_position,
                "new_position": new_position
            })
        
        elif self.action == "collect_money":
            amount = self.data.get("amount", 0)
            player.balance += amount
            
            result.update({
                "amount": amount,
                "new_balance": player.balance
            })
        
        elif self.action == "pay_money":
            amount = self.data.get("amount", 0)
            if player.balance >= amount:
                player.balance -= amount
                # Деньги обычно идут в банк или на бесплатную парковку
                result.update({
                    "amount": amount,
                    "new_balance": player.balance,
                    "success": True
                })
            else:
                result.update({
                    "amount": amount,
                    "balance": player.balance,
                    "success": False,
                    "error": "Недостаточно денег"
                })
        
        elif self.action == "go_to_jail":
            player.is_in_jail = True
            player.position = 10  # Позиция тюрьмы
            player.jail_turns = 0
            
            result.update({
                "jail_position": 10
            })
        
        elif self.action == "get_out_of_jail_free":
            player.has_jail_card = True
            
            result.update({
                "has_jail_card": True
            })
        
        elif self.action == "repairs":
            house_cost = self.data.get("house_cost", 0)
            hotel_cost = self.data.get("hotel_cost", 0)
            
            total_cost = 0
            houses_count = 0
            hotels_count = 0
            
            # Считаем стоимость для всех свойств игрока
            for prop in player.properties.values():
                if prop.houses > 0:
                    houses_count += prop.houses
                    total_cost += prop.houses * house_cost
                if prop.has_hotel:
                    hotels_count += 1
                    total_cost += hotel_cost
            
            if player.balance >= total_cost:
                player.balance -= total_cost
                result.update({
                    "house_cost": house_cost,
                    "hotel_cost": hotel_cost,
                    "houses_count": houses_count,
                    "hotels_count": hotels_count,
                    "total_cost": total_cost,
                    "new_balance": player.balance,
                    "success": True
                })
            else:
                result.update({
                    "total_cost": total_cost,
                    "balance": player.balance,
                    "success": False,
                    "error": "Недостаточно денег для ремонта"
                })
        
        elif self.action == "collect_from_players":
            amount = self.data.get("amount", 0)
            total_collected = 0
            
            # Собираем деньги со всех игроков
            for other_player in game.players.values():
                if other_player.user_id != player.user_id and not other_player.is_bankrupt:
                    if other_player.balance >= amount:
                        other_player.balance -= amount
                        total_collected += amount
                    else:
                        # Игрок не может заплатить
                        result["players_unable_to_pay"] = result.get("players_unable_to_pay", [])
                        result["players_unable_to_pay"].append(other_player.name)
            
            player.balance += total_collected
            
            result.update({
                "amount_per_player": amount,
                "total_collected": total_collected,
                "new_balance": player.balance
            })
        
        elif self.action == "pay_to_players":
            amount = self.data.get("amount", 0)
            total_paid = 0
            players_paid = 0
            
            # Платим всем игрокам
            if player.balance >= amount * (len(game.players) - 1):
                for other_player in game.players.values():
                    if other_player.user_id != player.user_id and not other_player.is_bankrupt:
                        other_player.balance += amount
                        player.balance -= amount
                        total_paid += amount
                        players_paid += 1
                
                result.update({
                    "amount_per_player": amount,
                    "total_paid": total_paid,
                    "players_paid": players_paid,
                    "new_balance": player.balance,
                    "success": True
                })
            else:
                result.update({
                    "amount_per_player": amount,
                    "total_needed": amount * (len(game.players) - 1),
                    "balance": player.balance,
                    "success": False,
                    "error": "Недостаточно денег для оплаты всем игрокам"
                })
        
        return result
    
    def to_dict(self) -> Dict:
        """Преобразовать карточку в словарь"""
        return {
            "card_id": self.card_id,
            "deck": self.deck,
            "text": self.text,
            "action": self.action,
            **self.data
        }


class CardSystem:
    """Система карточек шанса и общественной казны"""
    
    def __init__(self, cards_data_path: str = "data/cards.json"):
        self.cards_data_path = cards_data_path
        self.chance_cards: List[Card] = []
        self.chest_cards: List[Card] = []
        self.chance_discard: List[Card] = []
        self.chest_discard: List[Card] = []
        
        self.load_cards()
        self.shuffle_decks()
    
    def load_cards(self):
        """Загрузить карточки из файла или создать стандартные"""
        try:
            if Path(self.cards_data_path).exists():
                with open(self.cards_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._load_from_dict(data)
            else:
                self._create_standard_cards()
                
            logger.info(f"Загружено {len(self.chance_cards)} карточек шанса и {len(self.chest_cards)} карточек общественной казны")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки карточек: {e}")
            self._create_standard_cards()
    
    def _load_from_dict(self, data: Dict):
        """Загрузить карточки из словаря"""
        # Загружаем карточки шанса
        for card_data in data.get("chance", []):
            card = Card(**card_data)
            self.chance_cards.append(card)
        
        # Загружаем карточки общественной казны
        for card_data in data.get("chest", []):
            card = Card(**card_data)
            self.chest_cards.append(card)
    
    def _create_standard_cards(self):
        """Создать стандартные карточки для Монополии"""
        # Карточки шанса (Chance)
        self.chance_cards = [
            # Перемещение
            Card("chance_1", "chance", "Отправляйтесь на Старт", "move_to", position=0, position_name="Старт"),
            Card("chance_2", "chance", "Отправляйтесь на Арбат", "move_to", position=21, position_name="Арбат"),
            Card("chance_3", "chance", "Отправляйтесь на Пушкинскую", "move_to", position=31, position_name="Пушкинская"),
            Card("chance_4", "chance", "Отправляйтесь на ближайшую железную дорогу", "move_to_nearest", target_type="railroad"),
            Card("chance_5", "chance", "Отправляйтесь на ближайшее коммунальное предприятие", "move_to_nearest", target_type="utility"),
            Card("chance_6", "chance", "Вернитесь на три шага назад", "move_steps", steps=-3),
            
            # Деньги
            Card("chance_7", "chance", "Банк выплачивает вам дивиденды в размере 50$", "collect_money", amount=50),
            Card("chance_8", "chance", "Вы выиграли конкурс красоты. Получите 10$", "collect_money", amount=10),
            Card("chance_9", "chance", "Оплатите страховку - 50$", "pay_money", amount=50),
            Card("chance_10", "chance", "Оплатите налог на роскошь - 100$", "pay_money", amount=100),
            
            # Тюрьма
            Card("chance_11", "chance", "Отправляйтесь в тюрьму", "go_to_jail"),
            Card("chance_12", "chance", "Освобождение из тюрьмы. Эта карточка может быть сохранена", "get_out_of_jail_free"),
            
            # Ремонт
            Card("chance_13", "chance", "Ремонт улиц. За каждый дом заплатите 25$, за каждый отель - 100$", "repairs", house_cost=25, hotel_cost=100),
            
            # От игроков
            Card("chance_14", "chance", "С днем рождения! Получите по 10$ от каждого игрока", "collect_from_players", amount=10),
            Card("chance_15", "chance", "Вы избраны председателем правления. Заплатите каждому игроку 50$", "pay_to_players", amount=50),
            
            # Прочие
            Card("chance_16", "chance", "Оплатите штраф за превышение скорости - 15$", "pay_money", amount=15),
        ]
        
        # Карточки общественной казны (Community Chest)
        self.chest_cards = [
            # Перемещение
            Card("chest_1", "chest", "Отправляйтесь на Старт", "move_to", position=0, position_name="Старт"),
            Card("chest_2", "chest", "Отправляйтесь в тюрьму", "go_to_jail"),
            
            # Деньги (положительные)
            Card("chest_3", "chest", "Банковская ошибка в вашу пользу. Получите 200$", "collect_money", amount=200),
            Card("chest_4", "chest", "Вы заняли второе место на конкурсе красоты. Получите 10$", "collect_money", amount=10),
            Card("chest_5", "chest", "Возврат подоходного налога. Получите 20$", "collect_money", amount=20),
            Card("chest_6", "chest", "Получите наследство - 100$", "collect_money", amount=100),
            Card("chest_7", "chest", "Процент по вкладу - 50$", "collect_money", amount=50),
            Card("chest_8", "chest", "Выигрыш в лотерею - 100$", "collect_money", amount=100),
            
            # Деньги (отрицательные)
            Card("chest_9", "chest", "Оплатите лечение - 100$", "pay_money", amount=100),
            Card("chest_10", "chest", "Оплатите обучение - 150$", "pay_money", amount=150),
            Card("chest_11", "chest", "Оплатите счет за электричество - 50$", "pay_money", amount=50),
            Card("chest_12", "chest", "Штраф за парковку - 10$", "pay_money", amount=10),
            Card("chest_13", "chest", "Оплатите услуги врача - 50$", "pay_money", amount=50),
            
            # Тюрьма
            Card("chest_14", "chest", "Освобождение из тюрьмы. Эта карточка может быть сохранена", "get_out_of_jail_free"),
            
            # От игроков
            Card("chest_15", "chest", "Сбор на Рождество. Получите по 20$ от каждого игрока", "collect_from_players", amount=20),
            Card("chest_16", "chest", "Оплатите приём - 50$ каждому игроку", "pay_to_players", amount=50),
        ]
    
    def shuffle_decks(self):
        """Перемешать колоды карточек"""
        random.shuffle(self.chance_cards)
        random.shuffle(self.chest_cards)
        logger.info("Колоды карточек перемешаны")
    
    def draw_chance_card(self) -> Card:
        """Взять карточку шанса"""
        if not self.chance_cards:
            # Если колода пуста, перемешиваем сброс
            self.chance_cards = self.chance_discard.copy()
            self.chance_discard = []
            self.shuffle_decks()
            logger.info("Колода шанса перемешана заново")
        
        card = self.chance_cards.pop(0)
        return card
    
    def draw_chest_card(self) -> Card:
        """Взять карточку общественной казны"""
        if not self.chest_cards:
            # Если колода пуста, перемешиваем сброс
            self.chest_cards = self.chest_discard.copy()
            self.chest_discard = []
            random.shuffle(self.chest_cards)
            logger.info("Колода общественной казны перемешана заново")
        
        card = self.chest_cards.pop(0)
        return card
    
    def discard_chance_card(self, card: Card):
        """Сбросить карточку шанса"""
        self.chance_discard.append(card)
    
    def discard_chest_card(self, card: Card):
        """Сбросить карточку общественной казны"""
        self.chest_discard.append(card)
    
    def return_card_to_deck(self, card: Card):
        """Вернуть карточку в колоду (например, карточку выхода из тюрьмы)"""
        if card.deck == "chance":
            self.chance_cards.append(card)
            random.shuffle(self.chance_cards)
        else:
            self.chest_cards.append(card)
            random.shuffle(self.chest_cards)
        
        logger.info(f"Карточка {card.card_id} возвращена в колоду {card.deck}")
    
    def get_deck_info(self) -> Dict:
        """Получить информацию о колодах"""
        return {
            "chance": {
                "cards_in_deck": len(self.chance_cards),
                "cards_discarded": len(self.chance_discard),
                "total_cards": len(self.chance_cards) + len(self.chance_discard)
            },
            "chest": {
                "cards_in_deck": len(self.chest_cards),
                "cards_discarded": len(self.chest_discard),
                "total_cards": len(self.chest_cards) + len(self.chest_discard)
            }
        }
    
    def save_cards(self):
        """Сохранить карточки в файл"""
        try:
            data = {
                "chance": [card.to_dict() for card in self.chance_cards + self.chance_discard],
                "chest": [card.to_dict() for card in self.chest_cards + self.chest_discard]
            }
            
            # Создаем директорию если нужно
            Path(self.cards_data_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cards_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Карточки сохранены в {self.cards_data_path}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения карточек: {e}")
    
    def get_random_card_text(self, deck: str = None) -> str:
        """Получить случайный текст карточки (для демонстрации)"""
        if deck == "chance" or deck is None:
            if self.chance_cards:
                return random.choice(self.chance_cards).text
        
        if deck == "chest" or deck is None:
            if self.chest_cards:
                return random.choice(self.chest_cards).text
        
        return "Карточка не найдена"
