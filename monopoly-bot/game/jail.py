"""
Jail mechanics for Monopoly game
"""

import random
from typing import Dict, Optional
from .player import Player

class JailSystem:
    """Система тюрьмы в Монополии"""
    
    def __init__(self):
        self.jail_position = 10  # Позиция тюрьмы на поле
        self.go_to_jail_position = 30  # Позиция "Отправляйтесь в тюрьму"
        self.jail_fine = 50  # Штраф за выход из тюрьмы
    
    async def process_turn(self, player: Player) -> Dict:
        """Обработать ход игрока в тюрьме"""
        if not player.is_in_jail:
            return {"released": False, "error": "Игрок не в тюрьме"}
        
        # Игрок может:
        # 1. Попытаться выбросить дубль
        # 2. Заплатить штраф
        # 3. Использовать карточку освобождения
        # 4. Ожидать
        
        # Проверяем, не истекли ли 3 хода
        if player.jail_turns >= 3:
            # Автоматический выход с оплатой штрафа
            if player.balance >= self.jail_fine:
                player.balance -= self.jail_fine
                player.is_in_jail = False
                player.jail_turns = 0
                
                return {
                    "released": True,
                    "method": "forced_payment",
                    "fine": self.jail_fine,
                    "message": f"Вы вынуждены заплатить ${self.jail_fine} за выход из тюрьмы"
                }
            else:
                # Не может заплатить - банкротство
                return {
                    "released": False,
                    "method": "bankruptcy",
                    "message": "Не можете заплатить штраф - банкротство!"
                }
        
        return {
            "released": False,
            "turns_in_jail": player.jail_turns,
            "options": self.get_available_options(player)
        }
    
    def get_available_options(self, player: Player) -> Dict:
        """Получить доступные опции для выхода из тюрьмы"""
        options = {}
        
        # 1. Попытаться выбросить дубль (всегда доступно)
        options["roll_double"] = {
            "name": "🎲 Попытаться выбросить дубль",
            "description": "Бросить кубики. Если выпадет дубль - вы свободны!",
            "cost": 0,
            "available": True
        }
        
        # 2. Заплатить штраф
        options["pay_fine"] = {
            "name": f"💰 Заплатить ${self.jail_fine}",
            "description": f"Немедленно выйти из тюрьмы за ${self.jail_fine}",
            "cost": self.jail_fine,
            "available": player.balance >= self.jail_fine
        }
        
        # 3. Использовать карточку освобождения
        options["use_card"] = {
            "name": "🎫 Использовать карточку освобождения",
            "description": "Бесплатный выход из тюрьмы",
            "cost": 0,
            "available": player.has_jail_card or player.get_out_of_jail_cards > 0
        }
        
        # 4. Ожидать
        turns_left = 3 - player.jail_turns
        options["wait"] = {
            "name": f"⏳ Ожидать ({turns_left} ход{'а' if turns_left > 1 else ''})",
            "description": f"Остаться в тюрьме. Через {turns_left} ход{'а' if turns_left > 1 else ''} выйдете автоматически",
            "cost": 0,
            "available": True
        }
        
        return options
    
    async def attempt_double_roll(self, player: Player) -> Dict:
        """Попытаться выбросить дубль для выхода из тюрьмы"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        is_double = dice1 == dice2
        
        if is_double:
            # Успешный выход
            player.is_in_jail = False
            player.jail_turns = 0
            
            return {
                "success": True,
                "dice": (dice1, dice2),
                "message": f"🎯 Выбросили дубль {dice1}-{dice2}! Вы свободны!",
                "released": True
            }
        else:
            # Остаемся в тюрьме
            player.jail_turns += 1
            
            return {
                "success": False,
                "dice": (dice1, dice2),
                "message": f"🎲 Выпало {dice1}-{dice2}. Остаетесь в тюрьме.",
                "turns_in_jail": player.jail_turns,
                "released": False
            }
    
    async def pay_fine(self, player: Player) -> Dict:
        """Заплатить штраф за выход из тюрьмы"""
        if player.balance < self.jail_fine:
            return {
                "success": False,
                "message": f"Недостаточно денег для оплаты штрафа ${self.jail_fine}",
                "balance": player.balance
            }
        
        player.balance -= self.jail_fine
        player.is_in_jail = False
        player.jail_turns = 0
        
        return {
            "success": True,
            "fine": self.jail_fine,
            "balance": player.balance,
            "message": f"✅ Заплатили ${self.jail_fine} за выход из тюрьмы",
            "released": True
        }
    
    async def use_jail_card(self, player: Player) -> Dict:
        """Использовать карточку освобождения из тюрьмы"""
        if not player.has_jail_card and player.get_out_of_jail_cards == 0:
            return {
                "success": False,
                "message": "У вас нет карточек освобождения из тюрьмы"
            }
        
        if player.has_jail_card:
            player.has_jail_card = False
        else:
            player.get_out_of_jail_cards -= 1
        
        player.is_in_jail = False
        player.jail_turns = 0
        
        return {
            "success": True,
            "message": "✅ Использовали карточку освобождения из тюрьмы",
            "cards_left": player.get_out_of_jail_cards,
            "has_jail_card": player.has_jail_card,
            "released": True
        }
    
    def send_to_jail(self, player: Player, reason: str = "") -> Dict:
        """Отправить игрока в тюрьму"""
        player.is_in_jail = True
        player.position = self.jail_position
        player.jail_turns = 0
        
        return {
            "success": True,
            "position": self.jail_position,
            "reason": reason,
            "message": f"🚓 {reason}. Вы в тюрьме!"
        }
    
    def get_jail_info(self, player: Player) -> Dict:
        """Получить информацию о состоянии в тюрьме"""
        return {
            "is_in_jail": player.is_in_jail,
            "jail_turns": player.jail_turns,
            "turns_left": max(0, 3 - player.jail_turns),
            "has_jail_card": player.has_jail_card,
            "get_out_of_jail_cards": player.get_out_of_jail_cards,
            "jail_fine": self.jail_fine,
            "can_pay_fine": player.balance >= self.jail_fine,
            "available_options": self.get_available_options(player) if player.is_in_jail else {}
        }
    
    def add_jail_card(self, player: Player) -> Dict:
        """Добавить карточку освобождения из тюрьмы"""
        if player.has_jail_card:
            player.get_out_of_jail_cards += 1
        else:
            player.has_jail_card = True
        
        return {
            "success": True,
            "has_jail_card": player.has_jail_card,
            "get_out_of_jail_cards": player.get_out_of_jail_cards,
            "message": "✅ Получили карточку 'Выход из тюрьмы бесплатно'"
        }
