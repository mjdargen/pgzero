import copy

import pygame
import pygame.surfarray

from . import loaders


def _make_transparent(image, color):
    """Make every pixel of the given color fully transparent.

    set_colorkey() is ignored when drawing a surface that has its own
    transparency, as every frame does, so clear those pixels' alpha instead.
    A color of -1 means the color of the top-left pixel.
    """
    if isinstance(color, int) and color == -1:
        color = image.get_at((0, 0))
    r, g, b = pygame.Color(color)[:3]
    rgb = pygame.surfarray.pixels3d(image)
    alpha = pygame.surfarray.pixels_alpha(image)
    alpha[(rgb == (r, g, b)).all(axis=2)] = 0
    # The arrays lock the surface until they are deleted.
    del rgb, alpha


class SpriteSheet:
    def __init__(self, name):
        self.name = name
        self.sheet = loaders.sprites.load(name)

    def image_at(self, rectangle, color_key=None):
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), rect)

        if color_key is not None:
            _make_transparent(image, color_key)

        return image

    def images_at(self, rects, color_key=None):
        return [self.image_at(rect, color_key) for rect in rects]

    def load_strip(self, rect, image_count, color_key=None):
        rects = [(rect[0] + rect[2] * i, rect[1], rect[2], rect[3]) for i in range(image_count)]
        return self.images_at(rects, color_key)


class Sprite:
    """An animation: its frames, how fast to play them, and whether to loop.

    The frames come from one row of a sprite sheet in the sprites folder, or
    from a list of image names in the images folder.

    A Sprite doesn't keep track of which frame is showing; each Actor
    playing it does that. So one Sprite can be shared by many actors.
    """

    def __init__(
        self,
        image_name,
        frame_width=None,
        frame_height=None,
        row=0,
        frames=None,
        fps=10,
        transparent_color=None,
        loop=True,
    ):
        if fps <= 0:
            raise ValueError(f"fps must be more than 0, not {fps}")

        self.image_name = image_name
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.row = row
        self.frames = frames
        self.fps = fps
        self.transparent_color = transparent_color
        self.loop = loop

        if isinstance(image_name, str):
            self.images = self._cut_row()
        else:
            if (frame_width, frame_height, frames, transparent_color) != (None,) * 4 or row != 0:
                raise TypeError(
                    "frame_width, frame_height, row, frames and "
                    "transparent_color are only used with a sprite sheet, "
                    "not a list of images."
                )
            self.images = [loaders.images.load(name) for name in image_name]

        if not self.images:
            raise ValueError("Sprite must contain at least one frame")

    def _cut_row(self):
        """Cut the frames out of one row of the sprite sheet."""
        if self.frame_width is None or self.frame_height is None:
            raise TypeError(
                f"Sprite({self.image_name!r}) needs frame_width and "
                "frame_height, the size of one frame in pixels."
            )

        ss = SpriteSheet(self.image_name)
        sheet_width, sheet_height = ss.sheet.get_size()
        frame_count = self.frames
        if frame_count is None:
            # Use every frame that fits across the sheet
            frame_count = sheet_width // self.frame_width

        if self.frame_height * (self.row + 1) > sheet_height:
            raise ValueError(
                f"Row {self.row} is outside the sprite sheet. "
                f"The sheet is {sheet_width}x{sheet_height}, "
                f"but row {self.row} with frame height {self.frame_height} "
                f"would end at y={self.frame_height * (self.row + 1)}."
            )
        if self.frame_width * frame_count > sheet_width:
            raise ValueError(
                f"The requested frames go past the edge of the sprite sheet. "
                f"The sheet is {sheet_width} pixels wide, but "
                f"{frame_count} frames with width {self.frame_width} need "
                f"{self.frame_width * frame_count} pixels."
            )

        first_rect = (
            0,
            self.frame_height * self.row,
            self.frame_width,
            self.frame_height,
        )
        return ss.load_strip(first_rect, frame_count, self.transparent_color)

    def copy(self):
        # Older versions needed a copy of a Sprite for each actor. Sprites can
        # now be shared, but this is kept so that code still works.
        return copy.copy(self)
