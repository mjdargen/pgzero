import math
import numbers
import os
import types
from collections.abc import Sequence

import pygame
import xml.etree.ElementTree as ET

from . import loaders
from .actor import Actor

FLIP_H = 0x80000000
FLIP_V = 0x40000000
FLIP_D = 0x20000000
GID_MASK = 0x0FFFFFFF

_NO_PROPERTIES = types.MappingProxyType({})


def _get_tile_surface(tileset, tile_col, tile_row, width, height):
    """Return the tile's image at the given size.

    Every tile of the same kind and size shares one image, so that a big map
    doesn't keep thousands of copies of the same grass tile.
    """
    surfaces = tileset.setdefault("surfaces", {})
    key = (tile_col, tile_row, width, height)
    if key not in surfaces:
        tx = tileset["margin"] + tile_col * (tileset["tile_width"] + tileset["spacing"])
        ty = tileset["margin"] + tile_row * (tileset["tile_height"] + tileset["spacing"])

        tile_rect = (tx, ty, tileset["tile_width"], tileset["tile_height"])
        tile_surface = tileset["image"].subsurface(tile_rect)

        surfaces[key] = pygame.transform.scale(tile_surface, (width, height))
    return surfaces[key]


def _check_col_row(col, row):
    """Return col and row as ints, or explain what they should be."""
    for name, value in (("col", col), ("row", row)):
        if isinstance(value, bool) or not isinstance(value, numbers.Integral):
            raise TypeError(
                f"{name} should be a whole number, like 3, not {value!r}. "
                "To find the col and row at a position in pixels, use "
                "level.pos_to_map(x, y)."
            )
    return int(col), int(row)


def _check_tile_col_row(tile_col, tile_row):
    """Return tile_col and tile_row as ints, or explain what they should be."""
    for name, value in (("tile_col", tile_col), ("tile_row", tile_row)):
        if isinstance(value, bool) or not isinstance(value, numbers.Integral):
            raise TypeError(
                f"{name} should be a whole number, like 3, not {value!r}. It is the "
                "column or row of the image in the tileset, counting from 0."
            )
    return int(tile_col), int(tile_row)


def _check_number(name, value):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(
            f"{name} should be a number, not {value!r}. For a position like "
            "pos, split it into x and y first: x, y = pos"
        )


