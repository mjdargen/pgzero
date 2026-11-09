"""Tests for sprite sheets, Sprites, and Actors playing Sprites.

The fixture ``sprites/walk.png`` is a 64x32 sheet of 16x16 frames laid out
in 4 columns and 2 rows. Each frame is a solid color
``(col * 60, 100 + row * 100, 50)`` except for pixel (0, 0), which is magenta
so that color-key handling can be tested.

``sprites/spaced.png`` (a copy of ``maps/tiles.png``) has 3x2 frames of 8x8
pixels with a 1 pixel margin and 2 pixels of spacing. Each frame is filled
with ``(col * 100, row * 200, 77)``.

``sprites/padded.png`` has 4x2 frames of 8x8 pixels, some left empty: row 0 is
frame, empty, frame, empty and row 1 is frame, frame, empty, empty. Filled
frames are ``frame_color(col, row)``.

"""
import unittest
from unittest import mock

import pygame

from pgzero.loaders import images, set_root
from pgzero.actor import Actor
from pgzero.sprites import SpriteSheet, Sprite

# A size for the stand-in screen, so that Actor.draw() can tell the actor is on it
SCREEN_SIZE = {"get_size.return_value": (800, 600)}

MAGENTA = (255, 0, 255, 255)


def frame_color(col, row):
    return (col * 60, 100 + row * 100, 50, 255)


def drawn_color(image, pos):
    """The color a pixel of image comes out as when drawn on black."""
    surf = pygame.Surface(image.get_size())
    surf.blit(image, (0, 0))
    return tuple(surf.get_at(pos))[:3]


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
            row=0,
            frames=4,
            fps=10,
        )
        args.update(kwargs)
        return Sprite(**args)

    def make_actor(self, sprite=None, **kwargs):
        """Make an Actor playing a Sprite, whose animation clock has started at time 0."""
        a = Actor(sprite or self.make_sprite(), **kwargs)
        a._update_animation()
        return a

    def advance_to(self, actor, now):
        self.ticks.now = now
        actor._update_animation()


class SpriteSheetTest(SpriteTestBase):
    def test_image_at(self):
        """image_at() cuts the given rectangle out of the sheet."""
        sheet = SpriteSheet("walk")
        img = sheet.image_at((16, 16, 16, 16))
        self.assertEqual(img.get_size(), (16, 16))
        self.assertEqual(tuple(img.get_at((5, 5))), frame_color(1, 1))

    def test_image_at_no_color_key(self):
        sheet = SpriteSheet("walk")
        img = sheet.image_at((0, 0, 16, 16))
        self.assertEqual(drawn_color(img, (0, 0)), MAGENTA[:3])

    def test_image_at_color_key_is_transparent(self):
        """Pixels of the color key's color are not drawn."""
        sheet = SpriteSheet("walk")
        for color_key in [MAGENTA[:3], 'magenta']:
            with self.subTest(color_key=color_key):
                img = sheet.image_at((0, 0, 16, 16), color_key=color_key)
                self.assertEqual(drawn_color(img, (0, 0)), (0, 0, 0))
                self.assertEqual(drawn_color(img, (5, 5)), frame_color(0, 0)[:3])

    def test_image_at_color_key_minus_one_uses_top_left_pixel(self):
        """A color_key of -1 means 'use the color of pixel (0, 0)'."""
        sheet = SpriteSheet("walk")
        img = sheet.image_at((0, 0, 16, 16), color_key=-1)
        self.assertEqual(drawn_color(img, (0, 0)), (0, 0, 0))
        self.assertEqual(drawn_color(img, (5, 5)), frame_color(0, 0)[:3])

    def test_images_at(self):
        sheet = SpriteSheet("walk")
        imgs = sheet.images_at([(0, 0, 16, 16), (48, 16, 16, 16)])
        self.assertEqual(len(imgs), 2)
        self.assertEqual(tuple(imgs[0].get_at((5, 5))), frame_color(0, 0))
        self.assertEqual(tuple(imgs[1].get_at((5, 5))), frame_color(3, 1))

    def test_load_strip(self):
        """load_strip() returns consecutive frames moving to the right."""
        sheet = SpriteSheet("walk")
        imgs = sheet.load_strip((0, 16, 16, 16), 4)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in imgs],
            [frame_color(c, 1) for c in range(4)],
        )

    def test_missing_sheet(self):
        with self.assertRaises(KeyError):
            SpriteSheet("does_not_exist")


