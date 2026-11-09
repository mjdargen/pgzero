"""Tests for loading Tiled (.tmx/.tsx) maps into Tile actors.

Fixtures live in ``maps/``:

* ``tiles.png`` - 3x2 tiles of 8x8 pixels with margin=1 and spacing=2. Each
  tile is filled with ``(col * 100, row * 200, 77)`` and has a white
  top-left pixel so that flips can be detected.
* ``tilesets/extra.tsx`` + ``tilesets/extra.png`` - an external tileset of
  2x1 tiles whose image path is relative to the TSX file.
* ``level.tmx`` - a 4x2 map of 16x16 tiles using both tilesets, with
  flipped tiles, an empty cell, and an empty layer.
* ``base64_layer.tmx`` / ``bad_gid.tmx`` - invalid maps.

"""
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

import pygame

from pgzero import loaders
from pgzero.actor import Actor
from pgzero.loaders import set_root
from pgzero.tilemaps import (
    FLIP_D,
    FLIP_H,
    FLIP_V,
    GID_MASK,
    Tile,
    TileMap,
    TileLayer,
    _count_tiles_that_fit,
    _load_tilesets,
    _resolve_relative_map_path,
    load_tile_map_actors,
)

WHITE = (255, 255, 255, 255)


def tile_color(col, row):
    return (col * 100, row * 200, 77, 255)


class TilemapTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 200))
        set_root(__file__)

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()


class HelperFunctionTest(unittest.TestCase):
    def test_flag_constants(self):
        """The flip flags match the bits Tiled writes into gids."""
        self.assertEqual(FLIP_H, 1 << 31)
        self.assertEqual(FLIP_V, 1 << 30)
        self.assertEqual(FLIP_D, 1 << 29)
        self.assertEqual(GID_MASK & (FLIP_H | FLIP_V | FLIP_D), 0)

    def test_count_tiles_no_margin_or_spacing(self):
        self.assertEqual(_count_tiles_that_fit(64, 16, 0, 0), 4)

    def test_count_tiles_ignores_leftover_pixels(self):
        self.assertEqual(_count_tiles_that_fit(70, 16, 0, 0), 4)

    def test_count_tiles_with_margin_and_spacing(self):
        # 1 + 8 + 2 + 8 + 2 + 8 = 29, plus one unused trailing pixel.
        self.assertEqual(_count_tiles_that_fit(30, 8, 1, 2), 3)
        self.assertEqual(_count_tiles_that_fit(20, 8, 1, 2), 2)

    def test_count_tiles_margin_not_required_on_far_edge(self):
        self.assertEqual(_count_tiles_that_fit(29, 8, 1, 2), 3)

    def test_count_tiles_image_too_small(self):
        self.assertEqual(_count_tiles_that_fit(7, 8, 0, 0), 0)
        self.assertEqual(_count_tiles_that_fit(8, 8, 1, 0), 0)

    def test_count_tiles_invalid_arguments(self):
        with self.assertRaises(ValueError):
            _count_tiles_that_fit(64, 0, 0, 0)
        with self.assertRaises(ValueError):
            _count_tiles_that_fit(64, 16, -1, 0)
        with self.assertRaises(ValueError):
            _count_tiles_that_fit(64, 16, 0, -1)

    def test_resolve_path_without_directory(self):
        self.assertEqual(
            _resolve_relative_map_path("level.tmx", "tiles.png"),
            "tiles.png",
        )

    def test_resolve_path_relative_to_subdirectory(self):
        self.assertEqual(
            _resolve_relative_map_path("tilesets/extra.tsx", "extra.png"),
            "tilesets/extra.png",
        )

    def test_resolve_path_with_parent_reference(self):
        self.assertEqual(
            _resolve_relative_map_path("tilesets/extra.tsx", "../tiles.png"),
            "tiles.png",
        )


class LoadTilesetsTest(TilemapTestBase):
    def load(self, xml, tmx_name="test.tmx"):
        return _load_tilesets(ET.fromstring(xml), tmx_name)

    def test_embedded_tileset(self):
        tilesets = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1" tilecount="6" columns="3">
              <image source="tiles.png"/>
             </tileset>
            </map>
        """)
        self.assertEqual(list(tilesets), [1])
        ts = tilesets[1]
        self.assertEqual(ts["image_name"], "tiles.png")
        self.assertEqual(ts["image"].get_size(), (30, 20))
        self.assertEqual((ts["tile_width"], ts["tile_height"]), (8, 8))
        self.assertEqual((ts["columns"], ts["rows"]), (3, 2))
        self.assertEqual(ts["tile_count"], 6)
        self.assertEqual((ts["margin"], ts["spacing"]), (1, 2))

    def test_legacy_aliases(self):
        """sheet_w / sheet_h are kept for older student code."""
        ts = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1">
              <image source="tiles.png"/>
             </tileset>
            </map>
        """)[1]
        self.assertEqual(ts["sheet_w"], ts["columns"])
        self.assertEqual(ts["sheet_h"], ts["rows"])

    def test_columns_and_count_calculated_when_missing(self):
        ts = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1">
              <image source="tiles.png"/>
             </tileset>
            </map>
        """)[1]
        self.assertEqual((ts["columns"], ts["rows"]), (3, 2))
        self.assertEqual(ts["tile_count"], 6)

    def test_zero_columns_falls_back_to_calculation(self):
        ts = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1" columns="0">
              <image source="tiles.png"/>
             </tileset>
            </map>
        """)[1]
        self.assertEqual(ts["columns"], 3)

    def test_tilecount_controls_rows(self):
        """A partial final row is still counted as a row."""
        ts = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1" columns="3" tilecount="4">
              <image source="tiles.png"/>
             </tileset>
            </map>
        """)[1]
        self.assertEqual(ts["tile_count"], 4)
        self.assertEqual(ts["rows"], 2)

    def test_defaults_margin_and_spacing_to_zero(self):
        ts = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8">
              <image source="tilesets/extra.png"/>
             </tileset>
            </map>
        """)[1]
        self.assertEqual((ts["margin"], ts["spacing"]), (0, 0))
        self.assertEqual((ts["columns"], ts["rows"]), (2, 1))

    def test_external_tileset_image_relative_to_tsx(self):
        ts = self.load("""
            <map>
             <tileset firstgid="5" source="tilesets/extra.tsx"/>
            </map>
        """)[5]
        self.assertEqual(ts["image_name"], "tilesets/extra.png")
        self.assertEqual(ts["tile_count"], 2)

    def test_external_tileset_relative_to_tmx_directory(self):
        """The TSX path is resolved relative to the TMX file's directory."""
        ts = self.load(
            '<map><tileset firstgid="1" source="extra.tsx"/></map>',
            tmx_name="tilesets/some_map.tmx",
        )[1]
        self.assertEqual(ts["image_name"], "tilesets/extra.png")

    def test_multiple_tilesets(self):
        tilesets = self.load("""
            <map>
             <tileset firstgid="1" tilewidth="8" tileheight="8"
                      spacing="2" margin="1">
              <image source="tiles.png"/>
             </tileset>
             <tileset firstgid="7" source="tilesets/extra.tsx"/>
            </map>
        """)
        self.assertEqual(sorted(tilesets), [1, 7])

    def test_missing_image(self):
        with self.assertRaisesRegex(ValueError, "missing an <image>"):
            self.load("""
                <map>
                 <tileset firstgid="1" tilewidth="8" tileheight="8"/>
                </map>
            """)

    def test_tiles_bigger_than_image(self):
        with self.assertRaisesRegex(ValueError, "any columns"):
            self.load("""
                <map>
                 <tileset firstgid="1" tilewidth="64" tileheight="64">
                  <image source="tiles.png"/>
                 </tileset>
                </map>
            """)

    def test_zero_tilecount(self):
        with self.assertRaisesRegex(ValueError, "any tiles"):
            self.load("""
                <map>
                 <tileset firstgid="1" tilewidth="8" tileheight="8"
                          spacing="2" margin="1" tilecount="0">
                  <image source="tiles.png"/>
                 </tileset>
                </map>
            """)


