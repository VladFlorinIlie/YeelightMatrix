"""Exception types raised by the Yeelight Cube Matrix library."""

from __future__ import annotations


class YeelightMatrixError(Exception):
    """Base class for all errors raised by this library."""


class CubeMatrixError(YeelightMatrixError):
    """Raised when communication with the device fails."""


class LayoutError(YeelightMatrixError):
    """Raised when an operation is invalid for the current layout."""
