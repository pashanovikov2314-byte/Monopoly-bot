"""
Property class for Monopoly game (streets, railroads, utilities)
"""

from typing import List, Optional, Dict

class Property:
    """Класс недвижимости в Монополии"""
    
    def __init__(self, position: int, name: str, price: int, 
                 group: Optional[str] = None, rent: Optional[List[int]] = None,
                 multiplier: Optional[List[int]] = None):
        self.position = position
        self.name = name
        self.price = price
        self.group = group  # Цветовая группа для улиц
        self.rent = rent or []  # Арендная плата [0 домов, 1 дом, 2 дома, 3 дома, 4 дома, отель]
        self.multiplier = multiplier or []  # Множители для коммунальных предприятий
        
        # Владелец
        self.owner: Optional[int] = None  # user_id владельца
        
        # Состояние
        self.is_mortgaged = False
        self.houses = 0  # 0-4 дома
        self.has_hotel = False
        
        # Стоимость построек
        self.house_price = self._calculate_house_price()
        self.hotel_price = self._calculate_hotel_price()
        
        # Тип свойства
        if group:
            self.type = "property"
        elif "ж/д" in name or "railroad" in name.lower():
            self.type = "railroad"
        else:
            self.type = "utility"
    
    def _calculate_house_price(self) -> int:
        """Рассчитать стоимость дома"""
        if self.type == "property":
            if self.group in ["brown", "lightblue"]:
                return 50
            elif self.group in ["pink", "orange"]:
                return 100
            elif self.group in ["red", "yellow"]:
                return 150
            elif self.group in ["green", "darkblue"]:
                return 200
        return 0
    
    def _calculate_hotel_price(self) -> int:
        """Рассчитать стоимость отеля"""
        if self.type == "property":
            return self.house_price  # Отель стоит столько же, сколько дом
        return 0
    
    def calculate_rent(self, dice_roll: int = 0) -> int:
        """Рассчитать арендную плату"""
        if self.is_mortgaged:
            return 0
        
        if self.type == "property":
            if self.has_hotel:
                return self.rent[5] if len(self.rent) > 5 else self.rent[4] * 2
            elif self.houses > 0:
                return self.rent[self.houses] if len(self.rent) > self.houses else 0
            else:
                # Базовая рента (0 домов)
                base_rent = self.rent[0] if self.rent else 0
                
                # Если владелец имеет все свойства группы, рента удваивается
                # Это нужно проверять в контексте игры
                return base_rent
        
        elif self.type == "railroad":
            # Рента зависит от количества ж/д у владельца
            # 1 дорога = 25, 2 = 50, 3 = 100, 4 = 200
            railroad_count = 1  # Это нужно получить из игры
            rents = [25, 50, 100, 200]
            if 1 <= railroad_count <= 4:
                return rents[railroad_count - 1]
            return 25
        
        elif self.type == "utility":
            # Рента = множитель × результат броска кубиков
            # 1 предприятие = 4×, 2 предприятия = 10×
            utility_count = 1  # Это нужно получить из игры
            if utility_count == 1:
                multiplier = self.multiplier[0] if self.multiplier else 4
            else:
                multiplier = self.multiplier[1] if len(self.multiplier) > 1 else 10
            return multiplier * dice_roll
        
        return 0
    
    def calculate_railroad_rent(self, owned_railroads: int) -> int:
        """Рассчитать ренту для железной дороги"""
        if self.is_mortgaged:
            return 0
        
        rents = [25, 50, 100, 200]
        if 1 <= owned_railroads <= 4:
            return rents[owned_railroads - 1]
        return rents[0]
    
    def calculate_utility_rent(self, owned_utilities: int, dice_roll: int) -> int:
        """Рассчитать ренту для коммунального предприятия"""
        if self.is_mortgaged:
            return 0
        
        if owned_utilities == 1:
            multiplier = self.multiplier[0] if self.multiplier else 4
        else:
            multiplier = self.multiplier[1] if len(self.multiplier) > 1 else 10
        
        return multiplier * dice_roll
    
    def get_mortgage_value(self) -> int:
        """Получить сумму залога"""
        return self.price // 2
    
    def get_unmortgage_cost(self) -> int:
        """Получить стоимость выкупа из залога"""
        mortgage_value = self.get_mortgage_value()
        return int(mortgage_value * 1.1)  # Залог + 10%
    
    def get_value(self) -> int:
        """Получить общую стоимость (цена + постройки)"""
        total = self.price
        
        if self.houses > 0:
            total += self.houses * self.house_price
        
        if self.has_hotel:
            total += self.hotel_price
        
        return total
    
    def can_build_house(self) -> bool:
        """Можно ли построить дом"""
        return (self.type == "property" and 
                not self.is_mortgaged and 
                self.houses < 4 and 
                not self.has_hotel)
    
    def can_build_hotel(self) -> bool:
        """Можно ли построить отель"""
        return (self.type == "property" and 
                not self.is_mortgaged and 
                self.houses == 4 and 
                not self.has_hotel)
    
    def can_mortgage(self) -> bool:
        """Можно ли заложить"""
        return (self.owner is not None and 
                not self.is_mortgaged and 
                self.houses == 0 and 
                not self.has_hotel)
    
    def can_sell_house(self) -> bool:
        """Можно ли продать дом"""
        return self.houses > 0
    
    def can_sell_hotel(self) -> bool:
        """Можно ли продать отель"""
        return self.has_hotel
    
    def sell_house(self) -> int:
        """Продать дом и вернуть стоимость"""
        if self.houses > 0:
            self.houses -= 1
            return self.house_price // 2  # Дома продаются за половину
        return 0
    
    def sell_hotel(self) -> int:
        """Продать отель и вернуть стоимость"""
        if self.has_hotel:
            self.has_hotel = False
            self.houses = 4  # При продаже отеля остаются 4 дома
            return self.hotel_price // 2  # Отели продаются за половину
        return 0
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            "position": self.position,
            "name": self.name,
            "price": self.price,
            "group": self.group,
            "type": self.type,
            "owner": self.owner,
            "is_mortgaged": self.is_mortgaged,
            "houses": self.houses,
            "has_hotel": self.has_hotel,
            "house_price": self.house_price,
            "hotel_price": self.hotel_price,
            "rent": self.rent,
            "multiplier": self.multiplier
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Property':
        """Создать свойство из словаря"""
        prop = cls(
            position=data["position"],
            name=data["name"],
            price=data["price"],
            group=data.get("group"),
            rent=data.get("rent", []),
            multiplier=data.get("multiplier", [])
        )
        
        prop.owner = data.get("owner")
        prop.is_mortgaged = data.get("is_mortgaged", False)
        prop.houses = data.get("houses", 0)
        prop.has_hotel = data.get("has_hotel", False)
        prop.house_price = data.get("house_price", prop._calculate_house_price())
        prop.hotel_price = data.get("hotel_price", prop._calculate_hotel_price())
        
        return prop
    
    def __str__(self):
        status = []
        if self.is_mortgaged:
            status.append("заложено")
        if self.houses > 0:
            status.append(f"дома: {self.houses}")
        if self.has_hotel:
            status.append("отель")
        
        status_str = f" ({', '.join(status)})" if status else ""
        return f"Property({self.name}, ${self.price}{status_str})"
    
    def __repr__(self):
        return self.__str__()
