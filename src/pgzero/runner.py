from . import storage
from . import clock
from . import loaders
from . import __version__
from .game import PGZeroGame, DISPLAY_FLAGS
from contextlib import contextmanager
from types import ModuleType
from argparse import ArgumentParser
import warnings
import sys
import os
import pygame


@contextmanager
def quiet_stderr():
    """Hide anything that C libraries print straight to stderr.

    Python's own errors still show, as they are raised after this ends.
    Where stderr isn't a real file (e.g. in IDLE), this does nothing.
    """
    try:
        fd = sys.stderr.fileno()
    except (AttributeError, OSError, ValueError):
        yield
        return
    sys.stderr.flush()
    saved = os.dup(fd)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, fd)
    try:
        yield
    finally:
        os.dup2(saved, fd)
        os.close(saved)
        os.close(devnull)


def init_pygame():
    """Start pygame, using silent audio if there is no sound device.

    If audio can't start (e.g. on a virtual desktop with no sound device), try
    again with SDL's dummy driver, which gives working, silent sound. SDL reads
    SDL_AUDIODRIVER each time audio starts.
    """
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2)
    try:
        # On Linux without a sound card, ALSA prints a page of errors as the
        # first attempt fails. They mean nothing to students, so hide them.
        with quiet_stderr():
            pygame.mixer.init()
    except pygame.error:
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        pygame.mixer.init()
    # Start everything else. The mixer is already running, so this doesn't
    # try (and print errors for) the sound card again.
    pygame.init()


init_pygame()


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--fps",
        action="store_true",
        help="Print periodic FPS measurements on the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("game", help="The Pygame Zero game to run (a Python file or directory).")
    args = parser.parse_args()

    if __debug__:
        warnings.simplefilter("default", DeprecationWarning)

    try:
        load_and_run(args.game, fps=args.fps)
    except NoMainModule as e:
        sys.exit(e)


class NoMainModule(Exception):
    """Indicate that we couldn't find a main module to run."""


def load_and_run(path, *, fps: bool = False):
    """Load and run the given Python file or directory.

    If a file, run this as the main PGZero game module.

    If a directory, run the first file inside the directory containing:

    * `__main__.py`
    * `main.py`
    * `run_game.py`
    * `<name>.py` where `<name>` is the basename of the directory

    Note that the 'import pgzrun' IDE mode doesn't pass through this entry
    point, as the module is already loaded.

    """
    path = path.rstrip(os.sep)
    try:
        with open(path, "rb") as f:
            src = f.read()
    except FileNotFoundError:
        raise NoMainModule(f"Error: {path} does not exist.")
    except (IsADirectoryError, PermissionError):
        name = os.path.basename(path)
        for candidate in (
            "__main__.py",
            "main.py",
            "run_game.py",
            f"{name}.py",
        ):
            try:
                with open(os.path.join(path, candidate), "rb") as f:
                    src = f.read()
                    break
            except FileNotFoundError:
                pass
        else:
            raise NoMainModule(f"""\
Error: {path} is a directory.

To run a directory with pgzrun, it must contain a file named __main__.py,
main.py, run_game.py, or a .py file with the same name as the directory.

You can also run a specific file with:

    pgzrun path/to/your/file.py
""")
    else:
        name, _ = os.path.splitext(os.path.basename(path))

    code = compile(src, os.path.basename(path), "exec", dont_inherit=True)
    mod = ModuleType(name)
    mod.__file__ = path
    mod.__name__ = name
    sys.modules[name] = mod

    # Indicate that we're running with the pgzrun runner
    # This disables the 'import pgzrun' module
    sys._pgzrun = True

    prepare_mod(mod)
    exec(code, mod.__dict__)

    try:
        run_mod(mod, fps=fps)
    finally:
        # Clean some of the state we created, so that another game can run
        # in the same process (e.g. in the tests)
        pygame.display.quit()
        clock.clock.clear()
        del sys.modules[name]
        sys._pgzrun = False


def prepare_mod(mod):
    """Prepare to execute the module code for Pygame Zero.

    To allow the module to load assets, we configure the loader path to
    load relative to the module's __file__ path.

    When executing the module some things need to already exist:

    * Our extra builtins need to be defined (by copying them into Python's
      `builtins` module)
    * A window needs to exist (because we use convert_alpha() to convert
      image surfaces for blitting to the screen). See open_loading_window().

    """
    storage.storage._set_filename_from_path(mod.__file__)
    loaders.set_root(mod.__file__)

    # A game that ran earlier in this process (e.g. in Spyder, or the tests)
    # shut audio down when it ended, so start it again.
    if not pygame.mixer.get_init():
        init_pygame()

    open_loading_window()

    from .game import Game
    from . import builtins as pgzero_builtins
    import builtins as python_builtins

    for name in pgzero_builtins.__all__:
        python_builtins.__dict__.setdefault(name, getattr(pgzero_builtins, name))

    # setdefault() keeps any name that already exists, so these are replaced
    # explicitly:
    # * exit: Python already has its own exit(), which doesn't wait for
    #   sounds to finish playing.
    # * game: each run starts with a fresh Game, so score and state from an
    #   earlier run (e.g. in the test suite) don't carry over.
    python_builtins.exit = pgzero_builtins.exit
    python_builtins.game = pgzero_builtins.game = Game()


def open_loading_window():
    """Create a hidden window for the game module's top-level code to use.

    Several Pygame surface operations access the state of the screen as a
    global:

    * Surface.convert_alpha() without arguments converts a surface for fast
      blitting to the display.
    * Surface() without flags creates a surface identical to the display
      format.

    There's no good API to expose what the display format is until we create
    a window, so we create a hidden one, which lets code like a top-level
    ``Actor("alien")`` load its image. The expectation is that when we create
    the real window this will have the same display format and blits etc will
    still be fast.

    run_mod() closes this window before opening the real one. Resizing it
    instead would leave the game window off-center on the screen.

    """
    # An icon needs to exist before the window is created.
    PGZeroGame.show_default_icon()
    pygame.display.set_mode(
        (100, 100),
        flags=(DISPLAY_FLAGS & ~pygame.SHOWN) | pygame.HIDDEN,
    )


def run_mod(mod, **kwargs):
    """Run the module."""
    # Start from a fresh display so the game window opens centered, rather
    # than reusing the hidden loading window from prepare_mod().
    pygame.display.quit()
    pygame.display.init()

    try:
        PGZeroGame(mod, **kwargs).run()
    finally:
        # Save storage when the game ends, however it ends, so that high
        # scores and other saved values are there next time.
        storage.Storage.save_all()
