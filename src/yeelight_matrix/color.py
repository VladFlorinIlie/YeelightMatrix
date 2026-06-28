"""Color utilities for the Yeelight Cube Matrix.

A single LED is described by an RGB colour. Throughout the library a colour may
be supplied either as a hex string (``"#ff0000"`` or ``"ff0000"``) or as an
``(r, g, b)`` tuple of integers in the ``0..255`` range. The helpers here
normalise those representations and produce the base64 payload expected by the
device's ``update_leds`` command.
"""

from __future__ import annotations

import base64
from typing import Tuple, Union

#: A colour accepted by the public API: a hex string or an ``(r, g, b)`` tuple.
ColorLike = Union[str, Tuple[int, int, int]]

#: Black / "off".
BLACK: str = "#000000"


def to_rgb(color: ColorLike) -> Tuple[int, int, int]:
    """Return ``color`` as an ``(r, g, b)`` tuple of ints in ``0..255``.

    Accepts a hex string (with or without a leading ``#``) or an existing
    ``(r, g, b)`` tuple/list.

    Raises:
        ValueError: If the value cannot be interpreted as a colour.
    """
    if isinstance(color, str):
        value = color.lstrip("#")
        if len(value) != 6:
            raise ValueError(f"Invalid hex colour: {color!r}")
        try:
            return (
                int(value[0:2], 16),
                int(value[2:4], 16),
                int(value[4:6], 16),
            )
        except ValueError as exc:
            raise ValueError(f"Invalid hex colour: {color!r}") from exc

    if isinstance(color, (tuple, list)) and len(color) == 3:
        r, g, b = (int(channel) for channel in color)
        for channel in (r, g, b):
            if not 0 <= channel <= 255:
                raise ValueError(f"Colour channel out of range (0-255): {color!r}")
        return (r, g, b)

    raise ValueError(f"Unsupported colour value: {color!r}")


def to_hex(color: ColorLike) -> str:
    """Return ``color`` as a normalised ``"#rrggbb"`` lower-case hex string."""
    r, g, b = to_rgb(color)
    return f"#{r:02x}{g:02x}{b:02x}"


def encode(color: ColorLike) -> str:
    """Encode a single colour as the base64 string used by ``update_leds``."""
    return base64.b64encode(bytes(to_rgb(color))).decode("ascii")


def encode_many(colors) -> str:
    """Encode an iterable of colours into a single concatenated base64 string."""
    return "".join(encode(color) for color in colors)