class Tile(Actor):
    """One tile of a tile map. Each tile is an Actor, so it can be drawn,
    animated and checked for collisions like any other actor."""

    def __init__(
        self,
        tileset,
        tileset_firstgid,
        tile_col,
        tile_row,
        map_col,
        map_row,
        map_tile_width,
        map_tile_height,
        scale=1.0,
        flip_h=False,
        flip_v=False,
        flip_d=False,
        layer=None,
    ):
        self._tileset = tileset
        self._layer = layer
        self.tileset_firstgid = tileset_firstgid
        self._map_tile_width = map_tile_width
        self._map_tile_height = map_tile_height
        self._map_scale = max(0.0, scale)

        super().__init__(self._tile_surface(tile_col, tile_row))

        # Setting a flip redoes the tile's position and image, so only set the
        # flips that are used; most tiles in a map have none.
        if flip_h:
            self.flip_h = flip_h
        if flip_v:
            self.flip_v = flip_v
        if flip_d:
            self.flip_d = flip_d

        self._place(map_col, map_row)

    def __repr__(self):
        return "<Tile map_col={} map_row={} tile_col={} tile_row={}>".format(
            self.map_col, self.map_row, self.tile_col, self.tile_row
        )

    @property
    def scale(self):
        return self._map_scale

    @scale.setter
    def scale(self, scale):
        # Rather than scaling its own copy of its image like other Actors, a
        # tile uses the shared image for its kind of tile at the new size.
        self._map_scale = max(0.0, scale)
        self._set_image(self._tile_surface(self.tile_col, self.tile_row))

    @property
    def properties(self):
        """The custom properties given to this kind of tile in Tiled."""
        props = self._tileset.get("properties", {}).get(self.tile_id)
        if props is None:
            return _NO_PROPERTIES
        return types.MappingProxyType(props)

    def set_tile_image(self, tile_col, tile_row):
        self.image = self._tile_surface(tile_col, tile_row)

    def _tile_surface(self, tile_col, tile_row):
        """Check (tile_col, tile_row), record the tile ids and return the tile's surface."""
        columns = self._tileset["columns"]
        rows = self._tileset["rows"]
        tile_count = self._tileset["tile_count"]

        if tile_col < 0 or tile_col >= columns:
            raise ValueError(f"tile_col must be between 0 and {columns - 1}")

        if tile_row < 0 or tile_row >= rows:
            raise ValueError(f"tile_row must be between 0 and {rows - 1}")

        tile_id = tile_row * columns + tile_col

        if tile_id >= tile_count:
            raise ValueError(f"tile_col={tile_col}, tile_row={tile_row} points past the tileset's last tile.")

        self.tile_col = tile_col
        self.tile_row = tile_row
        self.tile_id = tile_id
        self.tile_gid = self.tileset_firstgid + self.tile_id

        return _get_tile_surface(
            self._tileset,
            tile_col,
            tile_row,
            max(1, round(self._map_tile_width * self._map_scale)),
            max(1, round(self._map_tile_height * self._map_scale)),
        )

    def set_map_position(self, map_col, map_row):
        """Move the tile to another square of the map. In a layer, this
        replaces any tile already in that square."""
        if self._layer is not None:
            self._layer._put(self, map_col, map_row)
        else:
            self._place(map_col, map_row)

    def _place(self, map_col, map_row):
        """Record the tile's square and put it there on the screen."""
        self.map_col = map_col
        self.map_row = map_row

        if self._layer is not None:
            # Use the map's grid, even if this one tile has been scaled.
            tile_map = self._layer._map
            origin_x, origin_y = tile_map.x, tile_map.y
            width, height = tile_map.tile_width, tile_map.tile_height
        else:
            origin_x = origin_y = 0
            width = self._map_tile_width * self.scale
            height = self._map_tile_height * self.scale

        self.topleft = (origin_x + width * map_col, origin_y + height * map_row)

    def copy(self, map_col=None, map_row=None):
        """Return a new tile like this one that isn't in any layer."""
        if map_col is None:
            map_col = self.map_col

        if map_row is None:
            map_row = self.map_row

        return Tile(
            tileset=self._tileset,
            tileset_firstgid=self.tileset_firstgid,
            tile_col=self.tile_col,
            tile_row=self.tile_row,
            map_col=map_col,
            map_row=map_row,
            map_tile_width=self._map_tile_width,
            map_tile_height=self._map_tile_height,
            scale=self.scale,
            flip_h=self.flip_h,
            flip_v=self.flip_v,
            flip_d=self.flip_d,
        )


