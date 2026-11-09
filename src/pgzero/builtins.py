# Expose clock API as a builtin
from . import clock
from . import music
from . import tone
from .actor import Actor
from .sprites import Sprite
from .storage import storage
from .keyboard import keyboard
from .animation import animate
from .rect import Rect, ZRect
from .loaders import images, sounds
from .constants import mouse, keys, keymods
from .game import Game, exit
from .tilemaps import load_tile_map, load_tile_map_actors

# The actual screen will be installed here
from .screen import screen_instance as screen

# Global game state object. The runner replaces this with a fresh Game each time a game is run.
game = Game()


__all__ = [
    "screen",  # graphics output
    "Actor",
    "images",
    "Sprite",  # graphics
    "sounds",
    "music",
    "tone",  # sound
    "clock",
    "animate",  # timing
    "Rect",
    "ZRect",  # geometry
    "keyboard",
    "mouse",
    "keys",
    "keymods",  # input
    "storage",  # persistence
    "Game",
    "game",
    "exit",
    "load_tile_map",
    "load_tile_map_actors",  # the old name of load_tile_map, kept so older games still run
]
