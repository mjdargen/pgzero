import pygame
import pygame.draw

from . import ptext
from .rect import RECT_CLASSES, ZRect
from . import loaders


def round_pos(pos):
    """Round a tuple position so it can be used for drawing."""
    try:
        x, y = pos
    except TypeError:
        raise TypeError("Coordinate must be a tuple (not {!r})".format(pos)) from None
    try:
        return round(x), round(y)
    except TypeError:
        raise TypeError("Coordinate values must be numbers (not {!r})".format(pos)) from None  # noqa


def make_color(arg):
    if isinstance(arg, tuple):
        return arg
    return tuple(pygame.Color(arg))


def _is_see_through(color):
    """Return True if color is an (r, g, b, a) color with a below 255."""
    return len(color) == 4 and color[3] < 255


def _with_opacity(color, opacity):
    """Return color as a tuple, made see-through by opacity.

    opacity works like Actor.opacity: 1.0 is solid and 0.0 is invisible, and
    it is kept between those. It multiplies any alpha the color already has.
    """
    color = make_color(color)
    if opacity >= 1:
        return color
    opacity = max(0.0, opacity)
    alpha = color[3] if len(color) == 4 else 255
    return (*color[:3], round(alpha * opacity))


class SurfacePainter:
    """Interface to pygame.draw that is bound to a surface."""

    def __init__(self, screen):
        self._screen = screen

    @property
    def _surf(self):
        return self._screen.surface

    def _draw(self, color, opacity, draw):
        """Call draw(surface, color), which draws with pygame.draw.

        pygame.draw doesn't blend: given (r, g, b, a) it writes a solid color
        to the screen and ignores a. So a see-through color is drawn onto a
        clear layer the size of the screen instead, and the part it covered
        is blended onto the screen and then cleared again. draw must return
        the Rect it covered, as pygame.draw functions do.
        """
        color = _with_opacity(color, opacity)
        if not _is_see_through(color):
            draw(self._surf, color)
            return
        if color[3] <= 0:
            return
        layer = self._screen._see_through_layer()
        area = draw(layer, color).clip(layer.get_rect())
        if area:
            self._surf.blit(layer, area.topleft, area)
            layer.fill((0, 0, 0, 0), area)

    def line(self, start, end, color, width=1, *, opacity=1.0):
        """Draw a line from start to end."""
        start = round_pos(start)
        end = round_pos(end)
        self._draw(color, opacity, lambda surf, c: pygame.draw.line(surf, c, start, end, width))

    def circle(self, pos, radius, color, width=1, *, opacity=1.0):
        """Draw a circle."""
        pos = round_pos(pos)
        self._draw(color, opacity, lambda surf, c: pygame.draw.circle(surf, c, pos, radius, width))

    def filled_circle(self, pos, radius, color, *, opacity=1.0):
        """Draw a filled circle."""
        pos = round_pos(pos)
        self._draw(color, opacity, lambda surf, c: pygame.draw.circle(surf, c, pos, radius, 0))

    def polygon(self, points, color, *, opacity=1.0):
        """Draw a polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._draw(color, opacity, lambda surf, c: pygame.draw.polygon(surf, c, points, 1))

    def filled_polygon(self, points, color, *, opacity=1.0):
        """Draw a filled polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.filled_polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._draw(color, opacity, lambda surf, c: pygame.draw.polygon(surf, c, points, 0))

    def _coerce_rect(self, rect, color_or_size, color, method_name):
        """Unpack ``(rect, color)`` or ``((x, y), (w, h), color)``.

        Return (pygame.Rect, (l, t, w, h), color).
        """
        if isinstance(rect, RECT_CLASSES):
            if color is None:
                color = color_or_size
            elif color_or_size is not None:
                raise TypeError(f"screen.draw.{method_name}() got too many positional arguments for rect form")
            l, t, w, h = rect
        else:
            try:
                (l, t), (w, h) = rect, color_or_size
                l, t, w, h = float(l), float(t), float(w), float(h)
            except (TypeError, ValueError):
                raise TypeError(f"screen.draw.{method_name}() requires a rect or ((x, y), (w, h))") from None
        if color is None:
            raise TypeError(f"screen.draw.{method_name}() requires a color")
        return pygame.Rect(round(l), round(t), round(w), round(h)), (l, t, w, h), color

    def rect(self, rect, color_or_size=None, color=None, width=1, *, opacity=1.0):
        """Draw a rectangle: rect(rect, color) or rect((x, y), (w, h), color)."""
        rect, (l, t, w, h), color = self._coerce_rect(rect, color_or_size, color, "rect")

        if width <= 1:
            self._draw(color, opacity, lambda surf, c: pygame.draw.rect(surf, c, rect, width))
            return

        hw = width / 2
        l1, l2 = round(l - hw), round(l + hw)
        r1, r2 = round(l + w - hw), round(l + w + hw)
        t1, t2 = round(t - hw), round(t + hw)
        b1, b2 = round(t + h - hw), round(t + h + hw)

        # A thick outline is drawn as four filled bars.
        def bars(surf, c):
            def r(x1, y1, x2, y2):
                rr = pygame.Rect(x1, y1, x2 - x1, y2 - y1)
                return pygame.draw.rect(surf, c, rr, 0)

            return r(l1, t1, r2, t2).unionall([
                r(l1, t2, l2, b1),
                r(r1, t2, r2, b1),
                r(l1, b1, r2, b2),
            ])

        self._draw(color, opacity, bars)

    def filled_rect(self, rect, color_or_size=None, color=None, *, opacity=1.0):
        """Draw a filled rectangle: filled_rect(rect, color) or filled_rect((x, y), (w, h), color)."""
        rect, _, color = self._coerce_rect(rect, color_or_size, color, "filled_rect")
        self._draw(color, opacity, lambda surf, c: pygame.draw.rect(surf, c, rect, 0))

    def _text_alpha(self, kwargs):
        """Turn opacity, and the alpha of an (r, g, b, a) color, into ptext's alpha.

        ptext draws see-through text with alpha (0.0 to 1.0), but ignores the
        alpha in a text color. opacity works like it does for shapes.
        """
        alpha = kwargs.pop("alpha", 1.0) * min(1.0, max(0.0, kwargs.pop("opacity", 1.0)))
        color = kwargs.get("color")
        if color is not None:
            color = make_color(color)
            if len(color) == 4:
                alpha *= color[3] / 255
                kwargs["color"] = color[:3]
        if alpha < 1:
            kwargs["alpha"] = alpha

    def text(self, *args, **kwargs):
        """Draw text to the screen."""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._text_alpha(kwargs)
        ptext.draw(*args, surf=self._surf, **kwargs)

    def textbox(self, *args, **kwargs):
        """Draw text to the screen, wrapped to fit a box"""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._text_alpha(kwargs)
        ptext.drawbox(*args, surf=self._surf, **kwargs)

    def darkness(self, amount):
        """Darken the whole screen, from 0.0 (no change) to 1.0 (black).

        Lights drawn after it shine through the darkness, showing the real
        colors of what's under them. To do that, the screen as it was before
        darkening is kept until the next frame.
        """
        amount = min(1.0, max(0.0, amount))
        self._screen._keep_scene()
        brightness = round(255 * (1 - amount))
        self._surf.fill((brightness,) * 3, special_flags=pygame.BLEND_RGB_MULT)

    def light(self, pos, radius, color="white", *, opacity=1.0):
        """Draw a soft round light, brightest in the middle.

        After darkness() this frame, the light shows the real colors of what's
        under it, tinted by color. Without darkness(), it brightens what's
        already on the screen. opacity makes the light weaker.
        """
        pos = round_pos(pos)
        radius = round(radius)
        opacity = min(1.0, max(0.0, opacity))
        if radius <= 0 or opacity == 0:
            return
        area = pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)
        on_screen = area.clip(self._surf.get_rect())
        if not on_screen:
            return
        screen = self._screen
        # Light = the scene under it x the light's falloff x its color, added on.
        work = screen._light_work_surface()
        part = pygame.Rect((0, 0), on_screen.size)
        work.blit(screen._scene_under_lights(), (0, 0), on_screen)
        work.blit(_light_falloff(radius), (area.x - on_screen.x, area.y - on_screen.y),
                  special_flags=pygame.BLEND_RGB_MULT)
        r, g, b = make_color(color)[:3]
        work.fill((round(r * opacity), round(g * opacity), round(b * opacity)), part,
                  special_flags=pygame.BLEND_RGB_MULT)
        self._surf.blit(work, on_screen.topleft, part, special_flags=pygame.BLEND_RGB_ADD)


