"""Tests for the beginner-friendly ``game`` state object and its hooks into
the game loop (``start()``, ``game.tick()`` and ``game.restart()``).

"""
import builtins
import io
import types
import unittest
from unittest import mock

import pygame

from pgzero import constants
from pgzero.clock import Clock
from pgzero.game import Game, PGZeroGame


class GameDefaultsTest(unittest.TestCase):
    def test_defaults(self):
        g = Game()
        self.assertEqual(g.state, "playing")
        self.assertEqual(g.score, 0)
        self.assertEqual(g.level, 1)
        self.assertEqual(g.timer, 0)
        self.assertEqual(g.frame_count, 0)
        self.assertFalse(hasattr(g, "data"))

    def test_reset(self):
        g = Game()
        g.state = "lost"
        g.score = 100
        g.level = 5
        g.timer = 12.5
        g.frame_count = 99
        g.reset()
        self.assertEqual(
            (g.state, g.score, g.level, g.timer, g.frame_count),
            ("playing", 0, 1, 0, 0),
        )

    def test_reset_keeps_custom_attributes(self):
        """Values like game.lives belong to the game's own start() function."""
        g = Game()
        g.lives = 3
        g.reset()
        self.assertEqual(g.lives, 3)

    def test_custom_attributes(self):
        g = Game()
        g.lives = 3
        self.assertEqual(g.lives, 3)

    def test_attribute_hooks_are_type_hinted(self):
        """__getattr__/__setattr__ exist so linters allow custom attributes;
        they must keep their ``Any`` hints (see the comment in game.py)."""
        from typing import Any, get_type_hints
        self.assertIs(get_type_hints(Game.__getattr__)["return"], Any)
        self.assertIs(get_type_hints(Game.__setattr__)["value"], Any)

    def test_unknown_attribute(self):
        g = Game()
        with self.assertRaisesRegex(AttributeError, "no attribute 'lives'"):
            g.lives

    def test_add_score(self):
        g = Game()
        g.add_score(10)
        g.add_score(5)
        self.assertEqual(g.score, 15)

    def test_next_level(self):
        g = Game()
        g.next_level()
        g.next_level()
        self.assertEqual(g.level, 3)


class GameStateTransitionTest(unittest.TestCase):
    def test_pause_and_resume(self):
        g = Game()
        g.pause()
        self.assertEqual(g.state, "paused")
        g.resume()
        self.assertEqual(g.state, "playing")

    def test_pause_only_when_playing(self):
        g = Game()
        g.state = "lost"
        g.pause()
        self.assertEqual(g.state, "lost")

    def test_resume_only_when_paused(self):
        g = Game()
        g.state = "won"
        g.resume()
        self.assertEqual(g.state, "won")

    def test_no_start_method(self):
        """game.start() was removed: start() is the game's own function."""
        self.assertFalse(hasattr(Game(), "start"))

    def test_win_lose_over(self):
        for method, state in [("win", "won"), ("lose", "lost"),
                              ("over", "over")]:
            with self.subTest(method=method):
                g = Game()
                getattr(g, method)()
                self.assertEqual(g.state, state)

    def test_cannot_end_twice(self):
        """Once the game has ended, a second win/lose call is ignored."""
        for first, second in [("lose", "win"), ("win", "over"),
                              ("over", "lose")]:
            with self.subTest(first=first, second=second):
                g = Game()
                getattr(g, first)()
                ended = g.state
                getattr(g, second)()
                self.assertEqual(g.state, ended)

    def test_can_end_while_paused(self):
        """e.g. choosing "quit" from a pause menu."""
        g = Game()
        g.pause()
        g.over()
        self.assertEqual(g.state, "over")

    def test_can_end_from_custom_state(self):
        """e.g. a "dying" state that plays an animation before losing."""
        g = Game()
        g.state = "dying"
        g.lose()
        self.assertEqual(g.state, "lost")

    def test_can_end_again_after_restart(self):
        g = Game()
        g.lose()
        g.restart()
        g.win()
        self.assertEqual(g.state, "won")