class TileLayer(Sequence):
    """One layer of a tile map.

    A layer works like a list of its tiles, so ``player.collidelist(walls)``,
    ``walls[i]``, ``walls.pop(i)`` and ``for wall in walls`` all work. Each
    square of the map holds at most one tile per layer, which
    ``get_tile(col, row)``, ``set_tile(col, row, tile)`` and
    ``remove_tile(col, row)`` use.
    """

    def __init__(self, tile_map, name, visible=True):
        self._map = tile_map
        self._tiles = {}  # (map_col, map_row): Tile, in drawing order
        self.name = name
        self.visible = visible

    def __repr__(self):
        return "<TileLayer {!r} with {} tiles>".format(self.name, len(self._tiles))

    # Working like a list of tiles

    def __len__(self):
        return len(self._tiles)

    def __getitem__(self, index):
        return list(self._tiles.values())[index]

    def __iter__(self):
        # Loop over a copy, so tiles can be removed in the middle of a loop.
        return iter(list(self._tiles.values()))

    def __contains__(self, tile):
        return isinstance(tile, Tile) and tile._layer is self

    def __reversed__(self):
        return reversed(list(self._tiles.values()))

    def index(self, tile, *args):
        return list(self._tiles.values()).index(tile, *args)

    def count(self, tile):
        return 1 if tile in self else 0

    def __add__(self, other):
        return list(self) + list(other)

    def __radd__(self, other):
        return list(other) + list(self)

    def pop(self, index=-1):
        """Remove the tile at index and return it, like list.pop()."""
        if not self._tiles:
            raise IndexError("pop from empty layer {!r}".format(self.name))
        tile = self[index]
        self._take(tile)
        return tile

    def remove(self, tile):
        """Remove tile from the layer, like list.remove()."""
        if tile not in self:
            raise ValueError("{!r} is not in layer {!r}".format(tile, self.name))
        self._take(tile)

    def append(self, tile):
        """Add tile to the layer at its map_col and map_row, replacing any
        tile already in that square."""
        if not isinstance(tile, Tile):
            raise TypeError("Only tiles can be added to a layer, not {!r}".format(tile))
        self._put(tile, tile.map_col, tile.map_row)

    def clear(self):
        """Remove every tile from the layer."""
        for tile in self._tiles.values():
            tile._layer = None
        self._tiles.clear()

    # Squares of the map

    def get_tile(self, col, row):
        """Return the tile in the square at col, row, or None if it is empty."""
        return self._tiles.get(_check_col_row(col, row))

    def set_tile(self, col, row, tile):
        """Put tile in the square at col, row, replacing any tile already
        there. Make the tile with level.create_tile(). Returns the tile."""
        if not isinstance(tile, Tile):
            raise TypeError(
                "set_tile() needs a tile, like "
                "walls.set_tile(col, row, level.create_tile(tile_col, tile_row)), not {!r}".format(tile)
            )
        self._put(tile, col, row)
        return tile

    def remove_tile(self, col, row):
        """Remove the tile in the square at col, row, if there is one.
        Returns the removed tile, or None if the square was empty."""
        tile = self._tiles.get(_check_col_row(col, row))
        if tile is not None:
            self._take(tile)
        return tile

    def draw(self):
        """Draw the layer's tiles, unless the layer is hidden."""
        if not self.visible:
            return
        from . import game

        if game.screen is None:
            for tile in self._tiles.values():
                tile.draw()
            return

        # A big map has thousands of tiles, most of them off the screen. Skip
        # those here, without calling draw(), using where each tile's image
        # was drawn last time compared to its rect (Actor.draw() saves this).
        # That covers images bigger than the rect, from rotation or a small
        # collision_rect. Tiles not drawn yet, or whose size has changed since,
        # go to Actor.draw(), which works it out again.
        width, height = game.screen.get_size()
        for tile in self._tiles.values():
            offset = tile._draw_offset
            r = tile._rect
            if offset is not None and offset[4] == r.w and offset[5] == r.h:
                x = r.x + offset[0]
                y = r.y + offset[1]
                if x >= width or y >= height or x + offset[2] <= 0 or y + offset[3] <= 0:
                    continue
            tile.draw()

    # Bookkeeping

    def _take(self, tile):
        del self._tiles[(tile.map_col, tile.map_row)]
        tile._layer = None

    def _put(self, tile, col, row):
        """Put tile in the square at col, row, replacing what is there."""
        col, row = _check_col_row(col, row)
        self._map._check_on_map(col, row)

        if tile._layer is not None:
            tile._layer._take(tile)
        old_tile = self._tiles.pop((col, row), None)
        if old_tile is not None:
            old_tile._layer = None

        tile._layer = self
        tile._place(col, row)
        self._tiles[(col, row)] = tile

    def _shift(self, dx, dy):
        # Scrolling moves every tile, so move their rects directly instead of
        # going through Actor.x and Actor.y, which is many times slower.
        for tile in self._tiles.values():
            r = tile._rect
            r.x += dx
            r.y += dy