_LIGHT_SIZE = 128  # radius of the falloff that lights are scaled from
_light_master = None
_light_falloffs = {}  # radius -> falloff scaled to that radius


def _light_falloff(radius):
    """Return a light's brightness as a gray image, scaled to radius.

    It's white in the middle, fading to black at the edge. It's drawn once,
    then each size a game uses is kept, so drawing a light is quick.
    """
    global _light_master
    falloff = _light_falloffs.get(radius)
    if falloff is not None:
        return falloff
    if _light_master is None:
        _light_master = pygame.Surface((_LIGHT_SIZE * 2, _LIGHT_SIZE * 2))
        _light_master.fill((0, 0, 0))
        for r in range(_LIGHT_SIZE, 0, -1):
            t = r / _LIGHT_SIZE  # 0 in the middle, 1 at the edge
            v = round(255 * (1 - t * t) ** 2)
            pygame.draw.circle(_light_master, (v, v, v), (_LIGHT_SIZE, _LIGHT_SIZE), r)
    falloff = pygame.transform.smoothscale(_light_master, (radius * 2, radius * 2))
    # a game that keeps changing a light's size could make many; keep the newest
    if len(_light_falloffs) >= 32:
        del _light_falloffs[next(iter(_light_falloffs))]
    _light_falloffs[radius] = falloff
    return falloff