class SpriteTest(SpriteTestBase):
    def test_frames_loaded_from_row(self):
        s = self.make_sprite(row=1, frames=3)
        self.assertEqual(len(s.images), 3)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in s.images],
            [frame_color(c, 1) for c in range(3)],
        )

    def test_defaults_to_every_frame_in_the_top_row(self):
        s = Sprite("walk", 16, 16)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in s.images],
            [frame_color(c, 0) for c in range(4)],
        )

    def test_transparent_color_applies_to_every_frame(self):
        s = self.make_sprite(transparent_color=-1)
        for img in s.images:
            self.assertEqual(drawn_color(img, (0, 0)), (0, 0, 0))

    def test_list_of_image_names(self):
        """A Sprite can be made from separate images in the images folder."""
        s = Sprite(["alien", "alien_as_webp"], fps=4, loop=False)
        self.assertEqual(s.images, [images.alien, images.alien_as_webp])
        self.assertEqual(s.fps, 4)
        self.assertFalse(s.loop)

    def test_list_of_images_rejects_sheet_arguments(self):
        for kwargs in [dict(frame_width=16), dict(row=1), dict(transparent_color=-1),
                       dict(spacing=2), dict(margin=1)]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(TypeError, "only used with a sprite sheet"):
                    Sprite(["alien"], **kwargs)

    def test_sheet_needs_frame_size(self):
        with self.assertRaisesRegex(TypeError, "needs frame_width and frame_height"):
            Sprite("walk")

    def test_row_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "Row 2 is outside"):
            self.make_sprite(row=2)

    def test_frames_wrap_onto_the_next_row(self):
        """Frames are read like a book, carrying on at the start of the next row."""
        s = self.make_sprite(frames=6)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in s.images],
            [frame_color(c, 0) for c in range(4)] + [frame_color(c, 1) for c in range(2)],
        )

    def test_too_many_frames(self):
        with self.assertRaisesRegex(ValueError, "has 8 frames from the start of row 0"):
            self.make_sprite(frames=9)
        with self.assertRaisesRegex(ValueError, "has 4 frames from the start of row 1"):
            self.make_sprite(row=1, frames=5)

    def test_spacing_and_margin(self):
        s = Sprite("spaced", 8, 8, frames=6, spacing=2, margin=1)
        self.assertEqual(
            [tuple(i.get_at((5, 5))) for i in s.images],
            [(c * 100, r * 200, 77, 255) for r in range(2) for c in range(3)],
        )

    def test_spacing_and_margin_without_frames(self):
        """Leaving out frames uses every frame across the row, between the gaps."""
        s = Sprite("spaced", 8, 8, row=1, spacing=2, margin=1)
        self.assertEqual([tuple(i.get_at((5, 5))) for i in s.images],
                         [(c * 100, 200, 77, 255) for c in range(3)])

    def test_empty_frames_at_the_end_are_skipped(self):
        """Leaving out frames skips empty padding at the end of the row."""
        s = Sprite("padded", 8, 8, row=1)
        self.assertEqual([tuple(i.get_at((5, 5))) for i in s.images],
                         [frame_color(0, 1), frame_color(1, 1)])

    def test_empty_frames_in_the_middle_are_kept(self):
        s = Sprite("padded", 8, 8, row=0)
        self.assertEqual(len(s.images), 3)
        self.assertEqual(s.images[1].get_bounding_rect().width, 0)

    def test_empty_frames_kept_when_frames_given(self):
        """Giving frames always gives exactly that many, blank or not."""
        s = Sprite("padded", 8, 8, row=1, frames=4)
        self.assertEqual(len(s.images), 4)

    def test_row_with_no_visible_frames(self):
        # The frames are solid colors, so making each frame's own color
        # see-through leaves the whole row empty.
        with self.assertRaisesRegex(ValueError, "Row 1 of the sprite sheet 'padded' has no visible frames"):
            Sprite("padded", 8, 8, row=1, transparent_color=-1)

    def test_negative_spacing(self):
        with self.assertRaisesRegex(ValueError, "can't be negative"):
            Sprite("spaced", 8, 8, spacing=-1)

    def test_zero_frames(self):
        with self.assertRaisesRegex(ValueError, "at least one frame"):
            self.make_sprite(frames=0)
        with self.assertRaisesRegex(ValueError, "at least one frame"):
            Sprite([])

    def test_invalid_fps(self):
        with self.assertRaisesRegex(ValueError, "fps must be more than 0"):
            self.make_sprite(fps=0)



