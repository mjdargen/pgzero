# Pygame Zero

The project is based on:

https://github.com/lordmauve/pgzero

Build instructions:

```bash
python -m build
python -m pip install --upgrade --force-reinstall ./dist/pgzero_mjd-0.0.1-py3-none-any.whl
```

Student installation command for Windows:

```bash
python -m pip install --upgrade --force-reinstall https://github.com/mjdargen/pgzero/releases/latest/download/pgzero_mjd-0.0.1-py3-none-any.whl
```

Student installation command for Mac:

```bash
python3 -m pip install --upgrade --force-reinstall https://github.com/mjdargen/pgzero/releases/latest/download/pgzero_mjd-0.0.1-py3-none-any.whl
```

## Documentation

The student guide lives in [`doc/`](doc/) and is built with Sphinx alongside
the upstream Pygame Zero docs. The classroom pages are `doc/classroom.rst`,
`doc/sprites.rst`, `doc/tilemaps.rst`, `doc/game.rst` and
`doc/actor-additions.rst`. To build it locally:

```bash
pip install sphinx
sphinx-build -b html doc doc/_build/html
```

then open `doc/_build/html/index.html`.
