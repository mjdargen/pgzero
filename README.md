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

### Install or update

Once published on PyPI:

**Windows:**

```bash
python -m pip install --upgrade pgzero-plus
```

**macOS / Linux:**

```bash
python3 -m pip install --upgrade pgzero-plus
```

### Switching from Pygame Zero or an older fork

If you have installed `pgzero` or the earlier `pgzero-mjd` fork, first remove any existing versions, then install this one. This also repairs environments where two versions were accidentally installed together.

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

The `--force-reinstall` option does **not** remove a differently named distribution, so it is not a substitute for uninstalling the original `pgzero` package.

### Running Games

Pygame Zero Plus supports running games as regular Python scripts, making it easy to use your editor's normal Run button (for example, in VS Code).

Start your program with:

```python
import pgzrun
from pgzero.builtins import *
```

The explicit `pgzero.builtins` import also helps editors such as VS Code (Pylance) recognize names like `Actor` and `screen`.

Define your game variables and functions, such as `start()`, `draw()`, and `update()`, then end your program with:

```python
pgzrun.go()
```

Run the script through your editor or from a terminal:

```bash
python game.py
```

Alternatively, use the traditional Pygame Zero runner:

```bash
pgzrun game.py
```

## Development

Clone the repository:

```bash
git clone https://github.com/mjdargen/pgzero.git
cd pgzero
```

Install the fork in editable mode and install the development dependencies:

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

Editable installation lets you test source changes without rebuilding the package. If you have the original `pgzero` installed in this environment, uninstall it first as described above.

## Pre-commit Checks

[Pre-commit](https://pre-commit.com/) runs quick checks for whitespace, file formatting, YAML/TOML syntax, merge conflict markers, and accidentally added large files. It is a developer tool; students don't need to install it.

**Set up once per clone** (after installing your development dependencies):

```bash
python -m pip install pre-commit
python -m pre_commit install
```

**Check the whole repository manually** whenever you want:

```bash
python -m pre_commit run --all-files
```

After setup, pre-commit also runs automatically on staged files whenever you use `git commit`. Some hooks fix files automatically; if a check fails, review the changes with `git diff`, stage any fixes with `git add`, and run the checks or commit again.

Using `python -m pre_commit` avoids Windows PATH issues where the `pre-commit` command is not recognized.

## Testing

Run the full test suite from the repository root:

```bash
python -m pytest
```

To see individual test results or run a specific test file:

```bash
python -m pytest -v
python -m pytest test/test_actor.py
```

## Documentation

Documentation is written in [Sphinx](https://www.sphinx-doc.org/) using the `.rst` files in `doc/`. Edit those files when you add or change features, and update `doc/index.rst` if you add a new page. The Sphinx configuration is in `doc/conf.py`; `.readthedocs.yaml` controls the hosted documentation build.

**Build and preview locally** (from the repository root):

```powershell
python -m pip install sphinx
python -m sphinx -b html doc doc/_build/html
start doc/_build/html/index.html
```

On macOS/Linux, open `doc/_build/html/index.html` in a browser instead of using `start`. Check Sphinx's output for warnings; after resolving existing warnings, you can also use `-W --keep-going` to make warnings fail the build.

**Automatic checks and publishing:** The GitHub Actions **Code Checks** workflow can build the documentation alongside the tests, catching documentation build errors. [Read the Docs](https://readthedocs.org/) handles **hosting and automatic publication** separately: import this GitHub repository into Read the Docs once, and its GitHub integration will rebuild the documentation after changes are pushed. You do not need a separate GitHub Action to deploy the website.

Documentation updates are not generated automatically from code changes: update the relevant `.rst` pages when the API or behavior changes.

## Building and Verification

Install the packaging tools:

```bash
python -m pip install --upgrade build twine
```

Before releasing, run pre-commit checks, tests, and the documentation build; then build both distributions and validate their metadata and README:

```bash
python -m pre_commit run --all-files
python -m pytest
python -m sphinx -b html doc doc/_build/html
python -m build
python -m twine check --strict dist/*
```

The wheel and source archive are written to `dist/`. For version `0.1.0`, the wheel is `dist/pgzero_plus-0.1.0-py3-none-any.whl`. Remove older files from `dist/` before publishing a new release.

**Verify the built wheel** in a fresh virtual environment so you test the release artifact rather than your editable source installation.

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

The wheel filename changes when you bump the package version.

**Python 3.6 compatibility:** This fork targets Python 3.6 through 3.13, including older Codio environments. Since its modern build backend cannot build from source on Python 3.6, verify installation using the **built wheel** in Codio and run a representative game there before publishing. Building and running pytest can be done on your newer development Python.

## Credits & License

This project is an independent fork of [Pygame Zero](https://github.com/lordmauve/pgzero), originally developed by Daniel Pope and contributors.

Original documentation: https://pygame-zero.readthedocs.io/

Licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later).
