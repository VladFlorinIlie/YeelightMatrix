"""Control library for the Yeelight Cube Matrix.

Typical usage::

    from yeelight_matrix import CubeMatrix, Layout

    cube = CubeMatrix("192.168.0.34")
    cube.set_fx_mode("direct")

    layout = Layout("vertical", "bottom", ["5x5_clear", "5x5_clear", "1x1"])
    layout.set_pixel(0, 2, 2, "#ff0000")      # one dot
    layout.set_module_colors(1, "#0000ff")     # whole module
    layout.set_image("art.png", start_module=0, max_modules=2)

    cube.update_leds(layout.render_frame())
"""

from __future__ import annotations

from .color import BLACK, ColorLike, encode, encode_many, to_hex, to_rgb
from .cube_matrix import FX_MODE_DIRECT, CubeMatrix
from .enums import BasePosition, ModuleType, Orientation
from .exceptions import CubeMatrixError, LayoutError, YeelightMatrixError
from .layout import Layout
from .module import Module

__version__ = "0.2.0"

__all__ = [
    "CubeMatrix",
    "Layout",
    "Module",
    "ModuleType",
    "Orientation",
    "BasePosition",
    "ColorLike",
    "to_rgb",
    "to_hex",
    "encode",
    "encode_many",
    "BLACK",
    "FX_MODE_DIRECT",
    "YeelightMatrixError",
    "CubeMatrixError",
    "LayoutError",
    "__version__",
]