class TileMap(dict):
    """A map loaded from Tiled: a dictionary from each layer's name to its
    layer, in the order Tiled draws them."""

    def __init__(self, name, map_tile_width, map_tile_height, scale=1, width=0, height=0, tilesets=None):
        super().__init__()
        self._name = name
        self._tilesets = tilesets if tilesets is not None else {}
        self._scale = scale
        self.width = width
        self.height = height
        self._map_tile_width = map_tile_width
        self._map_tile_height = map_tile_height
        self._x = 0
        self._y = 0

    def __repr__(self):
        return "<TileMap {!r} with layers {}>".format(self._name, list(self))

    def __missing__(self, key):
        raise KeyError(
            "{!r} has no layer named {!r}. Its layers are: {}".format(self._name, key, ", ".join(map(repr, self)))
        )

    @property
    def layers(self):
        """The layers, in the order they are drawn."""
        return list(self.values())

    @property
    def tile_width(self):
        """The width of one square of the map on the screen, in pixels."""
        return self._map_tile_width * self._scale

    @property
    def tile_height(self):
        """The height of one square of the map on the screen, in pixels."""
        return self._map_tile_height * self._scale

    @property
    def x(self):
        """How far the map has been scrolled right, in pixels."""
        return self._x

    @x.setter
    def x(self, x):
        self._scroll(x - self._x, 0)

    @property
    def y(self):
        """How far the map has been scrolled down, in pixels."""
        return self._y

    @y.setter
    def y(self, y):
        self._scroll(0, y - self._y)

    def _scroll(self, dx, dy):
        """Move the whole map by dx, dy pixels, in one pass over its tiles."""
        if not dx and not dy:
            return
        self._x += dx
        self._y += dy
        for layer in self.values():
            layer._shift(dx, dy)

    def pos_to_map(self, x, y=None):
        """Return the col and row of the square at a position in pixels."""
        if y is None:
            raise TypeError(
                "pos_to_map() needs x and y as two numbers, like "
                "level.pos_to_map(x, y). For a position like pos, write: x, y = pos"
            )
        _check_number("x", x)
        _check_number("y", y)
        return (
            math.floor((x - self._x) / self.tile_width),
            math.floor((y - self._y) / self.tile_height),
        )

    def map_to_pos(self, col, row):
        """Return the x and y, in pixels, of the center of the square at col, row."""
        col, row = _check_col_row(col, row)
        return (
            self._x + (col + 0.5) * self.tile_width,
            self._y + (row + 0.5) * self.tile_height,
        )

    def follow(self, actor, others=()):
        """Scroll the map so that actor is in the middle of the screen.

        Call it after moving the actor. The map stops scrolling at its edges,
        so the actor walks towards the edge of the screen instead. The actor,
        and every Actor in the list others, move with the map, so they stay
        in the same place in the world.

        Returns how far everything moved, as x, y.
        """
        from . import game

        if game.screen is None:
            raise RuntimeError(
                "level.follow() needs the game window, so call it in start() or update(), "
                "not at the top of your program."
            )
        if isinstance(others, Actor):
            others = [others]

        screen_width, screen_height = game.screen.get_size()
        dx = self._follow_shift(actor.x, self._x, self.width * self.tile_width, screen_width)
        dy = self._follow_shift(actor.y, self._y, self.height * self.tile_height, screen_height)

        if dx or dy:
            self._scroll(dx, dy)
            for thing in [actor, *others]:
                thing.x += dx
                thing.y += dy
        return dx, dy

    @staticmethod
    def _follow_shift(pos, map_pos, map_size, screen_size):
        """How far to move along one direction to put pos in the middle of the
        screen without showing past the map's edges."""
        if map_size <= screen_size:
            # The whole map fits on the screen, so keep it in the middle.
            return (screen_size - map_size) / 2 - map_pos
        shift = screen_size / 2 - pos
        shift = min(shift, -map_pos)  # the map's left/top edge can't come onto the screen
        shift = max(shift, screen_size - (map_pos + map_size))  # nor its right/bottom edge
        return shift

    def draw(self):
        """Draw every visible layer, in order."""
        for layer in self.values():
            layer.draw()

    def create_tile(self, tile_col, tile_row, tileset=None):
        """Return a new tile showing the image at tile_col, tile_row of the
        tileset. It isn't on the map until you put it there with
        layer.set_tile(col, row, tile).

        tileset is the tileset's name in Tiled. It can be left out if the
        map has only one tileset.
        """
        tile_col, tile_row = _check_tile_col_row(tile_col, tile_row)
        firstgid = self._find_tileset(tileset)
        return self._new_tile(None, self._tilesets[firstgid], firstgid, tile_col, tile_row, 0, 0)

    def _find_tileset(self, name):
        """Return the firstgid of the tileset called name, or of the map's
        only tileset if name is None."""
        names = [ts["name"] for ts in self._tilesets.values()]
        if name is None:
            if len(self._tilesets) == 1:
                return next(iter(self._tilesets))
            raise ValueError(
                "This map has more than one tileset, so say which one to use, e.g. "
                "level.create_tile(tile_col, tile_row, tileset={!r}). Its tilesets are: {}".format(
                    names[0], ", ".join(map(repr, names))
                )
            )
        for firstgid, ts in self._tilesets.items():
            if ts["name"] == name:
                return firstgid
        raise ValueError(
            "There is no tileset named {!r}. This map's tilesets are: {}".format(name, ", ".join(map(repr, names)))
        )

    def _check_on_map(self, col, row):
        if self.width and not 0 <= col < self.width or self.height and not 0 <= row < self.height:
            raise ValueError(
                f"col {col}, row {row} is off the map. This map is {self.width} "
                f"squares wide and {self.height} tall, so col goes from 0 to "
                f"{self.width - 1} and row from 0 to {self.height - 1}."
            )

    def _new_tile(self, layer, tileset, firstgid, tile_col, tile_row, col, row, flip_h=False, flip_v=False, flip_d=False):
        return Tile(
            tileset=tileset,
            tileset_firstgid=firstgid,
            tile_col=tile_col,
            tile_row=tile_row,
            map_col=col,
            map_row=row,
            map_tile_width=self._map_tile_width,
            map_tile_height=self._map_tile_height,
            scale=self._scale,
            flip_h=flip_h,
            flip_v=flip_v,
            flip_d=flip_d,
            layer=layer,
        )


