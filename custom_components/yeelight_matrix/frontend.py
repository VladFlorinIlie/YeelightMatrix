"""Serve and auto-register the painter Lovelace card.

The card is registered as a Lovelace *dashboard resource* when possible, because
the frontend guarantees resources are loaded before any card renders (this
avoids the intermittent "custom element doesn't exist" race, especially in the
mobile app). If the dashboards are in YAML mode (resources are read-only there)
we fall back to loading the card as a global extra JS module.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_URL = "/yeelight_matrix/yeelight-matrix-card.js"
# Bump when the card JS changes so clients fetch the new version (cache-busting).
CARD_VERSION = "4"

_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card file and make it load on the frontend (once per instance)."""
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

    versioned_url = f"{CARD_URL}?v={CARD_VERSION}"

    # Preferred: register as a dashboard resource (reliable load order).
    if not await _async_register_resource(hass, versioned_url):
        # Fallback: load it as a global extra JS module.
        try:
            from homeassistant.components.frontend import add_extra_js_url

            add_extra_js_url(hass, versioned_url)
        except Exception as exc:  # noqa: BLE001 - non-fatal; manual resource works
            _LOGGER.debug("Could not auto-add card module (%s); add it manually", exc)

    hass.data[_REGISTERED] = True


async def _async_register_resource(hass: HomeAssistant, url: str) -> bool:
    """Add the card to the Lovelace resource collection (storage mode only).

    Returns True if the resource is registered (or already present), False if it
    can't be (e.g. YAML-mode dashboards), so the caller can fall back.
    """
    try:
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None)
        if resources is None and isinstance(lovelace, dict):
            resources = lovelace.get("resources")
        # Storage-mode collections can create items; YAML-mode ones cannot.
        if resources is None or not hasattr(resources, "async_create_item"):
            return False

        if not getattr(resources, "loaded", True):
            await resources.async_load()
            resources.loaded = True

        base = url.split("?", 1)[0]
        for item in resources.async_items():
            if item.get("url", "").split("?", 1)[0] == base:
                if item.get("url") != url:
                    # Same card, new version: update so clients fetch the latest.
                    await resources.async_update_item(
                        item["id"], {"res_type": "module", "url": url}
                    )
                return True

        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.debug("Registered Lovelace resource %s", url)
        return True
    except Exception as exc:  # noqa: BLE001 - fall back to extra JS module
        _LOGGER.debug("Lovelace resource registration failed (%s)", exc)
        return False
