Tile maps from Tiled
====================

A tile map is a level built from small square pictures (**tiles**) placed on
a grid, like a mosaic. One image, the **tileset**, holds every tile; the map
says which tile goes in which cell. You draw the level in the free Tiled_
editor, save it as a ``.tmx`` file in your ``maps/`` folder, and
:func:`load_tile_map_actors` turns every placed tile into an :class:`Actor`
you can draw and collide with.

.. _Tiled: https://www.mapeditor.org/

Words you will meet
-------------------

tileset
    A PNG with all the tiles in a grid, plus a small ``.tsx`` file recording
    the tile size, the number of columns, and any margin or spacing between
    the tiles.
map
    The ``.tmx`` file: the grid size, the tile size, which tilesets the map
    uses, and one or more layers.
layer
    One grid of tile choices. Maps usually have several (``ground``,
    ``platforms``, ``hazards``, ``collectables``) so that your code can treat
    each group differently. Cells can be left empty on any layer.
gid
    A number that identifies a tile inside the map file; ``0`` means an
    empty cell. You rarely need it, but every loaded tile remembers its gid.

Making a map in Tiled
---------------------

1. Put the tileset image in your project's ``maps/`` folder, for example
   ``maps/platformer_pixel_kenney.png``.
2. In Tiled choose **File > New > New Map**: orientation *Orthogonal*, tile
   layer format **CSV**, the tile size of your tileset (``18 x 18`` for the
   Kenney pixel platformer pack), and the map size in tiles. ``30 x 20``
   tiles of 18 pixels drawn at scale 2 fill a 1080 x 720 window.
3. **File > New > New Tileset**: type *Based on Tileset Image*, pick the PNG
   from ``maps/``, and enter the tile size plus any margin and spacing the
   pack uses. Either tick **Embed in map**, or save the ``.tsx`` into the
   same ``maps/`` folder.
4. Rename the layer (double-click *Tile Layer 1*) and paint. Add more layers
   with the **+** button in the Layers panel and name them after what your
   code will do with them.
5. **File > Save As** into ``maps/``, for example ``platformer.tmx``.

The loader only reads CSV layers. If you opened an older map and get
``Layer 'ground' must use CSV encoding``, change **Map > Map Properties >
Tile Layer Format** to *CSV* and save again.

The files the example below needs::

    platformer.py
    maps/platformer.tmx                   the map
    maps/platformer_pixel_kenney.tsx      the tileset (unless embedded)
    maps/platformer_pixel_kenney.png      the tileset image
    sprites/fox.png

Tiled writes file references relative to the file that uses them, so as long
as the ``.tmx``, ``.tsx`` and ``.png`` sit together in ``maps/`` the map
loads on any computer. If the loader cannot find the image after you moved
things around, open the ``.tsx`` in a text editor and fix its
``<image source="...">`` line.

A complete example
------------------

A small platformer. The map has three layers named ``platforms``,
``hazards`` and ``collectables``; the fox walks and jumps on the platforms,
loses on a hazard, and wins when every collectable is gone.

::

    import pgzrun
    from pgzero.builtins import *

    TILE_SIZE = 18
    COLS = 30
    ROWS = 20
    SCALE = 2

    WIDTH = TILE_SIZE * COLS * SCALE
    HEIGHT = TILE_SIZE * ROWS * SCALE
    TITLE = "Platformer"

    gravity = 1

    # build the world from the Tiled map: one list of actors per layer
    layers = load_tile_map_actors("platformer.tmx", scale=SCALE)
    platforms = layers["platforms"]
    hazards = layers["hazards"]
    collectables = layers["collectables"]

    fox_idle = Sprite("fox.png", 24, 16, 0, 5, 4)
    fox_walk = Sprite("fox.png", 24, 16, 2, 8, 10)
    fox = SpriteActor(fox_idle)


    def start():
        fox.scale = 2.5
        fox.bottomleft = (0, HEIGHT)
        fox.velocity_x = 5
        fox.velocity_y = 0
        fox.jumping = False


    def draw():
        screen.clear()
        screen.fill("lightslateblue")
        for platform in platforms:
            platform.draw()
        for hazard in hazards:
            hazard.draw()
        for mushroom in collectables:
            mushroom.draw()
        if game.state != "lost":
            fox.draw()
        if game.state == "lost":
            screen.draw.text("Game Over", center=(WIDTH / 2, HEIGHT / 2), fontsize=60)
        elif game.state == "won":
            screen.draw.text("You win!", center=(WIDTH / 2, HEIGHT / 2), fontsize=60)


    def update():
        if game.state != "playing":
            return

        # left and right, stepping back out of any platform we walked into
        if keyboard.left and fox.left > 0:
            fox.x -= fox.velocity_x
            fox.sprite = fox_walk
            fox.flip_h = True
            index = fox.collidelist(platforms)
            if index != -1:
                fox.left = platforms[index].right
        elif keyboard.right and fox.right < WIDTH:
            fox.x += fox.velocity_x
            fox.sprite = fox_walk
            fox.flip_h = False
            index = fox.collidelist(platforms)
            if index != -1:
                fox.right = platforms[index].left

        # gravity, then land on a platform or bump our head on one
        fox.y += fox.velocity_y
        fox.velocity_y += gravity
        index = fox.collidelist(platforms)
        if index != -1:
            platform = platforms[index]
            if fox.velocity_y >= 0:
                fox.bottom = platform.top
                fox.jumping = False
            else:
                fox.top = platform.bottom
            fox.velocity_y = 0

        if fox.collidelist(hazards) != -1:
            game.lose()

        index = fox.collidelist(collectables)
        if index != -1:
            collectables.pop(index)
            game.add_score(1)

        if len(collectables) == 0:
            game.win()


    def on_key_down(key):
        if key == keys.UP and not fox.jumping:
            fox.velocity_y = -15
            fox.jumping = True


    def on_key_up(key):
        if key == keys.LEFT or key == keys.RIGHT:
            fox.sprite = fox_idle


    pgzrun.go()

