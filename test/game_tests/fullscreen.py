"""A game that starts fullscreen, then switches with F11.

Run by FullscreenTest in a separate process with SDL's dummy video driver,
whose screen is 1024x768. It prints what it saw and exits by itself.
"""
import sys

import pgzrun
import pygame
from pgzero.builtins import *

WIDTH = 400
HEIGHT = 300
FULLSCREEN = True

alien = Actor("alien", center=(200, 150))
frame = 0


def draw():
    screen.fill("black")
    alien.draw()


def update():
    global frame
    frame += 1
    if frame in (5, 10, 15):
        alien_drawn = screen.surface.get_at((200, 150))[:3] != (0, 0, 0)
        print(FULLSCREEN, pygame.display.get_window_size(), screen.surface.get_size(), alien_drawn)
        if frame < 15:
            # Hold a key while switching, then press F11
            keyboard._press(keys.RIGHT)
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11, mod=0, unicode=""))
    if frame == 16:
        print("right held:", keyboard.right)
        sys.exit()


pgzrun.go()
