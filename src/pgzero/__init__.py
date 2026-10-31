"""Pygame Zero Plus."""

import os
import warnings

# Every way of starting a game (``pgzrun game.py``, ``import pgzrun``,
# ``python -m pgzero``) imports this package before pygame, which is when
# SDL and pygame read these settings.

# Hide pygame welcome message
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Suppress pkg_resources deprecation warning
# Classic pygame imports pkg_resources, which warns on setuptools 67.5–80
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

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
