"""
Auction system for Monopoly game
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from .player import Player
from .property import Property

logger = logging.getLogger(__name__)

class Auction:
    """Система аукциона в Монополии"""
    
    def __init__(self):
        self.active_auctions: Dict[str, 'AuctionItem'] = {}
        self.auction_history: List[Dict] = []
    
    def start_auction(self, property_obj: Property, players: List[Player], 
                     starting_bid: int = 0, min_increment: int = 10) -> str:
        """Начать аукцион за свойство"""
        auction_id = f"auction_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        auction = AuctionItem(
            auction_id=auction_id,
            property_obj=property_obj,
            players=players,
            starting_bid=starting_bid,
            min_increment=min_increment
        )
        
        self.active_auctions[auction_id] = auction
        
        logger.info(f"Начат аукцион {auction_id} за {property_obj.name}, начальная ставка: ${starting_bid}")
        
        return auction_id
    
    def place_bid(self, auction_id: str, player: Player, amount: int) -> Dict:
        """Сделать ставку на аукционе"""
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Аукцион не найден"
            }
        
        auction = self.active_auctions[auction_id]
        
        if auction.is_finished:
            return {
                "success": False,
                "error": "Аукцион завершен"
            }
        
        return auction.place_bid(player, amount)
    
    def finish_auction(self, auction_id: str) -> Dict:
        """Завершить аукцион"""
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Аукцион не найден"
            }
        
        auction = self.active_auctions[auction_id]
        
        if auction.is_finished:
            return {
                "success": False,
                "error": "Аукцион уже завершен"
            }
        
        result = auction.finish()
        
        # Перемещаем в историю
        self.auction_history.append({
            **result,
            "finished_at": datetime.now().isoformat()
        })
        
        # Удаляем из активных
        del self.active_auctions[auction_id]
        
        logger.info(f"Аукцион {auction_id} завершен. Победитель: {result.get('winner_name', 'нет')}, цена: ${result.get('winning_bid', 0)}")
        
        return result
    
    def cancel_auction(self, auction_id: str) -> Dict:
        """Отменить аукцион"""
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Аукцион не найден"
            }
        
        auction = self.active_auctions[auction_id]
        
        if auction.is_finished:
            return {
                "success": False,
                "error": "Аукцион уже завершен"
            }
        
        result = auction.cancel()
        
        # Удаляем из активных
        del self.active_auctions[auction_id]
        
        logger.info(f"Аукцион {auction_id} отменен")
        
        return result
    
    def get_auction_info(self, auction_id: str) -> Optional[Dict]:
        """Получить информацию об аукционе"""
        if auction_id not in self.active_auctions:
            return None
        
        auction = self.active_auctions[auction_id]
        return auction.get_info()
    
    def get_active_auctions(self) -> List[Dict]:
        """Получить список активных аукционов"""
        return [auction.get_info() for auction in self.active_auctions.values()]
    
    def cleanup_old_auctions(self, hours: int = 24):
        """Очистить старые аукционы"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        expired_auctions = []
        
        for auction_id, auction in self.active_auctions.items():
            if auction.created_at < cutoff_time:
                expired_auctions.append(auction_id)
        
        for auction_id in expired_auctions:
            self.cancel_auction(auction_id)
            logger.info(f"Аукцион {auction_id} отменен по истечении времени")
        
        if expired_auctions:
            logger.info(f"Очищено {len(expired_auctions)} просроченных аукционов")


