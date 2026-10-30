"""Tests for Pygame Zero's runner system.

This module is also a Pygame Zero game so that we can run it with pgzero.

"""
import sys
import unittest
from pathlib import Path

from pgzero.runner import load_and_run
from pgzero import clock

game_tests = Path(__file__).parent / 'game_tests'


class RunnerTest(unittest.TestCase):
    """Test that we can load and run the current file."""

    def assert_runnable(self, path: Path):
        """Check that we can run the given file."""
        clock.schedule_unique(sys.exit, 0.05)
        with self.assertRaises(SystemExit):
            load_and_run(str(path))

    def test_run_utf8(self):
        """We can load and run a game saved as UTF-8."""
        self.assert_runnable(game_tests / 'utf8.py')

    def test_import(self):
        """Games can import other modules, which can acccess the builtins."""
        self.assert_runnable(game_tests / 'importing.py')

    def test_run_directory_dunder_main(self):
        """We can run a directory containing __main__.py"""
        self.assert_runnable(game_tests / 'red')

    def test_run_directory_main(self):
        """We can run a directory containing main.py"""
        self.assert_runnable(game_tests / 'pink')

    def test_run_directory_ane_name(self):
        """We can run a directory containing <basename>.py"""
        self.assert_runnable(game_tests / 'green')

    def test_run_directory_run_game(self):
        """We can run a directory containing run_game.py"""
        self.assert_runnable(game_tests / 'blue')


class GameStateRunnerTest(unittest.TestCase):
    """The runner wires up start() and the ``game`` builtin."""

    def assert_runnable(self, path: Path):
        clock.schedule_unique(sys.exit, 0.05)
        with self.assertRaises(SystemExit):
            load_and_run(str(path))

    def test_start_hook_and_restart(self):
        """start() runs before the first frame and again on restart."""
        self.assert_runnable(game_tests / 'start_hook.py')

    def test_new_builtins(self):
        """Sprite, SpriteActor, game etc. are available to games."""
        self.assert_runnable(game_tests / 'new_builtins.py')

    def test_each_run_gets_a_fresh_game(self):
        import builtins
        self.assert_runnable(game_tests / 'new_builtins.py')
        first = builtins.game
        first.score = 99
        self.assert_runnable(game_tests / 'new_builtins.py')
        self.assertIsNot(builtins.game, first)
        self.assertEqual(builtins.game.score, 0)
