"""Pygame Zero, a zero-boilerplate game framework for education.

You shouldn't need to import things from the 'pgzero' package directly; just
use 'pgzrun' to run the game file.

"""

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _dist_version

    try:
        __version__ = _dist_version("pgzero-plus")
    except PackageNotFoundError:
        __version__ = "unknown"
except ImportError:  # Python < 3.8
    __version__ = "unknown"

__all__ = ["__version__"]
