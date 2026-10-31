Built-in Objects
================

Pygame Zero provides useful built-in objects to help you make games easily.


.. _window:

The Game Window
---------------

Set these variables at the top of your game to set up its window:

``WIDTH``, ``HEIGHT``
    The size of the window in pixels. The default is 800 by 600.

``TITLE``
    The text in the window's title bar. The default is
    ``'Pygame Zero Game'``.

``ICON``
    The name of an image in the ``images`` directory to show as the window's
    icon. A small square image, such as 32 by 32 pixels, works best.

For example::

    WIDTH = 640
    HEIGHT = 480
    TITLE = 'Space Dodge'
    ICON = 'rocket'

These are read again on every frame, so changing them while the game is
running, such as ``TITLE = 'Paused'``, changes the window. Use ``global`` to
change them from inside a function.


.. _screen:

Screen
------

.. toctree::
    :hidden:

    ptext

The ``screen`` object represents your game screen.

It is a thin wrapper around a Pygame surface that allows you to easily
draw images to the screen ("blit" them).

.. class:: Screen

    .. attribute:: surface

        The raw `Pygame surface`_ that represents the screen buffer. You can
        use this for advanced graphics operations.

        .. _`Pygame surface`: https://www.pygame.org/docs/ref/surface.html

    .. method:: bounds()

        .. versionadded:: 1.3

        Return a ZRect representing the bounds of the screen.

    .. method:: clear()

        Reset the screen to black.

    .. method:: fill((red, green, blue), [gcolor=(r, g, b)])

        Fill the screen with a solid color.

        .. versionadded:: 1.3

            If ``gcolor`` is given then fill with a gradient, from ``color`` at
            the top of the screen to ``gcolor`` at the bottom.

    .. method:: blit(image, (left, top))

        Draw the image to the screen at the given position.

        ``blit()`` accepts either a Surface or a string as its ``image``
        parameter. If ``image`` is a ``str`` then the named image will be
        loaded from the ``images/`` directory.

    .. method:: draw.line(start, end, (r, g, b), width=1)

        Draw a line from start to end with a certain line width.

    .. method:: draw.circle(pos, radius, (r, g, b), width=1)

        Draw the outline of a circle with a certain line width.

    .. method:: draw.filled_circle(pos, radius, (r, g, b))

        Draw a filled circle.

    .. method:: draw.polygon(points, (r, g, b))

        Draw the outline of a shape with straight sides. ``points`` is a list
        of the ``(x, y)`` corners, in order::

            screen.draw.polygon([(100, 50), (150, 150), (50, 150)], 'red')

    .. method:: draw.filled_polygon(points, (r, g, b))

        Draw a filled shape with straight sides, such as a triangle or a star.

    .. method:: draw.rect(rect, (r, g, b), width=1)
                draw.rect((x, y), (w, h), (r, g, b), width=1)

        Draw the outline of a rectangle with a certain line width.

        Takes a :ref:`Rect <rect>`, or the position of the top-left corner
        and the size of the rectangle::

            screen.draw.rect((20, 20), (100, 50), 'yellow')

    .. method:: draw.filled_rect(rect, (r, g, b))
                draw.filled_rect((x, y), (w, h), (r, g, b))

        Draw a filled rectangle. Like ``draw.rect()``, this takes a
        :ref:`Rect <rect>` or a position and size.

    .. method:: draw.text(text, [pos], **kwargs)

        Draw text.

        There's an extremely rich API for positioning and formatting text; see
        :doc:`ptext` for full details.

    .. method:: draw.textbox(text, rect, **kwargs)

        Draw text, sized to fill the given :ref:`Rect`.

        There's an extremely rich API for formatting text; see
        :doc:`ptext` for full details.

.. tip::

    All of the colours can be specified as ``(r, g, b)`` tuples, or by
    name, using one of :doc:`Pygame's colour names <colors_ref>`

.. _rect:

Rect
----

The `Pygame Rect`_ class is available as a built in. This can be used in a
variety of ways, from detecting clicks within a region to drawing a box onto
the screen:

For example, you can draw a box with::

    RED = 200, 0, 0
    BOX = Rect((20, 20), (100, 100))

    def draw():
        screen.draw.rect(BOX, RED)


.. _`Pygame Rect`: https://www.pygame.org/docs/ref/rect.html


Resource Loading
----------------

The ``images`` and ``sounds`` objects can be used to load images and sounds
from files stored in the ``images`` and ``sounds`` subdirectories respectively.
Pygame Zero will handle loading of these resources on demand and will cache
them to avoid reloading them.

Pygame Zero Plus also loads sprite sheets from a ``sprites`` directory (see
:ref:`sprites`) and Tiled maps from a ``maps`` directory (see
:ref:`tile-maps`).

You generally need to ensure that your images are named with lowercase letters,
numbers and underscores only. They also have to start with a letter.

File names like these will work well with the resource loader::

    alien.png
    alien_hurt.png
    alien_run_7.png

These will not work::

    3.png
    3degrees.png
    my-cat.png
    sam's dog.png

