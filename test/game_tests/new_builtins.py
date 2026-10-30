"""Check that the pgzero-plus additions are available as builtins."""
from pgzero.game import Game

assert isinstance(game, Game)
assert game.state == "playing"
assert callable(Sprite)
assert callable(SpriteActor)
assert callable(load_tile_map_actors)
assert callable(clock.clear)

WIDTH = HEIGHT = 100


def draw():
    screen.clear()
