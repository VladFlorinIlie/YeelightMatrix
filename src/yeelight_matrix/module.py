"""A single cube module and its grid of LED colours."""

from __future__ import annotations

from typing import List, Sequence

from .color import BLACK, ColorLike, to_hex
from .enums import ModuleType


class Module:
    """One stackable cube module.

    A module owns a *logical* (un-rotated) grid of colours stored in row-major
    order. For a 5x5 module that is 25 colours; for a 1x1 spotlight it is one.
    Orientation/rotation is applied by :class:`~yeelight_matrix.layout.Layout`
    at render time, which keeps editing individual dots simple and intuitive.
    """

    def __init__(self, module_type: ModuleType | str, fill: ColorLike = BLACK) -> None:
        self.type = ModuleType(module_type)
        self._colors: List[str] = [to_hex(fill)] * self.type.led_count
        self.used = False

    # -- geometry -----------------------------------------------------------

    @property
    def width(self) -> int:
        """Number of LEDs across the module."""
        return self.type.width

    @property
    def height(self) -> int:
        """Number of LED rows in the module."""
        return self.type.height

    @property
    def led_count(self) -> int:
        """Total number of LEDs in the module."""
        return self.type.led_count

    @property
    def is_matrix(self) -> bool:
        """True if the module exposes an addressable 5x5 grid."""
        return self.type.is_matrix

    # -- colour access ------------------------------------------------------

    @property
    def colors(self) -> List[str]:
        """The logical, row-major list of LED colours (normalised hex)."""
        return list(self._colors)

    def _index(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(
                f"Pixel ({x}, {y}) is out of range for a {self.width}x{self.height} module"
            )
        return y * self.width + x

    def get_pixel(self, x: int, y: int) -> str:
        """Return the colour of the dot at column ``x``, row ``y``."""
        return self._colors[self._index(x, y)]

    def set_pixel(self, x: int, y: int, color: ColorLike) -> None:
        """Set a single dot at column ``x``, row ``y``."""
        self._colors[self._index(x, y)] = to_hex(color)
        self.used = True

    def set_grid(self, colors: Sequence[ColorLike]) -> None:
        """Replace the whole grid with ``colors`` (row-major, ``led_count`` long)."""
        if len(colors) != self.led_count:
            raise ValueError(
                f"{self.type.value} module expects {self.led_count} colours, "
                f"got {len(colors)}"
            )
        self._colors = [to_hex(color) for color in colors]
        self.used = True

    def fill(self, color: ColorLike) -> None:
        """Set every dot in the module to ``color``."""
        self._colors = [to_hex(color)] * self.led_count
        self.used = True

    def clear(self) -> None:
        """Turn every dot off and mark the module unused."""
        self._colors = [BLACK] * self.led_count
        self.used = False

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Module(type={self.type.value!r}, used={self.used})"
