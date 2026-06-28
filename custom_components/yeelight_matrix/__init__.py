"""The Yeelight Matrix integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from yeelight_matrix import CubeMatrix, Layout

from .const import (
    CONF_BASE_POSITION,
    CONF_LAYOUT_ORIENTATION,
    CONF_MODULES,
    DOMAIN,
)
from .controller import YeelightMatrixController
from .frontend import async_register_card

PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Yeelight Matrix from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    orientation = entry.data[CONF_LAYOUT_ORIENTATION]
    base = entry.data[CONF_BASE_POSITION]
    modules = entry.data[CONF_MODULES]

    # Constructing the cube performs network I/O; keep it off the event loop.
    cube = await hass.async_add_executor_job(CubeMatrix, host, port)
    layout = Layout(orientation, base, modules)
    controller = YeelightMatrixController(hass, cube, layout, entry.entry_id)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    await async_register_card(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
