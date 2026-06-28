"""Image helpers for mapping pictures onto the cube matrix.

These functions deal purely in *logical* (un-rotated) colour grids stored in
row-major order. Orientation is applied later by the layout via
:func:`rotate_grid`, so an image is split the same way regardless of how the
physical stack is mounted.
"""

from __future__ import annotations

from typing import List, Sequence

from PIL import Image

from .color import to_hex
from .enums import Orientation

#: Width/height in LEDs of a single 5x5 module.
MODULE_SIZE = 5


def image_to_hex(img: Image.Image) -> List[str]:
    """Flatten a PIL image into a row-major list of ``"#rrggbb"`` colours."""
    return ["#{:02x}{:02x}{:02x}".format(*pixel[:3]) for pixel in img.convert("RGB").getdata()]


def hex_to_image(colors: Sequence[str], width: int, height: int) -> Image.Image:
    """Build a PIL image from a row-major sequence of colours."""
    img = Image.new("RGB", (width, height))
    img.putdata([_hex_to_rgb(color) for color in colors])
    return img


def rotate_grid(colors: Sequence[str], degrees: int, size: int = MODULE_SIZE) -> List[str]:
    """Rotate a square colour grid by ``degrees`` (0/90/180/270, anticlockwise).

    Returns a new row-major list. A ``degrees`` of 0 (or a 1x1 grid) is returned
    unchanged.
    """
    if degrees % 360 == 0 or size == 1:
        return list(colors)
    img = hex_to_image(colors, size, size).rotate(degrees)
    return image_to_hex(img)


def load_image_grids(
    image_path: str,
    module_count: int,
    orientation: Orientation,
) -> List[List[str]]:
    """Load an image and slice it into ``module_count`` logical 5x5 grids.

    The image is resized to span ``module_count`` modules along the stacking
    axis (height for a vertical layout, width for a horizontal one) and then cut
    into consecutive 5x5 tiles.

    Returns:
        A list of ``module_count`` grids, each a row-major list of 25 colours.
    """
    if module_count < 1:
        raise ValueError("module_count must be at least 1")

    span = MODULE_SIZE * module_count
    if orientation is Orientation.VERTICAL:
        width, height = MODULE_SIZE, span
    else:
        width, height = span, MODULE_SIZE

    img = Image.open(image_path).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)

    grids: List[List[str]] = []
    for i in range(module_count):
        if orientation is Orientation.VERTICAL:
            box = (0, i * MODULE_SIZE, MODULE_SIZE, (i + 1) * MODULE_SIZE)
        else:
            box = (i * MODULE_SIZE, 0, (i + 1) * MODULE_SIZE, MODULE_SIZE)
        grids.append(image_to_hex(img.crop(box)))
    return grids


def _hex_to_rgb(color: str) -> tuple:
    value = color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