def _load_xml_from_maps(name):
    text = loaders.maps.load(name)
    return ET.fromstring(text)


def _resolve_relative_map_path(base_name, relative_path):
    base_dir = os.path.dirname(base_name)
    if base_dir:
        return os.path.normpath(os.path.join(base_dir, relative_path)).replace("\\", "/")
    return relative_path


def _read_properties(element):
    """Return the custom properties Tiled saved on element as a dict."""
    props = {}
    properties = element.find("properties")
    if properties is None:
        return props

    for prop in properties.findall("property"):
        name = prop.attrib["name"]
        kind = prop.attrib.get("type", "string")

        if kind == "class":
            props[name] = _read_properties(prop)
            continue

        # Text with several lines is saved inside the tag instead of in value.
        value = prop.attrib.get("value")
        if value is None:
            value = prop.text or ""

        if kind == "int":
            value = int(value)
        elif kind == "float":
            value = float(value)
        elif kind == "bool":
            value = value == "true"
        props[name] = value

    return props


def _count_tiles_that_fit(image_length, tile_length, margin, spacing):
    """
    Count how many tiles fit in one direction of a Tiled tileset image.

    In Tiled, margin is the offset from the top/left edge to the first tile.
    It is not necessarily repeated on the far right/bottom edge. Any extra
    pixels after the final tile are just unused image space.
    """
    if tile_length <= 0:
        raise ValueError("tile_length must be greater than 0")

    if margin < 0:
        raise ValueError("margin cannot be negative")

    if spacing < 0:
        raise ValueError("spacing cannot be negative")

    usable_length = image_length - margin
    if usable_length < tile_length:
        return 0

    return (usable_length + spacing) // (tile_length + spacing)


def _load_tilesets(root, tmx_name):
    tilesets = {}

    for ts in root.findall("tileset"):
        firstgid = int(ts.attrib["firstgid"])

        if "source" in ts.attrib:
            tsx_name = _resolve_relative_map_path(tmx_name, ts.attrib["source"])
            ts_root = _load_xml_from_maps(tsx_name)
            tileset_base_name = tsx_name
        else:
            ts_root = ts
            tileset_base_name = tmx_name

        image = ts_root.find("image")
        if image is None:
            raise ValueError("Tileset is missing an <image> tag")

        # For external TSX files, the image path is relative to the TSX file,
        # not necessarily the TMX map that imports it.
        image_name = _resolve_relative_map_path(tileset_base_name, image.attrib["source"])
        tilesheet = loaders.mapimages.load(image_name)

        tile_width = int(ts_root.attrib["tilewidth"])
        tile_height = int(ts_root.attrib["tileheight"])
        spacing = int(ts_root.attrib.get("spacing", 0))
        margin = int(ts_root.attrib.get("margin", 0))

        calculated_columns = _count_tiles_that_fit(
            tilesheet.get_width(),
            tile_width,
            margin,
            spacing,
        )
        calculated_rows = _count_tiles_that_fit(
            tilesheet.get_height(),
            tile_height,
            margin,
            spacing,
        )

        # Tiled writes columns and tilecount into image-based TSX tilesets.
        # Use values when present because they exactly describe how Tiled
        # assigned local tile ids. Fall back to image-based calculation for
        # older or hand-written files.
        columns = int(ts_root.attrib.get("columns", calculated_columns))
        if columns <= 0:
            columns = calculated_columns

        if columns <= 0:
            raise ValueError("Tileset does not contain any columns of tiles")

        tile_count = int(ts_root.attrib.get("tilecount", columns * calculated_rows))
        rows = (tile_count + columns - 1) // columns

        if tile_count <= 0:
            raise ValueError("Tileset does not contain any tiles")

        tile_properties = {}
        for tile in ts_root.findall("tile"):
            props = _read_properties(tile)
            if props:
                tile_properties[int(tile.attrib["id"])] = props

        name = ts_root.attrib.get("name") or ts.attrib.get("name")
        if not name:
            name = os.path.splitext(os.path.basename(image_name))[0]

        tilesets[firstgid] = {
            "name": name,
            "image": tilesheet,
            "image_name": image_name,
            "tile_width": tile_width,
            "tile_height": tile_height,
            "columns": columns,
            "rows": rows,
            "tile_count": tile_count,
            # Keep these aliases so older student code that checks sheet_w or
            # sheet_h does not immediately break.
            "sheet_w": columns,
            "sheet_h": rows,
            "spacing": spacing,
            "margin": margin,
            "properties": tile_properties,
        }

    return tilesets


