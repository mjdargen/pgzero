from pygame.mixer import music as _music
from .loaders import ResourceLoader
from . import constants


__all__ = [
    "rewind",
    "stop",
    "fadeout",
    "set_volume",
    "get_volume",
    "get_pos",
    "set_pos",
    "play",
    "play_once",
    "queue",
    "is_playing",
    "is_paused",
    "pause",
    "unpause",
]

_music.set_endevent(constants.MUSIC_END)


class _MusicLoader(ResourceLoader):
    """Pygame's music API acts as a singleton with one 'current' track.

    No objects are returned that represent different tracks, so this loader
    can't return anything useful. But it can perform all the path name
    validations and return the validated path, so that's what we do.

    This loader should not be exposed to the user.

    """

    EXTNS = ["mp3", "ogg", "oga"]
    TYPE = "music"

    def _load(self, path):
        return path


_loader = _MusicLoader("music")


# State of whether we are paused or not
_paused = False
# Current track that is playing
_current_track = None
# Track queued to play next, if any
_queued_track = None


def _play(name, loop):
    global _paused, _current_track, _queued_track
    path = _loader.load(name)
    _music.load(path)
    _music.play(loop)
    _paused = False
    _current_track = name
    _queued_track = None


def _on_music_end():
    """Update tracked music state when the current track finishes.

    If a queued track exists, it becomes the current track. Otherwise,
    no track is considered current anymore.

    """
    global _paused, _current_track, _queued_track

    _paused = False

    if _queued_track is not None:
        _current_track = _queued_track
        _queued_track = None
    else:
        _current_track = None


def play(name):
    """Play a music file from the music/ directory.

    The music will loop when it finishes playing.

    """
    _play(name, -1)


def play_once(name):
    """Play a music file from the music/ directory."""
    _play(name, 0)


def queue(name):
    """Queue a music file to follow the current track.

    This will load a music file and queue it. A queued music file will begin as
    soon as the current music naturally ends. If the current music is ever
    stopped or changed, the queued song will be lost.

    """
    global _queued_track
    path = _loader.load(name)
    _music.queue(path)
    _queued_track = name


def is_playing(name=None):
    """Return True if the music is playing and not paused.

    If `name` is provided, return True only if that specific track is the
    current track being played.

    """
    if not (_music.get_busy() and not _paused):
        return False

    if name is None:
        return True

    return _current_track == name


def is_paused():
    """Return True if the music is currently paused."""
    return _paused


def pause():
    """Temporarily stop playback of the music stream.

    Call `unpause()` to resume.

    """
    global _paused
    if _music.get_busy():
        _music.pause()
        _paused = True


def unpause():
    """Resume playback of the music stream after it has been paused."""
    global _paused
    if _paused:
        _music.unpause()
        _paused = False


def fadeout(seconds):
    """Fade out and eventually stop the music playback.

    :param seconds: The duration in seconds over which the sound will be faded
                    out. For example, to fade out over half a second, call
                    ``music.fadeout(0.5)``.

    """
    global _paused, _current_track, _queued_track
    _music.fadeout(int(seconds * 1000))
    _paused = False
    _current_track = None
    _queued_track = None


def stop():
    """Stop playback of the music."""
    global _paused, _current_track, _queued_track
    _music.stop()
    _paused = False
    _current_track = None
    _queued_track = None


rewind = _music.rewind
get_volume = _music.get_volume
set_volume = _music.set_volume
get_pos = _music.get_pos
set_pos = _music.set_pos
