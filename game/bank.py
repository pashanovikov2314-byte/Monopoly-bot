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
        self.loans_given[player.user_id] = self.loans_given.get(player.user_id, 0) + amount
        
        return {
            "success": True,
            "amount": amount,
            "player_balance": player.balance,
            "bank_balance": self.money,
            "total_loan": self.loans_given[player.user_id],
            "message": f"✅ Выдан кредит ${amount} игроку {player.name}"
        }
    
    def repay_loan(self, player: Player, amount: int) -> Dict:
        """Вернуть кредит"""
        player_loan = self.loans_given.get(player.user_id, 0)
        
        if player_loan == 0:
            return {
                "success": False,
                "error": "У вас нет кредитов"
            }
        
        if amount > player_loan:
            amount = player_loan  # Нельзя вернуть больше, чем взял
        
        if player.balance < amount:
            return {
                "success": False,
                "error": f"Недостаточно денег для возврата кредита. Нужно: ${amount}",
                "balance": player.balance
            }
        
        # Возвращаем кредит
        player.balance -= amount
        self.deposit(amount, f"Возврат кредита от {player.name}")
        
        # Обновляем запись о кредите
        self.loans_given[player.user_id] -= amount
        if self.loans_given[player.user_id] == 0:
            del self.loans_given[player.user_id]
        
        # Начисляем проценты (10%)
        interest = int(amount * 0.10)
        self.interest_earned += interest
        
        return {
            "success": True,
            "amount": amount,
            "interest": interest,
            "remaining_loan": self.loans_given.get(player.user_id, 0),
            "player_balance": player.balance,
            "message": f"✅ Возвращено ${amount} по кредиту (проценты: ${interest})"
        }
    
    def collect_interest(self, player: Player) -> Dict:
        """Собрать проценты по кредиту"""
        player_loan = self.loans_given.get(player.user_id, 0)
        
        if player_loan == 0:
            return {
                "success": False,
                "error": "У вас нет кредитов"
            }
        
        # Проценты = 10% от кредита
        interest = int(player_loan * 0.10)
        
        if player.balance < interest:
            return {
                "success": False,
                "error": f"Недостаточно денег для оплаты процентов. Нужно: ${interest}",
                "balance": player.balance
            }
        
        player.balance -= interest
        self.deposit(interest, f"Проценты по кредиту от {player.name}")
        self.interest_earned += interest
        
        return {
            "success": True,
            "amount": interest,
            "loan_amount": player_loan,
            "player_balance": player.balance,
            "message": f"Оплачены проценты по кредиту: ${interest}"
        }
    
    def get_player_loan_info(self, player: Player) -> Dict:
        """Получить информацию о кредите игрока"""
        player_loan = self.loans_given.get(player.user_id, 0)
        monthly_interest = int(player_loan * 0.10) if player_loan > 0 else 0
        
        return {
            "has_loan": player_loan > 0,
            "loan_amount": player_loan,
            "monthly_interest": monthly_interest,
            "can_pay_interest": player.balance >= monthly_interest if monthly_interest > 0 else True,
            "max_new_loan": player.balance * 2,  # Максимальный новый кредит
            "total_interest_paid": self.interest_earned
        }
    
    def _record_transaction(self, transaction_type: str, amount: int, description: str):
        """Записать транзакцию"""
        self.transactions.append({
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "timestamp": self._get_timestamp(),
            "bank_balance_after": self.money,
            "free_parking_after": self.free_parking
        })
        
        # Ограничиваем историю последними 100 транзакциями
        if len(self.transactions) > 100:
            self.transactions = self.transactions[-100:]
    
    def _get_timestamp(self) -> str:
        """Получить timestamp в строковом формате"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_bank_info(self) -> Dict:
        """Получить информацию о банке"""
        return {
            "money": self.money,
            "free_parking": self.free_parking,
            "active_loans": len(self.loans_given),
            "total_loans_amount": sum(self.loans_given.values()),
            "interest_earned": self.interest_earned,
            "transaction_count": len(self.transactions),
            "recent_transactions": self.transactions[-10:] if self.transactions else []
        }
    
    def print_money(self, amount: int) -> Dict:
        """Напечатать деньги (увеличить денежную массу)"""
        self.money += amount
        
        self._record_transaction("print_money", amount, "Напечатаны новые деньги")
        
        return {
            "success": True,
            "amount": amount,
            "new_total": self.money,
            "message": f"Напечатано ${amount} новых денег"
        }
    
    def destroy_money(self, amount: int) -> Dict:
        """Уничтожить деньги (уменьшить денежную массу)"""
        if amount > self.money:
            return {
                "success": False,
                "error": f"Нельзя уничтожить больше денег, чем есть в банке ({self.money})"
            }
        
        self.money -= amount
        
        self._record_transaction("destroy_money", amount, "Деньги уничтожены")
        
        return {
            "success": True,
            "amount": amount,
            "new_total": self.money,
            "message": f"Уничтожено ${amount} денег"
        }