def blit_gradient(start, stop, dest_surface):
    """Blit a gradient into a destination surface.

    The function does not return anything as the gradient is written
    in-place in the destination surface.

    Args:
      start: The starting (top) color as a tuple (red, green, blue).
      stop: The stopping (bottom) color as a tuple (red, green, blue).
      dest_surface: A pygame.Surface to write the gradient into.
    Returns:
      None."""
    surface_compact = pygame.Surface((2, 2))
    pixelarray = pygame.PixelArray(surface_compact)
    pixelarray[0][0] = start
    pixelarray[0][1] = stop
    pixelarray[1][0] = start
    pixelarray[1][1] = stop
    pygame.transform.smoothscale(
        surface_compact,
        pygame.PixelArray(dest_surface).shape,
        dest_surface=dest_surface,
    )


class Screen:
    """Interface to the screen."""

    _layer = None
    _scene = None  # the screen before darkness(), for lights to show
    _scene_kept = False
    _light_work = None

    def _set_surface(self, surface):
        self.surface = surface
        self.width, self.height = surface.get_size()

    def _start_frame(self):
        """Forget the scene kept by darkness(), at the start of each frame."""
        self._scene_kept = False

    def _keep_scene(self):
        """Copy the screen as it is, for lights drawn after darkness()."""
        size = self.surface.get_size()
        if self._scene is None or self._scene.get_size() != size:
            self._scene = pygame.Surface(size)
        self._scene.blit(self.surface, (0, 0))
        self._scene_kept = True

    def _scene_under_lights(self):
        """What lights show: the scene from before darkness(), or the screen."""
        return self._scene if self._scene_kept else self.surface

    def _light_work_surface(self):
        """A reusable surface the size of the screen, for building a light."""
        size = self.surface.get_size()
        if self._light_work is None or self._light_work.get_size() != size:
            self._light_work = pygame.Surface(size)
        return self._light_work

    def _see_through_layer(self):
        """Return a clear layer the size of the screen, for see-through drawing.

        The same layer is kept and reused. Whatever draws on it must clear
        what it drew afterwards, so the layer is clear for the next drawing.
        """
        size = self.surface.get_size()
        if self._layer is None or self._layer.get_size() != size:
            self._layer = pygame.Surface(size, pygame.SRCALPHA)
        return self._layer

    def bounds(self):
        """Return a Rect representing the bounds of the screen."""
        return ZRect((0, 0), (self.width, self.height))

    def clear(self):
        """Clear the screen to black."""
        self.fill((0, 0, 0))

    def fill(self, color, gcolor=None, *, opacity=1.0):
        """Fill the screen with a colour.

        A see-through color, from opacity or an (r, g, b, a) color, is blended
        over what's already on the screen, like tinted glass over the screen.
        """
        if gcolor:
            start = make_color(color)
            stop = make_color(gcolor)
            blit_gradient(start, stop, self.surface)
            return
        color = _with_opacity(color, opacity)
        if _is_see_through(color):
            self.draw.filled_rect(self.bounds(), color)
        else:
            self.surface.fill(color)

    def blit(self, image, pos):
        """Draw a sprite onto the screen.

        "blit" is an archaic name for this operation, but one that is is still
        frequently used, for example in Pygame. See the `Wikipedia article`__
        for more about the etymology of the term.

        .. __: http://en.wikipedia.org/wiki/Bit_blit

        :param image: A Surface or the name of an image object to load.
        :param pos: The coordinates at which the top-left corner of the sprite
                    will be positioned. This may be given as a pair of
                    coordinates or as a Rect. If a Rect is given the sprite
                    will be drawn at ``rect.topleft``.

        """
        if isinstance(image, str):
            image = loaders.images.load(image)
        self.surface.blit(image, pos, None, pygame.BLEND_ALPHA_SDL2)

    @property
    def draw(self):
        return SurfacePainter(self)

    def __repr__(self):
        return "<Screen width={} height={}>".format(self.width, self.height)


screen_instance = Screen()
