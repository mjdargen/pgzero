# Pygame Zero Plus

**Pygame Zero Plus** (`pgzero-plus`) is an independent fork of [Pygame Zero](https://github.com/lordmauve/pgzero), a beginner-friendly Python game development framework that reduces boilerplate code.

This fork adds features and quality-of-life improvements for introductory computer science and game design courses while retaining the familiar Pygame Zero API, including `Actor`, `screen`, and `pgzrun`.

## What's New

- **Enhanced Actors:** Scaling, flipping, opacity, and customizable collision rectangles.
- **Sprite Animations:** `Sprite` animations from sprite sheets or lists of images, played by any `Actor`.
- **Tilemaps:** Loading and rendering maps created with [Tiled Map Editor](https://www.mapeditor.org/), including tilesets and tile transformations.
- **Game Management:** A `Game` object for tracking scores, levels, game states, and restarting games.

## Installation

The PyPI distribution is named `pgzero-plus`, but it provides the same `pgzero` Python package and `pgzrun` command as the original Pygame Zero. **Do not install both distributions in the same Python environment.**

### Install or Update

**Windows:**

```bash
python -m pip install --upgrade pgzero-plus
```

**macOS / Linux:**

```bash
python3 -m pip install --upgrade pgzero-plus
```

### pygame and pygame-ce

On Python 3.10 and newer, Pygame Zero Plus installs [pygame-ce](https://pyga.me/), the actively developed community edition of pygame. On older Python versions it installs `pygame`, since pygame-ce needs Python 3.10 or newer.

Both provide the same `pygame` module, so they cannot be installed together. If `pygame` is already installed on Python 3.10 or newer, follow the steps below to switch cleanly. Note that this replaces `pygame` for every program in that Python environment.

### Switching from Pygame Zero, pygame, or an Older Fork

If you previously installed `pgzero` or `pygame`, uninstall any overlapping distributions before installing Pygame Zero Plus. This also helps repair environments where multiple forks have been installed together. Installing Pygame Zero Plus afterwards brings back the right version of pygame for your Python.

**Windows:**

```bash
python -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce
python -m pip install pgzero-plus
```

**macOS / Linux:**

```bash
python3 -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce
python3 -m pip install pgzero-plus
```

### Running Games

Pygame Zero Plus supports running games as regular Python scripts, including with the Run button in most code editors. Start your program with:

```python
import pgzrun
from pgzero.builtins import *
```

The explicit `pgzero.builtins` import helps editors such as VS Code (Pylance) recognize names like `Actor` and `screen`.

Define your variables and functions, such as `start()`, `draw()`, and `update()`, then end the program with:

```python
pgzrun.go()
```

Run the script through your editor or with:

```bash
python game.py
```

Alternatively, use the traditional Pygame Zero command:

```bash
pgzrun game.py
```

## Development

Clone the repository:

```bash
git clone https://github.com/mjdargen/pgzero.git
cd pgzero
```

Install the fork in editable mode **and** install all development tools with one command:

```bash
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes `-e .`, which installs the local package and its runtime dependencies. Source changes are available immediately without rebuilding the wheel. If the original `pgzero` is installed in this environment, uninstall it first as described above.

### Pre-commit Checks

[Pre-commit](https://pre-commit.com/) checks whitespace, file endings, YAML/TOML syntax, merge conflict markers, and accidentally added large files.

Activate it **once per clone**, after installing the development dependencies:

```bash
python -m pre_commit install
```

It then runs automatically on staged files before each `git commit`. If a hook modifies a file, review it with `git diff`, stage the fix with `git add`, and retry the commit.

To check all tracked files manually at any time:

```bash
python -m pre_commit run --all-files
```

Using `python -m pre_commit` avoids Windows PATH issues where the `pre-commit` command is not recognized.

### Testing

Run all tests from the repository root:

```bash
python -m pytest
```

For detailed output or one test file:

```bash
python -m pytest -v
python -m pytest test/test_actor.py
```

### Documentation

Documentation is written in [Sphinx](https://www.sphinx-doc.org/) using the `.rst` files in `doc/`. Update these pages when features or behavior change, and add new pages to `doc/index.rst` so they appear in the navigation.

Build and preview locally from the repository root:

```bash
python -m sphinx -b html doc doc/_build/html
```

Then open `doc/_build/html/index.html` in your browser.

### Automated Checks

GitHub Actions runs pre-commit, the tests on every supported Python version, the documentation build, and a package build on each pull request and push to `main`. Results appear on the pull request and on the [Actions page](https://github.com/mjdargen/pgzero/actions).

## Publishing a Release

Pushing a version tag triggers the release workflow, which tests, builds, publishes to PyPI, and creates a GitHub Release.

**1. Update the version** in `pyproject.toml`:

```toml
version = "0.1.0a2"
```

**2. Commit and push changes:**

```bash
git switch main
git status
git add .
git commit -m "Prepare v0.1.0a2"
git push origin main
```

**3. Confirm Code Checks passes** on the [GitHub Actions page](https://github.com/mjdargen/pgzero/actions).

**4. Create and push the release tag:**

```bash
git tag -a v0.1.0a2 -m "Release v0.1.0a2"
git push origin v0.1.0a2
```

**5. Verify publication:**

- [GitHub Actions](https://github.com/mjdargen/pgzero/actions)
- [GitHub Releases](https://github.com/mjdargen/pgzero/releases)
- [PyPI — pgzero-plus](https://pypi.org/project/pgzero-plus/)

## Credits & License

This project is an independent fork of [Pygame Zero](https://github.com/lordmauve/pgzero), originally developed by Daniel Pope and contributors.

Original documentation: https://pygame-zero.readthedocs.io/

Licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later).
