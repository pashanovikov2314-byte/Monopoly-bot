# -*- coding: utf-8 -*-
"""Логика игры Монополия"""

import random

class MonopolyGame:
    def __init__(self):
        self.players = []
    
    def add_player(self, player_id, name):
        player = {
            "id": player_id,
            "name": name,
            "balance": 1500,
            "position": 0,
            "properties": []
        }
        self.players.append(player)
        return player
    
    def roll_dice(self):
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1, dice2, dice1 + dice2

# Глобальный экземпляр игры
game_instance = MonopolyGame()

def get_game():
    return game_instance