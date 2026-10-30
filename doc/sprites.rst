Sprite sheets and animated actors
=================================

A plain :ref:`Actor <actor>` shows one picture. To make a character *animate*
(walk, jump, idle, die) you show a sequence of pictures one after another, a
few times per second. ``pgzero-mjd`` adds two builtins for this:

* :class:`Sprite` cuts one animation out of a **sprite sheet** and plays it
  frame by frame.
* :class:`SpriteActor` is an :class:`Actor` whose picture is a
  :class:`Sprite`, so it animates while it moves, collides, scales and flips
  like any other actor.

What is a sprite sheet?
-----------------------

A sprite sheet is a single PNG holding every frame of every animation for a
character, laid out in a grid:

* every frame is the same size (say 24 pixels wide and 16 pixels tall);
* each **row** is one animation (idle, walk, jump, ...);
* the frames of an animation run **left to right** along the row;
* rows are numbered from **0** at the top of the image and frames from 0 at
  the left.

Rows do not have to be full. If the longest animation has 14 frames the sheet
is 14 frames wide, and a 5-frame animation on another row leaves the rest of
its row empty::

    row 0   [idle 0][idle 1][idle 2][idle 3][idle 4][      ][      ][      ]
    row 1   [walk 0][walk 1][walk 2][walk 3][walk 4][walk 5][walk 6][walk 7]
    row 2   [jump 0][jump 1][jump 2][      ][      ][      ][      ][      ]

To use a sheet you need four numbers for each animation: the frame width,
the frame height, the row number, and how many frames are on that row.
Whoever drew the sheet normally tells you (the class ``sprites`` folder has a
``.md`` file next to each sheet with exactly these numbers); otherwise open
the PNG in an image editor and measure.

Where to put the file
---------------------

Sprite sheets live in a ``sprites/`` folder next to your game file, not in
``images/``::

    my_game.py
    sprites/fox.png
    images/background.png

As with every file Pygame Zero loads, the name must be lowercase letters,
numbers and underscores. You can write it with or without the extension:
``"fox"`` and ``"fox.png"`` both work.

A complete example
------------------

This fox idles until you press left or right, walks while the key is held,
faces the way it is moving, and jumps with the up arrow or space. The sheet
``sprites/fox.png`` has 24x16 frames; row 0 is a 5-frame idle and row 2 an
8-frame walk.

::

    import pgzrun
    from pgzero.builtins import *

    WIDTH = 800
    HEIGHT = 400
    TITLE = "Sprite Actor"

    gravity = 1

    # Sprite(filename, frame_width, frame_height, row_number, frame_count, fps)
    fox_idle = Sprite("fox.png", 24, 16, 0, 5, 4)
    fox_walk = Sprite("fox.png", 24, 16, 2, 8, 10)

    fox = SpriteActor(fox_idle)


    def start():
        fox.scale = 4
        fox.bottomleft = (0, HEIGHT)
        fox.velocity_x = 0
        fox.velocity_y = 0


    def draw():
        screen.clear()
        screen.fill("forestgreen")
        fox.draw()


    def update():
        if keyboard.left and fox.left > 0:
            fox.sprite = fox_walk
            fox.flip_h = True
            fox.velocity_x = -5
        elif keyboard.right and fox.right < WIDTH:
            fox.sprite = fox_walk
            fox.flip_h = False
            fox.velocity_x = 5
        else:
            fox.velocity_x = 0

        fox.x += fox.velocity_x
        fox.y += fox.velocity_y

        if fox.bottom >= HEIGHT:
            fox.velocity_y = 0
            fox.bottom = HEIGHT
        else:
            fox.velocity_y += gravity


    def on_key_down(key):
        if (key == keys.SPACE or key == keys.UP) and fox.bottom >= HEIGHT:
            fox.velocity_y = -10


    def on_key_up(key):
        if key == keys.LEFT or key == keys.RIGHT:
            fox.sprite = fox_idle


    pgzrun.go()

Things to notice:

* The sprites are created once, at the top of the file. Creating a
  :class:`Sprite` loads and slices the sheet, so do not do it inside
  ``update()``.
* ``fox.draw()`` advances the animation. You never call ``next_frame()``
  yourself in a normal game.
* Assigning ``fox.sprite = fox_walk`` every frame while the key is held is
  fine: assigning the sprite that is already showing does nothing.
* ``fox.flip_h`` mirrors the picture, so one row of right-facing frames
  serves both directions.
* ``fox.scale = 4`` is set before ``fox.bottomleft``: scaling changes the
  actor's size, so position it afterwards.

Sprite
------

