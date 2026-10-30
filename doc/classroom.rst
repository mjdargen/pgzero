What's different in this build
==============================

``pgzero-mjd`` is Mike D'Argenio's classroom build of `Pygame Zero`_. It is
the same library you will find in the rest of these docs, with some additions
that make it easier to build the kind of games we make in class:

* **Sprite sheets and animated actors**: :class:`Sprite` and
  :class:`SpriteActor`. See :doc:`sprites`.
* **Tile maps drawn in Tiled**: :func:`load_tile_map_actors`. See
  :doc:`tilemaps`.
* **A game object** for score, level and win/lose state, a ``start()`` hook
  that runs on every restart, and a clean ``exit()``. See :doc:`game`.
* **Extra actor features**: ``scale``, ``flip_h``, ``flip_v``,
  ``collision_rect``, ``collidelist()`` and more. See :doc:`actor-additions`.

The source code is at https://github.com/mjdargen/pgzero. The original
project, whose documentation this is based on, is at
https://github.com/lordmauve/pgzero.

.. _`Pygame Zero`: https://pygame-zero.readthedocs.io/

The shape of a game
-------------------

Every program in class looks like this::

    import pgzrun
    from pgzero.builtins import *

    WIDTH = 800
    HEIGHT = 600
    TITLE = "My Game"

    # create actors and sprites here


    def start():
        # runs once before the first frame, and again on every restart
        pass


    def draw():
        screen.clear()


    def update():
        pass


    pgzrun.go()  # must be the last line

The first two lines and the last one are what let you run the file like any
other Python program (``python my_game.py``, or the Run button in your
editor). ``import pgzrun`` has to come first: it sets up the window and the
folders your assets are loaded from. ``from pgzero.builtins import *``
brings the Pygame Zero names (``Actor``, ``screen``, ``keyboard``,
``game`` and so on) into your file so that your editor can autocomplete
them and so that ``exit()`` is Pygame Zero's version. You can also leave all
three lines out and run the file with ``pgzrun my_game.py``, as the rest of
these docs describe.

Where files go
--------------

Everything is loaded by name from a folder next to your game file. File
names must be lowercase letters, numbers and underscores, and you leave the
extension off when you use the name in code.

===============  ======================================  ==========================================
Folder           What goes in it                         How you use it
===============  ======================================  ==========================================
``images/``      Single pictures (``.png``, ``.jpg``,    ``Actor("alien")``,
                 ``.gif``, ``.webp``)                    ``screen.blit("alien", (0, 0))``,
                                                         ``images.alien``
``sprites/``     Sprite sheets (``.png``)                ``Sprite("fox.png", 24, 16, 0, 5)``
``maps/``        Tiled maps (``.tmx``), tilesets         ``load_tile_map_actors("level1.tmx")``
                 (``.tsx``) and their tileset images
``sounds/``      Short sound effects (``.wav``,          ``sounds.jump.play()``
                 ``.ogg``)
``music/``       Long music tracks (``.ogg``, ``.mp3``)  ``music.play("theme")``
``fonts/``       TrueType fonts (``.ttf``)               ``screen.draw.text(..., fontname="pixel")``
===============  ======================================  ==========================================

Smaller differences
-------------------

* A :func:`start` function in your file is called once before the first
  frame and again on every ``game.restart()``.
* The ``game`` object is ticked every frame, so ``game.timer`` and
  ``game.frame_count`` keep counting without any code from you.
* ``actor.image`` is always a string: the image name, or ``""`` for an actor
  built from a surface such as a :class:`SpriteActor` or a map
  :class:`Tile`.
* ``music.is_playing("name")`` tells you whether a particular track is
  playing, and ``music.is_paused()`` whether the music is paused.
* ``screen.draw.rect((x, y), (w, h), color)`` and
  ``screen.draw.filled_rect((x, y), (w, h), color)`` work without creating a
  ``Rect`` first.
* ``keyboard.LEFT`` and ``keyboard.K_a`` work without printing a deprecation
  warning (``keyboard.left`` and ``keyboard.a`` are still the recommended
  spelling).
* Pygame's start-up banner and some library warnings are hidden, and when a
  game runs inside Codio the sound system is switched to a silent driver
  automatically so that games still run there.
* ``pgzrun --version`` prints the installed version.

Everything else, from ``Actor`` to ``storage``, is standard Pygame Zero and
documented in the rest of these pages.