class GameTickTest(unittest.TestCase):
    def test_tick_counts_frames_and_time(self):
        g = Game()
        g.tick(0.5)
        g.tick(0.25)
        self.assertEqual(g.frame_count, 2)
        self.assertAlmostEqual(g.timer, 0.75)

    def test_timer_only_runs_while_playing(self):
        g = Game()
        g.tick(1.0)
        g.pause()
        g.tick(1.0)
        self.assertEqual(g.frame_count, 2)
        self.assertAlmostEqual(g.timer, 1.0)


class GameRestartTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.start = mock.Mock()
        self.game = Game()
        self.game._bind_engine(start_callback=self.start, clock=self.clock)
        self.other_event = mock.Mock()

    def schedule_other(self):
        self.clock.schedule(self.other_event, 5.0)

    def test_restart_resets_and_calls_start(self):
        g = self.game
        g.score = 50
        g.lose()
        g.restart()
        self.assertEqual(g.state, "playing")
        self.assertEqual(g.score, 0)
        self.start.assert_called_once_with()

    def test_restart_without_engine(self):
        """An unbound game (e.g. in a unit test) can still restart."""
        g = Game()
        g.score = 10
        g.restart()
        self.assertEqual(g.score, 0)

    def test_restart_with_delay_without_engine_raises(self):
        """A delay needs the game clock, e.g. not at the top level of a file."""
        g = Game()
        g.score = 10
        with self.assertRaisesRegex(RuntimeError, "inside a function"):
            g.restart(delay=1)
        self.assertEqual(g.score, 10)

    def test_end_with_restart_after_without_engine_raises(self):
        for method in ("win", "lose", "over"):
            with self.subTest(method=method):
                g = Game()
                with self.assertRaisesRegex(RuntimeError, "inside a function"):
                    getattr(g, method)(restart_after=2)
                # The error is raised before anything changes.
                self.assertEqual(g.state, "playing")

    def test_zero_delay_without_engine_restarts_now(self):
        g = Game()
        g.score = 10
        g.restart(delay=0)
        g.lose(restart_after=0)
        self.assertEqual(g.state, "playing")
        self.assertEqual(g.score, 0)

    def test_end_without_restart_without_engine(self):
        g = Game()
        g.lose()
        self.assertEqual(g.state, "lost")

    def test_start_callback_not_callable(self):
        g = Game()
        g._bind_engine(start_callback=None, clock=self.clock)
        g.restart()  # must not raise
        self.assertEqual(g.state, "playing")

    def test_restart_clears_clock_immediately_by_default(self):
        self.schedule_other()
        self.game.restart()
        self.assertEqual(self.clock.events, [])

    def test_restart_never_clear(self):
        self.schedule_other()
        self.game.restart(clear_clock="never")
        self.clock.tick(5.0)
        self.other_event.assert_called_once_with()

    def test_restart_invalid_clear_mode(self):
        with self.assertRaisesRegex(ValueError, "clear_clock"):
            self.game.restart(clear_clock="sometimes")

    def test_delayed_restart(self):
        g = self.game
        g.score = 10
        g.restart(delay=2.0)
        self.assertEqual(g.score, 10)
        self.start.assert_not_called()

        self.clock.tick(1.9)
        self.start.assert_not_called()
        self.clock.tick(0.2)
        self.assertEqual(g.score, 0)
        self.start.assert_called_once_with()

    def test_delayed_restart_immediate_clears_now(self):
        self.schedule_other()
        self.game.restart(delay=1.0)
        self.clock.tick(10)
        self.other_event.assert_not_called()
        self.start.assert_called_once_with()

    def test_delayed_restart_on_restart_clears_later(self):
        """With on_restart, other events keep running until the restart."""
        self.clock.schedule(self.other_event, 0.5)
        late_event = mock.Mock()
        self.clock.schedule(late_event, 3.0)

        self.game.restart(delay=1.0, clear_clock="on_restart")
        self.clock.tick(0.6)
        self.other_event.assert_called_once_with()

        self.clock.tick(0.5)
        self.start.assert_called_once_with()
        self.clock.tick(5)
        late_event.assert_not_called()

    def test_delayed_restart_never_clears(self):
        late_event = mock.Mock()
        self.clock.schedule(late_event, 3.0)
        self.game.restart(delay=1.0, clear_clock="never")
        self.clock.tick(1.1)
        self.start.assert_called_once_with()
        self.clock.tick(2.0)
        late_event.assert_called_once_with()

    def test_second_restart_replaces_pending_restart(self):
        self.game.restart(delay=1.0, clear_clock="never")
        self.game.restart(delay=3.0, clear_clock="never")
        self.clock.tick(2.0)
        self.start.assert_not_called()
        self.clock.tick(1.1)
        self.start.assert_called_once_with()

    def test_restart_inside_start_raises(self):
        g = self.game

        def start():
            g.restart()

        g._bind_engine(start_callback=start, clock=self.clock)
        with self.assertRaisesRegex(RuntimeError, "inside start"):
            g.restart()
        # The flag must be cleared even though start() raised.
        self.assertFalse(g._is_restarting)

    def test_start_callback_may_set_up_state(self):
        g = self.game

        def start():
            g.lives = 3
            g.score = 7

        g._bind_engine(start_callback=start, clock=self.clock)
        g.restart()
        self.assertEqual(g.lives, 3)
        self.assertEqual(g.score, 7)


class GameEndWithRestartTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.start = mock.Mock()
        self.game = Game()
        self.game._bind_engine(start_callback=self.start, clock=self.clock)
        self.other_event = mock.Mock()
        self.clock.schedule(self.other_event, 0.5)

    def test_end_clears_clock_by_default(self):
        self.game.lose()
        self.clock.tick(1)
        self.other_event.assert_not_called()

    def test_end_never_clear(self):
        self.game.win(clear_clock="never")
        self.clock.tick(1)
        self.other_event.assert_called_once_with()

    def test_end_without_restart_does_not_restart(self):
        self.game.over()
        self.clock.tick(100)
        self.start.assert_not_called()
        self.assertEqual(self.game.state, "over")

    def test_end_with_restart_after(self):
        g = self.game
        g.score = 30
        g.lose(restart_after=2.0)
        self.assertEqual(g.state, "lost")
        self.clock.tick(1.0)
        self.assertEqual(g.state, "lost")
        self.clock.tick(1.1)
        self.assertEqual(g.state, "playing")
        self.assertEqual(g.score, 0)
        self.start.assert_called_once_with()

    def test_end_with_restart_after_zero_restarts_now(self):
        self.game.win(restart_after=0)
        self.assertEqual(self.game.state, "playing")
        self.start.assert_called_once_with()

    def test_end_immediate_clear_does_not_cancel_its_own_restart(self):
        self.game.over(restart_after=1.0, clear_clock="immediate")
        self.other_event.assert_not_called()
        self.clock.tick(1.1)
        self.other_event.assert_not_called()
        self.start.assert_called_once_with()

    def test_end_on_restart_clear(self):
        self.game.lose(restart_after=1.0, clear_clock="on_restart")
        self.clock.tick(0.6)
        self.other_event.assert_called_once_with()
        self.clock.tick(0.5)
        self.start.assert_called_once_with()

    def test_restart_after_is_ignored_when_already_ended(self):
        g = self.game
        g.lose()
        g.win(restart_after=1.0)
        self.clock.tick(2)
        self.start.assert_not_called()
        self.assertEqual(g.state, "lost")


