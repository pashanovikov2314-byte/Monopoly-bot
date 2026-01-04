#!/usr/bin/env python3
"""Система лобби для сбора игроков"""

import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class LobbyStatus(Enum):
    WAITING = "waiting"
    STARTING = "starting"
    ACTIVE = "active"
    FINISHED = "finished"

class Player:
    """Игрок в лобби"""
    
    def __init__(self, user_id: int, username: str, first_name: str):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.joined_at = datetime.now()
        self.is_ready = False
        self.avatar = random.choice(["👤", "🧑", "👨", "👩", "🧑‍💼", "👨‍💼", "👩‍💼"])
    
    def to_dict(self) -> Dict:
        return {
            "id": self.user_id,
            "username": self.username,
            "name": self.first_name,
            "avatar": self.avatar,
            "joined": self.joined_at.strftime("%H:%M:%S"),
            "ready": self.is_ready
        }

class GameLobby:
    """Игровое лобби"""
    
    def __init__(self, lobby_id: str, creator_id: int, chat_id: int):
        self.lobby_id = lobby_id
        self.creator_id = creator_id
        self.chat_id = chat_id
        self.created_at = datetime.now()
        self.status = LobbyStatus.WAITING
        self.players: List[Player] = []
        self.min_players = 2
        self.max_players = 8
        self.game_settings = {
            "start_balance": 1500,
            "double_go_bonus": True,
            "auction_enabled": True,
            "max_turn_time": 120,
            "max_game_time": 7200  # 2 часа
        }
        self.messages = []  # Сообщения в лобби
    
    def add_player(self, player: Player) -> bool:
        if len(self.players) >= self.max_players:
            return False
        if any(p.user_id == player.user_id for p in self.players):
            return False
        
        self.players.append(player)
        self.add_message(f"{player.avatar} {player.first_name} присоединился к лобби")
        return True
    
    def remove_player(self, user_id: int) -> bool:
        for i, player in enumerate(self.players):
            if player.user_id == user_id:
                removed_player = self.players.pop(i)
                self.add_message(f"{removed_player.avatar} {removed_player.first_name} покинул лобби")
                return True
        return False
    
    def toggle_player_ready(self, user_id: int) -> bool:
        for player in self.players:
            if player.user_id == user_id:
                player.is_ready = not player.is_ready
                status = "готов" if player.is_ready else "не готов"
                self.add_message(f"{player.avatar} {player.first_name} теперь {status}")
                return True
        return False
    
    def can_start(self) -> bool:
        if len(self.players) < self.min_players:
            return False
        ready_players = sum(1 for p in self.players if p.is_ready)
        return ready_players >= self.min_players
    
    def add_message(self, message: str):
        """Добавление сообщения в историю лобби"""
        self.messages.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": message
        })
        # Храним только последние 20 сообщений
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def get_lobby_display(self) -> str:
        """Отображение лобби для пользователей"""
        display = f"""
🎪 *ЛОББИ #{self.lobby_id}*

👥 *Игроки ({len(self.players)}/{self.max_players}):*
"""
        
        for player in self.players:
            status = "✅" if player.is_ready else "⏳"
            name_display = f"@{player.username}" if player.username else player.first_name
            display += f"\n{player.avatar} {status} {name_display}"
        
        ready_count = sum(1 for p in self.players if p.is_ready)
        display += f"\n\n🎯 *Готовы:* {ready_count}/{len(self.players)}"
        display += f"\n🚀 *Для старта нужно:* {self.min_players}+ готовых игроков"
        
        # Последние сообщения
        if self.messages:
            display += "\n\n💭 *Последние события:*"
            for msg in self.messages[-3:]:  # Последние 3 сообщения
                display += f"\n• [{msg['time']}] {msg['text']}"
        
        return display

class LobbyManager:
    """Менеджер лобби"""
    
    def __init__(self):
        self.lobbies: Dict[str, GameLobby] = {}
        self.user_to_lobby: Dict[int, str] = {}  # user_id -> lobby_id
    
    def create_lobby(self, creator_id: int, chat_id: int) -> GameLobby:
        """Создание нового лобби"""
        lobby_id = f"lobby_{random.randint(1000, 9999)}"
        while lobby_id in self.lobbies:
            lobby_id = f"lobby_{random.randint(1000, 9999)}"
        
        lobby = GameLobby(lobby_id, creator_id, chat_id)
        self.lobbies[lobby_id] = lobby
        self.user_to_lobby[creator_id] = lobby_id
        return lobby
    
    def get_lobby(self, lobby_id: str) -> Optional[GameLobby]:
        return self.lobbies.get(lobby_id)
    
    def get_user_lobby(self, user_id: int) -> Optional[GameLobby]:
        lobby_id = self.user_to_lobby.get(user_id)
        return self.lobbies.get(lobby_id) if lobby_id else None
    
    def join_lobby(self, lobby_id: str, player: Player) -> bool:
        lobby = self.get_lobby(lobby_id)
        if not lobby or lobby.status != LobbyStatus.WAITING:
            return False
        
        if lobby.add_player(player):
            self.user_to_lobby[player.user_id] = lobby_id
            return True
        return False
    
    def leave_lobby(self, user_id: int) -> bool:
        lobby = self.get_user_lobby(user_id)
        if not lobby:
            return False
        
        # Удаляем игрока
        success = lobby.remove_player(user_id)
        
        # Удаляем из user_to_lobby
        if user_id in self.user_to_lobby:
            del self.user_to_lobby[user_id]
        
        # Если лобби пустое - удаляем его
        if len(lobby.players) == 0:
            del self.lobbies[lobby.lobby_id]
        
        return success

# Глобальный экземпляр
lobby_manager = LobbyManager()

def get_lobby_manager():
    return lobby_manager