class LoadTileMapActorsTest(TilemapTestBase):
    def setUp(self):
        self.layers = load_tile_map_actors("level")
        self.ground = self.layers["ground"]

    def by_cell(self):
        return {(t.map_col, t.map_row): t for t in self.ground}

    def test_layers(self):
        self.assertEqual(sorted(self.layers), ["empty", "ground"])

    def test_empty_layer(self):
        self.assertEqual(len(self.layers["empty"]), 0)
        self.assertEqual(list(self.layers["empty"]), [])

    def test_empty_cells_are_skipped(self):
        self.assertEqual(len(self.ground), 7)
        self.assertNotIn((1, 0), self.by_cell())

    def test_tiles_are_actors(self):
        from pgzero.actor import Actor
        for t in self.ground:
            self.assertIsInstance(t, Tile)
            self.assertIsInstance(t, Actor)

    def test_row_major_order(self):
        self.assertEqual(
            [(t.map_col, t.map_row) for t in self.ground],
            [(0, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
        )

    def test_positions(self):
        for t in self.ground:
            self.assertEqual(t.topleft, (t.map_col * 16, t.map_row * 16))
            self.assertEqual((t.width, t.height), (16, 16))

    def test_tiles_scaled_to_map_tile_size(self):
        """8x8 tileset tiles are stretched to the map's 16x16 grid."""
        t = self.by_cell()[0, 0]
        self.assertEqual(t._orig_surf.get_size(), (16, 16))

    def test_tile_ids(self):
        cells = self.by_cell()
        expected = {
            # cell: (firstgid, col, row, id, gid)
            (0, 0): (1, 0, 0, 0, 1),
            (2, 0): (1, 2, 1, 5, 6),
            (3, 0): (1, 0, 1, 3, 4),
            (0, 1): (1, 1, 0, 1, 2),
            (1, 1): (1, 2, 0, 2, 3),
            (2, 1): (7, 1, 0, 1, 8),
            (3, 1): (7, 0, 0, 0, 7),
        }
        for cell, values in expected.items():
            t = cells[cell]
            self.assertEqual(
                (t.tileset_firstgid, t.tile_col, t.tile_row,
                 t.tile_id, t.tile_gid),
                values,
                cell,
            )

    def test_tile_pixels(self):
        t = self.by_cell()[2, 0]
        self.assertEqual(tuple(t._orig_surf.get_at((8, 8))), tile_color(2, 1))
        self.assertEqual(tuple(t._orig_surf.get_at((0, 0))), WHITE)

    def test_margin_and_spacing_respected(self):
        """No tile should pick up the transparent margin/spacing pixels."""
        for t in self.ground:
            if t.tileset_firstgid != 1:
                continue
            surf = t._orig_surf
            for x in range(16):
                for y in range(16):
                    self.assertEqual(surf.get_at((x, y)).a, 255)

    def test_external_tileset_pixels(self):
        cells = self.by_cell()
        self.assertEqual(tuple(cells[3, 1]._orig_surf.get_at((4, 4))),
                         (10, 20, 30, 255))
        self.assertEqual(tuple(cells[2, 1]._orig_surf.get_at((4, 4))),
                         (40, 50, 60, 255))

    def test_flip_flags(self):
        cells = self.by_cell()
        flips = {
            cell: (t.flip_h, t.flip_v, t.flip_d) for cell, t in cells.items()
        }
        self.assertEqual(flips[0, 0], (False, False, False))
        self.assertEqual(flips[0, 1], (True, False, False))
        self.assertEqual(flips[1, 1], (False, True, False))
        self.assertEqual(flips[3, 0], (False, False, True))

    def test_flipped_tiles_are_drawn_flipped(self):
        cells = self.by_cell()
        h = cells[0, 1]._build_transformed_surf()
        self.assertEqual(tuple(h.get_at((15, 0))), WHITE)
        self.assertNotEqual(tuple(h.get_at((0, 0))), WHITE)

        v = cells[1, 1]._build_transformed_surf()
        self.assertEqual(tuple(v.get_at((0, 15))), WHITE)
        self.assertNotEqual(tuple(v.get_at((0, 0))), WHITE)

        # A diagonal flip (transpose) leaves the top-left corner in place.
        d = cells[3, 0]._build_transformed_surf()
        self.assertEqual(tuple(d.get_at((0, 0))), WHITE)

    def test_flipped_tiles_keep_grid_position(self):
        cells = self.by_cell()
        for cell in [(0, 1), (1, 1), (3, 0)]:
            t = cells[cell]
            self.assertEqual(t.topleft, (cell[0] * 16, cell[1] * 16))

    def test_scale(self):
        ground = load_tile_map_actors("level", scale=2)["ground"]
        for t in ground:
            self.assertEqual(t.scale, 2)
            self.assertEqual((t.width, t.height), (32, 32))
            self.assertEqual(t.topleft, (t.map_col * 32, t.map_row * 32))

    def test_load_with_extension(self):
        layers = load_tile_map_actors("level.tmx")
        self.assertEqual(len(layers["ground"]), 7)

    def test_missing_map(self):
        with self.assertRaises(KeyError):
            load_tile_map_actors("no_such_map")

    def test_non_csv_layer(self):
        with self.assertRaisesRegex(ValueError, "CSV encoding"):
            load_tile_map_actors("base64_layer")

    def test_gid_past_end_of_tileset(self):
        with self.assertRaisesRegex(ValueError, "points past the end"):
            load_tile_map_actors("bad_gid")


class TileTest(TilemapTestBase):
    def setUp(self):
        ground = load_tile_map_actors("level")["ground"]
        self.tile = ground[0]  # gid 1, cell (0, 0)
        self.tileset = self.tile._tileset

    def make_tile(self, **kwargs):
        args = dict(
            tileset=self.tileset,
            tileset_firstgid=1,
            tile_col=0,
            tile_row=0,
            map_col=0,
            map_row=0,
            map_tile_width=16,
            map_tile_height=16,
        )
        args.update(kwargs)
        return Tile(**args)

    def test_construct_directly(self):
        t = self.make_tile(tile_col=1, tile_row=1, map_col=2, map_row=3)
        self.assertEqual(t.tile_id, 4)
        self.assertEqual(t.tile_gid, 5)
        self.assertEqual(t.topleft, (32, 48))

    def test_invalid_tile_col(self):
        with self.assertRaisesRegex(ValueError, "tile_col"):
            self.make_tile(tile_col=3)
        with self.assertRaisesRegex(ValueError, "tile_col"):
            self.make_tile(tile_col=-1)

    def test_invalid_tile_row(self):
        with self.assertRaisesRegex(ValueError, "tile_row"):
            self.make_tile(tile_row=2)

    def test_tile_past_tile_count(self):
        """Cells in a partial last row of the tileset are rejected."""
        tileset = dict(self.tileset, tile_count=4)
        with self.assertRaisesRegex(ValueError, "past the tileset"):
            self.make_tile(tileset=tileset, tile_col=1, tile_row=1)

    def test_set_tile_image(self):
        t = self.tile
        t.set_tile_image(2, 1)
        self.assertEqual((t.tile_col, t.tile_row), (2, 1))
        self.assertEqual(t.tile_id, 5)
        self.assertEqual(t.tile_gid, 6)
        self.assertEqual(tuple(t._orig_surf.get_at((8, 8))),
                         tile_color(2, 1))
        self.assertEqual(t.topleft, (0, 0))

    def test_set_tile_image_invalid_leaves_tile_unchanged(self):
        t = self.tile
        with self.assertRaises(ValueError):
            t.set_tile_image(5, 0)
        self.assertEqual((t.tile_col, t.tile_row, t.tile_gid), (0, 0, 1))

    def test_set_map_position(self):
        t = self.tile
        t.set_map_position(3, 1)
        self.assertEqual((t.map_col, t.map_row), (3, 1))
        self.assertEqual(t.topleft, (48, 16))

    def test_set_map_position_scaled(self):
        t = self.make_tile(scale=2)
        t.set_map_position(1, 2)
        self.assertEqual(t.topleft, (32, 64))

    def test_copy(self):
        t = self.make_tile(tile_col=2, tile_row=1, map_col=1, map_row=1,
                           scale=2, flip_h=True, flip_v=True, flip_d=True)
        c = t.copy()
        self.assertIsNot(c, t)
        for attr in ("tile_col", "tile_row", "tile_id", "tile_gid",
                     "tileset_firstgid", "map_col", "map_row", "scale",
                     "flip_h", "flip_v", "flip_d", "topleft"):
            self.assertEqual(getattr(c, attr), getattr(t, attr), attr)

    def test_copy_to_new_position(self):
        c = self.tile.copy(map_col=2, map_row=1)
        self.assertEqual((c.map_col, c.map_row), (2, 1))
        self.assertEqual(c.topleft, (32, 16))
        self.assertEqual((self.tile.map_col, self.tile.map_row), (0, 0))

    def test_copy_only_one_coordinate(self):
        t = self.make_tile(map_col=1, map_row=1)
        c = t.copy(map_row=0)
        self.assertEqual((c.map_col, c.map_row), (1, 0))

    def test_copy_is_independent(self):
        c = self.tile.copy()
        c.set_tile_image(1, 1)
        self.assertEqual((self.tile.tile_col, self.tile.tile_row), (0, 0))


class MapLoaderTest(TilemapTestBase):
    """The map loaders skip lowercase validation (Tiled names files freely)."""

    def test_map_text_loader_allows_mixed_case(self):
        text = loaders.maps.load("Upper_Extra.tsx")
        self.assertIn("<tileset", text)

    def test_map_image_loader_allows_mixed_case(self):
        surf = loaders.mapimages.load("UpperTiles.png")
        self.assertEqual(surf.get_size(), (30, 20))

    def test_image_loader_still_validates_case(self):
        loader = loaders.ImageLoader("maps")
        with self.assertRaises(loaders.InvalidCase):
            loader.load("UpperTiles.png")

    def test_map_loader_extensions(self):
        self.assertEqual(loaders.maps.EXTNS, ["tmx", "tsx"])
        self.assertIn("<map", loaders.maps.load("level"))

    def test_mixed_case_external_tileset(self):
        ts = _load_tilesets(
            ET.fromstring(
                '<map><tileset firstgid="1" source="Upper_Extra.tsx"/></map>'
            ),
            "level.tmx",
        )[1]
        self.assertEqual(ts["tile_count"], 2)


TILESET_XML = """
 <tileset firstgid="1" tilewidth="8" tileheight="8"
          spacing="2" margin="1" tilecount="6" columns="3">
  <image source="tiles.png"/>
 </tileset>
"""


class MapSettingsTest(TilemapTestBase):
    """Map settings that aren't supported fail clearly instead of loading wrongly."""

    def load(self, map_attrs, body):
        xml = f'<map {map_attrs} tilewidth="8" tileheight="8">{TILESET_XML}{body}</map>'
        with mock.patch("pgzero.tilemaps._load_xml_from_maps", return_value=ET.fromstring(xml)):
            return load_tile_map_actors("test")

    def layer(self, name, csv="1,2"):
        return f'<layer name="{name}" width="2" height="1"><data encoding="csv">{csv}</data></layer>'

    def test_infinite_map(self):
        with self.assertRaisesRegex(ValueError, "untick Infinite"):
            self.load('orientation="orthogonal" infinite="1"', self.layer("ground"))

    def test_isometric_map(self):
        with self.assertRaisesRegex(ValueError, "isometric map"):
            self.load('orientation="isometric"', self.layer("ground"))

    def test_layers_inside_groups(self):
        body = (
            self.layer("sky")
            + '<group name="level">' + self.layer("ground")
            + '<group name="inner">' + self.layer("coins", "0,3") + "</group></group>"
        )
        layers = self.load('orientation="orthogonal" infinite="0"', body)
        self.assertEqual(list(layers), ["sky", "ground", "coins"])
        self.assertEqual([t.tile_gid for t in layers["coins"]], [3])

    def test_duplicate_layer_names(self):
        body = self.layer("ground") + '<group name="g">' + self.layer("ground") + "</group>"
        with self.assertRaisesRegex(ValueError, "more than one layer named 'ground'"):
            self.load('orientation="orthogonal"', body)


class SharedTileImageTest(TilemapTestBase):
    """Tiles of the same kind share one image."""

    def test_same_kind_of_tile_shares_an_image(self):
        tile = load_tile_map_actors("level")["ground"][0]
        self.assertIs(tile.copy(map_col=3)._orig_surf, tile._orig_surf)

    def test_scaled_tiles_share_a_scaled_image(self):
        ground = load_tile_map_actors("level", scale=3)["ground"]
        tile = ground[0]
        self.assertEqual(tile.scale, 3)
        self.assertEqual(tile._orig_surf.get_size(), (48, 48))
        self.assertIs(tile.copy(map_col=3)._orig_surf, tile._orig_surf)
        # The shared image is already the right size, so it isn't scaled again
        self.assertIs(tile._build_transformed_surf(), tile._orig_surf)

    def test_changing_a_tiles_scale(self):
        tile = load_tile_map_actors("level")["ground"][0]
        pos = tile.pos
        tile.scale = 2
        self.assertEqual(tile.scale, 2)
        self.assertEqual((tile.width, tile.height), (32, 32))
        self.assertEqual(tile.pos, pos)


# level.tmx's "ground" layer is 4x2 squares of 16x16 pixels, with (1, 0) empty:
#
#     (0, 0) tiles (0, 0)   (1, 0) empty          (2, 0) tiles (2, 1)   (3, 0) tiles (0, 1)
#     (0, 1) tiles (1, 0)   (1, 1) tiles (2, 0)   (2, 1) extra (1, 0)   (3, 1) extra (0, 0)


def map_pos(tile):
    return (tile.map_col, tile.map_row)


class TileMapTest(TilemapTestBase):
    def setUp(self):
        self.level = load_tile_map_actors("level")

    def test_returns_a_tile_map(self):
        self.assertIsInstance(self.level, TileMap)
        self.assertIsInstance(self.level, dict)
        self.assertIsInstance(self.level["ground"], TileLayer)

    def test_layers_in_drawing_order(self):
        self.assertEqual(list(self.level), ["ground", "empty"])
        self.assertEqual([layer.name for layer in self.level.layers], ["ground", "empty"])

    def test_sizes(self):
        self.assertEqual((self.level.width, self.level.height), (4, 2))
        self.assertEqual((self.level.tile_width, self.level.tile_height), (16, 16))

    def test_scaled_sizes(self):
        level = load_tile_map_actors("level", scale=2)
        self.assertEqual((level.tile_width, level.tile_height), (32, 32))

    def test_missing_layer_lists_layers(self):
        with self.assertRaisesRegex(KeyError, "no layer named 'walls'.*'ground', 'empty'"):
            self.level["walls"]

    def test_get_missing_layer(self):
        self.assertIsNone(self.level.get("walls"))

    def test_reprs(self):
        self.assertEqual(repr(self.level), "<TileMap 'level' with layers ['ground', 'empty']>")
        self.assertEqual(repr(self.level["ground"]), "<TileLayer 'ground' with 7 tiles>")
        self.assertEqual(repr(self.level["ground"][0]), "<Tile map_col=0 map_row=0 tile_col=0 tile_row=0>")


class LayerAsListTest(TilemapTestBase):
    """A layer works like a list of its tiles."""

    def setUp(self):
        self.level = load_tile_map_actors("level")
        self.ground = self.level["ground"]

    def test_len_and_bool(self):
        self.assertEqual(len(self.ground), 7)
        self.assertTrue(self.ground)
        self.assertFalse(self.level["empty"])

    def test_indexing(self):
        tiles = list(self.ground)
        self.assertEqual(map_pos(self.ground[0]), (0, 0))
        self.assertIs(self.ground[-1], tiles[-1])
        self.assertEqual(self.ground[1:3], tiles[1:3])
        with self.assertRaises(IndexError):
            self.ground[7]

    def test_index_and_count(self):
        tile = self.ground[3]
        self.assertEqual(self.ground.index(tile), 3)
        self.assertEqual(self.ground.count(tile), 1)
        self.assertEqual(self.ground.count(tile.copy()), 0)

    def test_reversed(self):
        self.assertEqual(list(reversed(self.ground)), list(self.ground)[::-1])

    def test_collidelist(self):
        player = Actor(pygame.Surface((4, 4)), topleft=(36, 4))  # in square (2, 0)
        index = player.collidelist(self.ground)
        self.assertEqual(map_pos(self.ground[index]), (2, 0))

    def test_collidelist_misses_empty_square(self):
        player = Actor(pygame.Surface((4, 4)), topleft=(20, 4))  # in empty square (1, 0)
        self.assertEqual(player.collidelist(self.ground), -1)

    def test_adding_layers_and_lists(self):
        player = Actor(pygame.Surface((4, 4)))
        both = self.ground + self.level["empty"]
        self.assertEqual(both, list(self.ground))
        self.assertEqual(self.ground + [player], list(self.ground) + [player])
        self.assertEqual([player] + self.ground, [player] + list(self.ground))

    def test_in(self):
        tile = self.ground[0]
        self.assertIn(tile, self.ground)
        self.assertNotIn(tile.copy(), self.ground)
        self.assertNotIn("grass", self.ground)
        self.assertNotIn(tile, self.level["empty"])

    def test_pop_collected_item(self):
        """The way students collect items: collidelist() then pop()."""
        player = Actor(pygame.Surface((4, 4)), topleft=(36, 4))  # in square (2, 0)
        index = player.collidelist(self.ground)
        tile = self.ground.pop(index)
        self.assertEqual(map_pos(tile), (2, 0))
        self.assertNotIn(tile, self.ground)
        self.assertIsNone(self.ground.get_tile(2, 0))
        self.assertEqual(len(self.ground), 6)
        self.assertEqual(player.collidelist(self.ground), -1)

    def test_pop_last(self):
        last = self.ground[-1]
        self.assertIs(self.ground.pop(), last)
        self.assertEqual(len(self.ground), 6)

    def test_pop_bad_index(self):
        with self.assertRaises(IndexError):
            self.ground.pop(7)
        self.assertEqual(len(self.ground), 7)

    def test_pop_empty_layer(self):
        with self.assertRaisesRegex(IndexError, "empty layer 'empty'"):
            self.level["empty"].pop()

    def test_remove(self):
        tile = self.ground[0]
        self.ground.remove(tile)
        self.assertNotIn(tile, self.ground)
        self.assertIsNone(self.ground.get_tile(0, 0))
        self.assertEqual(len(self.ground), 6)

    def test_remove_tile_not_in_layer(self):
        with self.assertRaisesRegex(ValueError, "not in layer 'ground'"):
            self.ground.remove(self.ground[0].copy())

    def test_removing_while_looping(self):
        for tile in self.ground:
            if tile.tileset_firstgid == 1:
                self.ground.remove(tile)
        self.assertEqual([map_pos(t) for t in self.ground], [(2, 1), (3, 1)])

    def test_append(self):
        tile = self.ground[0].copy(map_col=1, map_row=0)
        self.ground.append(tile)
        self.assertIs(self.ground.get_tile(1, 0), tile)
        self.assertIs(self.ground[-1], tile)
        self.assertEqual(tile.topleft, (16, 0))
        self.assertEqual(len(self.ground), 8)

    def test_append_replaces_tile_in_that_square(self):
        old = self.ground.get_tile(2, 0)
        tile = self.ground[0].copy(map_col=2, map_row=0)
        self.ground.append(tile)
        self.assertIs(self.ground.get_tile(2, 0), tile)
        self.assertNotIn(old, self.ground)
        self.assertEqual(len(self.ground), 7)

    def test_append_moves_tile_from_another_layer(self):
        empty = self.level["empty"]
        tile = self.ground[0]
        empty.append(tile)
        self.assertIn(tile, empty)
        self.assertNotIn(tile, self.ground)
        self.assertEqual(len(self.ground), 6)

    def test_append_not_a_tile(self):
        with self.assertRaisesRegex(TypeError, "Only tiles"):
            self.ground.append("grass")

    def test_append_off_the_map(self):
        with self.assertRaisesRegex(ValueError, "off the map"):
            self.ground.append(self.ground[0].copy(map_col=4))

    def test_item_assignment_is_not_supported(self):
        with self.assertRaises(TypeError):
            self.ground[0] = self.ground[1]

    def test_clear(self):
        tile = self.ground[0]
        self.ground.clear()
        self.assertEqual(len(self.ground), 0)
        self.assertNotIn(tile, self.ground)


class GetSetTileTest(TilemapTestBase):
    def setUp(self):
        self.level = load_tile_map_actors("level")
        self.ground = self.level["ground"]

    def test_get_tile(self):
        tile = self.ground.get_tile(2, 0)
        self.assertEqual(map_pos(tile), (2, 0))
        self.assertEqual((tile.tile_col, tile.tile_row), (2, 1))
        self.assertIn(tile, self.ground)

    def test_get_empty_square(self):
        self.assertIsNone(self.ground.get_tile(1, 0))

    def test_get_tile_off_the_map(self):
        self.assertIsNone(self.ground.get_tile(-1, 0))
        self.assertIsNone(self.ground.get_tile(10, 10))

    def test_get_tile_with_pixels(self):
        with self.assertRaisesRegex(TypeError, "col should be a whole number.*pos_to_map"):
            self.ground.get_tile(40.5, 12)

    def test_get_tile_with_a_pair(self):
        with self.assertRaises(TypeError):
            self.ground.get_tile((2, 0))

    def test_create_tile(self):
        tile = self.level.create_tile(2, 1, tileset="tiles")
        self.assertIsInstance(tile, Tile)
        self.assertNotIn(tile, self.ground)
        self.assertEqual((tile.tile_col, tile.tile_row, tile.tile_gid), (2, 1, 6))
        self.assertEqual((tile.width, tile.height), (16, 16))
        self.assertEqual(tuple(tile._orig_surf.get_at((8, 8))), tile_color(2, 1))

    def test_create_tile_from_other_tileset(self):
        tile = self.level.create_tile(1, 0, tileset="extra")
        self.assertEqual(tile.tile_gid, 8)
        self.assertEqual(tuple(tile._orig_surf.get_at((4, 4))), (40, 50, 60, 255))

    def test_create_tile_needs_tileset_when_map_has_several(self):
        with self.assertRaisesRegex(ValueError, "more than one tileset.*'tiles', 'extra'"):
            self.level.create_tile(0, 0)

    def test_create_tile_unknown_tileset(self):
        with self.assertRaisesRegex(ValueError, "no tileset named 'grass'"):
            self.level.create_tile(0, 0, tileset="grass")

    def test_create_tile_bad_image(self):
        with self.assertRaisesRegex(ValueError, "tile_col"):
            self.level.create_tile(5, 0, tileset="tiles")
        with self.assertRaisesRegex(TypeError, "tile_row should be a whole number"):
            self.level.create_tile(0, 0.5, tileset="tiles")

    def test_create_tile_on_scaled_map(self):
        level = load_tile_map_actors("level", scale=2)
        tile = level.create_tile(0, 0, tileset="tiles")
        self.assertEqual((tile.width, tile.height), (32, 32))

    def test_set_tile_in_empty_square(self):
        tile = self.level.create_tile(2, 1, tileset="tiles")
        self.assertIs(self.ground.set_tile(1, 0, tile), tile)
        self.assertIs(self.ground.get_tile(1, 0), tile)
        self.assertIn(tile, self.ground)
        self.assertEqual(len(self.ground), 8)
        self.assertEqual(map_pos(tile), (1, 0))
        self.assertEqual(tile.topleft, (16, 0))

    def test_set_tile_replaces(self):
        old = self.ground.get_tile(0, 0)
        new = self.ground.set_tile(0, 0, self.level.create_tile(1, 1, tileset="tiles"))
        self.assertIs(self.ground.get_tile(0, 0), new)
        self.assertNotIn(old, self.ground)
        self.assertEqual(len(self.ground), 7)

    def test_set_tile_places_that_tile_not_a_copy(self):
        """Placing the same tile again moves it, rather than adding another."""
        tile = self.level.create_tile(0, 0, tileset="tiles")
        self.ground.set_tile(1, 0, tile)
        self.ground.set_tile(0, 0, tile)
        self.assertIs(self.ground.get_tile(0, 0), tile)
        self.assertIsNone(self.ground.get_tile(1, 0))
        self.assertEqual(len(self.ground), 7)

    def test_set_tile_from_another_layer(self):
        empty = self.level["empty"]
        tile = self.ground.get_tile(3, 1)
        empty.set_tile(3, 1, tile)
        self.assertIn(tile, empty)
        self.assertNotIn(tile, self.ground)
        self.assertEqual(len(self.ground), 6)

    def test_change_image_of_tile_on_map(self):
        wall = self.ground.get_tile(0, 0)
        wall.set_tile_image(2, 1)
        self.assertEqual(wall.tile_gid, 6)
        self.assertIs(self.ground.get_tile(0, 0), wall)
        self.assertEqual(wall.topleft, (0, 0))

    def test_set_tile_needs_a_tile(self):
        with self.assertRaisesRegex(TypeError, "needs a tile.*create_tile"):
            self.ground.set_tile(1, 0, (2, 1))

    def test_set_tile_off_the_map(self):
        tile = self.level.create_tile(0, 0, tileset="tiles")
        with self.assertRaisesRegex(ValueError, "off the map.*4 squares wide and 2 tall"):
            self.ground.set_tile(4, 0, tile)
        with self.assertRaisesRegex(ValueError, "off the map"):
            self.ground.set_tile(0, -1, tile)
        self.assertEqual(len(self.ground), 7)
        self.assertNotIn(tile, self.ground)

    def test_set_tile_on_scaled_map(self):
        level = load_tile_map_actors("level", scale=2)
        tile = level["ground"].set_tile(1, 0, level.create_tile(0, 0, tileset="tiles"))
        self.assertEqual(tile.topleft, (32, 0))
        self.assertEqual((tile.width, tile.height), (32, 32))

    def test_remove_tile(self):
        wall = self.ground.get_tile(2, 0)
        self.assertIs(self.ground.remove_tile(2, 0), wall)
        self.assertIsNone(self.ground.get_tile(2, 0))
        self.assertNotIn(wall, self.ground)
        self.assertEqual(len(self.ground), 6)

    def test_remove_tile_from_empty_square(self):
        self.assertIsNone(self.ground.remove_tile(1, 0))
        self.assertIsNone(self.ground.remove_tile(10, 10))
        self.assertEqual(len(self.ground), 7)

    def test_remove_tile_with_pixels(self):
        with self.assertRaisesRegex(TypeError, "pos_to_map"):
            self.ground.remove_tile(40.5, 12)

    def test_set_map_position_moves_tile_in_layer(self):
        tile = self.ground.get_tile(0, 0)
        tile.set_map_position(1, 0)
        self.assertIs(self.ground.get_tile(1, 0), tile)
        self.assertIsNone(self.ground.get_tile(0, 0))
        self.assertEqual(tile.topleft, (16, 0))

    def test_set_map_position_replaces_tile_there(self):
        tile = self.ground.get_tile(0, 0)
        replaced = self.ground.get_tile(2, 0)
        tile.set_map_position(2, 0)
        self.assertIs(self.ground.get_tile(2, 0), tile)
        self.assertNotIn(replaced, self.ground)
        self.assertEqual(len(self.ground), 6)

    def test_set_map_position_off_the_map(self):
        tile = self.ground.get_tile(0, 0)
        with self.assertRaisesRegex(ValueError, "off the map"):
            tile.set_map_position(9, 0)
        self.assertIs(self.ground.get_tile(0, 0), tile)


class PositionTest(TilemapTestBase):
    def setUp(self):
        self.level = load_tile_map_actors("level")
        self.ground = self.level["ground"]

    def test_map_to_pos_is_square_center(self):
        self.assertEqual(self.level.map_to_pos(0, 0), (8, 8))
        self.assertEqual(self.level.map_to_pos(3, 1), (56, 24))
        self.assertEqual(self.level.map_to_pos(3, 1), self.ground.get_tile(3, 1).pos)

    def test_pos_to_map(self):
        self.assertEqual(self.level.pos_to_map(0, 0), (0, 0))
        self.assertEqual(self.level.pos_to_map(15.9, 15.9), (0, 0))
        self.assertEqual(self.level.pos_to_map(16, 16), (1, 1))
        self.assertEqual(self.level.pos_to_map(50, 20), (3, 1))

    def test_pos_to_map_off_the_map(self):
        self.assertEqual(self.level.pos_to_map(-1, -1), (-1, -1))
        self.assertEqual(self.level.pos_to_map(100, 0), (6, 0))

    def test_pos_to_map_with_a_pair(self):
        with self.assertRaisesRegex(TypeError, "x, y = pos"):
            self.level.pos_to_map((50, 20))

    def test_pos_to_map_with_a_non_number(self):
        with self.assertRaisesRegex(TypeError, "y should be a number"):
            self.level.pos_to_map(50, "20")

    def test_map_to_pos_with_pixels(self):
        with self.assertRaisesRegex(TypeError, "row should be a whole number"):
            self.level.map_to_pos(1, 2.5)

    def test_round_trip(self):
        for col, row in [(0, 0), (3, 1), (-2, 5)]:
            self.assertEqual(self.level.pos_to_map(*self.level.map_to_pos(col, row)), (col, row))

    def test_scaled_map(self):
        level = load_tile_map_actors("level", scale=2)
        self.assertEqual(level.map_to_pos(1, 1), (48, 48))
        self.assertEqual(level.pos_to_map(48, 48), (1, 1))

    def test_tile_at_actor_position(self):
        player = Actor(pygame.Surface((4, 4)), center=(40, 8))
        col, row = self.level.pos_to_map(player.x, player.y)
        self.assertEqual(map_pos(self.ground.get_tile(col, row)), (2, 0))

    def test_scrolling_the_map_moves_every_tile(self):
        self.level.x = -10
        self.level.y += 5
        self.assertEqual((self.level.x, self.level.y), (-10, 5))
        for tile in self.ground:
            self.assertEqual(tile.topleft, (tile.map_col * 16 - 10, tile.map_row * 16 + 5))

    def test_conversions_follow_scrolling(self):
        self.level.x = -10
        self.assertEqual(self.level.map_to_pos(0, 0), (-2, 8))
        self.assertEqual(self.level.pos_to_map(0, 0), (0, 0))
        self.assertEqual(self.level.pos_to_map(-11, 0), (-1, 0))

    def test_new_and_moved_tiles_follow_scrolling(self):
        self.level.x = -10
        added = self.ground.set_tile(1, 0, self.level.create_tile(0, 0, tileset="tiles"))
        self.assertEqual(added.topleft, (6, 0))
        moved = self.ground.get_tile(0, 0)
        moved.set_map_position(0, 1)
        self.assertEqual(moved.topleft, (-10, 16))

    def test_scrolling_keeps_tiles_moved_by_hand(self):
        tile = self.ground[0]
        tile.y -= 3  # e.g. a bouncing block
        self.level.x = 5
        self.assertEqual(tile.topleft, (5, -3))

    def test_tile_not_in_a_layer_ignores_scrolling(self):
        tile = self.ground.pop(0)
        self.level.x = 50
        tile.set_map_position(1, 1)
        self.assertEqual(tile.topleft, (16, 16))


class FollowTest(TilemapTestBase):
    """level.follow(): the ground layer is 64 x 32 pixels; most tests use a
    32 x 16 screen, so the map is twice the size of the screen each way."""

    def setUp(self):
        self.level = load_tile_map_actors("level")
        self.player = Actor(pygame.Surface((4, 4)))
        patcher = mock.patch("pgzero.game.screen", pygame.Surface((32, 16)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_centers_the_actor(self):
        self.player.pos = self.level.map_to_pos(2, 1)  # (40, 24)
        self.assertEqual(self.level.follow(self.player), (-24, -16))
        self.assertEqual(self.player.pos, (16, 8))
        self.assertEqual((self.level.x, self.level.y), (-24, -16))

    def test_actor_stays_in_the_same_square(self):
        self.player.pos = self.level.map_to_pos(2, 1)
        self.level.follow(self.player)
        self.assertEqual(self.level.pos_to_map(self.player.x, self.player.y), (2, 1))
        self.assertEqual(self.level["ground"].get_tile(2, 1).pos, self.player.pos)

    def test_stops_at_left_and_top_edges(self):
        self.player.pos = (8, 4)
        self.assertEqual(self.level.follow(self.player), (0, 0))
        self.assertEqual(self.player.pos, (8, 4))
        self.assertEqual((self.level.x, self.level.y), (0, 0))

    def test_stops_at_right_and_bottom_edges(self):
        self.player.pos = self.level.map_to_pos(3, 1)  # (56, 24)
        self.level.follow(self.player)
        self.assertEqual((self.level.x, self.level.y), (-32, -16))
        self.assertEqual(self.player.pos, (24, 8))  # right of the middle

    def test_others_move_with_the_map(self):
        carrot = Actor(pygame.Surface((4, 4)), pos=(30, 20))
        rock = Actor(pygame.Surface((4, 4)), pos=(50, 5))
        self.player.pos = self.level.map_to_pos(2, 1)
        self.level.follow(self.player, [carrot, rock])
        self.assertEqual(carrot.pos, (6, 4))
        self.assertEqual(rock.pos, (26, -11))

    def test_one_other_actor(self):
        carrot = Actor(pygame.Surface((4, 4)), pos=(30, 20))
        self.player.pos = self.level.map_to_pos(2, 1)
        self.level.follow(self.player, carrot)
        self.assertEqual(carrot.pos, (6, 4))

    def test_following_again_does_nothing(self):
        self.player.pos = self.level.map_to_pos(2, 1)
        self.level.follow(self.player)
        self.assertEqual(self.level.follow(self.player), (0, 0))

    def test_map_smaller_than_screen_stays_in_the_middle(self):
        with mock.patch("pgzero.game.screen", pygame.Surface((100, 50))):
            self.player.pos = (10, 10)
            self.assertEqual(self.level.follow(self.player), (18, 9))
        self.assertEqual((self.level.x, self.level.y), (18, 9))
        self.assertEqual(self.player.pos, (28, 19))

    def test_needs_the_game_window(self):
        with mock.patch("pgzero.game.screen", None):
            with self.assertRaisesRegex(RuntimeError, r"start\(\) or update\(\)"):
                self.level.follow(self.player)


class DrawTest(TilemapTestBase):
    def setUp(self):
        self.level = load_tile_map_actors("level")
        self.ground = self.level["ground"]
        # The ground layer is 64 x 32 pixels, so it all fits on this screen.
        patcher = mock.patch("pgzero.game.screen", pygame.Surface((200, 200)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def drawn(self):
        """Draw the layer once for real (so each tile knows where its image
        goes), then return the tiles whose draw() is called."""
        self.ground.draw()
        with mock.patch.object(Tile, "draw", autospec=True) as draw:
            self.ground.draw()
        return [call[0][0] for call in draw.call_args_list]

    def test_layer_draws_every_tile(self):
        self.assertEqual(self.drawn(), list(self.ground))

    def test_tiles_off_the_screen_are_skipped(self):
        self.level.x = -40  # columns 0 and 1 are now off the left of the screen
        self.assertEqual([map_pos(t) for t in self.drawn()], [(2, 0), (3, 0), (2, 1), (3, 1)])

    def test_tile_partly_on_the_screen_is_drawn(self):
        self.level.x = -20  # column 1 is 4 pixels on the screen
        self.assertIn((1, 1), [map_pos(t) for t in self.drawn()])

    def test_tiles_scrolled_onto_the_screen_are_drawn(self):
        self.level.x = -1000
        self.assertEqual(self.drawn(), [])
        self.level.x = 0
        self.assertEqual(self.drawn(), list(self.ground))

    def test_tile_moved_by_hand_onto_the_screen_is_drawn(self):
        self.level.x = -1000
        tile = self.ground[0]
        tile.x = 50  # e.g. a moving platform
        self.assertEqual(self.drawn(), [tile])

    def test_tile_with_small_collision_rect_near_the_edge_is_drawn(self):
        """Its image is bigger than its rect, so the image can be on the
        screen while the rect isn't."""
        tile = self.ground.get_tile(0, 0)
        tile.collision_rect = (2, 2)  # the image pokes 7 pixels out each side
        self.level.x = -10  # the rect is off the screen, the image isn't
        self.assertLess(tile.right, 0)
        self.assertIn(tile, self.drawn())

    def test_rotated_tile_partly_on_the_screen_is_drawn(self):
        tile = self.ground.get_tile(0, 0)
        tile.angle = 45  # the rect grows to fit the rotated image
        self.level.x = -18  # only its corner is on the screen
        self.assertTrue(0 < tile.right < 2)
        self.assertIn(tile, self.drawn())

    def test_draws_every_tile_before_the_game_starts(self):
        with mock.patch("pgzero.game.screen", None):
            with mock.patch.object(Tile, "draw", autospec=True) as draw:
                self.ground.draw()
        self.assertEqual([call[0][0] for call in draw.call_args_list], list(self.ground))


    def test_hidden_layer_is_not_drawn(self):
        self.ground.visible = False
        with mock.patch.object(Tile, "draw") as draw:
            self.ground.draw()
            self.level.draw()
        draw.assert_not_called()

    def test_map_draws_layers_in_order(self):
        with mock.patch.object(TileLayer, "draw", autospec=True) as draw:
            self.level.draw()
        self.assertEqual([call[0][0] for call in draw.call_args_list], self.level.layers)


PROPERTIES_XML = """
<map orientation="orthogonal" width="2" height="1" tilewidth="8" tileheight="8">
 <tileset firstgid="1" name="tiles" tilewidth="8" tileheight="8"
          spacing="2" margin="1" tilecount="6" columns="3">
  <image source="tiles.png"/>
  <tile id="0">
   <properties>
    <property name="solid" type="bool" value="true"/>
    <property name="damage" type="int" value="5"/>
    <property name="speed" type="float" value="1.5"/>
    <property name="label" value="rock"/>
    <property name="note">two
lines</property>
    <property name="spawn" type="class">
     <properties>
      <property name="count" type="int" value="3"/>
     </properties>
    </property>
   </properties>
  </tile>
  <tile id="1">
   <properties>
    <property name="solid" type="bool" value="false"/>
   </properties>
  </tile>
 </tileset>
 <layer name="walls" width="2" height="1">
  <data encoding="csv">1,2</data>
 </layer>
 <layer name="hidden" width="2" height="1" visible="0">
  <data encoding="csv">3,0</data>
 </layer>
 <group name="group" visible="0">
  <layer name="in_hidden_group" width="2" height="1">
   <data encoding="csv">0,3</data>
  </layer>
 </group>
</map>
"""


class PropertiesTest(TilemapTestBase):
    """Custom tile properties and layer visibility set in Tiled."""

    def setUp(self):
        root = ET.fromstring(PROPERTIES_XML)
        with mock.patch("pgzero.tilemaps._load_xml_from_maps", return_value=root):
            self.level = load_tile_map_actors("test")
        self.walls = self.level["walls"]

    def test_tile_properties(self):
        props = self.walls.get_tile(0, 0).properties
        self.assertEqual(
            dict(props),
            {
                "solid": True,
                "damage": 5,
                "speed": 1.5,
                "label": "rock",
                "note": "two\nlines",
                "spawn": {"count": 3},
            },
        )

    def test_false_bool_property(self):
        self.assertIs(self.walls.get_tile(1, 0).properties["solid"], False)

    def test_tile_without_properties(self):
        props = self.level["hidden"].get_tile(0, 0).properties
        self.assertEqual(dict(props), {})
        self.assertFalse(props.get("solid", False))

    def test_properties_cannot_be_changed(self):
        """Every tile of a kind shares its properties, so one tile can't change them."""
        with self.assertRaises(TypeError):
            self.walls.get_tile(0, 0).properties["solid"] = False

    def test_new_tile_has_its_kinds_properties(self):
        tile = self.walls.set_tile(1, 0, self.level.create_tile(0, 0))  # only one tileset, so none named
        self.assertTrue(tile.properties["solid"])

    def test_visibility(self):
        self.assertTrue(self.walls.visible)
        self.assertFalse(self.level["hidden"].visible)
        self.assertFalse(self.level["in_hidden_group"].visible)

    def test_hidden_layers_still_collide(self):
        player = Actor(pygame.Surface((4, 4)), topleft=(0, 0))
        self.assertEqual(player.collidelist(self.level["hidden"]), 0)


if __name__ == "__main__":
    unittest.main()
