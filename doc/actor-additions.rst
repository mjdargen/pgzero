Actor additions
===============

This build adds a few things to the standard :ref:`Actor <actor>`. They all
work on :class:`SpriteActor` and on the :class:`Tile` actors from a map as
well.

A complete example
------------------

Walk the fox into the rock and the tree. The red outlines are each actor's
collision body: the rock's is a box smaller than its picture, and the tree's
is pushed down so that only the trunk counts.

::

    import pgzrun
    from pgzero.builtins import *

    WIDTH = 500
    HEIGHT = 500
    TITLE = "Collision Boxes"

    fox_idle = Sprite("fox.png", 24, 16, 0, 5, 4)
    player = SpriteActor(fox_idle)
    rock = Actor("rock")
    tree = Actor("tree")


    def start():
        player.scale = 3
        player.pos = (WIDTH / 2, 300)
        # the frame is 24x16 but only a 16x8 box, shifted 2 right and
        # 4 down from the frame's centre, should count as "the fox"
        player.collision_rect = (16, 8, 2, 4)

        rock.pos = (100, 200)
        rock.collision_rect = (40, 30)          # a centred 40x30 box
        tree.pos = (400, 200)
        tree.collision_rect = (30, 50, 0, 20)   # 30x50, shifted 20 down


    def draw():
        screen.clear()
        player.draw()
        rock.draw()
        tree.draw()
        # red outlines show what will collide
        player.draw_collision_rect()
        rock.draw_collision_rect()
        tree.draw_collision_rect()
        if player.colliderect(rock):
            screen.draw.text("Rock!", center=(WIDTH / 2, 50), color="red", fontsize=40)
        elif player.colliderect(tree):
            screen.draw.text("Tree!", center=(WIDTH / 2, 50), color="red", fontsize=40)


    def update():
        if keyboard.left:
            player.x -= 5
            player.flip_h = True
        if keyboard.right:
            player.x += 5
            player.flip_h = False
        if keyboard.up:
            player.y -= 5
        if keyboard.down:
            player.y += 5


    pgzrun.go()

Scale
-----

.. attribute:: Actor.scale

    Multiply the drawn size by this number: ``1.0`` is normal size, ``2``
    double, ``0.5`` half. The actor's ``width`` and ``height``, its
    collision body and its anchor all scale with it, and the anchor point
    stays where it is, so a centred actor grows around its centre. Resizing
    does not blur, which keeps pixel art crisp.

    Set ``scale`` *before* you position an actor by an edge, because
    scaling changes where the edges are::

        fox.scale = 4
        fox.bottomleft = (0, HEIGHT)

Flipping
--------

.. attribute:: Actor.flip_h
               Actor.flip_v
               Actor.flip_d

    ``True`` to mirror the picture left-to-right (``flip_h``), top-to-bottom
    (``flip_v``), or across the diagonal (``flip_d``, which swaps the
    picture's x and y axes; Tiled uses it to store rotated tiles, and you
    will rarely set it yourself). All default to ``False``. The anchor point
    stays in place when you flip, so a walking character can turn round
    without moving.

    Flipping is the usual way to get a left-facing walk from a right-facing
    sprite sheet::

        if keyboard.left:
            fox.flip_h = True
        elif keyboard.right:
            fox.flip_h = False

    When several transforms are set they apply in this order: opacity,
    scale, flips, then ``angle``.

.. _collision-rect:

The collision body
------------------

By default an actor's rectangle is the whole picture, so a character with a
big sword or a tree with a wide crown "touches" things that are nowhere near
its body. ``collision_rect`` lets you choose a smaller box.

