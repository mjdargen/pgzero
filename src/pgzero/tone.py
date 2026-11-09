"""Tone generator for Pygame Zero.

Tones are generated with numpy: a waveform at the requested pitch, faded in
and out briefly so that notes don't click. Samples are made in whatever format
the mixer is using. Tones are kept in a LRU cache which in typical
applications will reduce the number of times they need to be regenerated.

"""
import re
from functools import lru_cache
from collections import namedtuple
from enum import Enum

import numpy
import pygame
import pygame.sndarray


__all__ = (
    'play',
    'create',
)


# Longest note to allow
MAX_DURATION = 4

# Fade in and fade out times in seconds. Each is cut to a quarter of the note
# for very short notes.
FADE_IN = 0.01
FADE_OUT = 0.05


class Waveform(Enum):
    SIN = 'sin'
    SQUARE = 'square'
    SAW = 'saw'
    TRIANGLE = 'triangle'


ToneParams = namedtuple('ToneParams', 'hz duration waveform volume')


# numpy type, peak value and silent value for each pygame.mixer sample size
SAMPLE_FORMATS = {
    -8: (numpy.int8, 127, 0),
    8: (numpy.uint8, 127, 128),
    -16: (numpy.int16, 32767, 0),
    16: (numpy.uint16, 32767, 32768),
    32: (numpy.float32, 1.0, 0),
}

NOTE_PATTERN = re.compile(r'([A-G])([#b]?)([0-8])')

# Semitones from A in the same octave
NOTE_OFFSETS = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
ACCIDENTALS = {'': 0, '#': 1, 'b': -1}


def note_to_hertz(note):
    """Convert a note name such as 'A4', 'C#5' or 'Bb3' to a frequency."""
    match = NOTE_PATTERN.fullmatch(note)
    if not match:
        raise ValueError(
            "%s is not a valid note. Notes are A-G, either natural, flat (b) "
            "or sharp (#), in octaves 0-8, such as 'C4' or 'F#5'" % note
        )
    letter, accidental, octave = match.groups()
    semitones = (
        NOTE_OFFSETS[letter] + ACCIDENTALS[accidental] + 12 * (int(octave) - 4)
    )
    return 440 * 2 ** (semitones / 12)


def _wave(waveform, cycles):
    """Sample a waveform, returning values from -1 to 1.

    cycles is an array of how many cycles of the wave have passed at each
    sample.

    """
    if waveform is Waveform.SIN:
        return numpy.sin(2 * numpy.pi * cycles)
    position = cycles % 1
    if waveform is Waveform.SQUARE:
        return numpy.where(position < 0.5, 1.0, -1.0)
    if waveform is Waveform.SAW:
        return 2 * position - 1
    return 4 * numpy.abs(position - 0.5) - 1


def create(*args, **kwargs):
    """Create a tone of a given duration at the given pitch.

    Return a Sound which can be played later.

    """
    return _create(_convert_args(*args, **kwargs))


@lru_cache()
def _create(params):
    """Actually create a tone."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    rate, size, channels = pygame.mixer.get_init()
    try:
        dtype, peak, silence = SAMPLE_FORMATS[size]
    except KeyError:
        raise ValueError(
            "Tones can't be created for the mixer's sample size %r" % size
        ) from None

    count = max(1, int(rate * params.duration))
    samples = _wave(params.waveform, params.hz * numpy.arange(count) / rate)

    envelope = numpy.ones(count)
    fade_in = min(int(rate * FADE_IN), count // 4)
    fade_out = min(int(rate * FADE_OUT), count // 4)
    envelope[:fade_in] = numpy.linspace(0, 1, fade_in)
    envelope[count - fade_out:] = numpy.linspace(1, 0, fade_out)

    data = (samples * envelope * peak + silence).astype(dtype)
    if channels > 1:
        # Stereo (or more) sounds need the same samples in every channel
        data = numpy.repeat(data[:, numpy.newaxis], channels, axis=1)

    snd = pygame.sndarray.make_sound(data)
    snd.set_volume(params.volume)
    return snd


def _convert_args(pitch, duration, waveform=Waveform.SIN, volume=0.8):
    """Convert the given arguments to _create parameters."""
    if duration > MAX_DURATION:
        raise ValueError(
            'Note duration %ss is too long: notes may be at most %ss long' %
            (duration, MAX_DURATION)
        )
    if duration <= 0:
        raise ValueError("Note duration must be more than 0 seconds")
    if isinstance(pitch, str):
        pitch = note_to_hertz(pitch)
    return ToneParams(pitch, duration, Waveform(waveform), volume)


def play(*args, **kwargs):
    """Plays a tone of a certain length from a note or frequency in hertz.

    Tones have a maximum duration of 4 seconds. This limitation is imposed to
    avoid accidentally creating sounds that take too long to generate and
    require a lot of memory.

    To work around this, create the sounds you want to use up-front with
    create() and hold onto them, perhaps in an array.

    """
    create(*args, **kwargs).play()
