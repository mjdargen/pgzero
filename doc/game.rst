The game object, start() and exit()
===================================

Nearly every game needs a score, a current level, and a way to tell whether
the player is still playing, has won or has lost. ``pgzero-mjd`` gives you a
ready-made object called ``game`` for this, a :func:`start` hook that runs
when the game begins and again every time it restarts, and an :func:`exit`
function that quits cleanly.

A complete example
------------------

Collect five coins to win; touch the bomb and you lose. Either way the game
restarts itself five seconds later by calling ``start()`` again.

::

    import pgzrun
    from pgzero.builtins import *
    import random

    WIDTH = 500
    HEIGHT = 500
    TITLE = "Coins and Bombs"

    robot = Actor("alien_beige")
    coin = Actor("coin_gold")
    bomb = Actor("bomb")


    def start():
        # runs once before the first frame, and again after every restart
        robot.pos = (WIDTH / 2, HEIGHT / 2)
        robot.speed = 5
        move(bomb)
        move(coin)


    def move(thing):
        thing.x = random.randint(20, WIDTH - 20)
        thing.y = random.randint(20, HEIGHT - 20)
        if thing.colliderect(robot):
            move(thing)


    def draw():
        screen.clear()
        screen.fill("darkslategray")
        coin.draw()
        bomb.draw()
        if game.state != "lost":
            robot.draw()
        screen.draw.text(f"Score: {game.score}", midleft=(20, 20))
        screen.draw.text(f"Time: {game.timer:.0f}", midright=(WIDTH - 20, 20))
        if game.state == "lost":
            screen.draw.text("Game over!", center=(WIDTH / 2, HEIGHT / 2), fontsize=50)
        elif game.state == "won":
            screen.draw.text("You won!", center=(WIDTH / 2, HEIGHT / 2), fontsize=50)


    def update():
        if game.state != "playing":
            return
        if keyboard.left and robot.left > 0:
            robot.x -= robot.speed
        elif keyboard.right and robot.right < WIDTH:
            robot.x += robot.speed
        elif keyboard.up and robot.top > 0:
            robot.y -= robot.speed
        elif keyboard.down and robot.bottom < HEIGHT:
            robot.y += robot.speed

        if robot.colliderect(coin):
            game.add_score(1)
            move(coin)
            if game.score >= 5:
                game.win(5.0)
        if robot.colliderect(bomb):
            game.lose(5.0)


    pgzrun.go()

Things to notice:

* Everything that must be fresh for a new game is set in ``start()``, not
  at the top of the file. The top of the file runs once; ``start()`` runs
  on every restart.
* ``game.win(5.0)`` sets the state to ``"won"`` straight away and restarts
  the game five seconds later. In between, ``update()`` returns early
  because the state is no longer ``"playing"``, while ``draw()`` keeps
  showing the message.
* ``game.score`` and ``game.timer`` are reset to zero on restart without any
  code from you.

The start() hook
----------------

If your file defines a function called :func:`start`, Pygame Zero calls it
once after the file has loaded and before the first ``draw()``, and again
every time the game restarts through :meth:`Game.restart`, including the
automatic restarts after :meth:`Game.win`, :meth:`Game.lose` and
:meth:`Game.over`.

Put *everything that has to be reset for a new game* in ``start()``: actor
positions and velocities, lists of enemies and projectiles, scheduled clock
events, the music. ``start()`` takes no arguments and must not call
``game.restart()``: the library raises ``RuntimeError`` if it does, because
that would restart forever.

The game object
---------------

``game`` is an instance of :class:`Game` that the engine looks after. It
calls :meth:`Game.tick` every frame, and it connects ``game.restart()`` to
your ``start()`` function and to the clock. You can create more ``Game()``
objects of your own if you want one per player, but only the builtin
``game`` is ticked and restarted automatically.

