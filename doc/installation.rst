Installing Pygame Zero Plus
===========================

Pygame Zero Plus is installed from PyPI as ``pgzero-plus``. It provides the same
``pgzero`` package and ``pgzrun`` command as the original Pygame Zero, so
**don't install both in the same Python environment**.

On Windows, type this in a terminal::

    python -m pip install --upgrade pgzero-plus

On Mac or Linux, type this in a Terminal window::

    python3 -m pip install --upgrade pgzero-plus

This also installs pygame. On Python 3.10 and newer it installs `pygame-ce`_,
the actively developed community edition of pygame. On older Pythons it
installs ``pygame``. Both provide the same ``pygame`` module, so only one of
them can be installed at a time.

.. _pygame-ce: https://pyga.me/

If there is no sound device, such as on some online coding platforms, games
still run with silent sound.


Switching from Pygame Zero or pygame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have installed the original Pygame Zero (``pgzero``), or ``pygame`` on
Python 3.10 or newer, uninstall them first. Then install Pygame Zero Plus,
which installs the right pygame for your Python again.

On Windows::

    python -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce
    python -m pip install pgzero-plus

On Mac or Linux::

    python3 -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce
    python3 -m pip install pgzero-plus

Note that this replaces ``pygame`` for every program that uses that Python.

Raspberry Pi OS may come with the original Pygame Zero already installed. Use
a `virtual environment`_ for Pygame Zero Plus there, so the two don't
conflict.

.. _`virtual environment`: https://docs.python.org/3/library/venv.html


For flake8/pyflakes
~~~~~~~~~~~~~~~~~~~

Checkers like Pyflakes are unaware of Pygame Zero's extra builtins.

If you use ``flake8``, you can add Pygame Zero's list of builtins to your
`flake8 configuration file <https://flake8.pycqa.org/en/latest/user/configuration.html>`_:

.. code-block:: ini

    [flake8]
    builtins = Actor,Game,Rect,Sprite,ZRect,animate,clock,exit,game,images,keyboard,keymods,keys,load_tile_map_actors,mouse,music,screen,sounds,storage,tone

If you use `pyflakes` directly then this is configured using the environment
variable ``$PYFLAKES_BUILTINS``. On Linux and Mac you could write this in your
terminal or put it in your shell configuration file (like ``~/.bashrc``)

.. code-block:: bash

    PYFLAKES_BUILTINS=Actor,Game,Rect,Sprite,ZRect,animate,clock,exit,game,images,keyboard,keymods,keys,load_tile_map_actors,mouse,music,screen,sounds,storage,tone
    export PYFLAKES_BUILTINS

On Windows:

.. code-block:: none

    set PYFLAKES_BUILTINS=Actor,Game,Rect,Sprite,ZRect,animate,clock,exit,game,images,keyboard,keymods,keys,load_tile_map_actors,mouse,music,screen,sounds,storage,tone
