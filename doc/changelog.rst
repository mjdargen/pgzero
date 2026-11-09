Changelog
=========

Pygame Zero Plus
----------------

0.1.0 - Initial release
~~~~~~~~~~~~~~~~~~~~~~~

* Enhanced Actors with scaling, flipping, opacity, and custom collisions.
* Added ``actor.move_toward(target, speed)``, e.g. to make an enemy chase the
  player.
* Added ``actor.visible``. Hidden actors aren't drawn but still move and
  collide, like ``visible`` in Godot.
* ``Actor()`` accepts ``scale``, ``angle``, ``opacity``, ``flip_h``, ``flip_v``
  and ``flip_d``, applied before positioning, so the position given is where
  the finished actor ends up, e.g.
  ``Actor('fox', midbottom=(100, HEIGHT), scale=4)``.
* ``Actor()`` no longer silently ignores keyword arguments it doesn't use. It
  says what to write instead: a position pair for ``right=0``, ``pos`` for
  ``position``, or the correct spelling of a typo.
* Added Sprites: animations from a sprite sheet or a list of images, which
  any Actor can play with ``actor.sprite = fox_walk``. Many actors can share
  one Sprite, and animations hold still while the game is paused. A Sprite
  with ``loop=False`` plays once, and plays again if it is set again after
  finishing. Sprite sheet animations can carry on over several rows, and
  sheets with gaps between frames are supported with ``spacing`` and
  ``margin``. Leaving out ``frames`` uses the whole row, apart from empty
  frames at the end.
* Added ``FULLSCREEN = True``, which scales the game to fill the screen while
  keeping its shape and its ``WIDTH`` x ``HEIGHT`` coordinates. F11 switches
  between fullscreen and a window.
* Added support for tilemaps created with Tiled Map Editor.
  ``load_tile_map_actors()`` returns a ``TileMap`` of layers that work like
  lists of tile Actors, so ``player.collidelist(walls)`` and
  ``coins.pop(index)`` work. ``walls.get_tile(col, row)``,
  ``walls.set_tile(col, row, tile)`` and ``walls.remove_tile(col, row)``
  find, place and remove tiles by square, ``level.create_tile(tile_col,
  tile_row)`` makes a new tile from the tileset, and
  ``level.pos_to_map(x, y)`` and ``level.map_to_pos(col, row)`` convert
  between pixels and squares. Maps scroll with ``level.x`` and ``level.y``,
  or with ``level.follow(player)``, which keeps the player in the middle of
  the screen and stops at the map's edges. ``level.draw()`` draws the
  visible layers, and custom properties set in
  Tiled are in ``tile.properties``.
* Actors that are completely off the screen are skipped when drawn, so big tile
  maps draw much faster.
* Added game management and restart functionality.
* Added a ``start()`` hook, called when the game starts and on every restart.
* ``screen.draw.rect()`` and ``screen.draw.filled_rect()`` also accept a
  position and size, e.g. ``screen.draw.rect((20, 20), (100, 50), 'red')``.
* ``music.is_playing()`` can check for a particular track, and
  ``music.is_paused()`` was added.
* Added ``clock.clear()`` to unschedule everything.
* Games still run, with silent sound, on computers without a sound device,
  without printing the sound system's errors (e.g. ALSA's on Linux).
* Games no longer print "no fast renderer available" on virtual desktops
  without graphics acceleration.
* Running games one after another in the same Python process (e.g. in Spyder)
  no longer crashes when they play sounds. ``sounds.unload()`` and
  ``unload_all()`` now really reload the sound next time.
* Removed an old macOS workaround that restarted ``pgzrun`` with a different
  Python when run from a virtual environment. pygame 2 doesn't need it.
* Uppercase keyboard names such as ``keyboard.LEFT`` no longer print
  deprecation warnings.
* Uses pygame-ce on Python 3.10 and newer, and supports Python 3.14 and 3.15.
* The tone generator no longer needs pyfxr. Tones now last exactly as long as
  requested, and waveforms can be given by name, e.g.
  ``tone.play('C4', 1, waveform='square')``.

Original Pygame Zero
--------------------

The following release history is inherited from the original
Pygame Zero project.

