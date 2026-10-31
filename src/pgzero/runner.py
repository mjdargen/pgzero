from . import storage
from . import clock
from . import loaders
from . import __version__
from .game import PGZeroGame, DISPLAY_FLAGS
from types import ModuleType
from argparse import ArgumentParser
import warnings
import sys
import os
import pygame


def init_pygame():
    """Start pygame, using silent audio if there is no sound device.

    pygame.init() doesn't raise when audio fails to start (e.g. on Codio,
    which has no sound device). It leaves the mixer off, so the first sound
    the game plays would raise an error. SDL reads SDL_AUDIODRIVER each time
    audio starts, so trying again with the dummy driver gives working,
    silent sound.
    """
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2)
    pygame.init()
    if not pygame.mixer.get_init():
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        pygame.mixer.init()


init_pygame()


def _check_python_ok_for_pygame():
    """If we're on a Mac, is this a full Framework python?

    There is a problem with PyGame on Macs running in a virtual env.
    If the Python used is from the venv, it will not allow full window and
    keyboard interaction. Instead, we need the original framework Python
    to get PyGame working properly.

    The problem doesn't occur on Linux and Windows.
    """
    if sys.platform == "darwin":  # This is a Mac
        return "Library/Frameworks" in sys.executable
    else:
        return True


def _substitute_full_framework_python():
    """Need to change the OS/X Python executable to the full Mac version,
    while maintaining the virtualenv environment, so things still run
    in an encapsulated way.

    We do this by extract the paths that virtualenv has added to the system
    path, and prefixing them to the current PYTHONPATH.

    Then we use os.execv() to start a replacement process that uses the
    same environment as the previous one.
    """
    PYVER = "{}.{}".format(*sys.version_info[:2])
    base_fw = "/Library/Frameworks/Python.framework/Versions/"
    framework_python = base_fw + "{pv}/bin/python{pv}".format(pv=PYVER)
    venv_base = os.environ.get("VIRTUAL_ENV")
    if not venv_base or not os.path.exists(framework_python):
        # Do nothing if virtual env hasn't been set up or if we can't
        # find the framework Python interpreter
        return
    venv_paths = [p for p in sys.path if p.startswith(venv_base)]
    # Need to allow for PYTHONPATH not already existing in environment
    os.environ["PYTHONPATH"] = ":".join(venv_paths + [os.environ.get("PYTHONPATH", "")]).rstrip(":")
    # Pass command line args to the new process
    os.execv(framework_python, ["python", "-m", "pgzero"] + sys.argv[1:])


def main():

    # Pygame won't run from a normal virtualenv copy of Python on a Mac
    if not _check_python_ok_for_pygame():
        _substitute_full_framework_python()

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
        # Clean some of the state we created, useful in testing
        pygame.display.quit()
        clock.clock.clear()
        del sys.modules[name]


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
    instead would leave the game window off-centre on the screen.

    """
    # An icon needs to exist before the window is created.
    PGZeroGame.show_default_icon()
    pygame.display.set_mode(
        (100, 100),
        flags=(DISPLAY_FLAGS & ~pygame.SHOWN) | pygame.HIDDEN,
    )


def run_mod(mod, **kwargs):
    """Run the module."""
    # Start from a fresh display so the game window opens centred, rather
    # than reusing the hidden loading window from prepare_mod().
    pygame.display.quit()
    pygame.display.init()
    PGZeroGame.show_default_icon()

    PGZeroGame(mod, **kwargs).run()
