"""Warn about installs that clash, which is the most common classroom problem.

pygame and pygame-ce both install a package called pygame, and pgzero and
pgzero-plus both install packages called pgzero and pgzrun. pip can't stop
both of a pair being installed, and when they are, files from one overwrite
the other's, so games crash or behave strangely in ways that are hard to
trace back to the install.
"""

import sys

try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    # Python 3.6 and 3.7
    from importlib_metadata import PackageNotFoundError, distribution

# Pairs of distributions that install the same Python packages.
CLASHING_PAIRS = [("pygame", "pygame-ce"), ("pgzero", "pgzero-plus")]


def _installed(name):
    try:
        distribution(name)
    except PackageNotFoundError:
        return False
    return True


def clashing_installs(installed=_installed):
    """Return the pairs from CLASHING_PAIRS that are both installed."""
    return [pair for pair in CLASHING_PAIRS if installed(pair[0]) and installed(pair[1])]


def warning_message(clashes, python=None):
    """Return a message explaining the clashes and how to fix them."""
    python = python or sys.executable
    names = ", ".join(" and ".join(pair) for pair in clashes)
    return (
        "Warning: {} are both installed. They overwrite each other's files, so "
        "games may crash or behave strangely. To fix it, run these two "
        "commands, then restart your editor:\n"
        '    "{python}" -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce\n'
        '    "{python}" -m pip install pgzero-plus'.format(names, python=python)
    )


def warn_about_clashing_installs():
    """Print a warning if clashing distributions are installed."""
    try:
        clashes = clashing_installs()
    except Exception:
        # Never stop a game from starting because the check went wrong.
        return
    if clashes:
        print(warning_message(clashes), file=sys.stderr)
