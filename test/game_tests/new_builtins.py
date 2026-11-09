"""Check that the pgzero-plus additions are available as builtins."""
from pgzero.game import Game

assert isinstance(game, Game)
assert game.state == "playing"
assert callable(Sprite)
assert callable(load_tile_map)
assert load_tile_map_actors is load_tile_map  # the old name still works
assert callable(clock.clear)

WIDTH = HEIGHT = 100


def draw():
    screen.clear()
