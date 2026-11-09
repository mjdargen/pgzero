"""Tests for Pygame Zero's runner system.

This module is also a Pygame Zero game so that we can run it with pgzero.

"""
import builtins
import io
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pygame

from pgzero.runner import load_and_run, prepare_mod
from pgzero import builtins as pgzero_builtins
from pgzero import clock
from pgzero.game import exit as pgzero_exit

test_dir = Path(__file__).parent
game_tests = test_dir / 'game_tests'


class RunnerTestCase(unittest.TestCase):
    def assert_runnable(self, path: Path):
        """Check that we can run the given file."""
        clock.schedule_unique(sys.exit, 0.05)
        with self.assertRaises(SystemExit):
            load_and_run(str(path))


class RunnerTest(RunnerTestCase):
    """Test that we can load and run the current file."""

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


class GameStateRunnerTest(RunnerTestCase):
    """The runner wires up start() and the ``game`` builtin."""

    def test_start_hook_and_restart(self):
        """start() runs before the first frame and again on restart."""
        self.assert_runnable(game_tests / 'start_hook.py')

    def test_new_builtins(self):
        """Sprite, load_tile_map, game etc. are available to games."""
        self.assert_runnable(game_tests / 'new_builtins.py')

    def test_each_run_gets_a_fresh_game(self):
        self.assert_runnable(game_tests / 'new_builtins.py')
        first = builtins.game
        first.score = 99
        self.assert_runnable(game_tests / 'new_builtins.py')
        self.assertIsNot(builtins.game, first)
        self.assertEqual(builtins.game.score, 0)


class PrepareModTest(unittest.TestCase):
    """prepare_mod() sets things up before a game module's code runs."""

    def setUp(self):
        mod = types.ModuleType('utf8')
        mod.__file__ = str(game_tests / 'utf8.py')
        with mock.patch.object(
            pygame.display, 'set_mode', wraps=pygame.display.set_mode
        ) as set_mode:
            prepare_mod(mod)
        self.set_mode = set_mode

    def tearDown(self):
        pygame.display.quit()

    def test_loading_window_is_hidden(self):
        """The window for loading images doesn't flash up on screen."""
        self.set_mode.assert_called_once()
        flags = self.set_mode.call_args[1]['flags']
        self.assertTrue(flags & pygame.HIDDEN)
        self.assertFalse(flags & pygame.SHOWN)
        self.assertIsNotNone(pygame.display.get_surface())

    def test_only_public_names_installed(self):
        """Only the names in pgzero.builtins.__all__ become builtins."""
        for name in ('__file__', '__cached__', '__all__', 'python_builtins'):
            self.assertNotIn(name, vars(builtins))

    def test_exit_replaces_python_exit(self):
        """exit() is Pygame Zero's, which lets sounds finish playing."""
        self.assertIs(builtins.exit, pgzero_exit)

    def test_game_is_shared(self):
        """``from pgzero.builtins import *`` gets the same game object."""
        self.assertIs(builtins.game, pgzero_builtins.game)


class AudioFallbackTest(unittest.TestCase):
    """Games still run, silently, on computers with no sound device."""

    def test_no_sound_device(self):
        # An unknown audio driver fails to start, like a missing sound device.
        # This runs in a new process because pygame starts when the runner is
        # imported.
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='nosuchdriver')
        script = (
            'import os, pygame, pgzero.runner\n'
            'print(pygame.mixer.get_init(), os.environ["SDL_AUDIODRIVER"])\n'
        )
        result = subprocess.run(
            [sys.executable, '-c', script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '(22050, -16, 2) dummy')

    def test_sound_library_messages_are_hidden(self):
        """Messages printed by C libraries, like ALSA's when there's no
        sound card, are hidden, but stderr works again afterwards."""
        script = """\
import os
from pgzero.runner import quiet_stderr
with quiet_stderr():
    os.write(2, b"ALSA lib pcm.c: Unknown PCM default")
os.write(2, b"after")
"""
        result = subprocess.run(
            [sys.executable, '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('ALSA', result.stderr)
        self.assertIn('after', result.stderr)


class FullscreenTest(unittest.TestCase):
    """FULLSCREEN = True scales the game to fill the screen, and F11 switches."""

    def test_fullscreen_and_f11(self):
        # In a separate process with the dummy video driver, so the test never
        # takes over a real screen. The dummy screen is 1024x768.
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, str(tmp))
        (tmp / 'images').mkdir()
        shutil.copy(str(test_dir / 'images' / 'alien.png'), str(tmp / 'images'))
        shutil.copy(str(game_tests / 'fullscreen.py'), str(tmp))
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        result = subprocess.run(
            [sys.executable, 'fullscreen.py'],
            cwd=str(tmp),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            # The window fills the screen, but the game still draws at 400x300
            'True (1024, 768) (400, 300) True',
            # F11: a normal window
            'False (400, 300) (400, 300) True',
            # F11 again: fullscreen, still drawing
            'True (1024, 768) (400, 300) True',
            # Keys held while switching don't stay stuck down
            'right held: False',
        ])


class IDEModeTest(unittest.TestCase):
    """Games can be started with ``import pgzrun`` and ``pgzrun.go()``.

    The game in game_tests/ide_mode.py exits by itself once it has checked
    that it loaded an image, ran start() and drew to the game window.
    """

    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        # resolve() expands Windows 8.3 short names (e.g. MICHAE~1), which
        # the loaders' case check would otherwise reject.
        self.game_dir = Path(tmp).resolve()
        (self.game_dir / 'images').mkdir()
        shutil.copy(str(test_dir / 'images' / 'alien.png'), str(self.game_dir / 'images'))
        shutil.copy(str(game_tests / 'ide_mode.py'), str(self.game_dir))

    def test_run_as_script(self):
        """Running the file directly with Python runs the game."""
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        result = subprocess.run(
            [sys.executable, 'ide_mode.py'],
            cwd=str(self.game_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ide_mode ok', result.stdout)

    def test_run_with_runner(self):
        """``import pgzrun`` and go() do nothing when run by pgzrun."""
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            load_and_run(str(self.game_dir / 'ide_mode.py'))
        self.assertIn('ide_mode ok', out.getvalue())
        # Once the game has ended, import pgzrun works again
        self.assertFalse(getattr(sys, '_pgzrun', False))


SOUND_GAME = """import sys
sounds.powerup.play()
tone.create('A4', 0.1).play()
print('played')
clock.schedule_unique(sys.exit, 0.1)
"""

RUN_TWICE = """from pgzero.runner import load_and_run
for run in (1, 2):
    try:
        load_and_run('game.py')
    except SystemExit:
        print('ended', run)
"""


class RepeatedRunTest(unittest.TestCase):
    """Games can run one after another in the same Python process."""

    def test_game_with_sounds_runs_twice(self):
        # In a separate process: before this was fixed, the second run
        # crashed Python by playing a sound left over from the first.
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, str(tmp))
        (tmp / 'sounds').mkdir()
        shutil.copy(str(test_dir / 'sounds' / 'powerup.wav'), str(tmp / 'sounds'))
        (tmp / 'game.py').write_text(SOUND_GAME)
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        result = subprocess.run(
            [sys.executable, '-c', RUN_TWICE],
            cwd=str(tmp),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ['played', 'ended', '1', 'played', 'ended', '2'])
        # Starting a game doesn't print pygame-ce's renderer warning
        self.assertNotIn('no fast renderer', result.stderr)