class AuctionItem:
    """Элемент аукциона"""
    
    def __init__(self, auction_id: str, property_obj: Property, 
                 players: List[Player], starting_bid: int = 0, 
                 min_increment: int = 10):
        self.auction_id = auction_id
        self.property_obj = property_obj
        self.players = players
        self.starting_bid = starting_bid
        self.min_increment = min_increment
        
        self.current_bid = starting_bid
        self.current_bidder: Optional[Player] = None
        self.bid_history: List[Dict] = []
        
        self.is_finished = False
        self.winner: Optional[Player] = None
        self.winning_bid = 0
        
        self.created_at = datetime.now()
        self.last_bid_time: Optional[datetime] = None
        
        # Настройки таймера
        self.auction_duration = timedelta(minutes=5)  # 5 минут на аукцион
        self.bid_timeout = timedelta(seconds=30)  # 30 секунд без ставок = завершение
    
    def place_bid(self, player: Player, amount: int) -> Dict:
        """Сделать ставку"""
        if self.is_finished:
            return {
                "success": False,
                "error": "Аукцион завершен"
            }
        
        # Проверяем, может ли игрок делать ставки
        if player not in self.players:
            return {
                "success": False,
                "error": "Вы не участвуете в этом аукционе"
            }
        
        if player.is_bankrupt:
            return {
                "success": False,
                "error": "Вы банкрот и не можете делать ставки"
            }
        
        # Проверяем минимальную ставку
        if amount < self.current_bid + self.min_increment:
            return {
                "success": False,
                "error": f"Минимальная ставка: ${self.current_bid + self.min_increment}"
            }
        
        # Проверяем, есть ли у игрока деньги
        if player.balance < amount:
            return {
                "success": False,
                "error": f"Недостаточно денег. Ваш баланс: ${player.balance}"
            }
        
        # Делаем ставку
        old_bidder = self.current_bidder
        old_bid = self.current_bid
        
        self.current_bid = amount
        self.current_bidder = player
        self.last_bid_time = datetime.now()
        
        # Записываем в историю
        bid_record = {
            "player_id": player.user_id,
            "player_name": player.name,
            "amount": amount,
            "timestamp": self.last_bid_time.isoformat(),
            "previous_bid": old_bid,
            "previous_bidder": old_bidder.name if old_bidder else None
        }
        
        self.bid_history.append(bid_record)
        
        logger.info(f"Игрок {player.name} сделал ставку ${amount} на аукционе {self.auction_id}")
        
        # Проверяем, не истекло ли время
        if self._check_should_finish():
            return self.finish()
        
        return {
            "success": True,
            "auction_id": self.auction_id,
            "player": player.name,
            "amount": amount,
            "is_highest_bid": True,
            "message": f"✅ {player.name} делает ставку ${amount} за {self.property_obj.name}"
        }
    
    def finish(self) -> Dict:
        """Завершить аукцион"""
        if self.is_finished:
            return {
                "success": False,
                "error": "Аукцион уже завершен"
            }
        
        self.is_finished = True
        
        if self.current_bidder:
            # Есть победитель
            self.winner = self.current_bidder
            self.winning_bid = self.current_bid
            
            # Проверяем, может ли победитель заплатить
            if self.winner.balance >= self.winning_bid:
                # Выполняем покупку
                self.winner.balance -= self.winning_bid
                self.property_obj.owner = self.winner.user_id
                self.winner.add_property(self.property_obj)
                
                result = {
                    "success": True,
                    "auction_id": self.auction_id,
                    "finished": True,
                    "has_winner": True,
                    "winner_id": self.winner.user_id,
                    "winner_name": self.winner.name,
                    "winning_bid": self.winning_bid,
                    "property": self.property_obj.name,
                    "message": f"🏆 {self.winner.name} выигрывает {self.property_obj.name} за ${self.winning_bid}!"
                }
            else:
                # Победитель не может заплатить
                result = {
                    "success": False,
                    "auction_id": self.auction_id,
                    "finished": True,
                    "has_winner": False,
                    "error": f"Победитель {self.winner.name} не может заплатить ${self.winning_bid}",
                    "message": "Аукцион отменен: победитель не может заплатить"
                }
        else:
            # Нет ставок - аукцион без победителя
            result = {
                "success": True,
                "auction_id": self.auction_id,
                "finished": True,
                "has_winner": False,
                "winning_bid": 0,
                "property": self.property_obj.name,
                "message": "Аукцион завершен без победителя"
            }
        
        return result
    
    def cancel(self) -> Dict:
        """Отменить аукцион"""
        self.is_finished = True
        
        return {
            "success": True,
            "auction_id": self.auction_id,
            "finished": True,
            "cancelled": True,
            "property": self.property_obj.name,
            "message": "Аукцион отменен"
        }
    
    def _check_should_finish(self) -> bool:
        """Проверить, следует ли завершить аукцион"""
        if not self.last_bid_time:
            return False
        
        # Если прошло больше времени таймаута с последней ставки
        time_since_last_bid = datetime.now() - self.last_bid_time
        if time_since_last_bid > self.bid_timeout:
            return True
        
        # Если прошло больше максимального времени аукциона
        time_since_creation = datetime.now() - self.created_at
        if time_since_creation > self.auction_duration:
            return True
        
        return False
    
    def get_info(self) -> Dict:
        """Получить информацию об аукционе"""
        time_since_creation = datetime.now() - self.created_at
        time_remaining = max(timedelta(0), self.auction_duration - time_since_creation)
        
        if self.last_bid_time:
            time_since_last_bid = datetime.now() - self.last_bid_time
            bid_timeout_remaining = max(timedelta(0), self.bid_timeout - time_since_last_bid)
        else:
            bid_timeout_remaining = self.bid_timeout
        
        return {
            "auction_id": self.auction_id,
            "property": self.property_obj.name,
            "property_position": self.property_obj.position,
            "property_price": self.property_obj.price,
            "starting_bid": self.starting_bid,
            "current_bid": self.current_bid,
            "current_bidder": self.current_bidder.name if self.current_bidder else None,
            "min_increment": self.min_increment,
            "is_finished": self.is_finished,
            "bid_count": len(self.bid_history),
            "players_count": len(self.players),
            "created_at": self.created_at.isoformat(),
            "last_bid_time": self.last_bid_time.isoformat() if self.last_bid_time else None,
            "time_remaining_seconds": int(time_remaining.total_seconds()),
            "bid_timeout_seconds": int(bid_timeout_remaining.total_seconds()),
            "recent_bids": self.bid_history[-5:] if self.bid_history else []
        }
    
    def get_bid_history(self) -> List[Dict]:
        """Получить историю ставок"""
        return self.bid_history.copy()