class ActorSpriteTest(SpriteTestBase):
    def test_initial_image_is_first_frame(self):
        s = self.make_sprite()
        a = Actor(s, pos=(50, 50))
        self.assertIs(a._orig_surf, s.images[0])
        self.assertEqual(a.frame, 0)
        self.assertFalse(a.animation_finished)
        self.assertEqual(a.pos, (50, 50))
        self.assertEqual((a.width, a.height), (16, 16))

    def test_image_is_empty_string(self):
        """Sprite frames are surfaces, so there's no image name."""
        a = Actor(self.make_sprite())
        self.assertEqual(a.image, "")

    def test_accepts_actor_kwargs(self):
        a = Actor(self.make_sprite(), topleft=(10, 20),
                        collision_rect=(8, 8))
        self.assertEqual(a.topleft, (10, 20))
        self.assertEqual((a.width, a.height), (8, 8))

    def test_time_before_first_draw_does_not_count(self):
        """The animation starts when the actor is first drawn."""
        a = Actor(self.make_sprite())
        self.advance_to(a, 5000)
        self.assertEqual(a.frame, 0)
        self.advance_to(a, 5100)
        self.assertEqual(a.frame, 1)

    def test_waits_for_frame_duration(self):
        """At 10 fps the frame shouldn't advance until 100ms have passed."""
        s = self.make_sprite(fps=10)
        a = self.make_actor(s)
        self.advance_to(a, 99)
        self.assertIs(a._orig_surf, s.images[0])
        self.advance_to(a, 100)
        self.assertEqual(a.frame, 1)
        self.assertIs(a._orig_surf, s.images[1])

    def test_keeps_to_fps_at_60_frames_a_second(self):
        """The fps is kept even when it doesn't divide into 60."""
        for fps in [10, 12, 24, 30]:
            with self.subTest(fps=fps):
                self.ticks.now = 0
                a = self.make_actor(self.make_sprite(fps=fps))
                changes = 0
                last = a.frame
                for frame in range(1, 601):  # 10 seconds at 60 fps
                    self.advance_to(a, round(frame * 1000 / 60))
                    if a.frame != last:
                        changes += 1
                        last = a.frame
                self.assertAlmostEqual(changes, fps * 10, delta=1)

    def test_catches_up_after_a_long_gap(self):
        a = self.make_actor(self.make_sprite(fps=10))
        self.advance_to(a, 250)
        self.assertEqual(a.frame, 2)
        self.advance_to(a, 300)
        self.assertEqual(a.frame, 3)

    def test_loops(self):
        a = self.make_actor(self.make_sprite(fps=10, loop=True))
        self.advance_to(a, 400)
        self.assertEqual(a.frame, 0)
        self.assertFalse(a.animation_finished)

    def test_no_loop_finishes_on_last_frame(self):
        s = self.make_sprite(fps=10, loop=False)
        a = self.make_actor(s)
        self.advance_to(a, 300)
        self.assertEqual(a.frame, 3)
        self.assertFalse(a.animation_finished)

        self.advance_to(a, 400)
        self.assertIs(a._orig_surf, s.images[3])
        self.assertTrue(a.animation_finished)

        # Once finished, it stays on the last frame.
        self.advance_to(a, 10000)
        self.assertEqual(a.frame, 3)

    def test_set_frame(self):
        s = self.make_sprite(loop=False)
        a = self.make_actor(s)
        self.advance_to(a, 1000)
        self.assertTrue(a.animation_finished)

        a.frame = 2
        self.assertIs(a._orig_surf, s.images[2])
        self.assertFalse(a.animation_finished)
        # The new frame shows for a whole frame duration
        self.advance_to(a, 1050)
        self.advance_to(a, 1149)
        self.assertEqual(a.frame, 2)
        self.advance_to(a, 1150)
        self.assertEqual(a.frame, 3)

    def test_set_frame_out_of_range(self):
        a = self.make_actor()
        for frame in [4, -1]:
            with self.assertRaisesRegex(ValueError, "frames 0 to 3"):
                a.frame = frame

    def test_reset_animation(self):
        a = self.make_actor(self.make_sprite(loop=False))
        self.advance_to(a, 1000)
        a.reset_animation()
        self.assertEqual(a.frame, 0)
        self.assertFalse(a.animation_finished)

    def test_pause_and_resume(self):
        s = self.make_sprite()
        a = self.make_actor(s)
        self.assertFalse(a.animation_paused)

        a.pause_animation()
        self.assertTrue(a.animation_paused)
        self.advance_to(a, 1000)
        self.assertIs(a._orig_surf, s.images[0])

        # Time spent paused doesn't count
        a.resume_animation()
        self.assertFalse(a.animation_paused)
        self.advance_to(a, 1050)
        self.assertEqual(a.frame, 0)
        self.advance_to(a, 1150)
        self.assertIs(a._orig_surf, s.images[1])

    def test_draw_updates_animation(self):
        from pgzero import game
        s = self.make_sprite()
        a = self.make_actor(s)
        with mock.patch.object(game, "screen", create=True, **SCREEN_SIZE) as screen:
            self.ticks.now = 100
            a.draw()
        self.assertEqual(a.frame, 1)
        screen.blit.assert_called_once()
        self.assertIs(screen.blit.call_args[0][0], s.images[1])

    def test_set_new_sprite_starts_it_from_the_beginning(self):
        walk = self.make_sprite(row=0)
        run = self.make_sprite(row=1)

        a = self.make_actor(walk)
        self.advance_to(a, 200)
        a.sprite = run
        self.assertIs(a.sprite, run)
        self.assertEqual(a.frame, 0)
        self.assertIs(a._orig_surf, run.images[0])

    def test_set_same_sprite_does_not_restart(self):
        s = self.make_sprite()
        a = self.make_actor(s)
        self.advance_to(a, 200)
        a.sprite = s
        self.assertEqual(a.frame, 2)
        self.assertIs(a._orig_surf, s.images[2])

    def test_set_finished_sprite_plays_again(self):
        """e.g. pressing attack again replays an attack that doesn't loop."""
        attack = self.make_sprite(loop=False)
        a = self.make_actor(attack)
        self.advance_to(a, 1000)
        self.assertTrue(a.animation_finished)
        a.sprite = attack
        self.assertEqual(a.frame, 0)
        self.assertFalse(a.animation_finished)
        # Like any new animation, its timing starts when it is next drawn
        self.advance_to(a, 1000)
        self.advance_to(a, 1100)
        self.assertEqual(a.frame, 1)

    def test_actors_can_share_a_sprite(self):
        """Each actor keeps its own place in a shared Sprite."""
        walk = self.make_sprite(row=0)
        stand = self.make_sprite(row=1)
        a = self.make_actor(walk)
        b = self.make_actor(walk)

        self.advance_to(a, 200)
        self.advance_to(b, 200)
        a.sprite = stand
        a.sprite = walk
        self.advance_to(b, 200)

        self.assertEqual(a.frame, 0)
        self.assertEqual(b.frame, 2)
        self.assertIs(b._orig_surf, walk.images[2])

    def test_list_of_images(self):
        s = Sprite(["alien", "alien_as_webp"], fps=10)
        a = self.make_actor(s)
        self.advance_to(a, 100)
        self.assertIs(a._orig_surf, images.alien_as_webp)

    def test_changing_frame_keeps_position(self):
        a = self.make_actor(pos=(40, 60))
        self.advance_to(a, 100)
        self.assertEqual(a.pos, (40, 60))

    def test_holds_still_while_game_is_paused(self):
        """game.pause() freezes animations; resuming carries on from the same frame."""
        from pgzero import game as game_module
        from pgzero.game import Game

        g = Game()
        with mock.patch.object(game_module, "current_game", g):
            s = self.make_sprite(fps=10)
            a = self.make_actor(s)
            self.advance_to(a, 100)
            self.assertEqual(a.frame, 1)

            g.pause()
            self.advance_to(a, 1000)
            self.assertEqual(a.frame, 1)

            g.resume()
            self.advance_to(a, 1050)
            self.assertEqual(a.frame, 1)
            self.advance_to(a, 1150)
            self.assertEqual(a.frame, 2)


    def test_keeps_time_while_hidden(self):
        """A hidden actor's animation carries on, like Godot's AnimatedSprite2D."""
        from pgzero import game
        s = self.make_sprite(fps=10)
        a = self.make_actor(s)
        a.visible = False
        with mock.patch.object(game, "screen", create=True, **SCREEN_SIZE):
            self.ticks.now = 200
            a.draw()  # hidden: nothing happens
            self.assertEqual(a.frame, 0)
            a.visible = True
            self.ticks.now = 250
            a.draw()
        self.assertEqual(a.frame, 2)


