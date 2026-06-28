"""Enumerations describing the physical configuration of a cube matrix."""

from __future__ import annotations

from enum import Enum


class ModuleType(str, Enum):
    """The kind of a single stackable cube module.

    The string values are kept stable because they are persisted in
    configuration (for example by the Home Assistant integration).
    """

    #: 5x5 matrix of individually addressable LEDs (sharp).
    CLEAR = "5x5_clear"
    #: 5x5 matrix of individually addressable LEDs (diffused / blurred).
    BLUR = "5x5_blur"
    #: Single-LED spotlight module.
    SPOTLIGHT = "1x1"

    @property
    def is_matrix(self) -> bool:
        """True for the 5x5 modules whose individual dots can be addressed."""
        return self in (ModuleType.CLEAR, ModuleType.BLUR)

    @property
    def width(self) -> int:
        """Number of LEDs across a single module."""
        return 5 if self.is_matrix else 1

    @property
    def height(self) -> int:
        """Number of LED rows in a single module."""
        return 5 if self.is_matrix else 1

    @property
    def led_count(self) -> int:
        """Total number of LEDs in the module."""
        return self.width * self.height


class Orientation(str, Enum):
    """The axis along which modules are stacked."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class BasePosition(str, Enum):
    """Where the base (first physical module) of the stack sits.

    ``TOP``/``BOTTOM`` apply to a :attr:`Orientation.VERTICAL` stack and
    ``LEFT``/``RIGHT`` to a :attr:`Orientation.HORIZONTAL` one.
    """

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
