"""
Text formatters for game messages
"""

from typing import Dict, List
from datetime import datetime

def format_money(amount: int) -> str:
    """Форматировать денежную сумму"""
    return f"${amount:,}".replace(",", " ")

def format_property_info(prop: Dict) -> str:
    """Форматировать информацию о недвижимости"""
    name = prop.get("name", "Неизвестно")
    price = prop.get("price", 0)
    rent = prop.get("rent", [0])[0] if prop.get("rent") else 0
    
    lines = [f"🏠 <b>{name}</b>"]
    lines.append(f"💰 Цена: {format_money(price)}")
    lines.append(f"🏦 Рента: {format_money(rent)}")
    
    if prop.get("houses", 0) > 0:
        lines.append(f"🏠 Дома: {prop['houses']}")
    if prop.get("has_hotel", False):
        lines.append("🏨 Есть отель")
    if prop.get("is_mortgaged", False):
        lines.append("💸 Заложено")
    
    return "\n".join(lines)

def format_player_info(player: Dict) -> str:
    """Форматировать информацию об игроке"""
    lines = [f"👤 <b>{player.get('name', 'Игрок')}</b>"]
    lines.append(f"💰 Баланс: {format_money(player.get('balance', 0))}")
    lines.append(f"📍 Позиция: {player.get('position', 0)}")
    
    if player.get("is_in_jail", False):
        lines.append(f"🏛️ В тюрьме ({player.get('jail_turns', 0)}/3)")
    
    if player.get("is_bankrupt", False):
        lines.append("💀 Банкрот")
    
    return "\n".join(lines)

def format_game_state(game_state: Dict) -> str:
    """Форматировать состояние игры"""
    lines = ["🎮 <b>Состояние игры</b>", ""]
    
    # Информация о текущем ходе
    current_player = game_state.get("current_player", {})
    if current_player:
        lines.append(f"🎯 <b>Сейчас ходит: {current_player.get('name', 'Игрок')}</b>")
        lines.append(f"Ход: {game_state.get('turn_number', 0)}")
    
    # Игроки
    players = game_state.get("players", [])
    if players:
        lines.append("")
        lines.append("<b>Игроки:</b>")
        for player in players:
            status = ""
            if player.get("is_bankrupt"):
                status = " 💀"
            elif player.get("is_in_jail"):
                status = " 🏛️"
            
            lines.append(f"• {player.get('name', 'Игрок')}: {format_money(player.get('balance', 0))}{status}")
    
    # Время
    if game_state.get("start_time"):
        try:
            start_time = datetime.fromisoformat(game_state["start_time"])
            duration = datetime.now() - start_time
            minutes = int(duration.total_seconds() // 60)
            lines.append(f"⏱️ Игра идет: {minutes} минут")
        except:
            pass
    
    return "\n".join(lines)

def format_dice_roll(dice1: int, dice2: int) -> str:
    """Форматировать результат броска кубиков"""
    dice_emojis = {
        1: "⚀", 2: "⚁", 3: "⚂", 
        4: "⚃", 5: "⚄", 6: "⚅"
    }
    
    total = dice1 + dice2
    is_double = dice1 == dice2
    
    result = [
        f"🎲 <b>Результат броска:</b>",
        f"{dice_emojis.get(dice1, '🎲')} {dice_emojis.get(dice2, '🎲')}",
        f"Кубики: {dice1} + {dice2} = {total}"
    ]
    
    if is_double:
        result.append("🎯 <b>Дубль!</b>")
    
    return "\n".join(result)

def format_trade_offer(offer: Dict) -> str:
    """Форматировать предложение обмена"""
    lines = ["🤝 <b>Предложение обмена</b>", ""]
    
    lines.append(f"От: {offer.get('from_player', 'Неизвестно')}")
    lines.append(f"Кому: {offer.get('to_player', 'Неизвестно')}")
    
    # Что предлагается
    offer_items = []
    if offer.get("offer_money", 0) > 0:
        offer_items.append(f"{format_money(offer['offer_money'])}")
    if offer.get("offer_properties"):
        for prop in offer["offer_properties"]:
            offer_items.append(prop.get("name", "Собственность"))
    
    if offer_items:
        lines.append("")
        lines.append("<b>Предлагается:</b>")
        lines.extend([f"• {item}" for item in offer_items])
    
    # Что запрашивается
    request_items = []
    if offer.get("request_money", 0) > 0:
        request_items.append(f"{format_money(offer['request_money'])}")
    if offer.get("request_properties"):
        for prop in offer["request_properties"]:
            request_items.append(prop.get("name", "Собственность"))
    
    if request_items:
        lines.append("")
        lines.append("<b>Запрашивается:</b>")
        lines.extend([f"• {item}" for item in request_items])
    
    # Статус
    status = offer.get("status", "pending")
    status_text = {
        "pending": "⏳ Ожидание",
        "accepted": "✅ Принято",
        "rejected": "❌ Отклонено",
        "cancelled": "🚫 Отменено"
    }.get(status, status)
    
    lines.append("")
    lines.append(f"<b>Статус:</b> {status_text}")
    
    return "\n".join(lines)
