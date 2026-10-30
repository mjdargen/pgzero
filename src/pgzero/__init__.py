"""Pygame Zero Plus."""

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    # Python 3.6 and 3.7
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("pgzero-plus")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
