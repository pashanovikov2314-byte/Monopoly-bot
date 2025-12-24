"""
Handlers package for Monopoly Premium Bot
"""

__all__ = [
    'setup_commands',
    'setup_callbacks',
    'setup_text_handlers'
]

from .commands import setup_commands
from .callback_handlers import setup_callbacks
from .text_handlers import setup_text_handlers
