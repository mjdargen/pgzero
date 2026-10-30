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
import xml.etree.ElementTree as ET

import pygame

from pgzero import loaders
from pgzero.loaders import set_root
from pgzero.tilemaps import (
    FLIP_D,
    FLIP_H,
    FLIP_V,
    GID_MASK,
    Tile,
    _count_tiles_that_fit,
    _load_tilesets,
    _resolve_relative_map_path,
    load_tile_map_actors,
)

WHITE = (255, 255, 255, 255)


def tile_colour(col, row):
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
        self.assertEqual(self.layers["empty"], [])

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
        self.assertEqual(tuple(t._orig_surf.get_at((8, 8))), tile_colour(2, 1))
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
                         tile_colour(2, 1))
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


if __name__ == "__main__":
    unittest.main()