.. class:: Sprite(image_name, frame_width, frame_height, row_number, frame_count, fps=10, transparent_color=None, loop=True)

    Cut one animation out of the sprite sheet ``sprites/<image_name>`` and
    play it.

    :param image_name: Name of the sheet in the ``sprites/`` folder, with or
        without its extension.
    :param frame_width: Width of one frame, in pixels.
    :param frame_height: Height of one frame, in pixels.
    :param row_number: Which row holds the animation. ``0`` is the top row.
    :param frame_count: How many frames to take from that row, starting at
        the left edge. Must be at least 1.
    :param fps: Animation speed in frames per second. ``10`` shows a new
        frame every 100 milliseconds, ``2`` every half second. This is the
        speed of the *animation*; the game itself still runs ``update()``
        60 times a second.
    :param transparent_color: For sheets that use a solid background colour
        instead of real transparency. Pass an ``(r, g, b)`` tuple to make
        that colour see-through, or ``-1`` to use whatever colour is in the
        top-left pixel of each frame. Leave it as ``None`` for PNGs with a
        transparent background, which is the normal case.
    :param loop: ``True`` (the default) plays the animation round and round.
        ``False`` plays it once and then stays on the last frame; see
        :ref:`one-shot`.

    Creating a sprite raises ``ValueError`` immediately if the row or the
    frames would fall outside the image (the message includes the sheet's
    real size, for example ``Row 7 is outside the sprite sheet. The sheet is
    336x112, but row 7 with frame height 16 would end at y=128.``) and
    ``KeyError`` if there is no such file in ``sprites/``.

    .. attribute:: images

        The frames, as a list of Pygame surfaces in order.

    .. attribute:: image

        The surface for the current frame. Read only.

    .. attribute:: frame_index

        Index of the current frame, from ``0`` to ``frame_count - 1``.

    .. attribute:: finished

        ``True`` once a ``loop=False`` animation has shown its last frame for
        a full frame time. Always ``False`` for a looping sprite.

    .. attribute:: fps
                   loop

        The values given to the constructor. You may change them at any time:
        ``fox_walk.fps = 20`` speeds the walk up.

    .. attribute:: image_name
                   frame_width
                   frame_height
                   row_number
                   frame_count

        The other constructor arguments, kept for reference.

    .. attribute:: last_update_time

        Time, in milliseconds since Pygame started, when the frame last
        changed. ``next_frame()`` uses it to decide when the next frame is
        due.

    .. method:: next_frame()

        Move to the next frame if ``1000 / fps`` milliseconds have passed
        since the last change, then return the current frame's surface.
        Calling it more often than that is harmless. After the last frame a
        looping sprite goes back to frame 0; a non-looping one sets
        ``finished`` and stays on the last frame. :class:`SpriteActor` calls
        this for you every time it is drawn.

    .. method:: set_frame(frame_index)

        Jump to a frame and restart the frame timer. Returns the frame's
        surface. Raises ``ValueError`` (``Frame index 7 is out of range``) if
        ``frame_index`` is negative or not less than ``frame_count``.

    .. method:: reset()

        Go back to frame 0 and restart the frame timer. It does **not** clear
        ``finished``: a one-shot animation that has finished stays finished
        after ``reset()``. Set ``finished = False`` yourself to play it again
        (see :ref:`one-shot`).

    .. method:: copy()

        Return a new, independent :class:`Sprite` cut from the same sheet
        with the same size, row, frame count and ``fps``. The copy starts at
        frame 0 with its own timer, so two actors can use the same sheet
        without sharing an animation position.

        ``copy()`` does **not** carry over ``transparent_color`` or ``loop``:
        the copy always loops and has no colour key. Set ``loop`` again by
        hand if you need it::

            death2 = death.copy()
            death2.loop = False

Sharing a sprite, or copying it
'''''''''''''''''''''''''''''''

A :class:`Sprite` remembers which frame it is on. If several actors use the
*same* ``Sprite`` object they animate in step, and when one of them switches
to another sprite and back, all of them restart from frame 0. That is fine
for a crowd of identical bats. When each actor needs its own timing (a
one-shot death animation, for instance) give each one a copy::

    bat_fly = Sprite("bat.png", 16, 16, 0, 4, 8)
    bats = []
    for x in range(50, 400, 60):
        bats.append(SpriteActor(bat_fly.copy(), pos=(x, 100)))

.. _one-shot:

One-shot animations
'''''''''''''''''''

With ``loop=False`` the sprite plays through once and ``finished`` becomes
``True``. Use it for explosions, attacks and deaths::

    fox_idle = Sprite("fox.png", 24, 16, 0, 5, 4)
    fox_die = Sprite("fox.png", 24, 16, 6, 7, 8, loop=False)
    fox = SpriteActor(fox_idle, pos=(200, 200))


    def update():
        if fox.sprite is fox_die and fox_die.finished:
            fox.pause()  # stay on the last frame


    def on_key_down(key):
        if key == keys.D:
            fox.sprite = fox_die

