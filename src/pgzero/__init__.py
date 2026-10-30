"""Pygame Zero Plus."""

import os
import warnings

# Every way of starting a game (``pgzrun game.py``, ``import pgzrun``,
# ``python -m pgzero``) imports this package before pygame, which is when
# SDL and pygame read these settings.

# Codio has no sound device, so use SDL's silent audio driver there.
if (
    "CODIO_BOX_DOMAIN" in os.environ
    or "CODIO_HOSTNAME" in os.environ
    or os.environ.get("USER") == "codio"
    or os.path.exists("/home/codio")
):
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    warnings.filterwarnings("ignore", message=".*avx2 capable.*", category=RuntimeWarning)

# Hide pygame welcome message
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Suppress pkg_resources deprecation warning (from pygame)
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
