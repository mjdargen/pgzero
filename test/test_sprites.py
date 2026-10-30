"""Tests for sprite sheets, animated sprites and SpriteActor.

The fixture ``sprites/walk.png`` is a 64x32 sheet of 16x16 frames laid out
in 4 columns and 2 rows. Each frame is a solid colour
``(col * 60, 100 + row * 100, 50)`` except for pixel (0, 0), which is magenta
so that colour-key handling can be tested.

"""
import unittest
from unittest import mock

import pygame

from pgzero.loaders import set_root
from pgzero.sprites import SpriteSheet, Sprite, SpriteActor

MAGENTA = (255, 0, 255, 255)


def frame_colour(col, row):
    return (col * 60, 100 + row * 100, 50, 255)


class FakeTicks:
    """Stand-in for pygame.time.get_ticks() that we can advance manually."""

    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now


class SpriteTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 200))
        set_root(__file__)

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()

    def setUp(self):
        self.ticks = FakeTicks()
        patcher = mock.patch("pygame.time.get_ticks", self.ticks)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_sprite(self, **kwargs):
        args = dict(
            image_name="walk",
            frame_width=16,
            frame_height=16,
            row_number=0,
            frame_count=4,
            fps=10,
        )
        args.update(kwargs)
        return Sprite(**args)


class SpriteSheetTest(SpriteTestBase):
    def test_image_at(self):
        """image_at() cuts the given rectangle out of the sheet."""
        sheet = SpriteSheet("walk")
        img = sheet.image_at((16, 16, 16, 16))
        self.assertEqual(img.get_size(), (16, 16))
        self.assertEqual(tuple(img.get_at((5, 5))), frame_colour(1, 1))

    def test_image_at_no_color_key(self):
        sheet = SpriteSheet("walk")
        img = sheet.image_at((0, 0, 16, 16))
        self.assertIsNone(img.get_colorkey())

    def test_image_at_explicit_color_key(self):
        sheet = SpriteSheet("walk")
        img = sheet.image_at((0, 0, 16, 16), color_key=(1, 2, 3))
        self.assertEqual(tuple(img.get_colorkey())[:3], (1, 2, 3))

    def test_image_at_color_key_minus_one_uses_top_left_pixel(self):
        """A color_key of -1 means 'use the colour of pixel (0, 0)'."""
        sheet = SpriteSheet("walk")
        img = sheet.image_at((0, 0, 16, 16), color_key=-1)
        self.assertEqual(tuple(img.get_colorkey())[:3], MAGENTA[:3])

    def test_images_at(self):
        sheet = SpriteSheet("walk")
        imgs = sheet.images_at([(0, 0, 16, 16), (48, 16, 16, 16)])
        self.assertEqual(len(imgs), 2)
        self.assertEqual(tuple(imgs[0].get_at((5, 5))), frame_colour(0, 0))
        self.assertEqual(tuple(imgs[1].get_at((5, 5))), frame_colour(3, 1))

    def test_load_strip(self):
        """load_strip() returns consecutive frames moving to the right."""
        sheet = SpriteSheet("walk")
        imgs = sheet.load_strip((0, 16, 16, 16), 4)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in imgs],
            [frame_colour(c, 1) for c in range(4)],
        )

    def test_missing_sheet(self):
        with self.assertRaises(KeyError):
            SpriteSheet("does_not_exist")


