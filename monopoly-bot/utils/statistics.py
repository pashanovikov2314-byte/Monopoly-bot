"""
Statistics and rating calculations
"""

from typing import List, Dict, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def calculate_rating(players_data: List[Dict], by: str = "games_won") -> List[Dict]:
    """Рассчитать рейтинг игроков"""
    if by == "games_won":
        sorted_players = sorted(
            players_data,
            key=lambda x: (x.get('games_won', 0), x.get('games_played', 0)),
            reverse=True
        )
    elif by == "total_money":
        sorted_players = sorted(
            players_data,
            key=lambda x: x.get('total_money', 0),
            reverse=True
        )
    elif by == "win_rate":
        for player in players_data:
            games_played = player.get('games_played', 0)
            games_won = player.get('games_won', 0)
            player['win_rate'] = (games_won / games_played * 100) if games_played > 0 else 0
        
        sorted_players = sorted(
            players_data,
            key=lambda x: x.get('win_rate', 0),
            reverse=True
        )
    else:
        sorted_players = players_data
    
    # Добавляем места
    for i, player in enumerate(sorted_players[:10], 1):
        player['place'] = i
    
    return sorted_players[:10]


def calculate_game_statistics(game_data: Dict) -> Dict:
    """Рассчитать статистику игры"""
    players = game_data.get("players", {})
    properties = game_data.get("properties", {})
    
    stats = {
        "total_players": len(players),
        "active_players": sum(1 for p in players.values() if not p.get("is_bankrupt", False)),
        "bankrupt_players": sum(1 for p in players.values() if p.get("is_bankrupt", False)),
        "total_money_in_game": 0,
        "total_properties": len(properties),
        "mortgaged_properties": sum(1 for p in properties.values() if p.get("is_mortgaged", False)),
        "total_houses": 0,
        "total_hotels": 0,
        "player_stats": {}
    }
    
    # Статистика по игрокам
    for player_id, player in players.items():
        player_stats = {
            "balance": player.get("balance", 0),
            "properties_count": len(player.get("properties", [])),
            "is_bankrupt": player.get("is_bankrupt", False),
            "net_worth": calculate_net_worth(player, properties),
            "position": player.get("position", 0),
            "turns_played": player.get("turns_played", 0)
        }
        
        stats["total_money_in_game"] += player_stats["balance"]
        stats["player_stats"][player_id] = player_stats
    
    # Считаем дома и отели
    for prop in properties.values():
        stats["total_houses"] += prop.get("houses", 0)
        if prop.get("hotel", False):
            stats["total_hotels"] += 1
    
    return stats


def calculate_net_worth(player: Dict, properties: Dict) -> int:
    """Рассчитать чистую стоимость игрока"""
    balance = player.get("balance", 0)
    player_properties = player.get("properties", [])
    
    property_value = 0
    for prop_id in player_properties:
        prop = properties.get(str(prop_id), {})
        if prop:
            # Базовая стоимость
            price = prop.get("price", 0)
            
            # Добавляем стоимость домов/отелей
            houses = prop.get("houses", 0)
            house_price = prop.get("house_price", price // 2)
            property_value += price + (houses * house_price)
            
            if prop.get("hotel", False):
                hotel_price = prop.get("hotel_price", price)
                property_value += hotel_price
    
    return balance + property_value


def get_game_duration(start_time: datetime, end_time: datetime = None) -> str:
    """Получить продолжительность игры в читаемом формате"""
    if not end_time:
        end_time = datetime.now()
    
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}ч {minutes}м {seconds}с"
    elif minutes > 0:
        return f"{minutes}м {seconds}с"
    else:
        return f"{seconds}с"


def format_statistics(stats: Dict) -> str:
    """Форматировать статистику для вывода"""
    if not stats:
        return "Статистика не доступна"
    
    lines = []
    
    if "games_played" in stats:
        lines.append(f"🎮 Сыграно игр: {stats.get('games_played', 0)}")
        lines.append(f"🏆 Побед: {stats.get('games_won', 0)}")
        
        win_rate = 0
        if stats.get('games_played', 0) > 0:
            win_rate = (stats.get('games_won', 0) / stats.get('games_played', 0)) * 100
        lines.append(f"📈 Винрейт: {win_rate:.1f}%")
    
    if "total_money" in stats:
        lines.append(f"💰 Всего денег: ${stats.get('total_money', 0):,}")
    
    if "total_houses" in stats:
        lines.append(f"🏠 Построено домов: {stats.get('total_houses', 0)}")
        lines.append(f"🏨 Построено отелей: {stats.get('total_hotels', 0)}")
    
    if "total_trades" in stats:
        lines.append(f"🤝 Сделок: {stats.get('total_trades', 0)}")
    
    if "total_jail_visits" in stats:
        lines.append(f"🏛️ Посещений тюрьмы: {stats.get('total_jail_visits', 0)}")
    
    return "\n".join(lines)
