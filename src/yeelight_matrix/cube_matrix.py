"""Low-level driver for a Yeelight Cube Matrix device.

This thin wrapper around :class:`yeelight.Bulb` exposes the handful of
matrix-specific commands (``activate_fx_mode`` and ``update_leds``) on top of
the standard bulb controls (power, brightness, colour) provided by the
underlying ``yeelight`` library.
"""

from __future__ import annotations

import logging
from typing import Sequence

from yeelight import Bulb

from .color import ColorLike, encode, encode_many
from .exceptions import CubeMatrixError

_LOGGER = logging.getLogger(__name__)

#: FX mode required for direct, per-LED control via :meth:`CubeMatrix.update_leds`.
FX_MODE_DIRECT = "direct"


class CubeMatrix:
    """Represents a physical Yeelight Cube Matrix on the network.

    Args:
        ip: IP address of the device.
        port: Control port (usually ``55443``).
        music_mode: If ``True`` (default) the device is put into "music mode"
            immediately. The cube reports itself as being in music mode once
            colour matrices are applied, so enabling it up front avoids the
            per-command rate limiting otherwise imposed by the device.
    """

    def __init__(self, ip: str, port: int = 55443, music_mode: bool = True) -> None:
        self._bulb = Bulb(ip, port)
        if music_mode:
            self.start_music()

    @property
    def bulb(self) -> Bulb:
        """The underlying :class:`yeelight.Bulb`, for standard bulb controls."""
        return self._bulb

    def start_music(self) -> None:
        """Enable music mode (best-effort; ignores an already-on state)."""
        try:
            self._bulb.start_music()
        except Exception as exc:  # noqa: BLE001 - yeelight raises broad errors
            _LOGGER.debug("start_music failed (may already be on): %s", exc)

    def set_fx_mode(self, mode: str = FX_MODE_DIRECT) -> None:
        """Activate an effect mode. Use ``"direct"`` for per-LED control."""
        self._send("activate_fx_mode", [{"mode": mode}])

    def update_leds(self, rgb_data: str) -> None:
        """Push a full frame of LED data (concatenated base64) to the device."""
        self._send("update_leds", [rgb_data])

    def set_pixels(self, colors: Sequence[ColorLike]) -> None:
        """Encode and push an ordered sequence of colours as one frame."""
        self.update_leds(encode_many(colors))

    @staticmethod
    def encode_color(color: ColorLike) -> str:
        """Encode a single colour to the device's base64 representation."""
        return encode(color)

    def _send(self, command: str, params: list) -> None:
        try:
            self._bulb.send_command(command, params)
        except Exception as exc:  # noqa: BLE001 - surface a typed error
            raise CubeMatrixError(f"Command {command!r} failed: {exc}") from exc

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"CubeMatrix(ip={self._bulb._ip!r}, port={self._bulb._port!r})"
