"""Light platform for Yeelight Matrix."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yeelight_matrix.cube_matrix import CubeMatrix
from yeelight_matrix.layout import Layout

from .const import (
    CONF_BASE_POSITION,
    CONF_LAYOUT_ORIENTATION,
    CONF_MODULES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_MODULE_COLORS = "set_module_colors"
SERVICE_SET_IMAGE = "set_image"
SERVICE_SET_FX_MODE = "set_fx_mode"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Yeelight Matrix light platform."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    layout_orientation = entry.data[CONF_LAYOUT_ORIENTATION]
    base_position = entry.data[CONF_BASE_POSITION]
    modules = entry.data[CONF_MODULES]

    cube = CubeMatrix(host, port)
    layout = Layout(layout_orientation, base_position, modules)

    light = YeelightMatrixLight(cube, layout, entry.entry_id)
    async_add_entities([light])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_MODULE_COLORS,
        {
            vol.Required("module_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required("colors"): vol.Any(vol.All(list, [vol.All(str)]), str),
        },
        "async_set_module_colors",
    )
    platform.async_register_entity_service(
        SERVICE_SET_IMAGE,
        {
            vol.Required("image_path"): str,
            vol.Required("start_module"): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required("max_modules"): vol.All(vol.Coerce(int), vol.Range(min=1)),
        },
        "async_set_image",
    )
    platform.async_register_entity_service(
        SERVICE_SET_FX_MODE,
        {
            vol.Required("mode"): str,
        },
        "async_set_fx_mode",
    )


class YeelightMatrixLight(LightEntity):
    """Representation of a Yeelight Matrix Light."""

    def __init__(self, cube: CubeMatrix, layout: Layout, unique_id: str) -> None:
        """Initialize the light."""
        self._cube = cube
        self._layout = layout
        self._attr_unique_id = unique_id
        self._attr_name = "Yeelight Matrix"
        self._attr_is_on = True
        self._attr_brightness = 255
        self._attr_rgb_color = (255, 255, 255)
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_color_mode = ColorMode.RGB

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        await self.hass.async_add_executor_job(self._cube.get_bulb().turn_on)
        self._attr_is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self.hass.async_add_executor_job(
                self._cube.get_bulb().set_brightness, brightness
            )
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            await self.hass.async_add_executor_job(self._cube.get_bulb().set_rgb, r, g, b)
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]

        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.hass.async_add_executor_job(self._cube.get_bulb().turn_off)
        self._attr_is_on = False
        await self.async_update_ha_state()

    async def async_update(self) -> None:
        """Update the light."""
        properties = await self.hass.async_add_executor_job(self._cube.get_bulb().get_properties)
        if properties:
            self._attr_is_on = properties["power"] == "on"
            self._attr_brightness = int(int(properties["bright"]) * 255 / 100)
            rgb_val = properties.get("rgb")
            if rgb_val is not None:
                if isinstance(rgb_val, str):
                    r = int(rgb_val[0:2], 16)
                    g = int(rgb_val[2:4], 16)
                    b = int(rgb_val[4:6], 16)
                    self._attr_rgb_color = (r, g, b)
                elif isinstance(rgb_val, int):
                    r = (rgb_val >> 16) & 0xFF
                    g = (rgb_val >> 8) & 0xFF
                    b = rgb_val & 0xFF
                    self._attr_rgb_color = (r, g, b)

    async def async_set_module_colors(self, module_index: int, colors: str | list[str]) -> None:
        """Set the colors of a module."""
        final_colors = []
        if isinstance(colors, str):
            try:
                # The layout object stores modules in reversed order if needed, so we use its internal list
                module = self._layout.device_layout[self._layout._get_index(module_index)]
                led_count = 25 if "5x5" in module.type else 1
                final_colors = [colors] * led_count
            except IndexError:
                _LOGGER.error("Module index %s out of range.", module_index)
                return
        else:
            final_colors = colors

        await self.hass.async_add_executor_job(
            self._layout.set_module_colors, module_index, final_colors
        )
        await self._async_draw_layout()

    async def async_set_image(
        self, image_path: str, start_module: int, max_modules: int
    ) -> None:
        """Set an image on the matrix."""
        await self.hass.async_add_executor_job(
            self._layout.set_image, image_path, start_module, max_modules
        )
        await self._async_draw_layout()

    async def async_set_fx_mode(self, mode: str) -> None:
        """Set the FX mode."""
        await self.hass.async_add_executor_job(self._cube.set_fx_mode, mode)

    async def _async_draw_layout(self) -> None:
        """Draw the layout on the cube."""
        raw_rgb_data = await self.hass.async_add_executor_job(self._layout.get_raw_rgb_data)
        await self.hass.async_add_executor_job(self._cube.draw_matrices, raw_rgb_data)
