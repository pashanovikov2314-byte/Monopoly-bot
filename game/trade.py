"""
Trade system for Monopoly game
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from .player import Player
from .property import Property

logger = logging.getLogger(__name__)

class TradeOffer:
    """Предложение обмена в Монополии"""
    
    def __init__(self, trade_id: str, from_player: Player, to_player: Player):
        self.trade_id = trade_id
        self.from_player = from_player
        self.to_player = to_player
        
        # Что предлагает первый игрок
        self.offer_money = 0
        self.offer_properties: List[Property] = []
        self.offer_get_out_of_jail_cards = 0
        
        # Что просит первый игрок
        self.request_money = 0
        self.request_properties: List[Property] = []
        self.request_get_out_of_jail_cards = 0
        
        # Статус сделки
        self.status = "pending"  # pending, accepted, rejected, cancelled
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=24)
        self.accepted_at: Optional[datetime] = None
        
        # История изменений
        self.history: List[Dict] = []
        
        self._add_history("created", "Сделка создана")
    
    def set_offer(self, money: int, properties: List[Property], 
                  get_out_of_jail_cards: int = 0):
        """Установить что предлагается"""
        self.offer_money = money
        self.offer_properties = properties.copy()
        self.offer_get_out_of_jail_cards = get_out_of_jail_cards
        
        self._add_history("offer_updated", 
                         f"Предложение обновлено: ${money}, {len(properties)} свойств")
    
    def set_request(self, money: int, properties: List[Property],
                    get_out_of_jail_cards: int = 0):
        """Установить что запрашивается"""
        self.request_money = money
        self.request_properties = properties.copy()
        self.request_get_out_of_jail_cards = get_out_of_jail_cards
        
        self._add_history("request_updated", 
                         f"Запрос обновлен: ${money}, {len(properties)} свойств")
    
    def accept(self) -> Tuple[bool, str]:
        """Принять сделку"""
        if self.status != "pending":
            return False, "Сделка уже обработана"
        
        if datetime.now() > self.expires_at:
            return False, "Срок действия сделки истек"
        
        # Проверяем, что у игроков есть то, что они предлагают
        if not self._validate_offer():
            return False, "Недействительное предложение"
        
        # Выполняем обмен
        success, message = self._execute_trade()
        if success:
            self.status = "accepted"
            self.accepted_at = datetime.now()
            self._add_history("accepted", "Сделка принята")
        
        return success, message
    
    def reject(self) -> bool:
        """Отклонить сделку"""
        if self.status != "pending":
            return False
        
        self.status = "rejected"
        self._add_history("rejected", "Сделка отклонена")
        return True
    
    def cancel(self) -> bool:
        """Отменить сделку"""
        if self.status != "pending":
            return False
        
        self.status = "cancelled"
        self._add_history("cancelled", "Сделка отменена")
        return True
    
    def _validate_offer(self) -> bool:
        """Проверить валидность предложения"""
        # Проверяем деньги
        if self.from_player.balance < self.offer_money:
            return False
        
        # Проверяем свойства
        for prop in self.offer_properties:
            if prop.owner != self.from_player.user_id:
                return False
            if prop.is_mortgaged:
                return False
        
        # Проверяем карточки освобождения
        if self.from_player.get_out_of_jail_cards < self.offer_get_out_of_jail_cards:
            return False
        
        # Проверяем запрашиваемые деньги
        if self.to_player.balance < self.request_money:
            return False
        
        # Проверяем запрашиваемые свойства
        for prop in self.request_properties:
            if prop.owner != self.to_player.user_id:
                return False
            if prop.is_mortgaged:
                return False
        
        # Проверяем запрашиваемые карточки
        if self.to_player.get_out_of_jail_cards < self.request_get_out_of_jail_cards:
            return False
        
        return True
    
    def _execute_trade(self) -> Tuple[bool, str]:
        """Выполнить обмен"""
        try:
            # Обмен деньгами
            self.from_player.balance -= self.offer_money
            self.to_player.balance += self.offer_money
            
            self.to_player.balance -= self.request_money
            self.from_player.balance += self.request_money
            
            # Обмен свойствами
            for prop in self.offer_properties:
                prop.owner = self.to_player.user_id
                self.to_player.add_property(prop)
                self.from_player.remove_property(prop.position)
            
            for prop in self.request_properties:
                prop.owner = self.from_player.user_id
                self.from_player.add_property(prop)
                self.to_player.remove_property(prop.position)
            
            # Обмен карточками освобождения
            self.from_player.get_out_of_jail_cards -= self.offer_get_out_of_jail_cards
            self.to_player.get_out_of_jail_cards += self.offer_get_out_of_jail_cards
            
            self.to_player.get_out_of_jail_cards -= self.request_get_out_of_jail_cards
            self.from_player.get_out_of_jail_cards += self.request_get_out_of_jail_cards
            
            # Если карточки "Выход из тюрьмы бесплатно" в виде отдельного флага
            if self.offer_get_out_of_jail_cards > 0 and self.from_player.has_jail_card:
                self.from_player.has_jail_card = False
                self.to_player.has_jail_card = True
            
            if self.request_get_out_of_jail_cards > 0 and self.to_player.has_jail_card:
                self.to_player.has_jail_card = False
                self.from_player.has_jail_card = True
            
            return True, "Сделка успешно завершена"
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении сделки: {e}")
            return False, f"Ошибка при выполнении сделки: {str(e)}"
    
    def _add_history(self, action: str, description: str):
        """Добавить запись в историю"""
        self.history.append({
            "action": action,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> Dict:
        """Получить сводку по сделке"""
        return {
            "trade_id": self.trade_id,
            "from_player": self.from_player.name,
            "to_player": self.to_player.name,
            "offer": {
                "money": self.offer_money,
                "properties": [prop.name for prop in self.offer_properties],
                "get_out_of_jail_cards": self.offer_get_out_of_jail_cards
            },
            "request": {
                "money": self.request_money,
                "properties": [prop.name for prop in self.request_properties],
                "get_out_of_jail_cards": self.request_get_out_of_jail_cards
            },
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "is_expired": datetime.now() > self.expires_at
        }
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            "trade_id": self.trade_id,
            "from_player_id": self.from_player.user_id,
            "to_player_id": self.to_player.user_id,
            "offer_money": self.offer_money,
            "offer_properties": [prop.position for prop in self.offer_properties],
            "offer_get_out_of_jail_cards": self.offer_get_out_of_jail_cards,
            "request_money": self.request_money,
            "request_properties": [prop.position for prop in self.request_properties],
            "request_get_out_of_jail_cards": self.request_get_out_of_jail_cards,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "history": self.history
        }


class TradeSystem:
    """Система торговли в Монополии"""
    
    def __init__(self):
        self.trades: Dict[str, TradeOffer] = {}
        self.trade_counter = 0
    
    def create_trade(self, from_player: Player, to_player: Player) -> TradeOffer:
        """Создать новое предложение обмена"""
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}"
        
        trade = TradeOffer(trade_id, from_player, to_player)
        self.trades[trade_id] = trade
        
        logger.info(f"Создана сделка {trade_id} между {from_player.name} и {to_player.name}")
        
        return trade
    
    def get_trade(self, trade_id: str) -> Optional[TradeOffer]:
        """Получить сделку по ID"""
        return self.trades.get(trade_id)
    
    def get_player_trades(self, player: Player) -> Dict[str, List[TradeOffer]]:
        """Получить все сделки игрока"""
        player_trades = {
            "outgoing": [],  # Сделки, которые игрок предложил
            "incoming": [],  # Сделки, которые предложили игроку
            "accepted": [],  # Принятые сделки
            "rejected": [],  # Отклоненные сделки
            "expired": []    # Просроченные сделки
        }
        
        for trade in self.trades.values():
            if trade.from_player.user_id == player.user_id:
                if trade.status == "pending":
                    player_trades["outgoing"].append(trade)
                elif trade.status == "accepted":
                    player_trades["accepted"].append(trade)
                elif trade.status == "rejected":
                    player_trades["rejected"].append(trade)
            
            elif trade.to_player.user_id == player.user_id:
                if trade.status == "pending":
                    player_trades["incoming"].append(trade)
                elif trade.status == "accepted":
                    player_trades["accepted"].append(trade)
                elif trade.status == "rejected":
                    player_trades["rejected"].append(trade)
            
            # Проверяем просроченные
            if trade.status == "pending" and datetime.now() > trade.expires_at:
                if trade.from_player.user_id == player.user_id or trade.to_player.user_id == player.user_id:
                    player_trades["expired"].append(trade)
        
        return player_trades
    
    def cleanup_expired_trades(self):
        """Очистить просроченные сделки"""
        expired_ids = []
        
        for trade_id, trade in self.trades.items():
            if trade.status == "pending" and datetime.now() > trade.expires_at:
                trade.status = "expired"
                expired_ids.append(trade_id)
        
        if expired_ids:
            logger.info(f"Очищено {len(expired_ids)} просроченных сделок")
    
    def can_trade_property(self, player: Player, property_obj: Property) -> bool:
        """Можно ли торговать этим свойством"""
        if property_obj.owner != player.user_id:
            return False
        
        if property_obj.is_mortgaged:
            return False
        
        # Проверяем, нет ли домов/отелей
        if property_obj.houses > 0 or property_obj.has_hotel:
            return False
        
        return True
    
    def calculate_property_value(self, property_obj: Property) -> int:
        """Рассчитать рыночную стоимость свойства"""
        base_value = property_obj.price
        
        # Дома/отели значительно увеличивают стоимость
        if property_obj.has_hotel:
            base_value += property_obj.hotel_price * 2
        elif property_obj.houses > 0:
            base_value += property_obj.houses * property_obj.house_price * 1.5
        
        # Если владелец имеет всю группу - увеличение стоимости
        # Это нужно проверять в контексте игры
        
        return int(base_value)
    
    def suggest_trade(self, from_player: Player, to_player: Player, 
                     desired_property: Property) -> Dict:
        """Предложить сделку на основе желаемого свойства"""
        suggestions = []
        
        # Вариант 1: Обмен свойство на свойство
        for prop in from_player.properties.values():
            if self.can_trade_property(from_player, prop):
                prop_value = self.calculate_property_value(prop)
                desired_value = self.calculate_property_value(desired_property)
                
                # Если стоимости примерно равны
                if abs(prop_value - desired_value) < 100:
                    suggestions.append({
                        "type": "property_for_property",
                        "offer": [prop],
                        "request": [desired_property],
                        "money_difference": desired_value - prop_value,
                        "description": f"{prop.name} за {desired_property.name}"
                    })
        
        # Вариант 2: Свойство + деньги
        desired_value = self.calculate_property_value(desired_property)
        for prop in from_player.properties.values():
            if self.can_trade_property(from_player, prop):
                prop_value = self.calculate_property_value(prop)
                money_needed = desired_value - prop_value
                
                if money_needed > 0 and money_needed <= from_player.balance:
                    suggestions.append({
                        "type": "property_plus_money",
                        "offer": [prop],
                        "offer_money": money_needed,
                        "request": [desired_property],
                        "description": f"{prop.name} + ${money_needed} за {desired_property.name}"
                    })
        
        # Вариант 3: Только деньги
        if from_player.balance >= desired_value:
            suggestions.append({
                "type": "money_only",
                "offer_money": desired_value,
                "request": [desired_property],
                "description": f"${desired_value} за {desired_property.name}"
            })
        
        return {
            "from_player": from_player.name,
            "to_player": to_player.name,
            "desired_property": desired_property.name,
            "suggestions": suggestions,
            "desired_value": desired_value
        }
