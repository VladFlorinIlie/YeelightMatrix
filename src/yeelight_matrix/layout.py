"""Arrangement of cube modules and rendering of the combined LED frame.

A :class:`Layout` knows how the physical modules are stacked (orientation and
which end is the base) and turns the per-module logical colour grids into the
single base64 frame understood by the device.

Modules are addressed by their *logical* index (0 is the visual first module,
matching the order you would read the picture). Internally the modules may be
stored reversed and each is rotated at render time so that pictures appear the
right way up regardless of how the stack is mounted.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from .color import ColorLike, encode_many
from .enums import BasePosition, ModuleType, Orientation
from .exceptions import LayoutError
from .image_utils import load_image_grids, rotate_grid
from .module import Module

_LOGGER = logging.getLogger(__name__)

# Mapping of (orientation, base) -> (rotation degrees, modules stored reversed).
_ORIENTATION_TABLE = {
    (Orientation.VERTICAL, BasePosition.BOTTOM): (180, True),
    (Orientation.VERTICAL, BasePosition.TOP): (0, False),
    (Orientation.HORIZONTAL, BasePosition.LEFT): (270, False),
    (Orientation.HORIZONTAL, BasePosition.RIGHT): (90, True),
}


class Layout:
    """A stack of :class:`Module` objects rendered as one LED frame.

    Args:
        orientation: Whether modules are stacked vertically or horizontally.
        base: Which end of the stack is the base.
        modules: Optional initial list of module types (strings or
            :class:`ModuleType`). Equivalent to calling :meth:`add_modules`.
    """

    def __init__(
        self,
        orientation: Orientation | str,
        base: BasePosition | str,
        modules: Optional[Sequence[ModuleType | str]] = None,
    ) -> None:
        self.orientation = Orientation(orientation)
        self.base = BasePosition(base)
        try:
            self.rotation, self._flipped = _ORIENTATION_TABLE[(self.orientation, self.base)]
        except KeyError as exc:
            raise LayoutError(
                f"Base {self.base.value!r} is not valid for a {self.orientation.value} layout"
            ) from exc

        # Modules in transmission/storage order (reversed when flipped).
        self._modules: List[Module] = []
        if modules:
            self.add_modules(modules)

    # -- module management --------------------------------------------------

    def __len__(self) -> int:
        return len(self._modules)

    @property
    def modules(self) -> List[Module]:
        """Modules in logical order (index 0 = visual first module)."""
        return list(reversed(self._modules)) if self._flipped else list(self._modules)

    def add_modules(self, modules: Sequence[ModuleType | str], clear: bool = True) -> None:
        """Add a list of module types, replacing existing modules by default."""
        if clear:
            self._modules = []
        wrapped = [Module(module_type) for module_type in modules]
        if self._flipped:
            wrapped = list(reversed(wrapped))
        self._modules.extend(wrapped)

    def add_module(self, module_type: ModuleType | str, index: Optional[int] = None) -> None:
        """Insert a single module at the given logical ``index`` (append if None)."""
        logical = len(self._modules) if index is None else index
        self._modules.insert(max(0, self._storage_index(logical)), Module(module_type))

    def module_at(self, index: int) -> Module:
        """Return the module at the given logical index."""
        try:
            return self._modules[self._storage_index(index)]
        except IndexError as exc:
            raise LayoutError(f"No module at index {index}") from exc

    def _storage_index(self, logical_index: int) -> int:
        if self._flipped:
            return len(self._modules) - logical_index - 1
        return logical_index

    # -- colour / pixel editing --------------------------------------------

    def set_pixel(self, module_index: int, x: int, y: int, color: ColorLike) -> None:
        """Set a single dot on a module's 5x5 grid (or the 0,0 dot of a spotlight)."""
        _LOGGER.debug("Set pixel (%s, %s) on module %s -> %s", x, y, module_index, color)
        self.module_at(module_index).set_pixel(x, y, color)

    def set_module_colors(self, index: int, colors: Sequence[ColorLike] | ColorLike) -> None:
        """Set a module's colours.

        ``colors`` may be a single colour (fills the whole module) or a
        row-major sequence matching the module's LED count.
        """
        _LOGGER.debug("Set colours on module %s -> %s", index, colors)
        module = self.module_at(index)
        if isinstance(colors, str) or (
            isinstance(colors, (tuple, list))
            and len(colors) == 3
            and all(isinstance(c, int) for c in colors)
        ):
            module.fill(colors)  # single colour
        else:
            module.set_grid(colors)

    def fill(self, color: ColorLike) -> None:
        """Fill every module in the layout with a single colour."""
        for module in self._modules:
            module.fill(color)

    def clear(self) -> None:
        """Turn every dot in the layout off."""
        for module in self._modules:
            module.clear()

    def set_image(self, image_path: str, start_module: int = 0, max_modules: Optional[int] = None) -> None:
        """Render a picture across consecutive unused 5x5 modules.

        Starting from logical index ``start_module`` the image is mapped onto up
        to ``max_modules`` consecutive, currently-unused 5x5 (clear) modules.
        """
        _LOGGER.debug("Set image %s from module %s (max %s)", image_path, start_module, max_modules)
        # Scan in transmission order. For base-at-end layouts (bottom/right) the
        # image always begins at the base; for base-at-start layouts (top/left)
        # it honours ``start_module``. This matches the device's reading order.
        scan_start = 0 if self._flipped else start_module
        limit = len(self._modules) if max_modules is None else max_modules

        # Find the first usable module at or after the scan position.
        first = next(
            (
                i
                for i in range(max(0, scan_start), len(self._modules))
                if self._is_free_matrix(self._modules[i])
            ),
            None,
        )
        if first is None:
            raise LayoutError("No free 5x5 module found to start the image")

        # Count consecutive usable modules, capped at the limit.
        count = 0
        for module in self._modules[first:]:
            if count >= limit or not self._is_free_matrix(module):
                break
            count += 1

        grids = load_image_grids(image_path, count, self.orientation)
        for module, grid in zip(self._modules[first : first + count], grids):
            module.set_grid(grid)

    @staticmethod
    def _is_free_matrix(module: Module) -> bool:
        return module.type is ModuleType.CLEAR and not module.used

    # -- rendering ----------------------------------------------------------

    def render_frame(self) -> str:
        """Return the full base64 LED frame for :meth:`CubeMatrix.update_leds`."""
        frame = ""
        for module in reversed(self._modules) if self._flipped else self._modules:
            colors = rotate_grid(module.colors, self.rotation, module.width) if module.is_matrix \
                else module.colors
            frame += encode_many(colors)
        return frame
