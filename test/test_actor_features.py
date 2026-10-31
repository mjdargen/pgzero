"""Tests for Actor features added in pgzero-plus: scale, flips, custom
collision rectangles, image lists/animation, and helper methods.

The ``alien`` test image is 66x92 pixels.

"""
import unittest
from math import isclose
from unittest import mock

import pygame

from pgzero import game
from pgzero.actor import Actor, rotate_vector
from pgzero.loaders import set_root
from pgzero.rect import Rect

ALIEN_W, ALIEN_H = 66, 92


def assert_pos_close(test, actual, expected, places=7):
    test.assertAlmostEqual(actual[0], expected[0], places=places)
    test.assertAlmostEqual(actual[1], expected[1], places=places)


class ActorTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 100))
        set_root(__file__)

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()


class RotateVectorTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(rotate_vector(3, 4, 0), (3, 4))

    def test_90_degrees_matches_pygame_rotation(self):
        """pygame rotates anticlockwise on screen (y points down)."""
        x, y = rotate_vector(1, 0, 90)
        self.assertTrue(isclose(x, 0, abs_tol=1e-9))
        self.assertTrue(isclose(y, -1))


class ImagePropertyTest(ActorTestBase):
    def test_image_name(self):
        self.assertEqual(Actor("alien").image, "alien")

    def test_image_surface_returns_empty_string(self):
        """Actors made from surfaces report "" so string comparisons work."""
        a = Actor(pygame.Surface((10, 20)))
        self.assertEqual(a.image, "")
        self.assertEqual((a.width, a.height), (10, 20))

    def test_image_comparison(self):
        a = Actor("alien")
        self.assertTrue(a.image == "alien")

    def test_change_image_keeps_pos(self):
        a = Actor("alien", pos=(50, 60))
        a.image = pygame.Surface((10, 10))
        self.assertEqual(a.pos, (50, 60))
        self.assertEqual((a.width, a.height), (10, 10))

    def test_unload_surface_image_is_noop(self):
        a = Actor(pygame.Surface((10, 10)))
        a.unload_image()  # must not raise


class ScaleTest(ActorTestBase):
    def test_default(self):
        self.assertEqual(Actor("alien").scale, 1.0)

    def test_scale_changes_size(self):
        a = Actor("alien")
        a.scale = 2
        self.assertEqual((a.width, a.height), (ALIEN_W * 2, ALIEN_H * 2))
        self.assertEqual(
            a._build_transformed_surf().get_size(),
            (ALIEN_W * 2, ALIEN_H * 2),
        )

    def test_scale_down(self):
        a = Actor("alien")
        a.scale = 0.5
        self.assertEqual((a.width, a.height), (33, 46))

    def test_scale_keeps_pos(self):
        a = Actor("alien", pos=(100, 100))
        a.scale = 3
        self.assertEqual(a.pos, (100, 100))

    def test_scale_with_anchor(self):
        a = Actor("alien", pos=(100, 100), anchor=("left", "bottom"))
        a.scale = 2
        self.assertEqual(a.pos, (100, 100))
        self.assertEqual(a.bottomleft, (100, 100))

    def test_tiny_scale_surface_is_at_least_one_pixel(self):
        a = Actor("alien")
        a.scale = 0.001
        self.assertEqual(a._build_transformed_surf().get_size(), (1, 1))

    def test_scale_and_rotate(self):
        a = Actor("alien", pos=(100, 100))
        a.scale = 2
        a.angle = 90
        self.assertEqual((a.width, a.height), (ALIEN_H * 2, ALIEN_W * 2))
        assert_pos_close(self, a.pos, (100, 100))


