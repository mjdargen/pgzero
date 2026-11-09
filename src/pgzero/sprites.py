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

    The frames come from a sprite sheet in the sprites folder, read like a
    book from the start of a row, or from a list of image names in the images
    folder.

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
        spacing=0,
        margin=0,
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
        self.spacing = spacing
        self.margin = margin

        if isinstance(image_name, str):
            self.images = self._cut_row()
        else:
            sheet_only = (frame_width, frame_height, frames, transparent_color, row, spacing, margin)
            if sheet_only != (None, None, None, None, 0, 0, 0):
                raise TypeError(
                    "frame_width, frame_height, row, frames, transparent_color, "
                    "spacing and margin are only used with a sprite sheet, "
                    "not a list of images."
                )
            self.images = [loaders.images.load(name) for name in image_name]

        if not self.images:
            raise ValueError("Sprite must contain at least one frame")

    def _cut_row(self):
        """Cut the frames out of the sprite sheet.

        Frames are read like a book: from the left of the row, across, and on
        to the start of the next row if there are more frames than fit.
        """
        if self.frame_width is None or self.frame_height is None:
            raise TypeError(
                f"Sprite({self.image_name!r}) needs frame_width and "
                "frame_height, the size of one frame in pixels."
            )
        if self.spacing < 0 or self.margin < 0:
            raise ValueError("spacing and margin can't be negative")

        ss = SpriteSheet(self.image_name)
        sheet_width, sheet_height = ss.sheet.get_size()

        # The margin is the gap around the outside of the sheet, and the
        # spacing is the gap between frames, as in Tiled.
        step_x = self.frame_width + self.spacing
        step_y = self.frame_height + self.spacing
        columns = (sheet_width - self.margin + self.spacing) // step_x
        rows = (sheet_height - self.margin + self.spacing) // step_y

        if not 0 <= self.row < rows:
            raise ValueError(
                f"Row {self.row} is outside the sprite sheet. With frames "
                f"{self.frame_width}x{self.frame_height}, the sheet has rows "
                f"0 to {rows - 1}."
            )

        frame_count = self.frames
        if frame_count is None:
            # The rest of the row
            frame_count = columns
        available = (rows - self.row) * columns
        if frame_count > available:
            raise ValueError(
                f"The sheet has {available} frames from the start of row "
                f"{self.row} to the end, but frames={frame_count} asks for more."
            )

        rects = []
        for i in range(frame_count):
            row = self.row + i // columns
            column = i % columns
            x = self.margin + column * step_x
            y = self.margin + row * step_y
            rects.append((x, y, self.frame_width, self.frame_height))
        images = ss.images_at(rects, self.transparent_color)

        if self.frames is None:
            # Rows of different-length animations are often padded with empty
            # frames at the end. Leave those out, but keep any blank frames in
            # the middle of the animation.
            while images and images[-1].get_bounding_rect().width == 0:
                images.pop()
            if not images:
                raise ValueError(
                    f"Row {self.row} of the sprite sheet {self.image_name!r} has no "
                    "visible frames."
                )
        return images
