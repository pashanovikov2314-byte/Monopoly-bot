"""
Bank system for Monopoly game
"""

from typing import Dict, List, Optional
from .player import Player

class Bank:
    """Банк в Монополии"""
    
    def __init__(self):
        # Деньги в банке
        self.money = 15140  # Стандартное количество денег в Монополии
        self.free_parking = 0  # Деньги на бесплатной парковке
        
        # Статистика
        self.transactions: List[Dict] = []
        self.loans_given: Dict[int, int] = {}  # player_id -> amount
        self.interest_earned = 0
    
    def can_withdraw(self, amount: int) -> bool:
        """Может ли банк выдать сумму"""
        return self.money >= amount
    
    def withdraw(self, amount: int, reason: str = "") -> Dict:
        """Снять деньги из банка"""
        if not self.can_withdraw(amount):
            return {
                "success": False,
                "error": f"В банке недостаточно денег. Доступно: ${self.money}",
                "available": self.money
            }
        
        self.money -= amount
        
        # Записываем транзакцию
        self._record_transaction("withdraw", amount, reason)
        
        return {
            "success": True,
            "amount": amount,
            "remaining": self.money,
            "message": f"Снято ${amount} из банка"
        }
    
    def deposit(self, amount: int, reason: str = "") -> Dict:
        """Внести деньги в банк"""
        self.money += amount
        
        # Записываем транзакцию
        self._record_transaction("deposit", amount, reason)
        
        return {
            "success": True,
            "amount": amount,
            "total": self.money,
            "message": f"Внесено ${amount} в банк"
        }
    
    def add_to_free_parking(self, amount: int) -> Dict:
        """Добавить деньги на бесплатную парковку"""
        self.free_parking += amount
        
        self._record_transaction("free_parking", amount, "Добавлено на бесплатную парковку")
        
        return {
            "success": True,
            "amount": amount,
            "free_parking_total": self.free_parking,
            "message": f"${amount} добавлено на бесплатную парковку"
        }
    
    def collect_free_parking(self) -> Dict:
        """Собрать деньги с бесплатной парковки"""
        amount = self.free_parking
        self.free_parking = 0
        
        self._record_transaction("collect_free_parking", amount, "Собрано с бесплатной парковки")
        
        return {
            "success": True,
            "amount": amount,
            "message": f"Собрано ${amount} с бесплатной парковки"
        }
    
    def give_loan(self, player: Player, amount: int) -> Dict:
        """Выдать кредит игроку"""
        if not self.can_withdraw(amount):
            return {
                "success": False,
                "error": "В банке недостаточно денег для выдачи кредита"
            }
        
        # Проверяем, не превышает ли кредит лимит
        max_loan = player.balance * 2  # Максимальный кредит = 200% от баланса
        if amount > max_loan:
            return {
                "success": False,
                "error": f"Максимальный кредит для вас: ${max_loan}",
                "max_loan": max_loan
            }
        
        # Выдаем кредит
        self.withdraw(amount, f"Кредит игроку {player.name}")
        player.balance += amount
        
        # Записываем кредит
        self.loans_given[player.user
