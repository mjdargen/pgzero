import warnings
import pygame
from math import radians, sin, cos, atan2, degrees, sqrt

from . import game
from . import loaders
from . import rect
from . import spellcheck
from .sprites import Sprite

ANCHORS = {
    "x": {
        "left": 0.0,
        "center": 0.5,
        "middle": 0.5,
        "right": 1.0,
    },
    "y": {
        "top": 0.0,
        "center": 0.5,
        "middle": 0.5,
        "bottom": 1.0,
    },
}


def calculate_anchor(value, dim, total):
    if isinstance(value, str):
        try:
            return total * ANCHORS[dim][value]
        except KeyError:
            raise ValueError("%r is not a valid %s-anchor name" % (value, dim))
    return float(value)


# These are methods (of the same name) on pygame.Rect
SYMBOLIC_POSITIONS = set(
    (
        "topleft",
        "bottomleft",
        "topright",
        "bottomright",
        "midtop",
        "midleft",
        "midbottom",
        "midright",
        "center",
    )
)

# Provides more meaningful default-arguments e.g. for display in IDEs etc.
POS_TOPLEFT = None
ANCHOR_CENTER = None

MAX_ALPHA = 255  # Based on pygame's max alpha.


def transform_anchor(ax, ay, w, h, angle):
    """Transform anchor based upon a rotation of a surface of size w x h."""
    theta = -radians(angle)

    sintheta = sin(theta)
    costheta = cos(theta)

    # Dims of the transformed rect
    tw = abs(w * costheta) + abs(h * sintheta)
    th = abs(w * sintheta) + abs(h * costheta)

    # Offset of the anchor from the center
    cax = ax - w * 0.5
    cay = ay - h * 0.5

    # Rotated offset of the anchor from the center
    rax = cax * costheta - cay * sintheta
    ray = cax * sintheta + cay * costheta

    return (tw * 0.5 + rax, th * 0.5 + ray)


def rotate_vector(x, y, angle):
    """Rotate a vector using the same rotation convention as pygame surfaces."""
    theta = -radians(angle)
    sintheta = sin(theta)
    costheta = cos(theta)

    return (
        x * costheta - y * sintheta,
        x * sintheta + y * costheta,
    )