class SpriteTest(SpriteTestBase):
    def test_frames_loaded_from_row(self):
        s = self.make_sprite(row_number=1, frame_count=3)
        self.assertEqual(len(s.images), 3)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in s.images],
            [frame_colour(c, 1) for c in range(3)],
        )

    def test_initial_state(self):
        s = self.make_sprite()
        self.assertEqual(s.frame_index, 0)
        self.assertFalse(s.finished)
        self.assertIs(s.image, s.images[0])

    def test_transparent_color_passed_to_frames(self):
        s = self.make_sprite(transparent_color=-1)
        for img in s.images:
            self.assertEqual(tuple(img.get_colorkey())[:3], MAGENTA[:3])

    def test_row_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "Row 2 is outside"):
            self.make_sprite(row_number=2)

    def test_too_many_frames(self):
        with self.assertRaisesRegex(ValueError, "past the edge"):
            self.make_sprite(frame_count=5)

    def test_zero_frames(self):
        with self.assertRaisesRegex(ValueError, "at least one frame"):
            self.make_sprite(frame_count=0)

    def test_next_frame_waits_for_frame_duration(self):
        """At 10 fps the frame shouldn't advance until 100ms have passed."""
        s = self.make_sprite(fps=10)
        self.ticks.now = 99
        self.assertIs(s.next_frame(), s.images[0])
        self.ticks.now = 100
        self.assertIs(s.next_frame(), s.images[1])
        self.assertEqual(s.frame_index, 1)

    def test_next_frame_only_advances_one_frame_per_call(self):
        s = self.make_sprite(fps=10)
        self.ticks.now = 1000
        s.next_frame()
        self.assertEqual(s.frame_index, 1)

    def test_next_frame_loops(self):
        s = self.make_sprite(fps=10, loop=True)
        for i in range(1, 5):
            self.ticks.now = i * 100
            s.next_frame()
        self.assertEqual(s.frame_index, 0)
        self.assertFalse(s.finished)

    def test_next_frame_no_loop_finishes_on_last_frame(self):
        s = self.make_sprite(fps=10, loop=False)
        for i in range(1, 4):
            self.ticks.now = i * 100
            s.next_frame()
        self.assertEqual(s.frame_index, 3)
        self.assertFalse(s.finished)

        self.ticks.now = 400
        self.assertIs(s.next_frame(), s.images[3])
        self.assertTrue(s.finished)

        # Once finished, it stays on the last frame.
        self.ticks.now = 10000
        s.next_frame()
        self.assertEqual(s.frame_index, 3)

    def test_set_frame(self):
        s = self.make_sprite()
        self.ticks.now = 500
        self.assertIs(s.set_frame(2), s.images[2])
        self.assertEqual(s.frame_index, 2)
        self.assertEqual(s.last_update_time, 500)

    def test_set_frame_clears_finished(self):
        s = self.make_sprite(loop=False)
        s.finished = True
        s.set_frame(1)
        self.assertFalse(s.finished)

    def test_set_frame_out_of_range(self):
        s = self.make_sprite()
        with self.assertRaises(ValueError):
            s.set_frame(4)
        with self.assertRaises(ValueError):
            s.set_frame(-1)

    def test_reset(self):
        s = self.make_sprite(loop=False)
        s.set_frame(3)
        s.finished = True
        s.reset()
        self.assertEqual(s.frame_index, 0)
        self.assertFalse(s.finished)

    def test_copy_is_independent(self):
        s = self.make_sprite(row_number=1, frame_count=3, fps=7,
                             transparent_color=-1, loop=False)
        s.set_frame(2)
        c = s.copy()

        self.assertIsNot(c, s)
        for attr in ("image_name", "frame_width", "frame_height",
                     "row_number", "frame_count", "fps",
                     "transparent_color", "loop"):
            self.assertEqual(getattr(c, attr), getattr(s, attr), attr)

        # The copy starts from frame 0 and doesn't share playback state.
        self.assertEqual(c.frame_index, 0)
        c.set_frame(1)
        self.assertEqual(s.frame_index, 2)


class SpriteActorTest(SpriteTestBase):
    def test_initial_image_is_first_frame(self):
        s = self.make_sprite()
        a = SpriteActor(s, pos=(50, 50))
        self.assertIs(a._orig_surf, s.images[0])
        self.assertEqual(a.pos, (50, 50))
        self.assertEqual((a.width, a.height), (16, 16))

    def test_sprite_actor_image_is_empty_string(self):
        """Sprite frames are surfaces, so there's no image name."""
        a = SpriteActor(self.make_sprite())
        self.assertEqual(a.image, "")

    def test_accepts_actor_kwargs(self):
        a = SpriteActor(self.make_sprite(), topleft=(10, 20),
                        collision_rect=(8, 8))
        self.assertEqual(a.topleft, (10, 20))
        self.assertEqual((a.width, a.height), (8, 8))

    def test_update_animation_advances(self):
        s = self.make_sprite()
        a = SpriteActor(s)
        self.ticks.now = 100
        a.update_animation()
        self.assertIs(a._orig_surf, s.images[1])

    def test_pause_and_resume(self):
        s = self.make_sprite()
        a = SpriteActor(s)
        self.assertFalse(a.paused)

        a.pause()
        self.assertTrue(a.paused)
        self.ticks.now = 100
        a.update_animation()
        self.assertEqual(s.frame_index, 0)
        self.assertIs(a._orig_surf, s.images[0])

        a.resume()
        self.assertFalse(a.paused)
        a.update_animation()
        self.assertIs(a._orig_surf, s.images[1])

    def test_draw_updates_animation(self):
        from pgzero import game
        s = self.make_sprite()
        a = SpriteActor(s)
        with mock.patch.object(game, "screen", create=True) as screen:
            self.ticks.now = 100
            a.draw()
        self.assertEqual(s.frame_index, 1)
        screen.blit.assert_called_once()
        self.assertIs(screen.blit.call_args[0][0], s.images[1])

    def test_set_new_sprite_resets_it(self):
        walk = self.make_sprite(row_number=0)
        run = self.make_sprite(row_number=1)
        run.set_frame(2)

        a = SpriteActor(walk)
        a.sprite = run
        self.assertIs(a.sprite, run)
        self.assertEqual(run.frame_index, 0)
        self.assertIs(a._orig_surf, run.images[0])

    def test_set_same_sprite_does_not_reset(self):
        s = self.make_sprite()
        a = SpriteActor(s)
        s.set_frame(2)
        a.sprite = s
        self.assertEqual(s.frame_index, 2)
        self.assertIs(a._orig_surf, s.images[2])

    def test_changing_frame_keeps_position(self):
        s = self.make_sprite()
        a = SpriteActor(s, pos=(40, 60))
        self.ticks.now = 100
        a.update_animation()
        self.assertEqual(a.pos, (40, 60))


if __name__ == "__main__":
    unittest.main()
