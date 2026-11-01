import unittest

import pygame

from pgzero.actor import calculate_anchor, Actor
from pgzero.loaders import set_root

TEST_MODULE = "pgzero.actor"
TEST_DISP_W, TEST_DISP_H = (200, 100)


class ModuleTest(unittest.TestCase):
    def test_calculate_anchor_with_float(self):
        self.assertEqual(calculate_anchor(1.23, "x", 12345), 1.23)

    def test_calculate_anchor_centre(self):
        self.assertEqual(calculate_anchor("center", "x", 100), 50)

    def test_calculate_anchor_bottom(self):
        self.assertEqual(calculate_anchor("bottom", "y", 100), 100)


class ActorTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        pygame.init()
        pygame.display.set_mode((TEST_DISP_W, TEST_DISP_H))
        set_root(__file__)

    @classmethod
    def tearDownClass(self):
        pygame.display.quit()

    def test_sensible_init_defaults(self):
        a = Actor("alien")

        self.assertEqual(a.image, "alien")
        self.assertEqual(a.topleft, (0, 0))

    def test_setting_absolute_initial_pos(self):
        a = Actor("alien", pos=(100, 200), anchor=("right", "bottom"))

        self.assertEqual(
            a.topleft,
            (100 - a.width, 200 - a.height),
        )

    def test_setting_relative_initial_pos_topleft(self):
        a = Actor("alien", topleft=(500, 500))
        self.assertEqual(a.topleft, (500, 500))

    def test_setting_relative_initial_pos_center(self):
        a = Actor("alien", center=(500, 500))
        self.assertEqual(a.center, (500, 500))

    def test_setting_relative_initial_pos_bottomright(self):
        a = Actor("alien", bottomright=(500, 500))
        self.assertEqual(a.bottomright, (500, 500))

    def test_setting_absolute_pos_and_relative_raises_typeerror(self):
        with self.assertRaises(TypeError):
            Actor("alien", pos=(0, 0), bottomright=(500, 500))

    def test_setting_multiple_relative_pos_raises_typeerror(self):
        with self.assertRaises(TypeError):
            Actor("alien", topleft=(500, 500), bottomright=(600, 600))

    def test_unexpected_kwargs(self):
        with self.assertRaises(TypeError) as cm:
            Actor("alien", toplift=(0, 0))

        self.assertEqual(
            cm.exception.args[0],
            "Unexpected keyword argument 'toplift' (did you mean 'topleft'?)",
        )

    def test_single_edge_kwarg(self):
        """right=0 can't place an actor on its own, so say what to use instead."""
        with self.assertRaises(TypeError) as cm:
            Actor("alien", right=0)
        self.assertEqual(
            cm.exception.args[0],
            "Actor() needs a position with both x and y in it, such as pos=(x, y) "
            "or midright=(x, y), not just right=0. Or make the actor first, then "
            "set it: actor.right = 0",
        )

    def test_single_x_kwarg_suggests_pos_once(self):
        with self.assertRaisesRegex(TypeError, r"such as pos=\(x, y\), not just x=5\."):
            Actor("alien", x=5)

    def test_two_edge_kwargs_suggest_the_matching_position(self):
        cases = [
            (dict(left=0, top=10), "topleft=(0, 10)"),
            (dict(right=800, bottom=600), "bottomright=(800, 600)"),
            (dict(x=100, y=200), "pos=(100, 200)"),
            (dict(x=100, bottom=300), "midbottom=(100, 300)"),
            (dict(centerx=10, centery=20), "center=(10, 20)"),
        ]
        for kwargs, suggestion in cases:
            with self.subTest(**kwargs):
                with self.assertRaises(TypeError) as cm:
                    Actor("alien", **kwargs)
                self.assertIn(f"use {suggestion}.", cm.exception.args[0])

    def test_scale_is_applied_before_the_position(self):
        """The position given is where the scaled actor ends up."""
        a = Actor("alien", midbottom=(100, 300), scale=2)
        self.assertEqual(a.scale, 2)
        self.assertEqual(a.midbottom, (100, 300))
        self.assertEqual(a.width, 132)

    def test_scale_without_a_position(self):
        """With no position, the scaled actor's top-left corner is at (0, 0)."""
        a = Actor("alien", scale=3)
        self.assertEqual(a.topleft, (0, 0))

    def test_other_settings_in_constructor(self):
        """Actor(..., setting=...) is the same as setting it before positioning."""
        a = Actor("alien", topleft=(10, 20), angle=90, opacity=0.5,
                  flip_h=True, flip_v=True, flip_d=True)
        self.assertEqual((a.angle, a.opacity), (90, 0.5))
        self.assertTrue(a.flip_h and a.flip_v and a.flip_d)
        self.assertEqual(a.topleft, (10, 20))

        b = Actor("alien")
        b.angle = 90
        b.opacity = 0.5
        b.flip_h = b.flip_v = b.flip_d = True
        b.topleft = (10, 20)
        self.assertEqual(a.pos, b.pos)
        self.assertEqual((a.width, a.height), (b.width, b.height))

    def test_sprite_kwarg(self):
        with self.assertRaisesRegex(TypeError, r"instead of an image name, e\.g\. Actor\(fox_walk\)"):
            Actor("alien", sprite=1)

    def test_misspelled_pos(self):
        for name in ["position", "postion"]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(TypeError, r"did you mean 'pos'\?"):
                    Actor("alien", **{name: (1, 2)})

    def test_typos_of_other_kwargs(self):
        cases = {"ancor": "anchor", "colision_rect": "collision_rect", "centre": "center",
                 "sclae": "scale", "opactiy": "opacity"}
        for typo, suggestion in cases.items():
            with self.subTest(typo=typo):
                with self.assertRaisesRegex(TypeError, f"did you mean '{suggestion}'"):
                    Actor("alien", **{typo: (1, 2)})

    def test_any_other_unknown_kwarg(self):
        with self.assertRaises(TypeError) as cm:
            Actor("alien", speed=5)
        self.assertEqual(
            cm.exception.args[0],
            "Unexpected keyword argument 'speed'. Actor() accepts a position such as "
            "pos or midbottom, anchor, collision_rect, scale, angle, opacity, flip_h, "
            "flip_v, flip_d and visible.",
        )

    def test_two_edges_on_the_same_side(self):
        with self.assertRaisesRegex(TypeError, r"not just left=1\."):
            Actor("alien", left=1, right=2)

    def test_set_pos_relative_to_anchor(self):
        a = Actor("alien", anchor=(10, 10))
        a.pos = (100, 100)
        self.assertEqual(a.topleft, (90, 90))

    def test_right_angle(self):
        a = Actor("alien")
        self.assertEqual(a.image, "alien")
        self.assertEqual(a.topleft, (0, 0))
        self.assertEqual(a.pos, (33.0, 46.0))
        self.assertEqual(a.width, 66)
        self.assertEqual(a.height, 92)
        a.angle += 90.0
        self.assertEqual(a.angle, 90.0)
        self.assertEqual(a.topleft, (-13, 13))
        self.assertEqual(a.pos, (33.0, 46.0))
        self.assertEqual(a.width, 92)
        self.assertEqual(a.height, 66)

    def test_rotation(self):
        """An actor's pos must not drift with continued small rotation."""
        a = Actor("alien", pos=(100.0, 100.0))
        for _ in range(360):
            a.angle += 1.0
        self.assertEqual(a.pos, (100.0, 100.0))

    def test_opacity_default(self):
        """Ensure opacity is initially set to its default value."""
        a = Actor("alien")

        self.assertEqual(a.opacity, 1.0)

    def test_opacity_value(self):
        """Ensure opacity gives the value it was set to."""
        a = Actor("alien")
        expected_opacity = 0.54321

        a.opacity = expected_opacity

        self.assertEqual(a.opacity, expected_opacity)

    def test_opacity_min_boundry(self):
        """Ensure opacity is not set below minimum allowable level."""
        a = Actor("alien")

        a.opacity = -0.1

        self.assertEqual(a.opacity, 0.0)

    def test_opacity_max_boundry(self):
        """Ensure opacity is not set above maximum allowable level."""
        a = Actor("alien")

        a.opacity = 1.1

        self.assertEqual(a.opacity, 1.0)

    def test_dir_correct(self):
        """Everything returned by dir should be indexable as an attribute."""
        a = Actor("alien")
        for attribute in dir(a):
            a.__getattr__(attribute)