.. class:: Game

    .. attribute:: state

        One of ``"playing"``, ``"paused"``, ``"won"``, ``"lost"`` or
        ``"over"``. Starts as ``"playing"``. Check it in ``draw()`` and
        ``update()``; usually ``update()`` returns early unless the state is
        ``"playing"``.

    .. attribute:: score

        Starts at ``0``. Change it directly (``game.score += 1``) or with
        :meth:`add_score`.

    .. attribute:: level

        Starts at ``1``. Change it directly or with :meth:`next_level`.

    .. attribute:: timer

        Seconds spent in the ``"playing"`` state since the last reset, as a
        float. It stops counting while the game is paused, won, lost or over.

    .. attribute:: frame_count

        Number of frames since the last reset, counted in every state.

    .. attribute:: data

        An empty dictionary for anything else you want to keep
        (``game.data["lives"] = 3``). You can also simply add attributes to
        the object (``game.lives = 3``). The difference is that ``data`` is
        emptied by :meth:`reset` and your own attributes are not.

    .. method:: reset()

        Put ``state``, ``score``, ``level``, ``timer``, ``frame_count`` and
        ``data`` back to their starting values. Does not call ``start()`` and
        does not touch the clock; you usually want :meth:`restart` instead.

    .. method:: restart(delay=0.0, clear_clock="immediate")

        Start a new game: :meth:`reset` the counters and call your
        ``start()`` function.

        :param delay: Seconds to wait before restarting. ``0`` restarts right
            now. A restart that was already scheduled is cancelled first, so
            calling ``restart(3.0)`` twice restarts once.
        :param clear_clock: What to do with functions scheduled on the
            ``clock`` with ``schedule()``, ``schedule_interval()`` and
            friends:

            * ``"immediate"`` (default): cancel them all now, before the
              delay. Any ``schedule_interval`` your game relies on must be
              scheduled again in ``start()``.
            * ``"on_restart"``: leave them running during the delay and
              cancel them at the moment of the restart.
            * ``"never"``: leave them alone.

        Raises ``ValueError`` for any other ``clear_clock`` value, and
        ``RuntimeError`` when called from inside ``start()``.

    .. method:: win(restart_after=None, clear_clock="immediate")
                lose(restart_after=None, clear_clock="immediate")
                over(restart_after=None, clear_clock="immediate")

        End the game with ``state`` set to ``"won"``, ``"lost"`` or
        ``"over"``. They only act while the state is ``"playing"``: a second
        call, or a ``lose()`` after a ``win()``, is ignored, so the first
        outcome sticks.

        :param restart_after: If given, seconds until the game restarts
            itself; ``game.lose(5.0)`` shows your game-over screen for five
            seconds. ``None`` (default) leaves the game in the ended state
            until you call :meth:`restart` or :meth:`start` yourself. ``0``
            restarts immediately.
        :param clear_clock: ``"immediate"`` (default) cancels every
            scheduled clock function now, so timers and spawners stop when
            the game ends. ``"on_restart"`` and ``"never"`` behave as for
            :meth:`restart`.

    .. method:: start()

        Set ``state`` to ``"playing"`` from any state, without resetting
        anything. Use it to leave a menu or ended state by hand. This is a
        method of the object; it is unrelated to the :func:`start` hook,
        which is a function in your file.

    .. method:: pause()

        Set ``state`` to ``"paused"``, but only if it is ``"playing"``.

    .. method:: resume()

        Set ``state`` back to ``"playing"``, but only if it is ``"paused"``.

    .. method:: next_level()

        Add 1 to ``level``.

    .. method:: add_score(points)

        Add ``points`` to ``score``.

    .. method:: tick(dt)

        Called by the engine every frame with the time since the previous
        frame in seconds. Adds 1 to ``frame_count`` and, while playing,
        ``dt`` to ``timer``. You do not call this yourself.

Pausing
'''''''

A pause key is two lines, because ``pause()`` and ``resume()`` only act in
the right state::

    def on_key_down(key):
        if key == keys.P:
            if game.state == "playing":
                game.pause()
            else:
                game.resume()

Remember to make ``update()`` return early while paused and to draw a
"Paused" message.

Gotchas
'''''''

* ``win()``, ``lose()``, ``over()`` and ``restart()`` clear the clock by
  default. If a ``schedule_interval`` callback has to survive the end of a
  game, pass ``clear_clock="never"`` or schedule it again in ``start()``.
* ``restart()`` resets the ``game`` counters and calls ``start()``. It does
  not reset your actors or your own global variables; ``start()`` has to.
* ``state`` is just a string. ``game.state = "menu"`` works, but then
  ``win()``, ``lose()``, ``over()`` and ``pause()`` do nothing until the
  state is ``"playing"`` again (``game.start()`` does that).
* Do not create a variable of your own called ``game``; it would hide the
  builtin.

exit()
------

.. function:: exit()

    Quit the game. Waits up to one second for any sounds still playing to
    finish, then ends the program. Use it for a quit key or button::

        def on_key_down(key):
            if key == keys.ESCAPE:
                exit()

    This version of ``exit`` comes from the ``from pgzero.builtins import *``
    line at the top of your file. Without that line, ``exit()`` is Python's
    own, which quits immediately and cuts sounds off. Ctrl-Q (Cmd-Q on a
    Mac) always quits as well.

Music: knowing what is playing
------------------------------

The ``music`` object (see :ref:`music`) now remembers which track it is
playing, so you can ask before starting a track again.

.. function:: music.is_playing(name=None)
    :noindex:

    With no argument, ``True`` if any music is playing and not paused, as
    before. With a track name, ``True`` only if *that* track is the one
    playing::

        if not music.is_playing("boss_theme"):
            music.play("boss_theme")

    The current track is set by ``play()`` and ``play_once()``; it moves on
    to the queued track when ``queue()`` was used and the first track ends;
    and it is forgotten by ``stop()``, ``fadeout()``, and when a track ends
    with nothing queued.

.. function:: music.is_paused()
    :noindex:

    ``True`` between ``music.pause()`` and ``music.unpause()``.

``music.pause()`` now does nothing when no music is playing, and
``music.unpause()`` does nothing unless the music really is paused, so both
are safe to call from a pause menu without checking first.