def _set_opacity(actor, current_surface):
    alpha = int(actor.opacity * MAX_ALPHA + 0.5)

    if alpha == MAX_ALPHA:
        return current_surface

    alpha_img = pygame.Surface(current_surface.get_size(), pygame.SRCALPHA)
    alpha_img.fill((255, 255, 255, alpha))
    alpha_img.blit(current_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return alpha_img


def _set_scale(actor, current_surface):
    if actor._scale == 1.0:
        return current_surface

    w, h = current_surface.get_size()
    sw = max(1, int(round(w * actor._scale)))
    sh = max(1, int(round(h * actor._scale)))
    return pygame.transform.scale(current_surface, (sw, sh))


def _set_flip(actor, current_surface):
    surf = current_surface

    if actor._flip_d:
        surf = pygame.transform.rotate(surf, -90)
        surf = pygame.transform.flip(surf, True, False)

    if actor._flip_h or actor._flip_v:
        surf = pygame.transform.flip(surf, actor._flip_h, actor._flip_v)

    return surf


def _set_angle(actor, current_surface):
    if actor._angle % 360 == 0:
        return current_surface
    return pygame.transform.rotate(current_surface, actor._angle)


class Actor:
    EXPECTED_INIT_KWARGS = SYMBOLIC_POSITIONS
    DELEGATED_ATTRIBUTES = [a for a in dir(rect.ZRect) if not a.startswith("_")]

    function_order = [_set_opacity, _set_scale, _set_flip, _set_angle]

    _anchor = _anchor_value = (0, 0)
    _angle = 0.0
    _opacity = 1.0
    _scale = 1.0
    _flip_h = False
    _flip_v = False
    _flip_d = False
    _collision_rect_spec = None

    # Sprite animation
    _sprite = None
    _frame_index = 0
    _animation_paused = False
    _animation_finished = False
    # When the current frame started showing, in milliseconds. None until the
    # actor is next drawn, so time before the game starts, or spent paused,
    # doesn't count.
    _frame_time = None

    def _build_transformed_surf(self):
        cache_len = len(self._surface_cache)
        if cache_len == 0:
            last = self._orig_surf
        else:
            last = self._surface_cache[-1]

        for f in self.function_order[cache_len:]:
            new_surf = f(self, last)
            self._surface_cache.append(new_surf)
            last = new_surf

        return self._surface_cache[-1]

    def __init__(self, image, pos=POS_TOPLEFT, anchor=ANCHOR_CENTER, collision_rect=None, **kwargs):
        self._handle_unexpected_kwargs(kwargs)

        self._surface_cache = []
        self.__dict__["_rect"] = rect.ZRect((0, 0), (0, 0))
        self._collision_rect_spec = collision_rect

        self.image = image
        self._init_position(pos, anchor, **kwargs)

    def __getattr__(self, attr):
        if attr in self.__class__.DELEGATED_ATTRIBUTES:
            return getattr(self._rect, attr)
        else:
            return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        if attr in self.__class__.DELEGATED_ATTRIBUTES:
            return setattr(self._rect, attr, value)
        else:
            return object.__setattr__(self, attr, value)

    def __iter__(self):
        return iter(self._rect)

    def __repr__(self):
        return "<{} {!r} pos={!r}>".format(type(self).__name__, self._image_name, self.pos)

    def __dir__(self):
        standard_attributes = [key for key in self.__dict__.keys() if not key.startswith("_")]
        return standard_attributes + self.__class__.DELEGATED_ATTRIBUTES

    def _handle_unexpected_kwargs(self, kwargs):
        unexpected_kwargs = set(kwargs.keys()) - self.EXPECTED_INIT_KWARGS
        if not unexpected_kwargs:
            return

        typos, _ = spellcheck.compare(unexpected_kwargs, self.EXPECTED_INIT_KWARGS)
        for found, suggested in typos:
            raise TypeError("Unexpected keyword argument '{}' (did you mean '{}'?)".format(found, suggested))

    def _init_position(self, pos, anchor, **kwargs):
        if anchor is None:
            anchor = ("center", "center")
        self.anchor = anchor

        symbolic_pos_args = {k: kwargs[k] for k in kwargs if k in SYMBOLIC_POSITIONS}

        if not pos and not symbolic_pos_args:
            self.topleft = (0, 0)
        elif pos and symbolic_pos_args:
            raise TypeError("'pos' argument cannot be mixed with 'topleft', " "'topright' etc. argument.")
        elif pos:
            self.pos = pos
        else:
            self._set_symbolic_pos(symbolic_pos_args)

    def _set_symbolic_pos(self, symbolic_pos_dict):
        if len(symbolic_pos_dict) == 0:
            raise TypeError("No position-setting keyword arguments ('topleft', " "'topright' etc) found.")
        if len(symbolic_pos_dict) > 1:
            raise TypeError("Only one 'topleft', 'topright' etc. argument is allowed.")

        setter_name, position = symbolic_pos_dict.popitem()
        setattr(self, setter_name, position)

    def _update_transform(self, function):
        if function in self.function_order:
            i = self.function_order.index(function)
            del self._surface_cache[i:]
        else:
            raise IndexError("function {!r} does not have a registered order." "".format(function))

    def _body_spec(self):
        """Return the unscaled body as (width, height, offset_x, offset_y).

        The body is the actor's authoritative rectangle. All position anchors,
        symbolic positions, and collision checks are based on this rectangle.

        collision_rect formats:
        - None: use the full image as the body
        - (width, height): centered body
        - (width, height, offset_x, offset_y): body center offset from image center
        """
        image_w, image_h = self._orig_surf.get_size()

        if self._collision_rect_spec is None:
            return float(image_w), float(image_h), 0.0, 0.0

        if len(self._collision_rect_spec) == 2:
            width, height = self._collision_rect_spec
            return float(width), float(height), 0.0, 0.0

        if len(self._collision_rect_spec) == 4:
            width, height, offset_x, offset_y = self._collision_rect_spec
            return float(width), float(height), float(offset_x), float(offset_y)

        raise ValueError("collision_rect must be None, (width, height), or " "(width, height, offset_x, offset_y).")

    def _transformed_body_size(self):
        body_w, body_h, _, _ = self._body_spec()

        w = body_w * self._scale
        h = body_h * self._scale

        if self._flip_d:
            w, h = h, w

        if self._angle != 0.0:
            ra = radians(self._angle)
            sin_a = sin(ra)
            cos_a = cos(ra)
            return (
                abs(w * cos_a) + abs(h * sin_a),
                abs(w * sin_a) + abs(h * cos_a),
            )

        return w, h

    @property
    def anchor(self):
        return self._anchor_value

    @anchor.setter
    def anchor(self, val):
        self._anchor_value = val
        self._calc_anchor()

    def _calc_anchor(self):
        if not hasattr(self, "_orig_surf"):
            return

        ax, ay = self._anchor_value
        body_w, body_h, _, _ = self._body_spec()

        ax = calculate_anchor(ax, "x", body_w)
        ay = calculate_anchor(ay, "y", body_h)
        self._untransformed_anchor = ax, ay

        transformed_w = body_w * self._scale
        transformed_h = body_h * self._scale

        anchor_x = ax * self._scale
        anchor_y = ay * self._scale

        if self._flip_d:
            anchor_x, anchor_y = anchor_y, anchor_x
            transformed_w, transformed_h = transformed_h, transformed_w

        if self._angle != 0.0:
            self._anchor = transform_anchor(
                anchor_x,
                anchor_y,
                transformed_w,
                transformed_h,
                self._angle,
            )
        else:
            self._anchor = anchor_x, anchor_y

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle = angle
        self._update_pos()
        self._update_transform(_set_angle)

    @property
    def opacity(self):
        """Get/set the current opacity value."""
        return self._opacity

    @opacity.setter
    def opacity(self, opacity):
        self._opacity = min(1.0, max(0.0, opacity))
        self._update_transform(_set_opacity)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale):
        # Like opacity, clamp rather than raise, so that a bouncy animate()
        # tween that briefly goes below 0 doesn't crash the game.
        self._scale = max(0.0, scale)
        self._update_pos()
        self._update_transform(_set_scale)

    @property
    def flip_h(self):
        return self._flip_h

    @flip_h.setter
    def flip_h(self, value):
        self._flip_h = value
        self._update_pos()
        self._update_transform(_set_flip)

    @property
    def flip_v(self):
        return self._flip_v

    @flip_v.setter
    def flip_v(self, value):
        self._flip_v = value
        self._update_pos()
        self._update_transform(_set_flip)

    @property
    def flip_d(self):
        return self._flip_d

    @flip_d.setter
    def flip_d(self, value):
        self._flip_d = value
        self._update_pos()
        self._update_transform(_set_flip)

    @property
    def pos(self):
        px, py = self.topleft
        ax, ay = self._anchor
        return px + ax, py + ay

    @pos.setter
    def pos(self, pos):
        px, py = pos
        ax, ay = self._anchor
        self.topleft = px - ax, py - ay

    def rect(self):
        return self._rect.copy()

    @property
    def x(self):
        ax = self._anchor[0]
        return self.left + ax

    @x.setter
    def x(self, px):
        self.left = px - self._anchor[0]

    @property
    def y(self):
        ay = self._anchor[1]
        return self.top + ay

    @y.setter
    def y(self, py):
        self.top = py - self._anchor[1]

    @property
    def image(self) -> str:
        return self._image_name or ""

    @image.setter
    def image(self, image):
        # A Sprite plays as an animation; any other image stops the animation.
        if isinstance(image, Sprite):
            self.sprite = image
            return
        self._sprite = None
        self._set_image(image)

    def _set_image(self, image):
        if isinstance(image, pygame.Surface):
            self._image_name = None
            self._orig_surf = image
        else:
            self._image_name = image
            self._orig_surf = loaders.images.load(image)

        self._surface_cache.clear()
        self._update_pos()

    def _update_pos(self):
        if not hasattr(self, "_orig_surf"):
            return

        p = getattr(self, "pos", (0, 0))

        self.width, self.height = self._transformed_body_size()

        self._calc_anchor()
        self.pos = p

    def _image_center_offset_from_body_center(self):
        _, _, offset_x, offset_y = self._body_spec()

        # offset_x / offset_y describe the body center compared to the image
        # center, before scale or transforms. To draw the image, we need the
        # opposite vector: image center compared to body center.
        x = -offset_x * self._scale
        y = -offset_y * self._scale

        # The diagonal flip used by Tiled/Pygame here acts like swapping x/y
        # around the body's center.
        if self._flip_d:
            x, y = y, x

        if self._flip_h:
            x = -x

        if self._flip_v:
            y = -y

        if self._angle != 0.0:
            x, y = rotate_vector(x, y, self._angle)

        return x, y

    def _image_topleft(self):
        s = self._build_transformed_surf()
        image_offset_x, image_offset_y = self._image_center_offset_from_body_center()
        body_cx, body_cy = self.center

        return (
            body_cx + image_offset_x - s.get_width() / 2,
            body_cy + image_offset_y - s.get_height() / 2,
        )

    def _move_body_to_preserve_image_topleft(self, image_topleft):
        s = self._build_transformed_surf()
        image_offset_x, image_offset_y = self._image_center_offset_from_body_center()

        image_cx = image_topleft[0] + s.get_width() / 2
        image_cy = image_topleft[1] + s.get_height() / 2

        self.center = (
            image_cx - image_offset_x,
            image_cy - image_offset_y,
        )

    def draw(self):
        self._update_animation()
        s = self._build_transformed_surf()
        game.screen.blit(s, self._image_topleft())

    @property
    def sprite(self):
        """The Sprite this actor is playing, or None."""
        return self._sprite

    @sprite.setter
    def sprite(self, sprite):
        # Setting the same sprite again does nothing, so it is safe to set
        # every frame.
        if sprite is self._sprite:
            return
        if sprite is not None and not isinstance(sprite, Sprite):
            raise TypeError(
                f"actor.sprite must be a Sprite, not {sprite!r}. "
                "To show a single image, use actor.image instead."
            )
        self._sprite = sprite
        if sprite is not None:
            self.reset_animation()

    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, frame_index):
        if self._sprite is None:
            raise ValueError("This actor isn't playing a Sprite, so it has no frames.")
        last = len(self._sprite.images) - 1
        if not 0 <= frame_index <= last:
            raise ValueError(f"Frame index {frame_index} is out of range. This sprite has frames 0 to {last}.")
        self._frame_index = frame_index
        self._animation_finished = False
        self._frame_time = None
        self._show_frame()

    @property
    def animation_finished(self):
        """True once a Sprite that doesn't loop has played to the end."""
        return self._animation_finished

    def reset_animation(self):
        """Play the Sprite again from its first frame."""
        if self._sprite is not None:
            self.frame_index = 0

    def pause_animation(self):
        self._animation_paused = True

    def resume_animation(self):
        self._animation_paused = False
        self._frame_time = None

    @property
    def animation_paused(self):
        return self._animation_paused

    def _update_animation(self):
        if self._sprite is None or self._animation_paused or self._animation_finished:
            return

        # Hold the current frame while the game is paused with game.pause(),
        # then carry on from it, rather than skipping ahead, on game.resume().
        if getattr(game.current_game, "state", None) == "paused":
            self._frame_time = None
            return

        now = pygame.time.get_ticks()
        if self._frame_time is None:
            self._frame_time = now
            return

        frame_duration = 1000 / self._sprite.fps
        steps = int((now - self._frame_time) // frame_duration)
        if steps <= 0:
            return

        # Count on from when the frame was due rather than from now, so the
        # animation keeps to its fps even though it is only checked once per
        # game frame.
        self._frame_time += steps * frame_duration

        frame_count = len(self._sprite.images)
        frame_index = self._frame_index + steps
        if self._sprite.loop:
            frame_index %= frame_count
        elif frame_index >= frame_count:
            frame_index = frame_count - 1
            self._animation_finished = True
        self._frame_index = frame_index
        self._show_frame()

    def _show_frame(self):
        frame = self._sprite.images[self._frame_index]
        if frame is not getattr(self, "_orig_surf", None):
            self._set_image(frame)

    def colliderect(self, other):
        if hasattr(other, "_rect"):
            other_rect = other._rect
        else:
            other_rect = other

        return self._rect.colliderect(other_rect)

    def collidelist(self, others):
        for n, other in enumerate(others):
            if self.colliderect(other):
                return n
        return -1

    def collidepoint(self, *args):
        return self._rect.collidepoint(*args)

    @property
    def collision_rect(self):
        return self._rect

    @collision_rect.setter
    def collision_rect(self, value):
        if value is not None and len(value) not in (2, 4):
            raise ValueError("collision_rect must be None, (width, height), or " "(width, height, offset_x, offset_y).")

        old_image_topleft = self._image_topleft() if hasattr(self, "_orig_surf") else None

        self._collision_rect_spec = value
        self._update_pos()

        # Changing the body should not make the image appear to jump.
        # The body moves to match the new collision rectangle, while the
        # already-drawn image stays in the same visual place.
        if old_image_topleft is not None:
            self._move_body_to_preserve_image_topleft(old_image_topleft)

    def draw_collision_rect(self):
        r = self.collision_rect
        pygame.draw.rect(
            game.screen,
            (255, 0, 0),
            (r.x, r.y, r.w, r.h),
            2,
        )

    def angle_to(self, target):
        """Return the angle from this actors position to target, in degrees."""
        if isinstance(target, Actor):
            tx, ty = target.pos
        else:
            tx, ty = target
        myx, myy = self.pos
        dx = tx - myx
        dy = myy - ty
        return degrees(atan2(dy, dx))

    def distance_to(self, target):
        """Return the distance from this actor's pos to target, in pixels."""
        if isinstance(target, Actor):
            tx, ty = target.pos
        else:
            tx, ty = target
        myx, myy = self.pos
        dx = tx - myx
        dy = ty - myy
        return sqrt(dx * dx + dy * dy)

    def move_towards(self, target, speed):
        """Move up to speed pixels straight towards target.

        target is another Actor or an (x, y) position. The actor stops on the
        target rather than going past it.
        """
        if isinstance(target, Actor):
            tx, ty = target.pos
        else:
            tx, ty = target
        distance = self.distance_to((tx, ty))
        # max() also covers already being on the target with a negative speed,
        # where there is no direction to move away in.
        if distance <= max(speed, 0):
            self.pos = (tx, ty)
            return
        myx, myy = self.pos
        self.pos = (
            myx + (tx - myx) / distance * speed,
            myy + (ty - myy) / distance * speed,
        )

    def unload_image(self):
        if self._image_name is not None:
            loaders.images.unload(self._image_name)


class SpriteActor(Actor):
    """Deprecated: Actor plays Sprites itself, e.g. Actor(fox_walk).

    Kept so that games written for older versions still run.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "SpriteActor is no longer needed and will be removed. "
            "Use Actor instead, e.g. Actor(fox_walk).",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