class FlipTest(ActorTestBase):
    def setUp(self):
        # An asymmetric 4x2 image: a single red pixel in the top-left.
        self.surf = pygame.Surface((4, 2), pygame.SRCALPHA)
        self.surf.fill((0, 0, 255, 255))
        self.surf.set_at((0, 0), (255, 0, 0, 255))

    def red_pixel(self, actor):
        s = actor._build_transformed_surf()
        for x in range(s.get_width()):
            for y in range(s.get_height()):
                if tuple(s.get_at((x, y))) == (255, 0, 0, 255):
                    return x, y

    def test_defaults(self):
        a = Actor("alien")
        self.assertEqual((a.flip_h, a.flip_v, a.flip_d), (False,) * 3)

    def test_flip_h(self):
        a = Actor(self.surf)
        a.flip_h = True
        self.assertTrue(a.flip_h)
        self.assertEqual(self.red_pixel(a), (3, 0))
        self.assertEqual((a.width, a.height), (4, 2))

    def test_flip_v(self):
        a = Actor(self.surf)
        a.flip_v = True
        self.assertEqual(self.red_pixel(a), (0, 1))

    def test_flip_h_and_v(self):
        a = Actor(self.surf)
        a.flip_h = True
        a.flip_v = True
        self.assertEqual(self.red_pixel(a), (3, 1))

    def test_flip_d_transposes(self):
        a = Actor(self.surf)
        a.flip_d = True
        self.assertEqual((a.width, a.height), (2, 4))
        self.assertEqual(a._build_transformed_surf().get_size(), (2, 4))
        self.assertEqual(self.red_pixel(a), (0, 0))

    def test_flip_d_moves_pixel_across_diagonal(self):
        self.surf.set_at((3, 0), (255, 0, 0, 255))
        self.surf.set_at((0, 0), (0, 0, 255, 255))
        a = Actor(self.surf)
        a.flip_d = True
        self.assertEqual(self.red_pixel(a), (0, 3))

    def test_flip_d_anchor_follows_image(self):
        """Anchors are mirrored across the diagonal along with the image."""
        a = Actor("alien", pos=(0, 0), anchor=("right", "top"))
        a.flip_d = True
        # Top-right of the original becomes bottom-left after transposing.
        assert_pos_close(self, a.bottomleft, (0, 0))

    def test_flip_d_anchor_is_drawn_there(self):
        """The anchored pixel is drawn at the actor's pos."""
        a = Actor(self.surf, pos=(10, 20), anchor=("left", "top"))
        a.flip_d = True
        with mock.patch.object(game, "screen", create=True) as screen:
            a.draw()
        surf, (x, y) = screen.blit.call_args[0]
        rx, ry = self.red_pixel(a)
        self.assertEqual((x + rx, y + ry), (10, 20))

    def test_flip_d_with_scale_and_offset_body(self):
        a = Actor("alien", pos=(100, 100), anchor=("left", "top"),
                  collision_rect=(20, 30, 10, 5))
        a.scale = 2
        a.flip_d = True
        self.assertEqual((a.width, a.height), (60, 40))
        assert_pos_close(self, a.topleft, (100, 100))

    def test_unflip(self):
        a = Actor(self.surf)
        a.flip_h = True
        a.flip_h = False
        self.assertEqual(self.red_pixel(a), (0, 0))

    def test_flip_keeps_pos(self):
        a = Actor("alien", pos=(50, 50), anchor=("left", "top"))
        a.flip_h = True
        a.flip_v = True
        self.assertEqual(a.pos, (50, 50))
        a.flip_d = True
        self.assertEqual(a.pos, (50, 50))

    def test_flip_d_anchor(self):
        """With a diagonal flip, a top-left anchor stays at the top-left."""
        a = Actor("alien", pos=(0, 0), anchor=("left", "top"))
        a.flip_d = True
        self.assertEqual((a.width, a.height), (ALIEN_H, ALIEN_W))
        assert_pos_close(self, a.topleft, (0, 0))


