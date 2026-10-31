Running Pygame Zero in IDLE and other IDEs
==========================================

.. versionadded:: 1.2

Pygame Zero is usually run using a command such as::

    pgzrun my_program.py

Certain programs, such as integrated development environments like IDLE,
VS Code and Edublocks, will only run ``python``, not ``pgzrun``.

Pygame Zero includes a way of writing a full Python program that can be run
using ``python``, for example with the Run button in VS Code. To do it, put ::

    import pgzrun
    from pgzero.builtins import *

as the very first lines of the Pygame Zero program, and put ::

    pgzrun.go()

as the very last line.

The second line is optional, but it lets editors such as VS Code know about
names like ``Actor`` and ``screen``, so they don't underline them as errors.

A program written this way still works with the ``pgzrun`` command.


Example
-------

Here is a Pygame Zero program that draws a circle. You can run this by pasting
it into IDLE::


    import pgzrun
    from pgzero.builtins import *


    WIDTH = 800
    HEIGHT = 600

    def draw():
        screen.clear()
        screen.draw.circle((400, 300), 30, 'white')


    pgzrun.go()