class PauseFreezesClockTest(unittest.TestCase):
    """While the game is paused, clock timers and animate() wait."""

    def setUp(self):
        self.game_obj = Game()
        mod = types.ModuleType("fake_game")
        mod.game = self.game_obj
        self.pgz = PGZeroGame(mod)
        patcher = mock.patch("pygame.event.get", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)
        self.clock = Clock()
        patcher = mock.patch("pgzero.clock.clock", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.fired = []
        self.clock.schedule(self.fire, 1.0)

    def fire(self):
        self.fired.append(True)

    def test_timer_fires_while_playing(self):
        self.pgz.handle_events(1.5, None)
        self.assertEqual(self.fired, [True])

    def test_timer_waits_while_paused(self):
        self.game_obj.pause()
        self.pgz.handle_events(1.5, None)
        self.assertEqual(self.fired, [])

    def test_timer_carries_on_after_resume(self):
        self.pgz.handle_events(0.6, None)
        self.game_obj.pause()
        self.pgz.handle_events(5.0, None)  # paused for a long time
        self.game_obj.resume()
        self.pgz.handle_events(0.3, None)
        self.assertEqual(self.fired, [])  # 0.9 seconds of play so far
        self.pgz.handle_events(0.2, None)
        self.assertEqual(self.fired, [True])

    def test_timer_runs_after_the_game_ends(self):
        """Only pausing stops the clock: e.g. lose(restart_after=3) still works."""
        self.game_obj.lose(clear_clock="never")
        self.pgz.handle_events(1.5, None)
        self.assertEqual(self.fired, [True])


class PGZeroGameHooksTest(unittest.TestCase):
    """Tests for how the game loop discovers start() and ticks ``game``."""

    def make(self, **attrs):
        mod = types.ModuleType("fake_game")
        for k, v in attrs.items():
            setattr(mod, k, v)
        return PGZeroGame(mod)

    def test_get_start_func_missing(self):
        self.assertIsNone(self.make().get_start_func())

    def test_get_start_func(self):
        def start():
            pass

        self.assertIs(self.make(start=start).get_start_func(), start)

    def test_start_variable_that_is_not_a_function_is_ignored(self):
        """A Pygame Zero game may use start for something else, like a position."""
        self.assertIsNone(self.make(start=(100, 200)).get_start_func())

    def test_start_function_with_parameters_is_not_called(self):
        """A game's own start(level) helper must not be called with nothing."""
        def start(level):
            pass

        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertIsNone(self.make(start=start).get_start_func())
        self.assertIn("start() needs an argument (level)", err.getvalue())

    def test_start_function_with_default_parameters_is_called(self):
        def start(level=1):
            pass

        self.assertIs(self.make(start=start).get_start_func(), start)

    def test_tick_game_state_uses_module_game(self):
        g = Game()
        pgz = self.make(game=g)
        self.assertTrue(pgz.tick_game_state(0.1))
        self.assertEqual(g.frame_count, 1)

    def test_tick_game_state_falls_back_to_builtins(self):
        g = Game()
        with mock.patch.object(builtins, "game", g, create=True):
            self.assertTrue(self.make().tick_game_state(0.1))
        self.assertEqual(g.frame_count, 1)

    def test_tick_game_state_prefers_module_game(self):
        mod_game = Game()
        builtin_game = Game()
        with mock.patch.object(builtins, "game", builtin_game, create=True):
            self.make(game=mod_game).tick_game_state(0.1)
        self.assertEqual(mod_game.frame_count, 1)
        self.assertEqual(builtin_game.frame_count, 0)

    def test_tick_game_state_without_game(self):
        with mock.patch.object(builtins, "game", None, create=True):
            self.assertFalse(self.make().tick_game_state(0.1))

    def test_tick_game_state_with_user_variable_named_game(self):
        """A user variable called ``game`` with no tick() is left alone."""
        with mock.patch.object(builtins, "game", None, create=True):
            self.assertFalse(self.make(game="pong").tick_game_state(0.1))

    def test_user_object_named_game_with_tick_is_left_alone(self):
        """A Pygame Zero game may have its own game object with a tick()."""
        class MyGame:
            ticks = 0

            def tick(self):
                self.ticks += 1

        mine = MyGame()
        builtin_game = Game()
        with mock.patch.object(builtins, "game", builtin_game, create=True):
            self.assertTrue(self.make(game=mine).tick_game_state(0.1))
        self.assertEqual(mine.ticks, 0)
        self.assertEqual(builtin_game.frame_count, 1)

    def test_handle_events_ticks_game(self):
        g = Game()
        pgz = self.make(game=g)
        pgz.handlers = {}
        with mock.patch("pygame.event.get", return_value=[]):
            updated = pgz.handle_events(0.25, None)
        self.assertTrue(updated)
        self.assertEqual(g.frame_count, 1)
        self.assertAlmostEqual(g.timer, 0.25)

    def test_handle_events_music_end_bookkeeping(self):
        """MUSIC_END events update music state before user handlers run."""
        from pgzero import music

        seen = []
        pgz = self.make()
        pgz.handlers = {
            constants.MUSIC_END: lambda e: seen.append(music._current_track)
        }
        event = pygame.event.Event(constants.MUSIC_END)
        with mock.patch.object(music, "_current_track", "intro"), \
                mock.patch.object(music, "_queued_track", "level1"), \
                mock.patch("pygame.event.get", return_value=[event]), \
                mock.patch.object(builtins, "game", None, create=True):
            pgz.handle_events(0.0, None)
        self.assertEqual(seen, ["level1"])


if __name__ == "__main__":
    unittest.main()
