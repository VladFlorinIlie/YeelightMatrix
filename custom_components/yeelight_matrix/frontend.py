"""Serve and auto-register the painter Lovelace card.

This lets the custom card load without the user manually adding a dashboard
resource: the integration serves the JS from its own ``www`` folder and asks the
frontend to load it as an extra module.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_URL = "/yeelight_matrix/yeelight-matrix-card.js"
_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Register the static path and frontend module once per HA instance."""
    if hass.data.get(_REGISTERED):
        return

    card_path = os.path.join(os.path.dirname(__file__), "www", "yeelight-matrix-card.js")
    if not os.path.isfile(card_path):
        _LOGGER.warning("Painter card not found at %s; skipping", card_path)
        return

    # Serve the file. Prefer the modern async API, fall back for older cores.
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, card_path, False)]
        )
    except ImportError:  # pragma: no cover - older Home Assistant
        hass.http.register_static_path(CARD_URL, card_path, False)

    # Load it on the frontend so the custom element registers itself.
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
    except Exception as exc:  # noqa: BLE001 - non-fatal; manual resource still works
        _LOGGER.debug("Could not auto-add card module (%s); add it manually", exc)

    hass.data[_REGISTERED] = True
