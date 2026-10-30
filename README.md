# Pygame Zero Plus

**Pygame Zero Plus** (`pgzero-plus`) is an independent fork of [Pygame Zero](https://github.com/lordmauve/pgzero), a beginner-friendly Python game development framework that reduces boilerplate code.

This fork adds features and quality-of-life improvements for introductory computer science and game design courses while retaining the familiar Pygame Zero API, including `Actor`, `screen`, and `pgzrun`.

## What's New

- **Enhanced Actors:** Scaling, flipping, opacity, and customizable collision rectangles.
- **Sprite Animations:** `Sprite` and `SpriteActor` classes for animated sprite sheets.
- **Tilemaps:** Loading and rendering maps created with [Tiled Map Editor](https://www.mapeditor.org/), including tilesets and tile transformations.
- **Game Management:** A `Game` object for tracking scores, levels, game states, and restarting games.

## Installation

The PyPI distribution is named `pgzero-plus`, but it provides the same `pgzero` Python package and `pgzrun` command as the original Pygame Zero. **Do not install both distributions in the same Python environment.**

### Install or Update

Once published on PyPI:

**Windows:**

```bash
python -m pip install --upgrade pgzero-plus
```

**macOS / Linux:**

```bash
python3 -m pip install --upgrade pgzero-plus
```

### Switching from Pygame Zero or an Older Fork

If you previously installed `pgzero` or `pgzero-mjd`, uninstall any overlapping distributions before installing Pygame Zero Plus. This also helps repair environments where multiple forks have been installed together.

**Windows:**

```bash
python -m pip uninstall -y pgzero pgzero-mjd pgzero-plus
python -m pip install pgzero-plus
```

**macOS / Linux:**

```bash
python3 -m pip uninstall -y pgzero pgzero-mjd pgzero-plus
python3 -m pip install pgzero-plus
```

`--force-reinstall` does **not** remove a differently named distribution, so it is not a substitute for uninstalling the original `pgzero` package.

### Running Games

Pygame Zero Plus supports running games as regular Python scripts, including with the Run button in VS Code.

Start your program with:

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

On Windows (PowerShell), open the generated documentation with:

```powershell
start doc/_build/html/index.html
```

On macOS or Linux, open that HTML file in your browser. The Sphinx configuration lives in `doc/conf.py`.

Once this repository is connected to [Read the Docs](https://readthedocs.org/), its `.readthedocs.yaml` configuration allows the hosted documentation to rebuild automatically after changes are pushed. GitHub Actions verifies that the documentation builds; Read the Docs hosts and publishes the website.

### Automated Checks on GitHub

The [Code Checks workflow](https://github.com/mjdargen/pgzero/actions) (`.github/workflows/checks.yml`) runs automatically on pushes to `main` and on pull requests. It runs pre-commit, pytest, Sphinx, the package build, and distribution validation.

These checks run **after** a push, so a failing check does not undo the push. Check the Actions page for results and fix any failures before publishing a release.

## Building and Verification

The automated release workflow builds distributions for publishing, so **manual builds are optional** during everyday development. To check a release locally, run:

```bash
python -m pre_commit run --all-files
python -m pytest
python -m sphinx -b html doc doc/_build/html
python -m build
python -m twine check --strict dist/*
```

The wheel (`.whl`) and source archive (`.tar.gz`) are written to `dist/`. Clear out older distributions from `dist/` before building a new version so you do not accidentally inspect or upload old files.

### Verify the Built Wheel

Install the built wheel in a **fresh virtual environment** to check the distribution itself instead of your editable development installation. The example filename below is for version `0.1.0`; update it when the version changes.

**Windows (PowerShell):**

```powershell
python -m venv .venv-wheel-check
.\.venv-wheel-check\Scripts\python.exe -m pip install dist/pgzero_plus-0.1.0-py3-none-any.whl
.\.venv-wheel-check\Scripts\python.exe -m pip check
.\.venv-wheel-check\Scripts\python.exe -c "import pgzero, pgzrun; print(pgzero.__file__)"
```

**macOS / Linux:**

```bash
python3 -m venv .venv-wheel-check
.venv-wheel-check/bin/python -m pip install dist/pgzero_plus-0.1.0-py3-none-any.whl
.venv-wheel-check/bin/python -m pip check
.venv-wheel-check/bin/python -c "import pgzero, pgzrun; print(pgzero.__file__)"
```

**Python 3.6 compatibility:** This fork targets Python 3.6 through 3.13, including older Codio environments. The modern build backend does not support building from source on Python 3.6. Before a release, install the **built wheel** in Codio and run a representative game there; passing tests on Python 3.13 does not establish compatibility with Python 3.6.

## Publishing Releases

GitHub Actions handles publishing through `.github/workflows/release.yml`. A new package is **not** published on every push to `main`; publishing starts only when you push a version tag.

### One-time PyPI Setup

1. Create a GitHub repository environment named `pypi` under **Settings → Environments**.
2. Configure [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for project `pgzero-plus`, GitHub owner `mjdargen`, repository `pgzero`, workflow `release.yml`, and environment `pypi`. For a first release, use a _pending trusted publisher_ if the project has not yet been created on PyPI.

This allows GitHub Actions to publish without storing a PyPI API token.

### Create a Release

1. Set the new `version` in `pyproject.toml`. For example, `version = "0.1.0"`.
2. Commit and push your changes to `main`, then confirm that **Code Checks** passes on the [Actions page](https://github.com/mjdargen/pgzero/actions).
3. Create and push a Git tag **matching** that version, with a leading `v`:

```bash
git switch main
git pull
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

The release workflow verifies the version, runs the checks, builds the wheel and source archive, publishes to PyPI, and creates a GitHub Release with the built files attached. If a check or build fails, publishing stops.

For a later release, update the version number and use its matching tag (for example, `0.1.1` and `v0.1.1`). Use patch releases for bug fixes and minor releases for new features. **PyPI does not allow replacing files for an existing published version.**

## Credits & License

This project is an independent fork of [Pygame Zero](https://github.com/lordmauve/pgzero), originally developed by Daniel Pope and contributors.

Original documentation: https://pygame-zero.readthedocs.io/

Licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later).
