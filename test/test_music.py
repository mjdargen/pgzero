"""Tests for music track bookkeeping (current/queued track, pause state).

pygame's mixer is replaced with a mock so these tests don't need audio
hardware or music files.

"""
import unittest
from unittest import mock

from pgzero import music


class MusicTest(unittest.TestCase):
    def setUp(self):
        self.mixer = mock.Mock()
        self.mixer.get_busy.return_value = False

        patches = [
            mock.patch.object(music, "_music", self.mixer),
            mock.patch.object(music._loader, "load",
                              side_effect=lambda name: "music/%s.ogg" % name),
            mock.patch.object(music, "_paused", False),
            mock.patch.object(music, "_current_track", None),
            mock.patch.object(music, "_queued_track", None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def play(self, name):
        music.play(name)
        self.mixer.get_busy.return_value = True

    def test_exports(self):
        for name in ["play", "play_once", "queue", "stop", "fadeout",
                     "pause", "unpause", "is_playing", "is_paused"]:
            self.assertIn(name, music.__all__)
            self.assertTrue(callable(getattr(music, name)), name)

    def test_play_loops_forever(self):
        music.play("theme")
        self.mixer.load.assert_called_once_with("music/theme.ogg")
        self.mixer.play.assert_called_once_with(-1)

    def test_play_once(self):
        music.play_once("jingle")
        self.mixer.play.assert_called_once_with(0)
        self.assertEqual(music._current_track, "jingle")

    def test_play_records_current_track(self):
        music.play("theme")
        self.assertEqual(music._current_track, "theme")

    def test_play_clears_queue(self):
        music.queue("next")
        music.play("theme")
        self.assertIsNone(music._queued_track)

    def test_is_playing(self):
        self.assertFalse(music.is_playing())
        self.play("theme")
        self.assertTrue(music.is_playing())

    def test_is_playing_named_track(self):
        self.play("theme")
        self.assertTrue(music.is_playing("theme"))
        self.assertFalse(music.is_playing("boss"))

    def test_is_playing_false_when_mixer_idle(self):
        music.play("theme")
        self.mixer.get_busy.return_value = False
        self.assertFalse(music.is_playing("theme"))

    def test_pause(self):
        self.play("theme")
        music.pause()
        self.mixer.pause.assert_called_once_with()
        self.assertTrue(music.is_paused())
        self.assertFalse(music.is_playing())
        self.assertFalse(music.is_playing("theme"))

    def test_pause_when_nothing_playing(self):
        music.pause()
        self.mixer.pause.assert_not_called()
        self.assertFalse(music.is_paused())

    def test_unpause(self):
        self.play("theme")
        music.pause()
        music.unpause()
        self.mixer.unpause.assert_called_once_with()
        self.assertFalse(music.is_paused())
        self.assertTrue(music.is_playing("theme"))

    def test_unpause_when_not_paused(self):
        self.play("theme")
        music.unpause()
        self.mixer.unpause.assert_not_called()

    def test_play_after_pause_clears_paused(self):
        self.play("theme")
        music.pause()
        self.play("boss")
        self.assertFalse(music.is_paused())

    def test_queue_records_track(self):
        self.play("theme")
        music.queue("next")
        self.mixer.queue.assert_called_once_with("music/next.ogg")
        self.assertEqual(music._queued_track, "next")
        self.assertTrue(music.is_playing("theme"))

    def test_music_end_moves_to_queued_track(self):
        self.play("theme")
        music.queue("next")
        music._on_music_end()
        self.assertEqual(music._current_track, "next")
        self.assertIsNone(music._queued_track)
        self.assertTrue(music.is_playing("next"))

    def test_music_end_without_queue(self):
        self.play("theme")
        music._on_music_end()
        self.assertIsNone(music._current_track)
        self.assertFalse(music.is_playing("theme"))

    def test_music_end_clears_paused(self):
        music._paused = True
        music._on_music_end()
        self.assertFalse(music.is_paused())

    def test_stop(self):
        self.play("theme")
        music.queue("next")
        music.pause()
        music.stop()
        self.mixer.stop.assert_called_once_with()
        self.assertIsNone(music._current_track)
        self.assertIsNone(music._queued_track)
        self.assertFalse(music.is_paused())

    def test_fadeout(self):
        self.play("theme")
        music.queue("next")
        music.fadeout(1.5)
        self.mixer.fadeout.assert_called_once_with(1500)
        self.assertIsNone(music._current_track)
        self.assertIsNone(music._queued_track)
        self.assertFalse(music.is_paused())


if __name__ == "__main__":
    unittest.main()
