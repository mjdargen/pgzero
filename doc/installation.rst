Installing pgzero-mjd
=====================

``pgzero-mjd`` is the classroom build of Pygame Zero. It installs the same
``pgzero`` package and ``pgzrun`` command as the original, so do not install
``pgzero`` as well: the two would overwrite each other. If you already have
the original, ``pip uninstall pgzero`` first.

On desktop systems
~~~~~~~~~~~~~~~~~~

::

    pip install pgzero-mjd

This will also install Pygame. Pre-compiled Pygame packages are available to pip
for Windows & Linux (32-bit and 64-bit), and for Mac OS (64-bit only). If you
have a different system, you'll need to find a way to install pygame first. Make
sure you are using Python 3 not Python 2.

Mac
'''

In a Terminal window, type

::

   python3 -m pip install pgzero-mjd


Note that there are currently no Wheels for Pygame that support python 3.4 for Mac,
so you will need to upgrade Python to >=3.6 (or use python 2.7) in
order to be able to install pygame. For a list of available Wheels, please visit
`pyPI_`

.. _pyPI: https://pypi.org/project/Pygame/#files

Linux
'''''

In a terminal window, type

::

   sudo pip install pgzero-mjd


Some Linux systems call it ``pip3``; if the above command printed something
like ``sudo: pip: command not found`` then try::

    sudo pip3 install pgzero-mjd

Sometimes pip is not installed and needs to be installed. If so try this before
running the above commands again::


    sudo python3 -m ensurepip


On Raspberry Pi
~~~~~~~~~~~~~~~

The original ``pgzero`` has been installed by default since the release of
Raspbian Jessie in September 2015. To use the classroom build instead, run
the Linux commands above; ``pgzero-mjd`` replaces it.


Checking and upgrading
~~~~~~~~~~~~~~~~~~~~~~

To check that the right build is installed::

    pgzrun --version

To upgrade to the newest release::

    pip install --upgrade pgzero-mjd


For flake8/pyflakes
~~~~~~~~~~~~~~~~~~~

Checkers like Pyflakes are unaware of Pygame Zero's extra builtins. The list
below includes the classroom additions (``Sprite``, ``SpriteActor``,
``Game``, ``game`` and ``load_tile_map_actors``). If your game starts with
``from pgzero.builtins import *`` the checker already knows the names and
you can skip this section.

If you use ``flake8``, you can add Pygame Zero's list of builtins to your
`flake8 configuration file <https://flake8.pycqa.org/en/latest/user/configuration.html>`_:

.. code-block:: ini

    [flake8]
    builtins = Actor,Rect,ZRect,animate,clock,exit,images,keyboard,keymods,keys,mouse,music,screen,sounds,storage,tone,Sprite,SpriteActor,Game,game,load_tile_map_actors

If you use ``ruff``, put the same list in ``pyproject.toml``:

.. code-block:: toml

    [tool.ruff]
    builtins = ["Actor", "Rect", "ZRect", "animate", "clock", "exit", "images", "keyboard", "keymods", "keys", "mouse", "music", "screen", "sounds", "storage", "tone", "Sprite", "SpriteActor", "Game", "game", "load_tile_map_actors"]

If you use `pyflakes` directly then this is configured using the environment
variable ``$PYFLAKES_BUILTINS``. On Linux and Mac you could write this in your
terminal or put it in your shell configuration file (like ``~/.bashrc``)

.. code-block:: bash

    PYFLAKES_BUILTINS=Actor,Rect,ZRect,animate,clock,exit,images,keyboard,keymods,keys,mouse,music,screen,sounds,storage,tone,Sprite,SpriteActor,Game,game,load_tile_map_actors
    export PYFLAKES_BUILTINS

On Windows:

.. code-block:: none

    set PYFLAKES_BUILTINS=Actor,Rect,ZRect,animate,clock,exit,images,keyboard,keymods,keys,mouse,music,screen,sounds,storage,tone,Sprite,SpriteActor,Game,game,load_tile_map_actors