Things to notice:

* ``load_tile_map_actors()`` is called once, at the top of the file, like
  the sprites. Loading a map takes a moment and creates many actors, so do
  not call it inside ``update()``.
* Each layer is an ordinary list of actors. ``collidelist()`` finds the
  first tile the fox touches, and ``pop()`` removes a collected tile from
  the game for good.
* ``WIDTH`` and ``HEIGHT`` are worked out from the map so the window fits
  it exactly.

load_tile_map_actors
--------------------

.. function:: load_tile_map_actors(tmx_name, scale=1)

    Load ``maps/<tmx_name>`` and return a dictionary mapping each layer name
    to a list of :class:`Tile` actors, one per non-empty cell.

    :param tmx_name: File name inside ``maps/``, with or without the
        ``.tmx`` extension. Subfolders are allowed: ``"world/level2.tmx"``.
    :param scale: Multiply every tile's size and position by this number.
        With ``scale=2`` an 18-pixel tile is drawn 36 pixels wide at twice
        the coordinates. Fractions such as ``2.5`` work.
    :return: ``{"ground": [Tile, ...], "walls": [Tile, ...], ...}``

    Details that matter:

    * Layers come back in the order they appear in the file, which is the
      order Tiled draws them: the bottom layer first. A layer with no tiles
      gives an empty list. Only tile layers are loaded; object layers and
      image layers are ignored, and so are tile layers that sit inside a
      *group* layer.
    * Within a layer, tiles are listed row by row: left to right, top to
      bottom.
    * Every tile's top-left corner is placed at
      ``(column * tile_width * scale, row * tile_height * scale)``, where
      ``tile_width`` and ``tile_height`` are the **map's** tile size. The map
      starts at the top-left corner of the window; move the tiles yourself
      for a scrolling world (see :ref:`scrolling`).
    * If a tileset's tiles are a different size from the map's grid (a
      16-pixel tileset on a 32-pixel map, say), each tile is stretched to
      the map's tile size first, then ``scale`` is applied.
    * Tiles you flipped or rotated in Tiled keep their flips
      (``flip_h``, ``flip_v`` and ``flip_d``).
    * Tileset margins and spacing from the ``.tsx`` are honoured, and a map
      may use several tilesets.
    * The ``.tmx``, ``.tsx`` and tileset images are all read from ``maps/``.
      External ``.tsx`` paths are resolved relative to the ``.tmx``, and
      image paths relative to the ``.tsx``, exactly as Tiled writes them.
    * Unlike images and sounds, files under ``maps/`` are not checked for
      lowercase names, but keep them lowercase anyway so the game runs on
      every operating system.
    * Every tile gets its own copy of its picture, so a 120 x 80 map can
      mean thousands of actors per layer. That is fine for class-sized maps;
      for very big worlds, draw only the tiles that are on screen.

    Errors you may see:

    * ``KeyError: No map file found like 'level1.tmx'``: wrong name, or the
      file is not in ``maps/``.
    * ``ValueError: Layer 'ground' must use CSV encoding``: set the map's
      tile layer format to CSV in Tiled and save again.
    * ``ValueError: Tileset is missing an <image> tag``: the tileset is an
      *image collection*; the loader needs a tileset based on one image.
    * ``ValueError: Tile gid ... points past the end of tileset``: the map
      refers to a tile the tileset image does not contain, usually because
      the image was swapped for a smaller one.

Tile
----

