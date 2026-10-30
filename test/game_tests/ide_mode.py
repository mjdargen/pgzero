"""A game started with ``import pgzrun`` and ``pgzrun.go()``, as in an IDE.

test_runner copies this next to an images/ directory containing alien.png
and runs it both as a script and with the pgzrun runner. Any failed assertion
fails the test.
"""
import sys

import pgzrun
import pygame
from pgzero.game import Game, exit as pgzero_exit

WIDTH = 200
HEIGHT = 150

# Top-level code can load images before the game window opens.
alien = Actor("alien")

assert isinstance(game, Game)
assert exit is pgzero_exit

started = []
drawn = []


def start():
    started.append(True)


def draw():
    screen.clear()
    alien.draw()
    drawn.append(pygame.display.get_surface().get_size())


def finish():
    assert started == [True], started
    assert drawn and drawn[-1] == (WIDTH, HEIGHT), drawn
    print("ide_mode ok")
    sys.exit()


clock.schedule_unique(finish, 0.05)

pgzrun.go()
