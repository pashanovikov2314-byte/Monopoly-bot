"""
Mortgage system for Monopoly game
"""

from typing import Dict, List, Optional
from .player import Player
from .property import Property

class MortgageSystem:
    """Система залога недвижимости в Монополии"""
    
    def __init__(self):
        self.mortgage_interest_rate = 0.10  # 10% за выкуп
    
    def can_mortgage(self, player: Player, property_obj: Property) -> Dict:
        """Можно ли заложить недвижимость"""
        if property_obj.owner != player.user_id:
            return {
                "can_mortgage": False,
                "reason": "Вы не владеете этой недвижимостью"
            }
        
        if property_obj.is_mortgaged:
            return {
                "can_mortgage": False,
                "reason": "Недвижимость уже заложена"
            }
        
        if property_obj.houses > 0 or property_obj.has_hotel:
            return {
                "can_mortgage": False,
                "reason": "Сначала продайте дома/отели"
            }
        
        mortgage_value = self.get_mortgage_value(property_obj)
        
        return {
            "can_mortgage": True,
            "property": property_obj.name,
            "mortgage_value": mortgage_value,
            "message": f"Можно заложить за ${mortgage_value}"
        }
    
    def mortgage(self, player: Player, property_obj: Property) -> Dict:
        """Заложить недвижимость"""
        check = self.can_mortgage(player, property_obj)
        if not check["can_mortgage"]:
            return {
                "success": False,
                "error": check["reason"]
            }
        
        mortgage_value = self.get_mortgage_value(property_obj)
        
        # Выполняем залог
        property_obj.is_mortgaged = True
        player.balance += mortgage_value
        
        return {
            "success": True,
            "property": property_obj.name,
            "mortgage_value": mortgage_value,
            "new_balance": player.balance,
            "message": f"✅ {property_obj.name} заложена за ${mortgage_value}"
        }
    
    def can_unmortgage(self, player: Player, property_obj: Property) -> Dict:
        """Можно ли выкупить недвижимость из залога"""
        if property_obj.owner != player.user_id:
            return {
                "can_unmortgage": False,
                "reason": "Вы не владеете этой недвижимостью"
            }
        
        if not property_obj.is_mortgaged:
            return {
                "can_unmortgage": False,
                "reason": "Недвижимость не заложена"
            }
        
        unmortgage_cost = self.get_unmortgage_cost(property_obj)
        
        if player.balance < unmortgage_cost:
            return {
                "can_unmortgage": False,
                "reason": f"Недостаточно денег. Нужно ${unmortgage_cost}",
                "cost": unmortgage_cost,
                "balance": player.balance
            }
        
        return {
            "can_unmortgage": True,
            "property": property_obj.name,
            "cost": unmortgage_cost,
            "message": f"Можно выкупить за ${unmortgage_cost}"
        }
    
    def unmortgage(self, player: Player, property_obj: Property) -> Dict:
        """Выкупить недвижимость из залога"""
        check = self.can_unmortgage(player, property_obj)
        if not check["can_unmortgage"]:
            return {
                "success": False,
                "error": check["reason"]
            }
        
        unmortgage_cost = self.get_unmortgage_cost(property_obj)
        
        # Выполняем выкуп
        player.balance -= unmortgage_cost
        property_obj.is_mortgaged = False
        
        return {
            "success": True,
            "property": property_obj.name,
            "cost": unmortgage_cost,
            "new_balance": player.balance,
            "message": f"✅ {property_obj.name} выкуплена за ${unmortgage_cost}"
        }
    
    def get_mortgage_value(self, property_obj: Property) -> int:
        """Получить сумму залога"""
        return property_obj.price // 2
    
    def get_unmortgage_cost(self, property_obj: Property) -> int:
        """Получить стоимость выкупа из залога"""
        mortgage_value = self.get_mortgage_value(property_obj)
        interest = int(mortgage_value * self.mortgage_interest_rate)
        return mortgage_value + interest
    
    def get_mortgage_summary(self, player: Player) -> Dict:
        """Получить сводку по залогам игрока"""
        mortgaged_properties = []
        unmortgageable_properties = []
        mortgageable_properties = []
        
        total_mortgage_value = 0
        total_unmortgage_cost = 0
        
        for prop in player.properties.values():
            if prop.is_mortgaged:
                mortgaged_properties.append({
                    "name": prop.name,
                    "position": prop.position,
                    "mortgage_value": self.get_mortgage_value(prop),
                    "unmortgage_cost": self.get_unmortgage_cost(prop),
                    "can_unmortgage": player.balance >= self.get_unmortgage_cost(prop)
                })
                total_mortgage_value += self.get_mortgage_value(prop)
                total_unmortgage_cost += self.get_unmortgage_cost(prop)
            
            elif self.can_mortgage(player, prop)["can_mortgage"]:
                mortgageable_properties.append({
                    "name": prop.name,
                    "position": prop.position,
                    "mortgage_value": self.get_mortgage_value(prop),
                    "price": prop.price
                })
            
            else:
                unmortgageable_properties.append({
                    "name": prop.name,
                    "position": prop.position,
                    "reason": self.can_mortgage(player, prop)["reason"]
                })
        
        return {
            "player": player.name,
            "balance": player.balance,
            "mortgaged_properties": mortgaged_properties,
            "mortgageable_properties": mortgageable_properties,
            "unmortgageable_properties": unmortgageable_properties,
            "total_mortgage_value": total_mortgage_value,
            "total_unmortgage_cost": total_unmortgage_cost,
            "can_unmortgage_all": player.balance >= total_unmortgage_cost if mortgaged_properties else True,
            "mortgage_count": len(mortgaged_properties),
            "available_for_mortgage": len(mortgageable_properties)
        }
    
    def sell_house_to_avoid_mortgage(self, player: Player, property_obj: Property) -> Dict:
        """Продать дом, чтобы избежать залога или собрать деньги"""
        if property_obj.houses == 0 and not property_obj.has_hotel:
            return {
                "success": False,
                "error": "На этой недвижимости нет построек"
            }
        
        if property_obj.has_hotel:
            # Продать отель
            sell_value = property_obj.hotel_price // 2
            property_obj.has_hotel = False
            property_obj.houses = 4
            
            player.balance += sell_value
            
            return {
                "success": True,
                "action": "sell_hotel",
                "property": property_obj.name,
                "value": sell_value,
                "new_balance": player.balance,
                "houses": property_obj.houses,
                "has_hotel": property_obj.has_hotel,
                "message": f"✅ Продан отель на {property_obj.name} за ${sell_value}"
            }
        
        else:
            # Продать дом
            sell_value = property_obj.house_price // 2
            property_obj.houses -= 1
            
            player.balance += sell_value
            
            return {
                "success": True,
                "action": "sell_house",
                "property": property_obj.name,
                "value": sell_value,
                "new_balance": player.balance,
                "houses": property_obj.houses,
                "message": f"✅ Продан дом на {property_obj.name} за ${sell_value}"
            }
    
    def calculate_mortgage_plan(self, player: Player, amount_needed: int) -> Dict:
        """Рассчитать план залога для сбора нужной суммы"""
        available_properties = []
        
        for prop in player.properties.values():
            if self.can_mortgage(player, prop)["can_mortgage"]:
                mortgage_value = self.get_mortgage_value(prop)
                available_properties.append({
                    "property": prop,
                    "name": prop.name,
                    "mortgage_value": mortgage_value,
                    "price": prop.price
                })
        
        # Сортируем по стоимости залога (от большей к меньшей)
        available_properties.sort(key=lambda x: x["mortgage_value"], reverse=True)
        
        plan = []
        total_raised = 0
        
        for item in available_properties:
            if total_raised >= amount_needed:
                break
            
            plan.append(item)
            total_raised += item["mortgage_value"]
        
        if total_raised >= amount_needed:
            return {
                "success": True,
                "amount_needed": amount_needed,
                "total_raised": total_raised,
                "properties_to_mortgage": [p["name"] for p in plan],
                "mortgage_values": [p["mortgage_value"] for p in plan],
                "message": f"Можно заложить {len(plan)} свойств и получить ${total_raised}"
            }
        else:
            # Нужно продавать дома/отели
            return {
                "success": False,
                "amount_needed": amount_needed,
                "total_raised": total_raised,
                "deficit": amount_needed - total_raised,
                "properties_to_mortgage": [p["name"] for p in plan],
                "message": f"Недостаточно. После залога останется дефицит ${amount_needed - total_raised}"
            }
