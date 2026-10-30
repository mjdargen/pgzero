"""A game that uses start(), the game builtin and game.restart().

Any failed assertion propagates out of the runner and fails the test.
"""
from pgzero.game import Game

WIDTH = HEIGHT = 100

calls = []
frames = []


def start():
    calls.append(game.score)
    game.score = 5


# start() must not have run while the module was being executed.
assert calls == []


def update():
    frames.append(1)
    assert isinstance(game, Game)

    if len(frames) == 1:
        # start() runs once before the first frame
        assert calls == [0], calls
        assert game.score == 5
        assert game.frame_count == 1
        # never clear the clock: the test harness has scheduled an exit
        game.restart(clear_clock="never")
        assert calls == [0, 0], calls
        assert game.score == 5
        assert game.frame_count == 0


def draw():
    screen.clear()