def _tile_layers(element, visible=True):
    """Yield (layer, visible) for the tile layers in element, including those
    inside groups. A layer in a hidden group is hidden too."""
    for child in element:
        child_visible = visible and child.attrib.get("visible", "1") != "0"
        if child.tag == "layer":
            yield child, child_visible
        elif child.tag == "group":
            yield from _tile_layers(child, child_visible)


def load_tile_map_actors(tmx_name, scale=1):
    """
    Load a Tiled TMX map into a TileMap: a dict of
        {layer_name: TileLayer}
    where each layer works like a list of tile Actors.

    The TMX/TSX/image files are loaded through pgzero loaders from the maps folder.
    """
    root = _load_xml_from_maps(tmx_name)

    orientation = root.attrib.get("orientation", "orthogonal")
    if orientation != "orthogonal":
        raise ValueError(
            f"{tmx_name!r} is an {orientation} map. Only orthogonal maps, "
            "where the tiles are laid out in a square grid, are supported."
        )
    if root.attrib.get("infinite") == "1":
        raise ValueError(
            f"{tmx_name!r} is an infinite map, which isn't supported. In Tiled, "
            "open Map > Map Properties, untick Infinite, and save the map again."
        )

    tilesets = _load_tilesets(root, tmx_name)

    tile_map = TileMap(
        name=tmx_name,
        map_tile_width=int(root.attrib["tilewidth"]),
        map_tile_height=int(root.attrib["tileheight"]),
        scale=max(0.0, scale),
        width=int(root.attrib.get("width", 0)),
        height=int(root.attrib.get("height", 0)),
        tilesets=tilesets,
    )

    for layer, visible in _tile_layers(root):
        name = layer.attrib["name"]
        if name in tile_map:
            raise ValueError(
                f"{tmx_name!r} has more than one layer named {name!r}. "
                "Give each layer a different name in Tiled."
            )
        width = int(layer.attrib["width"])
        height = int(layer.attrib["height"])

        map_layer = TileLayer(tile_map, name, visible=visible)
        tile_map[name] = map_layer

        data = layer.find("data")
        if data is None or data.text is None:
            continue

        encoding = data.attrib.get("encoding")
        if encoding != "csv":
            raise ValueError(f"Layer '{name}' must use CSV encoding. Found: {encoding!r}")

        gids = [int(v) for v in data.text.split(",") if v.strip()]

        for row in range(height):
            for col in range(width):
                tile_gid = gids[row * width + col]
                if tile_gid == 0:
                    continue

                flipped_h = bool(tile_gid & FLIP_H)
                flipped_v = bool(tile_gid & FLIP_V)
                flipped_d = bool(tile_gid & FLIP_D)
                tile_gid &= GID_MASK

                ts_firstgid = max(gid for gid in tilesets if gid <= tile_gid)
                tileset = tilesets[ts_firstgid]
                local_id = tile_gid - ts_firstgid

                if local_id >= tileset["tile_count"]:
                    raise ValueError(
                        f"Tile gid {tile_gid} points past the end of tileset " f"starting at firstgid {ts_firstgid}."
                    )

                map_layer._tiles[(col, row)] = tile_map._new_tile(
                    map_layer,
                    tileset,
                    ts_firstgid,
                    local_id % tileset["columns"],
                    local_id // tileset["columns"],
                    col,
                    row,
                    flipped_h,
                    flipped_v,
                    flipped_d,
                )

    return tile_map