class CollisionRectTest(ActorTestBase):
    def test_default_is_whole_image(self):
        a = Actor("alien")
        self.assertEqual((a.width, a.height), (ALIEN_W, ALIEN_H))
        self.assertIs(a.collision_rect, a._rect)

    def test_centered_body(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30))
        self.assertEqual((a.width, a.height), (20, 30))
        self.assertEqual(a.pos, (100, 100))
        self.assertEqual(a.center, (100, 100))
        # The image is drawn centred on the body.
        self.assertEqual(a._image_topleft(),
                         (100 - ALIEN_W / 2, 100 - ALIEN_H / 2))

    def test_offset_body(self):
        """The 4-tuple offset moves the body centre relative to the image."""
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 10, 5))
        self.assertEqual(a.center, (100, 100))
        self.assertEqual(a._image_topleft(),
                         (90 - ALIEN_W / 2, 95 - ALIEN_H / 2))

    def test_anchor_is_relative_to_body(self):
        a = Actor("alien", pos=(10, 10), anchor=("left", "top"),
                  collision_rect=(20, 30))
        self.assertEqual(a.topleft, (10, 10))
        self.assertEqual(a.bottomright, (30, 40))

    def test_symbolic_position_uses_body(self):
        a = Actor("alien", bottomleft=(0, 100), collision_rect=(20, 30))
        self.assertEqual(a.bottomleft, (0, 100))
        self.assertEqual(a.topleft, (0, 70))

    def test_scaled_body(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 4, 2))
        a.scale = 2
        self.assertEqual((a.width, a.height), (40, 60))
        self.assertEqual(a.center, (100, 100))
        self.assertEqual(a._image_topleft(),
                         (92 - ALIEN_W, 96 - ALIEN_H))

    def test_rotated_body(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30))
        a.angle = 90
        self.assertAlmostEqual(a.width, 30)
        self.assertAlmostEqual(a.height, 20)
        assert_pos_close(self, a.pos, (100, 100))

    def test_rotated_offset_body_image_follows(self):
        """Rotating 180 degrees mirrors the image offset around the body."""
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 10, 5))
        a.angle = 180
        x, y = a._image_topleft()
        s = a._build_transformed_surf()
        image_center = (x + s.get_width() / 2, y + s.get_height() / 2)
        assert_pos_close(self, image_center, (110, 105))

    def test_flip_h_mirrors_offset(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 10, 0))
        a.flip_h = True
        x, _ = a._image_topleft()
        self.assertAlmostEqual(x + ALIEN_W / 2, 110)

    def test_invalid_spec_in_constructor(self):
        with self.assertRaises(ValueError):
            Actor("alien", collision_rect=(1, 2, 3))

    def test_set_collision_rect(self):
        a = Actor("alien", pos=(100, 100))
        a.collision_rect = (20, 30)
        self.assertEqual((a.width, a.height), (20, 30))

    def test_set_collision_rect_does_not_move_image(self):
        a = Actor("alien", pos=(100, 100))
        before = a._image_topleft()
        a.collision_rect = (20, 30, 10, 5)
        assert_pos_close(self, a._image_topleft(), before)
        # ...but the body moved to sit over the offset region.
        self.assertEqual(a.center, (110, 105))

    def test_reset_collision_rect_to_none(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 10, 5))
        before = a._image_topleft()
        a.collision_rect = None
        self.assertEqual((a.width, a.height), (ALIEN_W, ALIEN_H))
        assert_pos_close(self, a._image_topleft(), before)

    def test_set_invalid_collision_rect(self):
        a = Actor("alien")
        with self.assertRaises(ValueError):
            a.collision_rect = (1, 2, 3)

    def test_collision_rect_survives_image_change(self):
        a = Actor("alien", collision_rect=(20, 30))
        a.image = "alien"
        self.assertEqual((a.width, a.height), (20, 30))

    def test_draw_collision_rect(self):
        a = Actor("alien", topleft=(5, 6), collision_rect=(20, 30))
        with mock.patch.object(game, "screen", create=True) as screen, \
                mock.patch("pygame.draw.rect") as draw_rect:
            a.draw_collision_rect()
        draw_rect.assert_called_once_with(
            screen, (255, 0, 0), (5, 6, 20, 30), 2
        )

    def test_draw_blits_image_at_image_topleft(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(20, 30, 10, 5))
        with mock.patch.object(game, "screen", create=True) as screen:
            a.draw()
        surf, pos = screen.blit.call_args[0]
        self.assertEqual(surf.get_size(), (ALIEN_W, ALIEN_H))
        self.assertEqual(pos, a._image_topleft())


