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
        """rect(rect, color) still works with a positional color."""
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

    def assertPixel(self, pos, expected):
        """Check the screen's color at pos, allowing for rounding."""
        actual = tuple(self.surf.get_at(pos))[:3]
        for a, e in zip(actual, expected):
            self.assertLessEqual(abs(a - e), 2, f"pixel {pos} is {actual}, expected {expected}")

    def test_filled_rect_see_through(self):
        """A see-through color is blended over what's already on the screen."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((10, 10), (50, 50)), (0, 0, 0, 128))
        self.assertPixel((30, 30), (127, 127, 127))
        self.assertPixel((5, 5), (255, 255, 255))

    def test_filled_rect_see_through_pos_size_form(self):
        """The (x, y), (w, h) form blends a see-through color too."""
        self.screen.fill('blue')
        self.screen.draw.filled_rect((10, 10), (50, 50), (255, 0, 0, 128))
        self.assertPixel((30, 30), (128, 0, 127))

    def test_see_through_overlaps_add_up(self):
        """Two see-through shapes over the same spot both darken it."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), (0, 0, 0, 128))
        self.screen.draw.filled_rect(Rect((50, 50), (100, 100)), (0, 0, 0, 128))
        self.assertPixel((25, 25), (127, 127, 127))
        self.assertPixel((75, 75), (63, 63, 63))
        self.assertPixel((125, 125), (127, 127, 127))

    def test_fully_transparent_draws_nothing(self):
        """A color with alpha 0 leaves the screen unchanged."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), (0, 0, 0, 0))
        self.assertPixel((50, 50), (255, 255, 255))

    def test_opaque_alpha_draws_solid(self):
        """Alpha 255 draws a solid color, the same as (r, g, b)."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), (255, 0, 0, 255))
        self.assertPixel((50, 50), (255, 0, 0))

    def test_see_through_shapes(self):
        """Circles, lines, polygons and outlines blend see-through colors."""
        self.screen.fill('white')
        half_black = (0, 0, 0, 128)
        self.screen.draw.filled_circle((50, 50), 20, half_black)
        self.screen.draw.circle((150, 50), 20, half_black, width=5)
        self.screen.draw.line((0, 150), (90, 150), half_black, width=5)
        self.screen.draw.filled_polygon([(110, 110), (190, 110), (150, 190)], half_black)
        self.screen.draw.polygon([(110, 110), (190, 110), (150, 190)], half_black)
        self.assertPixel((50, 50), (127, 127, 127))
        self.assertPixel((150, 32), (127, 127, 127))
        self.assertPixel((150, 50), (255, 255, 255))
        self.assertPixel((45, 150), (127, 127, 127))
        self.assertPixel((150, 130), (127, 127, 127))
        # the outline goes over the filled polygon's edge, so it's darker there
        self.assertPixel((150, 110), (63, 63, 63))

    def test_thick_rect_see_through(self):
        """A thick see-through outline is evenly blended, corners included."""
        self.screen.fill('white')
        self.screen.draw.rect(Rect((20, 20), (100, 100)), (0, 0, 0, 128), width=10)
        self.assertPixel((20, 20), (127, 127, 127))
        self.assertPixel((70, 20), (127, 127, 127))
        self.assertPixel((20, 70), (127, 127, 127))
        self.assertPixel((70, 70), (255, 255, 255))

    def test_see_through_partly_off_screen(self):
        """A see-through shape hanging off the screen blends the part that's on it."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((150, 150), (100, 100)), (0, 0, 0, 128))
        self.screen.draw.filled_circle((0, 0), 30, (0, 0, 0, 128))
        self.assertPixel((199, 199), (127, 127, 127))
        self.assertPixel((5, 5), (127, 127, 127))

    def test_opacity_keyword(self):
        """opacity makes any color see-through, including named colors."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), 'black', opacity=0.5)
        self.screen.draw.filled_circle((150, 50), 20, 'black', opacity=0.5)
        self.screen.draw.line((0, 150), (90, 150), 'black', width=5, opacity=0.5)
        self.screen.draw.rect((110, 110), (80, 80), 'black', width=10, opacity=0.5)
        self.assertPixel((50, 50), (127, 127, 127))
        self.assertPixel((150, 50), (127, 127, 127))
        self.assertPixel((45, 150), (127, 127, 127))
        self.assertPixel((110, 150), (127, 127, 127))

    def test_opacity_combines_with_alpha(self):
        """opacity multiplies the alpha a color already has."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), (0, 0, 0, 128), opacity=0.5)
        self.assertPixel((50, 50), (191, 191, 191))

    def test_opacity_is_kept_between_0_and_1(self):
        """Like Actor.opacity, opacity below 0 is invisible and above 1 is solid."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 100)), 'black', opacity=-1)
        self.screen.draw.filled_rect(Rect((100, 0), (100, 100)), 'black', opacity=2)
        self.assertPixel((50, 50), (255, 255, 255))
        self.assertPixel((150, 50), (0, 0, 0))

    def test_text_see_through(self):
        """Text is see-through with opacity, or with an (r, g, b, a) color."""
        def darkest(**kwargs):
            self.screen.fill('white')
            self.screen.draw.text("IIII", (10, 0), fontsize=90, **kwargs)
            return pygame.surfarray.array3d(self.surf).min()

        self.assertEqual(darkest(color='black'), 0)
        self.assertAlmostEqual(darkest(color='black', opacity=0.5), 127, delta=3)
        self.assertAlmostEqual(darkest(color=(0, 0, 0, 128)), 127, delta=3)
        self.assertAlmostEqual(darkest(color='black', alpha=0.5), 127, delta=3)

    def test_fill_opacity(self):
        """screen.fill() takes opacity too."""
        self.screen.fill('white')
        self.screen.fill('black', opacity=0.5)
        self.assertPixel((100, 100), (127, 127, 127))

    def test_fill_see_through(self):
        """screen.fill() with a see-through color tints the whole screen."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 200)), 'black')
        self.screen.fill((255, 0, 0, 128))
        self.assertPixel((50, 50), (128, 0, 0))
        self.assertPixel((150, 50), (255, 127, 127))

    def assertPixelNear(self, pos, expected, tolerance):
        """Check the screen's color at pos, within tolerance."""
        actual = tuple(self.surf.get_at(pos))[:3]
        for a, e in zip(actual, expected):
            self.assertLessEqual(abs(a - e), tolerance, f"pixel {pos} is {actual}, expected {expected}")

    def test_darkness(self):
        """darkness() darkens the whole screen."""
        self.screen.fill('white')
        self.screen.draw.darkness(0.5)
        self.assertPixel((10, 10), (127, 127, 127))
        self.screen.draw.darkness(1)
        self.assertPixel((10, 10), (0, 0, 0))

    def test_darkness_is_kept_between_0_and_1(self):
        """Like opacity, darkness below 0 changes nothing and above 1 is black."""
        self.screen.fill('white')
        self.screen.draw.darkness(-1)
        self.assertPixel((10, 10), (255, 255, 255))
        self.screen.draw.darkness(2)
        self.assertPixel((10, 10), (0, 0, 0))

    def test_light_shows_real_colors_in_the_dark(self):
        """A light after darkness() shows the scene's real colors under it."""
        self.screen.fill('white')
        self.screen.draw.filled_rect(Rect((0, 0), (100, 200)), 'red')
        self.screen.draw.darkness(1)
        self.screen.draw.light((100, 100), 60)
        # in the middle, the real colors are back (the light fades from its
        # exact middle, so 1 pixel away is a little dimmer)
        self.assertPixelNear((99, 100), (255, 0, 0), 25)
        self.assertPixelNear((101, 100), (255, 255, 255), 25)
        # it fades out toward the edge, and outside it's still dark
        self.assertLess(self.surf.get_at((150, 100))[1], 100)
        self.assertPixel((100, 170), (0, 0, 0))
        self.assertPixel((10, 10), (0, 0, 0))

    def test_light_color(self):
        """A light's color tints what it shines on."""
        self.screen.fill('white')
        self.screen.draw.darkness(1)
        self.screen.draw.light((100, 100), 60, 'orange')
        self.assertPixelNear((100, 100), (255, 165, 0), 12)

    def test_light_opacity(self):
        """opacity makes a light weaker."""
        self.screen.fill('white')
        self.screen.draw.darkness(1)
        self.screen.draw.light((100, 100), 60, opacity=0.5)
        self.assertPixelNear((100, 100), (127, 127, 127), 12)

    def test_light_without_darkness_brightens(self):
        """Without darkness(), a light brightens what's on the screen."""
        self.screen.fill((100, 100, 100))
        self.screen.draw.light((100, 100), 60)
        self.assertPixelNear((100, 100), (200, 200, 200), 12)
        self.assertPixel((10, 10), (100, 100, 100))

    def test_light_forgets_darkness_next_frame(self):
        """The scene kept by darkness() is forgotten when a new frame starts."""
        self.screen.fill('white')
        self.screen.draw.darkness(1)
        self.screen._start_frame()
        # the light now shines on the black screen, not last frame's white
        self.screen.draw.light((100, 100), 60)
        self.assertPixel((100, 100), (0, 0, 0))

    def test_light_partly_off_screen(self):
        """A light hanging off the edge of the screen lights the part on it."""
        self.screen.fill('white')
        self.screen.draw.darkness(1)
        self.screen.draw.light((0, 0), 60)
        self.screen.draw.light((300, 300), 60)  # completely off the screen
        self.assertPixelNear((1, 1), (255, 255, 255), 30)
        self.assertPixel((199, 199), (0, 0, 0))

    def test_light_that_shows_nothing(self):
        """A light with no size, or opacity 0, changes nothing."""
        self.screen.fill('white')
        self.screen.draw.darkness(1)
        self.screen.draw.light((100, 100), 0)
        self.screen.draw.light((100, 100), 60, opacity=0)
        self.assertPixel((100, 100), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