.. class:: Tile

    The actors returned by :func:`load_tile_map_actors`. A ``Tile`` is an
    :class:`Actor` built from one cell of a tileset image, so you can draw
    it, move it, scale it and test collisions against it like any actor. You
    do not normally create tiles yourself; use the attributes and methods
    below on the ones the loader gives you. The class is not a builtin: for
    an ``isinstance`` check, ``from pgzero.tilemaps import Tile``.

    .. attribute:: map_col
                   map_row

        The cell the tile was placed in, counting from 0 at the top-left of
        the map. These are only updated by :meth:`set_map_position`, not
        when you move the tile with ``x``, ``y`` or ``pos``.

    .. attribute:: tile_col
                   tile_row

        Which picture the tile shows: its column and row inside the tileset
        image, from 0.

    .. attribute:: tile_id

        The picture's index inside its tileset
        (``tile_row * columns + tile_col``). This is the *ID* Tiled shows
        when you hover over a tile in the Tilesets panel, so it is the
        easiest way to ask "is this a spike?" in code.

    .. attribute:: tile_gid
                   tileset_firstgid

        The global id used in the ``.tmx`` file and the first gid of the
        tile's tileset. ``tile_gid == tileset_firstgid + tile_id``.

    .. attribute:: scale
                   flip_h
                   flip_v
                   flip_d

        As for any actor (:doc:`actor-additions`), set from the ``scale``
        argument and the flips saved in the map.

    .. attribute:: image

        Tiles are built from surfaces, not image files, so ``image`` is
        ``""``. Use ``tile_id`` or ``tile_gid`` to tell tiles apart.

    .. method:: set_tile_image(tile_col, tile_row)

        Swap the picture for another tile from the same tileset, keeping the
        position. Use it for doors that open, switches, or blocks that crack.
        Updates ``tile_col``, ``tile_row``, ``tile_id`` and ``tile_gid``.
        Raises ``ValueError`` if the column or row is outside the tileset
        (``tile_col must be between 0 and 19``), or if that cell is past the
        tileset's last tile.

    .. method:: set_map_position(map_col, map_row)

        Move the tile to a grid cell. The pixel position is
        ``(map_col * tile_width * scale, map_row * tile_height * scale)``
        using the tile's *current* ``scale`` and measured from the window's
        top-left corner. If you have scrolled the map this puts the tile at
        its unscrolled place.

    .. method:: copy(map_col=None, map_row=None)

        Return a new ``Tile`` with the same picture, tileset, scale and
        flips, in the same cell or in the cell given. Nothing is shared with
        the original: the copy has its own surface and position. Use it to
        stamp extra copies of a tile while the game runs.

Finding tiles
'''''''''''''

To know which cell a pixel position is in, divide by the scaled tile size;
to find the tile in a cell, search the layer::

    cell = TILE_SIZE * SCALE


    def cell_at(pos):
        x, y = pos
        return int(x // cell), int(y // cell)


    def tile_at(layer, col, row):
        for tile in layer:
            if tile.map_col == col and tile.map_row == row:
                return tile
        return None

For example, ``tile_at(platforms, *cell_at(fox.midbottom))`` is the platform
tile directly under the fox's feet, or ``None``.

Levels
''''''

To change level, load another map and replace the layer lists. Because the
lists are globals that other functions use, declare them ``global`` in the
function that reloads them::

    level_maps = ["tl1.tmx", "tl2.tmx"]


    def load_level():
        global ground, walls, hazards, collectables
        layers = load_tile_map_actors(level_maps[game.level - 1], scale=SCALE)
        ground = layers["ground"]
        walls = layers["walls"]
        hazards = layers["hazards"]
        collectables = layers["collectables"]


    def start():
        load_level()
        rabbit.pos = (200, HEIGHT / 2)


    def update():
        ...
        if len(collectables) == 0:
            if game.level < len(level_maps):
                game.next_level()
                load_level()
                rabbit.pos = (0, rabbit.y)
            else:
                game.win()

``game.level`` goes back to 1 on every restart, so ``start()`` reloads the
first map automatically.

.. _scrolling:

Scrolling
'''''''''

The loader places the map at the top-left of the window and does not know
about cameras. For a world bigger than the window, keep the player in the
middle and move every tile the opposite way::

    world = ground + walls + hazards + collectables


    def scroll(dx, dy):
        for tile in world:
            tile.x += dx
            tile.y += dy

Then, in ``update()``, test the move before you make it: move the player,
check ``collidelist(walls)``, and if nothing was hit move the player back and
``scroll()`` the world instead.

Changing tiles
''''''''''''''

Tiles are actors, so you can treat them individually. A door that opens when
the player has the key::

    door = tile_at(walls, 12, 5)


    def open_door():
        door.set_tile_image(7, 2)   # the open-door picture in the tileset
        walls.remove(door)          # no longer blocks the player
        ground.append(door)         # still drawn, as floor

And a tile stamped somewhere new::

    walls.append(door.copy(map_col=13))