class CollisionTest(ActorTestBase):
    def test_colliderect_actor(self):
        a = Actor("alien", topleft=(0, 0))
        b = Actor("alien", topleft=(50, 50))
        c = Actor("alien", topleft=(500, 500))
        self.assertTrue(a.colliderect(b))
        self.assertFalse(a.colliderect(c))

    def test_colliderect_uses_collision_rect(self):
        a = Actor("alien", pos=(0, 0), collision_rect=(10, 10))
        b = Actor("alien", pos=(30, 0), collision_rect=(10, 10))
        # The images overlap but the bodies don't.
        self.assertFalse(a.colliderect(b))

    def test_colliderect_rect(self):
        a = Actor("alien", topleft=(0, 0))
        self.assertTrue(a.colliderect(Rect(10, 10, 5, 5)))
        self.assertTrue(a.colliderect((10, 10, 5, 5)))
        self.assertFalse(a.colliderect(Rect(100, 100, 5, 5)))

    def test_collidelist(self):
        a = Actor("alien", topleft=(0, 0))
        others = [
            Actor("alien", topleft=(500, 500)),
            Rect(1000, 0, 5, 5),
            Actor("alien", topleft=(10, 10)),
            Actor("alien", topleft=(20, 20)),
        ]
        self.assertEqual(a.collidelist(others), 2)

    def test_collidelist_no_hit(self):
        a = Actor("alien", topleft=(0, 0))
        self.assertEqual(a.collidelist([Rect(500, 500, 1, 1)]), -1)
        self.assertEqual(a.collidelist([]), -1)

    def test_collidepoint(self):
        a = Actor("alien", pos=(100, 100), collision_rect=(10, 10))
        self.assertTrue(a.collidepoint((100, 100)))
        self.assertTrue(a.collidepoint(100, 100))
        self.assertFalse(a.collidepoint((120, 100)))


class OwnAttributesTest(ActorTestBase):
    def test_images_is_an_ordinary_attribute(self):
        """Students can keep their own list of images on an actor."""
        a = Actor("alien")
        a.images = ["alien_as_webp", "alien"]
        self.assertEqual(a.images, ["alien_as_webp", "alien"])
        self.assertEqual(a.image, "alien")


class AngleDistanceTest(ActorTestBase):
    def test_angle_to_point(self):
        a = Actor("alien", pos=(100, 100))
        self.assertAlmostEqual(a.angle_to((200, 100)), 0)
        self.assertAlmostEqual(a.angle_to((100, 0)), 90)
        self.assertAlmostEqual(a.angle_to((0, 100)), 180)
        self.assertAlmostEqual(a.angle_to((100, 200)), -90)

    def test_angle_to_actor(self):
        a = Actor("alien", pos=(0, 0))
        b = Actor("alien", pos=(10, -10))
        self.assertAlmostEqual(a.angle_to(b), 45)

    def test_distance_to_point(self):
        a = Actor("alien", pos=(0, 0))
        self.assertAlmostEqual(a.distance_to((3, 4)), 5)

    def test_distance_to_actor(self):
        a = Actor("alien", pos=(0, 0))
        b = Actor("alien", pos=(-6, 8))
        self.assertAlmostEqual(a.distance_to(b), 10)
        self.assertAlmostEqual(b.distance_to(a), 10)


if __name__ == "__main__":
    unittest.main()
