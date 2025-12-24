"""
Dice mechanics for Monopoly game
"""

import random
from typing import Tuple, List, Optional

class Dice:
    """Класс для работы с кубиками"""
    
    def __init__(self):
        self.last_roll: Optional[Tuple[int, int]] = None
        self.roll_history: List[Tuple[int, int]] = []
        self.double_count = 0
    
    def roll(self) -> Tuple[int, int]:
        """Бросить два кубика"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        self.last_roll = (dice1, dice2)
        self.roll_history.append(self.last_roll)
        
        # Считаем дубли
        if dice1 == dice2:
            self.double_count += 1
        else:
            self.double_count = 0
        
        # Ограничиваем историю последними 100 бросками
        if len(self.roll_history) > 100:
            self.roll_history = self.roll_history[-100:]
        
        return self.last_roll
    
    def get_last_roll(self) -> Optional[Tuple[int, int]]:
        """Получить последний бросок"""
        return self.last_roll
    
    def is_double(self) -> bool:
        """Был ли последний бросок дублем?"""
        if not self.last_roll:
            return False
        return self.last_roll[0] == self.last_roll[1]
    
    def get_total(self) -> int:
        """Получить сумму последнего броска"""
        if not self.last_roll:
            return 0
        return self.last_roll[0] + self.last_roll[1]
    
    def get_consecutive_doubles(self) -> int:
        """Получить количество дублей подряд"""
        return self.double_count
    
    def reset_double_count(self):
        """Сбросить счетчик дублей"""
        self.double_count = 0
    
    def get_statistics(self) -> Dict:
        """Получить статистику бросков"""
        if not self.roll_history:
            return {
                "total_rolls": 0,
                "doubles_count": 0,
                "average_roll": 0,
                "most_common_roll": None
            }
        
        total_rolls = len(self.roll_history)
        doubles_count = sum(1 for d1, d2 in self.roll_history if d1 == d2)
        average_roll = sum(d1 + d2 for d1, d2 in self.roll_history) / total_rolls
        
        # Находим наиболее частую сумму
        roll_sums = [d1 + d2 for d1, d2 in self.roll_history]
        most_common = max(set(roll_sums), key=roll_sums.count)
        
        return {
            "total_rolls": total_rolls,
            "doubles_count": doubles_count,
            "doubles_percentage": (doubles_count / total_rolls * 100) if total_rolls > 0 else 0,
            "average_roll": round(average_roll, 2),
            "most_common_roll": most_common,
            "last_roll": self.last_roll
        }
    
    def simulate_rolls(self, num_rolls: int = 1000) -> Dict:
        """Симулировать большое количество бросков для анализа"""
        results = {
            2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
            8: 0, 9: 0, 10: 0, 11: 0, 12: 0
        }
        
        doubles = 0
        
        for _ in range(num_rolls):
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            total = dice1 + dice2
            
            results[total] += 1
            if dice1 == dice2:
                doubles += 1
        
        # Рассчитываем проценты
        percentages = {k: (v / num_rolls * 100) for k, v in results.items()}
        
        return {
            "total_rolls": num_rolls,
            "results": results,
            "percentages": percentages,
            "doubles": doubles,
            "doubles_percentage": (doubles / num_rolls * 100),
            "expected_values": self.get_expected_values()
        }
    
    @staticmethod
    def get_expected_values() -> Dict[int, float]:
        """Получить ожидаемые вероятности для сумм кубиков"""
        # Теоретические вероятности для двух кубиков
        return {
            2: 1/36 * 100,    # ~2.78%
            3: 2/36 * 100,    # ~5.56%
            4: 3/36 * 100,    # ~8.33%
            5: 4/36 * 100,    # ~11.11%
            6: 5/36 * 100,    # ~13.89%
            7: 6/36 * 100,    # ~16.67%
            8: 5/36 * 100,    # ~13.89%
            9: 4/36 * 100,    # ~11.11%
            10: 3/36 * 100,   # ~8.33%
            11: 2/36 * 100,   # ~5.56%
            12: 1/36 * 100    # ~2.78%
        }
    
    def get_emoji_representation(self, dice1: int = None, dice2: int = None) -> str:
        """Получить эмодзи представление кубиков"""
        if dice1 is None or dice2 is None:
            if not self.last_roll:
                return "🎲🎲"
            dice1, dice2 = self.last_roll
        
        dice_emojis = {
            1: "⚀",
            2: "⚁", 
            3: "⚂",
            4: "⚃",
            5: "⚄",
            6: "⚅"
        }
        
        return f"{dice_emojis.get(dice1, '🎲')} {dice_emojis.get(dice2, '🎲')}"