1.3 - unreleased
~~~~~~~~~~~~~~~~

* New: :ref:`Actors can be made transparent <transparency>` by assigning to
  ``actor.opacity`` (based on work by Rhys Puddephatt and charlesej)
* New: screen.fill() now takes ``gcolor``, creating a vertical-linear gradient
* New: Added a :ref:`storage API <data-storage>`, which preserves data across
  game runs (based on work by Ian Salmons and Gustavo Ferreira)


1.2 - 2018-02-24
----------------

* New: :ref:`Actors can be rotated <rotation>` by assigning to ``actor.angle``
* New: Actors now have :meth:`~Actor.angle_to()` and
  :meth:`~Actor.distance_to()` methods.
* New: Actors are no longer subclasses of Rect, though they provide the same
  methods/properties. However they are now provided with floating point
  precision.
* New: ``tone.play()`` function to allow playing musical notes.
* New: ``pgzrun.go()`` to allow running Pygame Zero from an IDE (see
  :doc:`ide-mode`).
* New: show joypad icon by default
* Examples: add Asteroids example game (thanks to Ian Salmons)
* Examples: add Flappy Bird example game
* Examples: add Tetra example game (thanks to David Bern)
* Docs: Add a logo, fonts and colours to the documentation.
* Docs: Documentation for the :ref:`anchor point system for Actors <anchor>`
* Docs: Add :doc:`from-scratch` documentation
* Fix: ``on_mouse_move()`` did not correctly handle the ``buttons`` parameter.
* Fix: Error message when resource not found incorrectly named last extension
  searched.
* Fix: Drawing wrapped text would cause crashes.
* Fix: :func:`animate()` now replaces animations of the same property, rather
  than creating two animations which fight.
* Updated ptext to a revision as of 2016-11-17.
* Removed: removed undocumented British English ``centrex``, ``centrey``,
  ``centre`` attribute aliases on ZRect (because they are not Rect-compatible).

1.1 - 2015-08-03
----------------

* Added a spell checker that will point out hook or parameter names that have
  been misspelled when the program starts.
* New ZRect built-in class, API compatible with Rect, but which accepts
  coordinates with floating point precision.
* Refactor of built-in ``keyboard`` object to fix attribute case consistency.
  This also allows querying key state by ``keys`` constants, eg.
  ``keyboard[keys.LEFT]``.
* Provide much better information when sound files are in an unsupported
  format.
* ``screen.blit()`` now accepts an image name string as well as a Surface
  object, for consistency with Actor.
* Fixed a bug with non-focusable windows and other event bugs when running in
  a virtualenv on Mac OS X.
* Actor can now be positioned by any of its border points (eg. ``topleft``,
  ``midright``) directly in the constructor.
* Added additional example games in the ``examples/`` directory.

1.0.2 - 2015-06-04
------------------

* Fix: ensure compatibility with Python 3.2

1.0.1 - 2015-05-31
------------------

This is a bugfix release.

* Fix: Actor is now positioned to the top left of the window if ``pos`` is
  unspecified, rather than appearing partially off-screen.

* Fix: repeating clock events can now unschedule/reschedule themselves

  Previously a callback that tried to unschedule itself would have had no
  effect, because after the callback returns it was rescheduled by the clock.

  This applies also to ``schedule_unique``.

* Fix: runner now correctly displays tracebacks from user code

* New: Eliminate redraws when nothing has changed

  Redraws will now happen only if:

      * The screen has not yet been drawn
      * You have defined an update() function
      * An input event has been fired
      * The clock has dispatched an event


1.0 - 2015-05-29
----------------

* New: Added ``anchor`` parameter to Actor, offering control over where its
  ``pos`` attribute refers to. By default it now refers to the center.

* New: Added Ctrl-Q/⌘-Q as a hard-coded keyboard shortcut to exit a game.

* New: ``on_mouse_*`` and ``on_key_*`` receive ``IntEnum`` values as ``button``
  and ``key`` parameters, respectively. This simplifies debugging and enables
  usage like::

        if button is button.LEFT:


1.0beta1 - 2015-05-19
---------------------

Initial public (preview) release.
