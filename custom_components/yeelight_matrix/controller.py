"""Shared controller that owns the cube device and its layout.

A single :class:`YeelightMatrixController` is created per config entry and shared
by every entity and service. It serialises access to the device and turns the
high-level "edit then draw" operations into the single ``update_leds`` frame the
hardware expects.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from typing import Iterable, Sequence, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from yeelight_matrix import CubeMatrix, Layout
from yeelight_matrix.color import ColorLike

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

#: A single dot edit: (module_index, x, y, colour).
PixelEdit = Tuple[int, int, int, ColorLike]


def updated_signal(entry_id: str) -> str:
    """Dispatcher signal fired after the matrix is redrawn."""
    return f"{DOMAIN}_{entry_id}_updated"


class YeelightMatrixController:
    """Owns one cube + layout and provides async, drawing-aware operations."""

    def __init__(
        self, hass: HomeAssistant, cube: CubeMatrix, layout: Layout, entry_id: str
    ) -> None:
        self._hass = hass
        self._cube = cube
        self._layout = layout
        self._entry_id = entry_id
        self._lock = asyncio.Lock()

    @property
    def cube(self) -> CubeMatrix:
        return self._cube

    @property
    def layout(self) -> Layout:
        return self._layout

    # -- editing operations -------------------------------------------------

    async def async_set_pixel(
        self, module_index: int, x: int, y: int, color: ColorLike, draw: bool = True
    ) -> None:
        """Set a single dot, then optionally push the frame."""
        self._layout.set_pixel(module_index, x, y, color)
        if draw:
            await self.async_draw()

    async def async_set_pixels(self, edits: Iterable[PixelEdit], draw: bool = True) -> None:
        """Apply many dot edits as one batch and push a single frame."""
        for module_index, x, y, color in edits:
            self._layout.set_pixel(module_index, x, y, color)
        if draw:
            await self.async_draw()

    async def async_set_module_color(
        self, module_index: int, color: ColorLike, draw: bool = True
    ) -> None:
        """Fill a whole module with one colour."""
        self._layout.set_module_colors(module_index, color)
        if draw:
            await self.async_draw()

    async def async_set_module_grid(
        self, module_index: int, colors: Sequence[ColorLike], draw: bool = True
    ) -> None:
        """Set a module's full row-major colour grid."""
        self._layout.set_module_colors(module_index, list(colors))
        if draw:
            await self.async_draw()

    async def async_set_image(
        self,
        start_module: int,
        max_modules: int,
        image_path: str | None = None,
        image_data: str | None = None,
    ) -> None:
        """Render a picture (from a path or base64 data) across the matrix."""
        path, cleanup = await self._hass.async_add_executor_job(
            _resolve_image, image_path, image_data
        )
        try:
            await self._hass.async_add_executor_job(
                self._layout.set_image, path, start_module, max_modules
            )
            await self.async_draw()
        finally:
            if cleanup:
                await self._hass.async_add_executor_job(_safe_unlink, path)

    async def async_clear(self, draw: bool = True) -> None:
        """Turn every dot off."""
        self._layout.clear()
        if draw:
            await self.async_draw()

    async def async_set_fx_mode(self, mode: str) -> None:
        """Activate a device effect mode (use ``direct`` for per-LED control)."""
        await self._hass.async_add_executor_job(self._cube.set_fx_mode, mode)

    # -- rendering ----------------------------------------------------------

    async def async_draw(self) -> None:
        """Render the current layout and push it to the device (serialised)."""
        async with self._lock:
            await self._hass.async_add_executor_job(self._draw)
        async_dispatcher_send(self._hass, updated_signal(self._entry_id))

    def _draw(self) -> None:
        # Ensure the cube is on and in direct mode before pushing a frame, so
        # editing a dot "just works" even if the device was off or had been
        # switched to another effect mode.
        self._cube.bulb.turn_on()
        self._cube.set_fx_mode("direct")
        self._cube.update_leds(self._layout.render_frame())


def _resolve_image(image_path: str | None, image_data: str | None) -> Tuple[str, bool]:
    """Return ``(path, is_temporary)`` for the requested image source."""
    if image_data:
        raw = base64.b64decode(image_data)
        fd, path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
        return path, True
    if image_path:
        return image_path, False
    raise ValueError("Either image_path or image_data must be provided")


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:  # pragma: no cover - best effort cleanup
        pass