class ActorImageAndSpriteTest(SpriteTestBase):
    """An actor can switch between still images and Sprites."""

    def test_image_actor_starts_a_sprite(self):
        s = self.make_sprite()
        a = Actor("alien")
        self.assertIsNone(a.sprite)
        a.sprite = s
        self.assertIs(a.sprite, s)
        self.assertEqual(a.image, "")
        self.assertIs(a._orig_surf, s.images[0])

    def test_image_does_not_take_a_sprite(self):
        """actor.image and actor.sprite each only hold their own kind of thing."""
        a = Actor("alien")
        with self.assertRaisesRegex(TypeError, "use actor.sprite instead"):
            a.image = self.make_sprite()
        self.assertEqual(a.image, "alien")
        self.assertIsNone(a.sprite)

    def test_whichever_was_set_last_is_shown(self):
        s = self.make_sprite()
        a = Actor(s)
        self.assertEqual((a.image, a.sprite), ("", s))
        a.image = "alien"
        self.assertEqual((a.image, a.sprite), ("alien", None))
        a.sprite = s
        self.assertEqual((a.image, a.sprite), ("", s))

    def test_assigning_an_image_stops_the_sprite(self):
        a = self.make_actor()
        a.image = "alien"
        self.assertIsNone(a.sprite)
        self.assertEqual(a.image, "alien")
        self.advance_to(a, 1000)
        self.assertIs(a._orig_surf, images.alien)

    def test_sprite_none_stops_on_current_frame(self):
        s = self.make_sprite()
        a = self.make_actor(s)
        self.advance_to(a, 200)
        a.sprite = None
        self.advance_to(a, 1000)
        self.assertIs(a._orig_surf, s.images[2])

    def test_sprite_must_be_a_sprite(self):
        a = Actor("alien")
        with self.assertRaisesRegex(TypeError, "use actor.image instead"):
            a.sprite = "alien"

    def test_no_frames_without_a_sprite(self):
        a = Actor("alien")
        a.reset_animation()  # does nothing
        with self.assertRaisesRegex(ValueError, "isn't playing a Sprite"):
            a.frame = 1


if __name__ == "__main__":
    unittest.main()