To play a one-shot again later, put it back to the start and clear the flag
before switching to it::

    fox_die.set_frame(0)
    fox_die.finished = False
    fox.sprite = fox_die
    fox.resume()

Both lines are needed because neither ``set_frame()`` nor ``reset()``
clears ``finished``, and because ``fox.sprite = fox_die`` does nothing when
``fox_die`` is already the sprite being shown.

SpriteActor
-----------

.. class:: SpriteActor(sprite, pos=None, anchor=('center', 'center'), collision_rect=None, **kwargs)

    An :class:`Actor` drawn with an animated :class:`Sprite` instead of a
    fixed image. Everything in :ref:`Actors <actor>` and
    :doc:`actor-additions` applies: ``pos``, ``x``, ``y``, ``topleft`` and
    the other rectangle attributes, ``anchor``, ``angle``, ``opacity``,
    ``scale``, ``flip_h``, ``collision_rect``, ``colliderect()``,
    ``collidelist()``, ``distance_to()`` and so on. Only the picture is
    different.

    :param sprite: A :class:`Sprite`. Passing a file name here is a common
        mistake; it fails with ``AttributeError: 'str' object has no
        attribute 'image'``.
    :param pos: Position of the anchor point, as for :class:`Actor`. If no
        position is given the actor starts with its top-left corner at
        ``(0, 0)``.
    :param anchor: Anchor point, as for :class:`Actor`.
    :param collision_rect: Optional collision body; see
        :ref:`collision-rect`.
    :param kwargs: One position keyword such as ``center=`` or
        ``bottomleft=``, as for :class:`Actor`. It cannot be combined with
        ``pos``.

    .. attribute:: sprite

        The :class:`Sprite` currently playing. Assign another sprite to
        switch animation. The new sprite is reset to its first frame, unless
        it is the very object already playing, in which case nothing
        happens, so assigning in ``update()`` every frame is safe.

    .. method:: draw()

        Advance the animation (unless paused) and draw the current frame at
        the actor's position with its scale, flips, angle and opacity
        applied.

    .. method:: update_animation()

        Advance the animation without drawing. ``draw()`` calls this for you;
        call it yourself only when an actor should keep animating while it
        is not being drawn.

    .. method:: pause()

        Freeze on the current frame. The actor is still drawn and can still
        move.

    .. method:: resume()

        Continue animating after :meth:`pause`.

    .. attribute:: paused

        ``True`` while paused. Read only.

    .. attribute:: image

        For a plain :class:`Actor` this is the image name. A
        :class:`SpriteActor` has no image name, so its ``image`` is the empty
        string ``""``. Do not use ``image`` to tell sprite actors apart;
        compare sprites (``if fox.sprite is fox_walk``) or give the actor
        your own attribute (``fox.kind = "fox"``).

The animation speed and the game speed are independent: ``update()`` runs 60
times a second, but a sprite with ``fps=10`` only changes frame on every
sixth draw.

SpriteSheet
-----------

:class:`Sprite` is built on a lower-level helper that pulls arbitrary
rectangles out of a sheet. Use it directly when a sheet holds icons or tiles
that are not laid out as animation rows. It is not a builtin; import it with
``from pgzero.sprites import SpriteSheet``.

.. class:: SpriteSheet(name)

    Load ``sprites/<name>``.

    .. attribute:: sheet

        The whole image as a Pygame surface.

    .. method:: image_at(rectangle, color_key=None)

        Copy the region ``(x, y, width, height)`` into a new surface and
        return it. ``color_key`` works like ``transparent_color`` above.

    .. method:: images_at(rects, color_key=None)

        :meth:`image_at` for each rectangle in ``rects``; returns a list.

    .. method:: load_strip(rect, image_count, color_key=None)

        Return ``image_count`` surfaces starting at ``rect`` and stepping
        right by the rectangle's width each time. :class:`Sprite` uses this
        with ``rect = (0, row_number * frame_height, frame_width,
        frame_height)``.

An :class:`Actor` accepts a surface in place of an image name, so you can
show the pieces directly::

    from pgzero.sprites import SpriteSheet

    icons = SpriteSheet("icons").load_strip((0, 0, 16, 16), 6)
    heart = Actor(icons[0], pos=(20, 20))

Making sprite sheets
--------------------

Free sheets are easy to find online (itch.io and Kenney.nl are good places
to start), and the class repository ships a ``sprites/`` folder of ready-made
ones with a ``.md`` file for each giving the frame size and the rows. To draw
your own, Aseprite_ and Piskel_ both export sprite sheets with one animation
per row, which is the layout :class:`Sprite` expects. If a sheet is packed
differently, the ``utils/`` folder of the class repository has scripts to
re-pack it.

.. _Aseprite: https://www.aseprite.org/
.. _Piskel: https://www.piskelapp.com/
