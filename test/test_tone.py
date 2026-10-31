import re
from unittest import TestCase

import pygame
import pygame.sndarray

from pgzero import tone
from pgzero.tone import _convert_args, Waveform


TEST_NOTES = {
    'A4': dict(val=0, hertz=440, parts=('A', '', 4)),
    'C4': dict(val=-9, hertz=261.63, parts=('C', '', 4)),
    'C0': dict(val=-57, hertz=16.35, parts=('C', '', 0)),
    'B8': dict(val=50, hertz=7902.13, parts=('B', '', 8)),
    'G4': dict(val=-2, hertz=392.00, parts=('G', '', 4)),
    'A#4': dict(val=1, hertz=466.16, parts=('A', '#', 4)),
    'Ab4': dict(val=-1, hertz=415.30, parts=('A', 'b', 4)),
    'Bb4': dict(val=1, hertz=466.16, parts=('B', 'b', 4)),
}


class ToneTest(TestCase):
    def test_invalid_note(self):
        for note in ['A9', 'H4', '4A', 'a4', 'Az4']:
            errmsg = re.escape(
                "%s is not a valid note. Notes are A-G, either natural, "
                "flat (b) or sharp (#), in octaves 0-8" % note
            )
            with self.assertRaisesRegex(ValueError, errmsg):
                _convert_args(note, 1)

    def test_note_to_hertz(self):
        for note, val in TEST_NOTES.items():
            params = _convert_args(note, 1.0)
            self.assertAlmostEqual(params.hz, val['hertz'], 2)

    def test_invalid_duration(self):
        for duration in [0, -1, tone.MAX_DURATION + 1]:
            with self.assertRaises(ValueError):
                _convert_args('A4', duration)

    def test_waveform_by_name(self):
        """Waveforms can be given as a name as well as a Waveform."""
        params = _convert_args('A4', 1, waveform='square')
        self.assertIs(params.waveform, Waveform.SQUARE)


class CreateToneTest(TestCase):
    """Tones are generated in the mixer's own sample format."""

    @classmethod
    def setUpClass(cls):
        # init() does nothing if the mixer is already running, so restart it
        # to get a known format.
        pygame.mixer.quit()
        pygame.mixer.init(frequency=22050, size=-16, channels=2)

    @classmethod
    def tearDownClass(cls):
        pygame.mixer.quit()

    def setUp(self):
        # Sounds cached by other tests may belong to a different mixer
        tone._create.cache_clear()

    def test_length(self):
        """A tone lasts exactly as long as asked for."""
        for duration in [0.05, 0.5, 2]:
            snd = tone.create('C4', duration)
            self.assertAlmostEqual(snd.get_length(), duration, places=3)

    def test_every_waveform(self):
        """Each waveform is loud in the middle and fades in and out."""
        for waveform in Waveform:
            with self.subTest(waveform=waveform):
                snd = tone.create(440, 0.5, waveform=waveform)
                samples = pygame.sndarray.array(snd)
                self.assertEqual(samples.shape, (11025, 2))
                self.assertEqual(samples[0, 0], 0)
                self.assertEqual(samples[-1, 0], 0)
                self.assertGreater(abs(samples).max(), 30000)
                # Both stereo channels carry the same tone
                self.assertTrue((samples[:, 0] == samples[:, 1]).all())

    def test_volume(self):
        snd = tone.create('A4', 0.1, volume=0.3)
        self.assertAlmostEqual(snd.get_volume(), 0.3, places=2)

    def test_tones_are_cached(self):
        self.assertIs(tone.create('A4', 1), tone.create('A4', 1))
