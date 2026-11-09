"""Tests for names exported to games and other small module-level additions."""

import unittest
from unittest import mock

import pgzero
from pgzero import builtins as pgz_builtins
from pgzero import clock
from pgzero.game import Game


class BuiltinsTest(unittest.TestCase):
    def test_all_names_exist(self):
        for name in pgz_builtins.__all__:
            self.assertTrue(hasattr(pgz_builtins, name), name)

    def test_new_exports(self):
        for name in ["Sprite", "Game", "game", "load_tile_map", "load_tile_map_actors"]:
            self.assertIn(name, pgz_builtins.__all__)

    def test_game_is_a_game(self):
        self.assertIsInstance(pgz_builtins.game, Game)


class ClockClearTest(unittest.TestCase):
    def test_module_level_clear(self):
        self.assertIn("clear", clock.__all__)
        c = clock.Clock()
        cb = mock.Mock()
        with mock.patch.object(clock, "clock", c), mock.patch.object(clock, "clear", c.clear):
            c.schedule(cb, 1)
            c.each_tick(cb)
            clock.clear()
            c.tick(2)
        cb.assert_not_called()
        self.assertEqual(c.events, [])

    def test_clear_is_bound_to_default_clock(self):
        self.assertEqual(clock.clear, clock.clock.clear)


class VersionTest(unittest.TestCase):
    def test_version_matches_installed_distribution(self):
        """__version__ comes from the installed pgzero-plus package."""
        try:
            from importlib.metadata import version
        except ImportError:
            from importlib_metadata import version
        self.assertEqual(pgzero.__version__, version("pgzero-plus"))


if __name__ == "__main__":
    unittest.main()