The resource loader caches loaded images and sounds. To clear the cache (for
instance, if you are running into memory issues), use the `unload()` and
`unload_all()` functions.

Example::

    cow = Actor('cow')
    loader.images.unload('cow')  # clears the cache of cow.png
    loader.images.unload_all()  # clears all cached image files


Images
''''''

Pygame Zero can load images in ``.png``, ``.gif``, ``.jpg``, ``.bmp`` and
``.webp`` formats. PNG is recommended: it will allow high quality images with
transparency.

We need to ensure an images directory is set up. If your project contains the
following files::

    space_game.py
    images/alien.png

Then ``space_game.py`` could draw the 'alien' sprite to the screen with this
code::

    def draw():
        screen.clear()
        screen.blit('alien', (10, 10))

The name passed to ``blit()`` is the name of the image file within the images
directory, without the file extension.

Or using the :ref:`actor` API, ::

    alien = Actor('alien')

    def draw():
        alien.draw()

There are some restrictions on the file names in both cases: they may only
contain lowercase latin letters, numbers and underscores. This is to prevent
compatibility problems when your game is played on a different operating system
that has different case sensitivity.

Image Surfaces
''''''''''''''

You can also load images from the ``images`` directory using the ``images``
object. This allows you to work with the image data itself, query its
dimensions and so on::

    forest = []
    for i in range(5):
        forest.append(
            Actor('tree', topleft=(images.tree.get_width() * i, 0))
        )

Each loaded image is a Pygame ``Surface``. You will typically use
``screen.blit(...)`` to draw this to the screen. It also provides handy methods
to query the size of the image in pixels:

.. class:: Surface

    .. method:: get_width()

        Returns the width of the image in pixels.

    .. method:: get_height()

        Returns the height of the image in pixels.

    .. method:: get_size()

        Returns a tuple (width, height) indicating the size in pixels of the
        surface.

    .. method:: get_rect()

        Get a :class:`Rect` that is pre-populated with the bounds of the image
        if the image was located at the origin.

        Effectively this is equivalent to::

            Rect((0, 0), image.get_size())


Sounds
''''''

Pygame Zero can load sounds in ``.wav`` and ``.ogg`` formats. WAV is great for
small sound effects, while OGG is a compressed format that is more suited to
music. You can find free .ogg and .wav files online that can be used in your
game.

We need to ensure a sounds directory is set up. If your project contains the
following files::

    drum_kit.py
    sounds/drum.wav

Then ``drum_kit.py`` could play the drum sound whenever the mouse is clicked
with this code::

    def on_mouse_down():
        sounds.drum.play()

Each loaded sound is a Pygame ``Sound``, and has various methods to play and
stop the sound as well as query its length in seconds:

.. class:: Sound

    .. method:: play()
        :noindex:

        Play the sound.

    .. method:: play(loops)

        Play the sound, but loop it a number of times.

        :param loops: The number of times to loop. If you pass ``-1`` as the
                      number of times to loop, the sound will loop forever (or
                      until you call :meth:`.Sound.stop()`

    .. method:: stop()

        Stop playing the sound.

    .. method:: get_length()

        Get the duration of the sound in seconds.

    .. method:: set_volume(volume)

        Set how loud this sound plays, from 0 (silent) to 1 (full volume)::

            sounds.explosion.set_volume(0.5)

    .. method:: get_volume()

        Get this sound's volume, from 0 to 1.

You should avoid using the ``sounds`` object to play longer pieces of music.
Because the sounds sytem will fully load the music into memory before playing
it, this can use a lot of memory, as well as introducing a delay while the
music is loaded.

.. _music:

Music
-----

.. versionadded:: 1.1

.. warning::

    The music API is experimental and may be subject to cross-platform
    portability issues.

    In particular:

    * MP3 may not be available on some Linux distributions.
    * Some OGG Vorbis files seem to hang Pygame with 100% CPU.

    In the case of the latter issue, the problem may be fixed by re-encoding
    (possibly with a different encoder).


A built-in object called ``music`` provides access to play music from within
a ``music/`` directory (alongside your ``images/`` and ``sounds/`` directories,
if you have them). The music system will load the track a little bit at a time
while the music plays, avoiding the problems with using ``sounds`` to play
longer tracks.

Another difference to the sounds system is that only one music track can be
playing at a time. If you play a different track, the previously playing track
will be stopped.


.. function:: music.play(name)

    Play a music track from the given file. The track will loop indefinitely.

    This replaces the currently playing track and cancels any tracks previously
    queued with ``queue()``.

    You do not need to include the extension in the track name; for example, to
    play the file ``handel.mp3`` on a loop::

        music.play('handel')

.. function:: music.play_once(name)

    Similar to ``play()``, but the music will stop after playing through once.

.. function:: music.queue(name)

    Similar to ``play_once()``, but instead of stopping the current music, the
    track will be queued to play after the current track finishes (or after
    any other previously queued tracks).

.. function:: music.stop()

    Stop the music.

.. function:: music.pause()

    Pause the music temporarily. It can be resumed by calling
    ``unpause()``.

.. function:: music.unpause()

    Unpause the music.

.. function:: music.is_playing(name=None)

    Returns True if the music is playing (and is not paused), False otherwise.

    If you give a track name, returns True only if that track is the one
    playing::

        if not music.is_playing('boss_theme'):
            music.play('boss_theme')

.. function:: music.is_paused()

    Returns True if the music has been paused with ``pause()``.

.. function:: music.fadeout(duration)

    Fade out and eventually stop the current music playback.

    :param duration: The duration in seconds over which the sound will be faded
                    out. For example, to fade out over half a second, call
                    ``music.fadeout(0.5)``.

.. function:: music.set_volume(volume)

    Set the volume of the music system.

    This takes a number between 0 (meaning silent) and 1 (meaning full volume).

.. function:: music.get_volume()

    Get the current volume of the music system.

.. function:: music.rewind()

    Start the current track again from the beginning.

.. function:: music.get_pos()

    Get how long the current track has been playing, in milliseconds.

.. function:: music.set_pos(seconds)

    Jump to a point in the current track. For OGG files, this is the number of
    seconds from the start of the track.


If you have started a music track playing using :func:`music.play_once()`, you
can use the :func:`on_music_end() hook <on_music_end>` to do something when the
music ends - for example, to pick another track at random.


.. _clock:

Clock
-----

Often when writing a game, you will want to schedule some game event to occur
at a later time. For example, we may want a big boss alien to appear after 60
seconds. Or perhaps a power-up will appear every 20 seconds.

More subtle are the situations when you want to delay some action for a shorter
period. For example you might have a laser weapon that takes 1 second to charge
up.

We can use the ``clock`` object to schedule a function to happen in the
future.

Let's start by defining a function ``fire_laser`` that we want to run in the
future::

    def fire_laser():
        lasers.append(player.pos)

Then when the fire button is pressed, we will ask the ``clock`` to call it for
us after exactly 1 second::

    def on_mouse_down():
        clock.schedule(fire_laser, 1.0)

Note that ``fire_laser`` is the function itself; without parentheses, it is
not being called here! The clock will call it for us.

(It is a good habit to write out times in seconds with a decimal point, like
``1.0``. This makes it more obvious when you are reading it back, that you are
referring to a time value and not a count of things.)

``clock`` provides the following useful methods:

.. class:: Clock

    .. method:: schedule(callback, delay)

        Schedule `callback` to be called after the given delay.

        Repeated calls will schedule the callback repeatedly.

        :param callback: A callable that takes no arguments.
        :param delay: The delay, in seconds, before the function should be
                      called.

    .. method:: schedule_unique(callback, delay)

        Schedule `callback` to be called once after the given delay.

        If `callback` was already scheduled, cancel and reschedule it. This
        applies also if it was scheduled multiple times: after calling
        ``schedule_unique``, it will be scheduled exactly once.

        :param callback: A callable that takes no arguments.
        :param delay: The delay, in seconds, before the function should be
                      called.

    .. method:: schedule_interval(callback, interval)

        Schedule `callback` to be called repeatedly.

        :param callback: A callable that takes no arguments.
        :param interval: The interval in seconds between calls to `callback`.

    .. method:: unschedule(callback)

        Unschedule callback if it has been previously scheduled (either because
        it has been scheduled with ``schedule()`` and has not yet been called,
        or because it has been scheduled to repeat with
        ``schedule_interval()``.

    .. method:: clear()

        Unschedule everything that has been scheduled. This also stops any
        animations started with :func:`animate`.


Note that the Pygame Zero clock only holds weak references to each callback
you give it. It will not fire scheduled events if the objects and methods are
not referenced elsewhere. This can help prevent the clock keeping objects
alive and continuing to fire unexpectedly after they are otherwise dead.

The downside to the weak references is that you won't be able to schedule
lambdas or any other object that has been created purely to be scheduled. You
will have to keep a reference to the object.

.. _actor:

Actors
------

Once you have many images moving around in a game it can be convenient to have
something that holds in one place the image and where it is on screen. We'll
call each moving image on screen an ``Actor``. You can create an actor by supplying
at least an image name (from the images folder above). To draw the alien talked
about above::

    alien = Actor('alien', (50, 50))

    def draw():
        screen.clear()
        alien.draw()

You can move the actor around by setting its pos attribute in an update::

    def update():
        if keyboard.left:
            alien.x -= 1
        elif keyboard.right:
            alien.x += 1

And you may change the image used to draw the actor by setting its image
attribute to some new image name::

    alien.image = 'alien_hurt'

You can also give an actor a :ref:`Sprite <sprites>` instead of an image name,
to make it play an animation, or a Pygame ``Surface``.

Actors have all the same attributes and methods as :ref:`Rect <rect>`,
including methods like `.colliderect()`__ which can be used to test whether
two actors have collided. Collisions use the actor's
:ref:`collision rectangle <collision-rect>`, which is the whole image unless
you choose a smaller one.

.. __: https://www.pygame.org/docs/ref/rect.html#pygame.Rect.colliderect


Positioning Actors
''''''''''''''''''

If you assign a new value to one of the position attributes then the actor will
be moved. For example::

    alien.right = WIDTH

will position the alien so its right-hand side is set to ``WIDTH``.

Similarly, you can also set the initial position of the actor in the
constructor, by passing one of these as a keyword argument: ``pos``,
``topleft``, ``topright``, ``bottomleft``, ``bottomright``, ``midtop``,
``midleft``, ``midright``, ``midbottom`` or ``center``:

.. image:: _static/actor/anchor_points.png

This can be done during creation or by assigning a pair of x, y co-ordinates.
For example::

    WIDTH = 200
    HEIGHT = 200

    alien = Actor('alien', center=(100,100))

    def draw():
        screen.clear()
        alien.draw()

.. image:: _static/actor/alien_center.png

Changing ``center=(100, 100)`` to ``midbottom=(100, 200)`` gives you:

.. image:: _static/actor/alien_midbottom.png

If you don't specify an initial position, the actor will initially be
positioned in the top-left corner (equivalent to ``topleft=(0, 0)``).

.. tip::

    To stop an actor from leaving the screen, move it back inside after
    moving it, instead of checking each edge yourself::

        def update():
            if keyboard.left:
                player.x -= 5
            if keyboard.right:
                player.x += 5
            player.clamp_ip(screen.bounds())

.. _anchor:

Anchor point
''''''''''''

Actors have an "anchor position", which is a convenient way to position the
actor in the scene. By default, the anchor position is the center, so the
``.pos`` attribute refers to the center of the actor (and so do the ``x`` and
``y`` coordinates). It's common to want to set the anchor point to another
part of the sprite (perhaps the feet - so that you can easily set the Actor to
be "standing on" something)::

    alien = Actor('alien', anchor=('center', 'bottom'))
    spaceship = Actor('spaceship', anchor=(10, 50))

``anchor`` is specified as a tuple ``(xanchor, yanchor)``, where the values can
be floats or the strings ``left``, ``center``/``middle``, ``right``, ``top`` or
``bottom`` as appropriate.


.. _rotation:

Rotation
''''''''

.. versionadded:: 1.2

The ``.angle`` attribute of an Actor controls the rotation of the sprite, in
degrees, anticlockwise (counterclockwise).

The centre of rotation is the Actor's :ref:`anchor point <anchor>`.

Note that this will change the ``width`` and ``height`` of the Actor.

For example, to make an asteroid sprite spinning slowly anticlockwise in
space::

    asteroid = Actor('asteroid', center=(300, 300))

    def update():
        asteroid.angle += 1

To have it spin clockwise, we'd change ``update()`` to::

    def update():
        asteroid.angle -= 1

As a different example, we could make an actor ``ship`` always face the mouse
pointer. Because :meth:`~Actor.angle_to()` returns 0 for "right", the sprite we
use for "ship" should face right::

    ship = Actor('ship')

    def on_mouse_move(pos):
        ship.angle = ship.angle_to(pos)

.. image:: _static/rotation.svg
    :alt: Diagram showing how to set up sprites for rotation with angle_to()

Remember that angles loop round, so 0 degrees == 360 degrees == 720 degrees.
Likewise -180 degrees == 180 degrees.


Distance, angle and moving towards
''''''''''''''''''''''''''''''''''

.. versionadded:: 1.2

Actors have convenient methods for calculating their distance or angle to other
Actors or ``(x, y)`` coordinate pairs, and for moving towards them.

.. method:: Actor.move_towards(target, speed)

    Move this actor up to ``speed`` pixels in a straight line towards target.
    It stops on the target instead of going past it. Call it from
    ``update()`` to keep moving, for example to make an enemy chase the
    player::

        def update():
            enemy.move_towards(player, 2)

    A negative ``speed`` moves away from the target instead.

.. method:: Actor.distance_to(target)

    Return the distance from this actor's position to target, in pixels.


.. method:: Actor.angle_to(target)

    Return the angle from this actor's position to target, in degrees.

    This will return a number between -180 and 180 degrees. Right is 0 degrees
    and the angles increase going anticlockwise.

    Therefore:

    * Left is 180 degrees.
    * Up is 90 degrees.
    * Down is -90 degrees.


.. _transparency:

Transparency
''''''''''''

.. versionadded:: 1.3

In some cases it is useful to make an Actor object partially transparent. This
can be used to fade it in or out, or to indicate that it is "disabled".

The ``.opacity`` attribute of an Actor controls how transparent or opaque it
is.

* When an actor is not at all transparent, we say it is "opaque" and it has
  ``opacity`` of ``1.0``, and you can't see through it at all.
* When an actor is completely transparent, it has an ``opacity`` of ``0.0``.
  This will make it completely invisible.

To make an actor that is half-transparent (like a ghost), you could write::

    ghost = Actor('ghost')
    ghost.opacity = 0.5

This diagram shows the scale; the grey checkerboard is used to give the sense
of transparency:

.. image:: _static/opacity.svg
    :alt: The opacity scale in Pygame Zero.

.. tip::

    The order in which you draw overlapping transparent objects still matters.
    A ghost seen through a window looks slightly different to a window seen
    through a ghost.


.. _scaling:

Scaling
'''''''

The ``.scale`` attribute of an Actor makes it bigger or smaller. ``1.0`` is the
image's normal size, ``2.0`` is twice as big and ``0.5`` is half the size::

    boss = Actor('alien', center=(400, 300))
    boss.scale = 3

The actor stays at the same ``pos`` while it changes size. Its ``width``,
``height`` and collision rectangle change size too. A scale below ``0``
counts as ``0``; to mirror an actor, use :ref:`flipping <flipping>` instead.


.. _flipping:

Flipping
''''''''

Setting ``.flip_h`` to ``True`` mirrors an Actor's image from left to right,
and ``.flip_v`` flips it upside down. This saves drawing a second image for a
character that can face either way::

    def update():
        if keyboard.left:
            player.x -= 3
            player.flip_h = True
        elif keyboard.right:
            player.x += 3
            player.flip_h = False

``.flip_d`` flips the image along its diagonal, swapping its width and height.
This is the third kind of flip that `Tiled`_ uses for map tiles. Together with
``flip_h`` and ``flip_v`` it can turn a tile to face any of the four
directions.


.. _collision-rect:

Collision rectangle
'''''''''''''''''''

Many images have empty, transparent space around the character. By default,
an actor collides using its whole image, so two actors can "collide" when only
their empty space touches.

Give an actor a smaller ``collision_rect`` to fix this. It can be set when
the actor is created, or changed later:

* ``(width, height)`` - a rectangle of this size in the middle of the image.
* ``(width, height, offset_x, offset_y)`` - the same, but with its center moved
  ``offset_x`` pixels right and ``offset_y`` pixels down from the image's
  center.
* ``None`` - use the whole image again.

For example::

    # Only a 30x40 area, 10 pixels below the image's center, counts
    alien = Actor('alien', collision_rect=(30, 40, 0, 10))

The collision rectangle becomes the actor's rectangle: ``pos``, ``x``, ``y``,
``width``, ``height``, the anchor point and methods like ``colliderect()``
all use it. The image is still drawn in full around it. The collision
rectangle grows and shrinks with :ref:`scale <scaling>` and turns with
:ref:`flips <flipping>` and :ref:`rotation <rotation>`.

.. method:: Actor.draw_collision_rect()

    Draw the collision rectangle as a red outline. Call this in ``draw()``,
    after drawing the actor, to check that the rectangle is where you expect.


To animate an actor, give it a :ref:`Sprite <sprites>`.

.. _`Tiled`: https://www.mapeditor.org/


.. _sprites:

Sprite Animations
-----------------

A ``Sprite`` is one animation, such as walking or jumping: its frames, how
fast to play them, and whether to loop. Give an :ref:`Actor <actor>` a Sprite
instead of an image name, and the actor plays it, moving on to the next frame
by itself each time it is drawn.

The frames usually come from a sprite sheet: one image that contains every
frame, laid out in a grid. Each row holds one animation, with its frames side
by side and all the same size. Put sprite sheets in a ``sprites`` directory
next to your game::

    platformer.py
    sprites/hero.png

Then make a Sprite for each row you want to use::

    # hero.png has 48x48 frames. Row 0 has 4 standing frames and
    # row 1 has 6 walking frames.
    standing = Sprite('hero', frame_width=48, frame_height=48, row=0, frames=4, fps=6)
    walking = Sprite('hero', frame_width=48, frame_height=48, row=1, frames=6, fps=12)

    hero = Actor(standing, pos=(100, 300))

    def update():
        if keyboard.right:
            hero.x += 3
            hero.sprite = walking
        else:
            hero.sprite = standing

    def draw():
        screen.clear()
        hero.draw()

Instead of a sprite sheet, a Sprite can be made from a list of image names in
the ``images`` directory::

    flapping = Sprite(['bird1', 'bird2', 'bird3'], fps=8)

Many actors can share one Sprite. Each actor keeps track of its own frame, so
they don't all move in step::

    enemies = [Actor(walking, pos=(x, 300)) for x in range(100, 600, 100)]

An actor can switch between Sprites and still images. Setting ``image`` stops
the animation::

    hero.image = 'hero_hurt'

.. class:: Sprite(image_name, frame_width, frame_height, row=0, frames=None, fps=10, transparent_color=None, loop=True)

    One animation.

    :param image_name: The name of the sprite sheet in the ``sprites``
                       directory, without the file extension. Or a list of
                       image names in the ``images`` directory, in which case
                       leave out the next five parameters.
    :param frame_width: The width of each frame, in pixels.
    :param frame_height: The height of each frame, in pixels.
    :param row: Which row of the sheet to use. The top row is ``0``.
    :param frames: How many frames to take from the row, starting at the
                   left edge. Leave it out to use every frame that fits
                   across the sheet.
    :param fps: How many frames to show each second.
    :param transparent_color: A color to make see-through, for sheets that
                              have a background color instead of
                              transparency. ``-1`` uses the color of each
                              frame's top-left pixel.
    :param loop: If ``False``, the animation stops on its last frame instead
                 of starting again.

These Actor attributes and methods control the Sprite it is playing:

.. attribute:: Actor.sprite

    The Sprite being played, or ``None`` for a still image. Assigning a
    different Sprite switches animation and starts the new one from its first
    frame. Assigning the Sprite that is already playing does nothing, so it is
    safe to do every frame. Assigning ``None`` stops on the current frame.

.. attribute:: Actor.frame_index

    The number of the frame showing, starting from ``0``. Assign to it to jump
    to another frame.

.. attribute:: Actor.animation_finished

    ``True`` once a Sprite with ``loop=False`` has played to the end. For
    example, to remove an explosion once it has finished::

        def update():
            for boom in explosions[:]:
                if boom.animation_finished:
                    explosions.remove(boom)

.. method:: Actor.reset_animation()

    Play the Sprite again from its first frame.

.. method:: Actor.pause_animation()

    Stop on the current frame.

.. method:: Actor.resume_animation()

    Carry on animating after ``pause_animation()``.

.. attribute:: Actor.animation_paused

    ``True`` while the animation is paused.

While the whole game is paused with :meth:`game.pause() <Game.pause>`, every
actor holds its current frame, and carries on from it after ``game.resume()``.


.. _tile-maps:

Tile Maps
---------

`Tiled`_ is a free map editor for building game levels out of small square
tiles. Pygame Zero Plus can load maps saved by Tiled, so you can design a
level in Tiled and turn every tile into an :ref:`Actor <actor>`.

Save the map (``.tmx``), any external tilesets (``.tsx``) and the tileset
images together in a ``maps`` directory next to your game::

    adventure.py
    maps/level1.tmx
    maps/terrain.tsx
    maps/terrain.png

Tiled must save tile layers in CSV format, which is its default. Only tile
layers at the top level of the map are loaded: object layers, image layers and
layers inside a group are ignored.

.. function:: load_tile_map_actors(tmx_name, scale=1)

    Load a Tiled map from the ``maps`` directory. The extension is optional.

    Returns a dictionary from each tile layer's name to a list of the tiles
    in that layer. Empty cells are left out. Each tile is an Actor, so you
    can draw it, move it and check it for collisions.

    :param scale: Draw the map bigger or smaller. ``2`` makes every tile, and
                  the space between them, twice the size.

For example, with a map that has layers called ``ground`` and ``walls``::

    WIDTH = 640
    HEIGHT = 480

    layers = load_tile_map_actors('level1')
    ground = layers['ground']
    walls = layers['walls']

    player = Actor('player', pos=(100, 100))

    def update():
        old_pos = player.pos
        if keyboard.left:
            player.x -= 2
        if keyboard.right:
            player.x += 2
        if player.collidelist(walls) != -1:
            player.pos = old_pos  # Don't walk through walls

    def draw():
        screen.clear()
        for tile in ground + walls:
            tile.draw()
        player.draw()

Tiles that were flipped or rotated in Tiled keep those changes, using the
actor's :ref:`flip attributes <flipping>`. Each tile also knows where it came
from:

.. class:: Tile

    .. attribute:: map_col
                   map_row

        The tile's column and row in the map.

    .. attribute:: tile_col
                   tile_row

        The column and row of the tile's image in its tileset.

    .. attribute:: tile_gid

        The tile's number in Tiled. Use this to find every tile of one kind,
        such as all the coins.

    .. method:: set_map_position(map_col, map_row)

        Move the tile to another cell of the map.

    .. method:: set_tile_image(tile_col, tile_row)

        Change the tile to show another image from the same tileset.

    .. method:: copy(map_col=None, map_row=None)

        Return a new tile like this one, optionally in a different cell.


.. _game:

Game State
----------

The ``game`` object keeps track of things most games need, such as the score,
the level, and whether the player has won or lost. It saves you from writing
lots of ``global`` variables, and it can restart the game for you.

::

    def update():
        if game.state != 'playing':
            return

        if player.colliderect(coin):
            game.add_score(10)
        if player.colliderect(enemy):
            game.lose(restart_after=3)

    def draw():
        screen.clear()
        player.draw()
        screen.draw.text(f'Score: {game.score}', (10, 10))
        if game.state == 'lost':
            screen.draw.text('Game over!', center=(WIDTH / 2, HEIGHT / 2))

``game`` updates its ``timer`` and ``frame_count`` each frame by itself.
Everything else changes only when your code changes it. For example, pausing
the game doesn't stop ``update()`` being called, so check ``game.state`` in
``update()`` to decide what should still move.

You can store your own values on ``game`` too, such as ``game.lives = 3``.

.. class:: Game

    .. attribute:: state

        One of ``'playing'``, ``'paused'``, ``'won'``, ``'lost'`` or
        ``'over'``. It starts as ``'playing'``.

    .. attribute:: score

        Starts at ``0``.

    .. attribute:: level

        Starts at ``1``.

    .. attribute:: timer

        Seconds spent in the ``'playing'`` state. It doesn't count while the
        game is paused or over.

    .. attribute:: frame_count

        How many frames have run.

    .. attribute:: data

        An empty dictionary for anything else you want to keep track of.

    .. method:: add_score(points)

        Add ``points`` to the score.

    .. method:: next_level()

        Add 1 to the level.

    .. method:: pause()

        Change from ``'playing'`` to ``'paused'``.

    .. method:: resume()

        Change from ``'paused'`` back to ``'playing'``.

    .. method:: start()

        Change the state to ``'playing'``.

    .. method:: win(restart_after=None, clear_clock='immediate')
                lose(restart_after=None, clear_clock='immediate')
                over(restart_after=None, clear_clock='immediate')

        End the game, changing the state to ``'won'``, ``'lost'`` or
        ``'over'``. This does nothing unless the state is ``'playing'``, so it
        is safe to call every frame.

        :param restart_after: If given, restart the game after this many
                              seconds.
        :param clear_clock: When to cancel everything scheduled with
                            :ref:`clock <clock>`, so that timers from the
                            finished game don't keep firing: ``'immediate'``
                            (now), ``'on_restart'`` (when the game restarts)
                            or ``'never'``.

    .. method:: restart(delay=0, clear_clock='immediate')

        Start the game again, after ``delay`` seconds if given. This resets
        ``state``, ``score``, ``level``, ``timer``, ``frame_count`` and
        ``data``, then calls your :func:`start` function.

        ``clear_clock`` works the same as for ``win()``.

    .. method:: reset()

        Set ``state``, ``score``, ``level``, ``timer``, ``frame_count`` and
        ``data`` back to their starting values, without calling ``start()``.

.. tip::

    ``restart()`` only resets the values above. Set up everything else, such
    as your own variables, actor positions and ``game.lives``, in a
    :func:`start` function, so that it is set up again on every restart::

        def start():
            global coins
            coins = []
            game.lives = 3
            player.pos = (100, 100)

When you call ``restart()`` or ``win()`` with a delay, call it from inside a
function such as ``update()``. The game must already be running for the delay
to work.


Quitting the Game
-----------------

.. function:: exit()

    Close the game window and stop the game. Any sounds that are still
    playing get up to a second to finish first::

        def on_key_down(key):
            if key == keys.ESCAPE:
                exit()

Players can also quit with Ctrl+Q (⌘+Q on a Mac), or by closing the window.


The Keyboard
------------

You probably noticed that we used the ``keyboard`` in the above code.
If you'd like to know what keys are pressed on the keyboard, you can query the
attributes of the ``keyboard`` builtin. If, say, the left arrow is held down,
then ``keyboard.left`` will be ``True``, otherwise it will be ``False``.

There are attributes for every key; some examples::

    keyboard.a  # The 'A' key
    keyboard.left  # The left arrow key
    keyboard.rshift  # The right shift key
    keyboard.kp0  # The '0' key on the keypad
    keyboard.k_0  # The main '0' key

The full set of key constants is given in the `Buttons and Keys`_
documentation, but the attributes are lowercase, because these are variables
not constants.

Uppercase and prefixed attribute names (eg. ``keyboard.LEFT`` or
``keyboard.K_a``) also work, but lowercase names are recommended.

.. _`Buttons and Keys`: hooks.html#buttons-and-keys

.. versionadded:: 1.1

    You can now also query the state of the keys using the keyboard constants
    themselves::

        keyboard[keys.A]  # True if the 'A' key is pressed
        keyboard[keys.SPACE]  # True if the space bar is pressed


Animations
----------

You can animate most things in pygame using the builtin ``animate()``. For
example, to move an :ref:`Actor <actor>` from its current position on the
screen to the position ``(100, 100)``::

    animate(alien, pos=(100, 100))

.. function:: animate(object, tween='linear', duration=1, on_finished=None, **targets)

    Animate the attributes on object from their current value to that
    specified in the targets keywords.

    :param tween: The type of *tweening* to use.
    :param duration: The duration of the animation, in seconds.
    :param on_finished: Function called when the animation finishes.
    :param targets: The target values for the attributes to animate.

The tween argument can be one of the following:

+--------------------+------------------------------------------------------+----------------------------------------+
| 'linear'           | Animate at a constant speed from start to finish     | .. image:: images/linear.png           |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'accelerate'       | Start slower and accelerate to finish                | .. image:: images/accelerate.png       |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'decelerate'       | Start fast and decelerate to finish                  | .. image:: images/decelerate.png       |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'accel_decel'      | Accelerate to mid point and decelerate to finish     | .. image:: images/accel_decel.png      |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'in_elastic'       | Give a little wobble at the end                      | .. image:: images/in_elastic.png       |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'out_elastic'      | Have a little wobble at the start                    | .. image:: images/out_elastic.png      |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'in_out_elastic'   | Have a wobble at both ends                           | .. image:: images/in_out_elastic.png   |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'bounce_end'       | Accelerate to the finish and bounce there            | .. image:: images/bounce_end.png       |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'bounce_start'     | Bounce at the start                                  | .. image:: images/bounce_start.png     |
+--------------------+------------------------------------------------------+----------------------------------------+
| 'bounce_start_end' | Bounce at both ends                                  | .. image:: images/bounce_start_end.png |
+--------------------+------------------------------------------------------+----------------------------------------+

The ``animate()`` function returns an ``Animation`` instance:

.. class:: Animation

    .. method:: stop(complete=False)

        Stop the animation, optionally completing the transition to the final
        property values.

        :param complete: Set the animated attribute to the target value.

    .. attribute:: running

        This will be True if the animation is running. It will be False
        when the duration has run or the ``stop()`` method was called before
        then.

    .. attribute:: on_finished

        You may set this attribute to a function which will be called
        when the animation duration runs out. The ``on_finished`` argument
        to ``animate()`` also sets this attribute. It is not called when
        ``stop()`` is called. This function takes no arguments.


Tone Generator
--------------

.. versionadded:: 1.2

Pygame Zero can play tones using a built-in synthesizer.

.. function:: tone.play(pitch, duration, waveform='sin', volume=0.8)

    Play a note at the given pitch for the given duration.

    Duration is in seconds, up to a maximum of 4 seconds.

    The `waveform` changes the sound of the note. It can be ``'sin'`` (a pure,
    soft tone), ``'square'``, ``'saw'`` or ``'triangle'``. `volume` is from 0
    (silent) to 1 (loudest).

    The `pitch` can be specified as a number in which case it is the frequency
    of the note in hertz.

    Alternatively, the pitch can be specified as a string representing a note
    name and octave. For example:

    * ``'E4'`` would be E in octave 4.
    * ``'A#5'`` would be A-sharp in octave 5.
    * ``'Bb3'`` would be B-flat in octave 3.

Creating notes, particularly long notes, takes time - up to several
milliseconds. You can create your notes ahead of time so that this doesn't slow
your game down while it is running:

.. function:: tone.create(pitch, duration, waveform='sin', volume=0.8)

    Create and return a Sound object.

    The arguments are as for play(), above.

This could be used in a Pygame Zero program like this::

    beep = tone.create('A3', 0.5)

    def on_mouse_down():
        beep.play()


.. _data-storage:

Data Storage
------------

The ``storage`` object behaves just like a Python dictionary but its contents
are preserved across game sessions. The values you assign to storage will be
saved as JSON_, which means you can only store certain types of objects in it:
``list``/``tuple``, ``dict``, ``str``, ``float``/``int``, ``bool``, and
``None``.

.. _JSON: https://en.wikipedia.org/wiki/JSON

The ``storage`` for a game is initially empty. Your code will need to handle
the case that values are loaded as well as the case that no values are found.

A tip is to use ``setdefault()``, which inserts a default if there is no value
for the key, but does nothing if there is.

For example, we could write::

    storage.setdefault('highscore', 0)

After this line is executed, ``storage['highscore']`` will contain a value -
``0`` if there was no value loaded, or the loaded value otherwise. You could
add all of your ``setdefault`` lines towards the top of your game, before
anything else looks at ``storage``::

    storage.setdefault('level', 1)
    storage.setdefault('player_name', 'Anonymous')
    storage.setdefault('inventory', [])

Now, during gameplay we can update some values::

    if player.colliderect(mushroom):
        score += 5
        if score > storage['highscore']:
            storage['highscore'] = score

You can read them back at any time::

    def draw():
        ...
        screen.draw.text('Highscore: ' + storage['highscore'], ...)

...and of course, they'll be preserved when the game next launches.

These are some of the most useful methods of ``storage``:

.. class:: Storage(dict)

    .. method:: storage[key] = value

        Set a value in the storage.

    .. method:: storage[key]

        Get a value from the storage. Raise KeyError if there is no such key
        in the storage.

    .. method:: setdefault(key, default)

        Insert a default value into the storage, only if no value already
        exists for this key.

    .. method:: get(key, default=None)

        Get a value from the storage. If there is no such key, return default,
        or None if no default was given.

    .. method:: clear()

        Remove all stored values. Use this if you get into a bad state.

    .. method:: save()

        Saves the data to disk now. You don't usually need to call this, unless
        you're planning on using ``load()`` to reload a checkpoint, for
        example.

    .. method:: load()

        Reload the contents of the storage with data from the save file. This
        will replace any existing data in the storage.

    .. attribute:: path

        The actual path to which the save data will be written.


.. caution::

    As you make changes to your game, ``storage`` could contain values that
    don't work with your current code. You can either check for this, or call
    ``.clear()`` to remove all old values, or delete the save game file.


.. tip::

    Remember to check that your game still works if the storage is empty!
