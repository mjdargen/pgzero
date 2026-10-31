import sys
import unittest
from pathlib import Path
import os
import warnings

import numpy as np
import pygame
import pygame.image
import pygame.surfarray

from pgzero.screen import Screen
from pgzero.loaders import set_root, images
from pgzero.rect import Rect, ZRect


ROOT = Path(__file__).parent


def assert_screen_match(computed, name, max_diff_pixels=0):
    """Check that the image on the screen matches the reference image.

    If the reference image is missing, raise an exception, unless the
    environment variable $W2D_SAVE_REF is given; if given, save current output
    as new reference images. These will need to be checked and committed.

    Up to max_diff_pixels pixels may differ, for shapes whose edges pygame and
    pygame-ce draw slightly differently.

    """
    ref_image = ROOT / 'expected-image' / f'{name}.png'

    if not ref_image.exists():
        if os.environ.get('PGZ_SAVE_REF'):
            warnings.warn(
                f"No reference image exists for {name}; saving new screenshot",
                UserWarning
            )
            pygame.image.save(computed, str(ref_image))
            return
        else:
            raise AssertionError(
                f"No reference image exists for {name}; set $PGZ_SAVE_REF "
                "to create."
            )
    else:
        expected = pygame.image.load(str(ref_image))

    comp_surf = pygame.surfarray.array3d(computed)
    exp_surf = pygame.surfarray.array3d(expected)

    failname = ROOT / 'failed-image' / f'{name}.png'

    differs = np.abs(comp_surf.astype(int) - exp_surf.astype(int)) > 2
    if np.count_nonzero(differs.any(axis=2)) <= max_diff_pixels:
        if failname.exists():
            failname.unlink()
        return

    failname.parent.mkdir(exist_ok=True)

    w, h = computed.get_size()
    out = pygame.Surface(
        (w * 2 + 1, w),
        depth=32,
    )
    out.blit(computed, (0, 0))
    out.blit(expected, (w + 1, 0))
    WHITE = (255, 255, 255)
    FONTHEIGHT = 40
    pygame.draw.line(
        out,
        WHITE,
        (w, 0),
        (w, h),
    )
    font = pygame.font.SysFont(pygame.font.get_default_font(), FONTHEIGHT)
    y = h - FONTHEIGHT
    out.blit(font.render("Computed", True, WHITE), (10, y))
    lbl = font.render("Expected", True, WHITE)
    out.blit(lbl, (w * 2 - 9 - lbl.get_width(), y))
    pygame.image.save(out, str(failname))

    raise AssertionError(
        "Images differ; saved comparison images to {}".format(failname)
    )


class ScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialise the display and set loaders to target the current dir."""
        pygame.init()
        cls.surf = pygame.display.set_mode((200, 200))
        set_root(__file__)

    @classmethod
    def tearDownClass(cls):
        """Shut down the display."""
        pygame.display.quit()

    def setUp(self):
        self.screen = Screen()
        self.screen._set_surface(self.surf)
        self.screen.clear()

    def assertImagesAlmostEqual(self, computed, expected):
        """Check that 2 images are approximately equal."""
        comp_surf = pygame.surfarray.array3d(computed)
        exp_surf = pygame.surfarray.array3d(expected)

        if np.allclose(comp_surf, exp_surf, atol=2):
            return

        name = sys._getframe(1).f_code.co_name
        tmpdir = Path(__file__).parent / 'failed-image'
        tmpdir.mkdir(exist_ok=True)
        pygame.image.save(
            computed,
            str(tmpdir / '{}-computed.png'.format(name))
        )
        pygame.image.save(
            expected,
            str(tmpdir / '{}-expected.png'.format(name))
        )

        raise AssertionError(
            "Images differ; saved comparison images to {}".format(tmpdir)
        )

    def test_blit_surf(self):
        """We can blit a surface to the screen."""
        self.screen.blit(images.alien, (0, 0))
        assert_screen_match(self.surf, 'alien_blit')

    def test_blit_name(self):
        """screen.blit() accepts an image name instead of a Surface."""
        self.screen.blit('alien', (0, 0))
        assert_screen_match(self.surf, 'alien_blit')

    def test_fill_gradient(self):
        """We can fill the screen with a gradient."""
        self.screen.fill('black', gcolor='blue')
        assert_screen_match(self.surf, 'gradient')

    def test_line(self):
        yellow = (255, 255, 0)
        """We can draw a line."""
        self.screen.draw.line(start=(0, 50), end=(100, 30), color=yellow, width=9)
        assert_screen_match(self.surf, 'line')

    def test_line_errors(self):
        """draw.line raises errors as expected."""
        yellow = (255, 255, 0)
        with self.assertRaises(TypeError):
            self.screen.draw.line(2, yellow)
        with self.assertRaises(TypeError):
            self.screen.draw.line([2], yellow)

    def test_circle(self):
        yellow = (255, 255, 0)
        """We can draw a circle."""
        self.screen.draw.circle(pos=(50, 50), radius=50, color=yellow, width=9)
        assert_screen_match(self.surf, 'circle')

    def test_filled_circle(self):
        yellow = (255, 255, 0)
        """We can draw a filled circle."""
        self.screen.draw.filled_circle(pos=(50, 50), radius=50, color=yellow)
        assert_screen_match(self.surf, 'filled_circle')

    def test_circle_errors(self):
        """draw.circle raises errors as expected."""
        yellow = (255, 255, 0)
        with self.assertRaises(TypeError):
            self.screen.draw.circle(2, yellow)
        with self.assertRaises(TypeError):
            self.screen.draw.circle([2], yellow)

    def test_polygon(self):
        poly = [(0, 99), (49, 0), (99, 99)]
        yellow = (255, 255, 0)
        """We can draw a polygon."""
        self.screen.draw.polygon(poly, yellow)
        assert_screen_match(self.surf, 'polygon')

    def test_filled_polygon(self):
        poly = [(0, 99), (49, 0), (99, 99)]
        yellow = (255, 255, 0)
        """We can draw a filled polygon."""
        self.screen.draw.filled_polygon(poly, yellow)
        # pygame-ce fills about 100 edge pixels differently from pygame
        assert_screen_match(self.surf, 'filled_polygon', max_diff_pixels=150)

    def test_polygon_errors(self):
        """draw.polygon raises errors as expected."""
        yellow = (255, 255, 0)
        with self.assertRaisesRegex(TypeError, r"screen\.draw\.polygon\(\)"):
            self.screen.draw.polygon(2, yellow)
        with self.assertRaises(TypeError):
            self.screen.draw.polygon([2], yellow)

    def test_rect(self):
        yellow = (255, 255, 0)
        """We can draw a rectangle."""
        self.screen.draw.rect(rect=Rect((20, 20), (100, 100)), color=yellow, width=9)
        assert_screen_match(self.surf, 'rect')

    def test_filled_rect(self):
        yellow = (255, 255, 0)
        """We can draw a filled rectangle."""
        self.screen.draw.filled_rect(rect=Rect((0, 0), (100, 100)), color=yellow)
        assert_screen_match(self.surf, 'filled_rect')

    def test_rect_positional_color(self):
        """rect(rect, color) still works with a positional colour."""
        yellow = (255, 255, 0)
        self.screen.draw.rect(Rect((20, 20), (100, 100)), yellow, width=9)
        assert_screen_match(self.surf, 'rect')

    def test_rect_pos_size_form(self):
        """We can draw a rectangle from ((x, y), (w, h), color)."""
        yellow = (255, 255, 0)
        self.screen.draw.rect((20, 20), (100, 100), yellow, width=9)
        assert_screen_match(self.surf, 'rect')

    def test_rect_pos_size_form_color_keyword(self):
        self.screen.draw.rect((20, 20), (100, 100), color='yellow', width=9)
        assert_screen_match(self.surf, 'rect')

    def test_rect_zrect(self):
        self.screen.draw.rect(ZRect((20, 20), (100, 100)), 'yellow', width=9)
        assert_screen_match(self.surf, 'rect')

    def test_filled_rect_pos_size_form(self):
        """We can draw a filled rectangle from ((x, y), (w, h), color)."""
        yellow = (255, 255, 0)
        self.screen.draw.filled_rect((0, 0), (100, 100), yellow)
        assert_screen_match(self.surf, 'filled_rect')

    def test_filled_rect_pos_size_form_lists_and_floats(self):
        """Positions and sizes can be lists and are rounded."""
        self.screen.draw.filled_rect([0.2, 0.4], [99.6, 100.3], 'yellow')
        assert_screen_match(self.surf, 'filled_rect')

    def test_rect_form_errors(self):
        """The two calling conventions can't be mixed or left incomplete."""
        yellow = (255, 255, 0)
        r = Rect((0, 0), (10, 10))
        for method in (self.screen.draw.rect, self.screen.draw.filled_rect):
            with self.subTest(method=method.__name__):
                with self.assertRaisesRegex(TypeError, "too many"):
                    method(r, (10, 10), yellow)
                with self.assertRaisesRegex(TypeError, "requires a color"):
                    method(r)
                with self.assertRaisesRegex(TypeError, "requires a color"):
                    method((0, 0), (10, 10))
                with self.assertRaisesRegex(TypeError, "requires a rect"):
                    method((0, 0), yellow, yellow)
                with self.assertRaisesRegex(TypeError, "requires a rect"):
                    method(('a', 0), (10, 10), yellow)

    def test_rect_errors(self):
        """draw.rect raises errors as expected."""
        yellow = (255, 255, 0)
        with self.assertRaises(TypeError):
            self.screen.draw.rect(2, yellow)
        with self.assertRaises(TypeError):
            self.screen.draw.rect([2], yellow)

    def test_wrapped_gradient_text(self):
        """We can draw wrapped gradient text.

        Relates to issue #165 https://github.com/lordmauve/pgzero/issues/165

        """
        self.screen.draw.text(
            'gradient\ntext',
            (0, 0),
            fontname='eunomia_regular',
            fontsize=18,
            color='red',
            gcolor='blue'
        )
        assert_screen_match(self.surf, 'wrapped_gradient_text')

    def test_bounds(self):
        """We can get a bounding rect for the screen."""
        self.assertEqual(
            self.screen.bounds(),
            ZRect(0, 0, 200, 200)
        )


if __name__ == '__main__':
    unittest.main()