.. attribute:: Actor.collision_rect

    Set it to one of:

    * ``None``: the whole picture (the default);
    * ``(width, height)``: a box of that size centred on the picture;
    * ``(width, height, offset_x, offset_y)``: the same box moved by
      ``offset_x`` pixels to the right and ``offset_y`` pixels down from the
      picture's centre (use negative numbers for left and up).

    The numbers are in the picture's own pixels, before ``scale``; the box
    is scaled, flipped and rotated along with the picture. Any other shape
    of tuple raises ``ValueError``.

    The box becomes the actor's rectangle: ``width``, ``height``, ``pos``,
    ``x``, ``y``, ``left``, ``bottom`` and all the other position attributes
    now describe the box, and so do ``colliderect()``, ``collidelist()`` and
    ``collidepoint()``. The picture is drawn around the box, offset the
    opposite way. Assigning a new ``collision_rect`` keeps the picture where
    it was on screen and moves the box, so an actor never visibly jumps
    when you change it.

    Reading ``collision_rect`` gives the actor's current rectangle (a
    :ref:`Rect <rect>` in screen coordinates), not the tuple you set.

    You can also pass it when creating an actor::

        tree = Actor("tree", pos=(400, 200), collision_rect=(30, 50, 0, 20))
        fox = SpriteActor(fox_idle, collision_rect=(16, 8, 2, 4))

.. method:: Actor.draw_collision_rect()

    Draw the collision body as a 2-pixel red outline. Call it in ``draw()``
    after ``actor.draw()`` while you are tuning the box, then remove it.

Collision methods
-----------------

These exist in Pygame Zero already, through the :ref:`Rect <rect>`
attributes every actor has; this build makes sure they use the collision
body and accept other actors directly.

.. method:: Actor.colliderect(other)

    ``True`` if this actor's body overlaps ``other``, which may be another
    actor or a ``Rect``.

.. method:: Actor.collidelist(others)

    Given a list of actors or rects, return the index of the *first* one
    this actor overlaps, or ``-1`` if it overlaps none. Typical use::

        index = fox.collidelist(coins)
        if index != -1:
            coins.pop(index)

.. method:: Actor.collidepoint(pos)

    ``True`` if the point ``(x, y)`` is inside the actor's body. Useful in
    ``on_mouse_down(pos)``.

Image names and surfaces
------------------------

.. attribute:: Actor.image

    Always a string: the image name you gave, or ``""`` for an actor built
    from a surface (a :class:`SpriteActor`, a map :class:`Tile`, or
    ``Actor(some_surface)``). That makes ``if coin.image == "coin_gold"``
    safe to write, and lets you use the image name as a dictionary key for
    an inventory.

    You may assign a name or a Pygame surface::

        alien.image = "alien_hurt"           # from images/
        alien.image = images.alien_hurt      # the same surface, loaded by you
        heart = Actor(icons[0], pos=(20, 20))  # a surface cut from a sheet

Frame animation from separate files
-----------------------------------

If your frames are separate files in ``images/`` (``walk01.png``,
``walk02.png``, ...) rather than a sprite sheet, an ordinary actor can
cycle through them::

    alien = Actor("alien_green_walk01", pos=(100, 100))
    alien.images = ["alien_green_walk01", "alien_green_walk02", "alien_green_walk03"]
    alien.fps = 8


    def update():
        alien.animate()

.. attribute:: Actor.images

    A list of image names. Assigning a non-empty list also shows its first
    image. Defaults to an empty list.

.. attribute:: Actor.fps

    How many times per second :meth:`animate` moves to the next image.
    Defaults to ``5``.

.. method:: Actor.next_image()

    Show the next name in ``images``, wrapping round to the first after the
    last. If the current image is not in the list, show the first. Does
    nothing when ``images`` is empty.

.. method:: Actor.animate()

    Call it every frame (from ``update()``): it calls :meth:`next_image`
    ``fps`` times per second, based on the clock, so the animation speed
    does not depend on the frame rate. (This method on an actor is
    unrelated to the builtin :func:`animate` function, which moves
    attributes smoothly over time.)

For anything beyond a short loop, a sprite sheet and :class:`SpriteActor`
are easier; see :doc:`sprites`.

.. attribute:: Actor.sprite

    ``None`` on a plain actor. On a :class:`SpriteActor` it is the
    :class:`Sprite` being played.

Drawing rectangles without a Rect
---------------------------------

``screen.draw.rect()`` and ``screen.draw.filled_rect()`` accept a position
and a size instead of a :ref:`Rect <rect>`::

    screen.draw.filled_rect((10, 10), (120, 40), "red")       # health bar
    screen.draw.rect((10, 10), (120, 40), "white", width=2)   # its border

The ``Rect`` form still works (``screen.draw.rect(box, "white", width=2)``).
In this build pass ``width`` by keyword in both forms; a positional width
such as ``screen.draw.rect(box, "white", 2)`` raises ``TypeError``.
