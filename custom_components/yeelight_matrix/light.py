"""Light platform for Yeelight Matrix.

Exposes three things:

* a whole-device light (power / brightness / colour) backed by the bulb;
* optional per-dot light entities, one per addressable LED, so individual dots
  can be tapped and coloured straight from the dashboard;
* a set of services (``set_pixel``, ``set_pixels``, ``set_image`` …) for
  scripted and custom-card control of individual dots and pixel-art images.
"""

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
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DOT_ENTITIES,
    DEFAULT_DOT_ENTITIES,
    DOMAIN,
    SERVICE_CLEAR,
    SERVICE_SET_FX_MODE,
    SERVICE_SET_IMAGE,
    SERVICE_SET_MODULE_COLOR,
    SERVICE_SET_MODULE_COLORS,
    SERVICE_SET_PIXEL,
    SERVICE_SET_PIXELS,
)
from .controller import YeelightMatrixController, updated_signal

_LOGGER = logging.getLogger(__name__)

BLACK_RGB = (0, 0, 0)

_PIXEL_SCHEMA = vol.Schema(
    {
        vol.Required("module_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("x"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("y"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("color"): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Yeelight Matrix light platform."""
    controller: YeelightMatrixController = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Yeelight Matrix",
        manufacturer="Yeelight",
        model="Cube Matrix",
    )

    entities: list[LightEntity] = [
        YeelightMatrixLight(controller, entry, device_info)
    ]

    if entry.data.get(CONF_DOT_ENTITIES, DEFAULT_DOT_ENTITIES):
        for module_index, module in enumerate(controller.layout.modules):
            if not module.is_matrix:
                # Spotlight modules are a single dot; still addressable at (0, 0).
                entities.append(
                    YeelightMatrixDot(controller, entry, device_info, module_index, 0, 0)
                )
                continue
            for y in range(module.height):
                for x in range(module.width):
                    entities.append(
                        YeelightMatrixDot(
                            controller, entry, device_info, module_index, x, y
                        )
                    )

    async_add_entities(entities)
    _register_services()


def _register_services() -> None:
    """Register the matrix services on this platform (idempotent)."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_PIXEL, _PIXEL_SCHEMA.schema, "async_service_set_pixel"
    )
    platform.async_register_entity_service(
        SERVICE_SET_PIXELS,
        {vol.Required("pixels"): vol.All(cv.ensure_list, [_PIXEL_SCHEMA])},
        "async_service_set_pixels",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MODULE_COLOR,
        {
            vol.Required("module_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required("color"): cv.string,
        },
        "async_service_set_module_color",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MODULE_COLORS,
        {
            vol.Required("module_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required("colors"): vol.All(cv.ensure_list, [cv.string]),
        },
        "async_service_set_module_colors",
    )
    platform.async_register_entity_service(
        SERVICE_SET_IMAGE,
        {
            vol.Optional("image_path"): cv.string,
            vol.Optional("image_data"): cv.string,
            vol.Required("start_module", default=0): vol.All(
                vol.Coerce(int), vol.Range(min=0)
            ),
            vol.Required("max_modules", default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1)
            ),
        },
        "async_service_set_image",
    )
    platform.async_register_entity_service(
        SERVICE_CLEAR, {}, "async_service_clear"
    )
    platform.async_register_entity_service(
        SERVICE_SET_FX_MODE, {vol.Required("mode"): cv.string}, "async_service_set_fx_mode"
    )


class _MatrixEntity(LightEntity):
    """Base entity sharing the controller and the matrix-level services."""

    _attr_has_entity_name = True

    def __init__(
        self,
        controller: YeelightMatrixController,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        self._controller = controller
        self._entry = entry
        self._attr_device_info = device_info

    # -- services (callable on any entity of this integration) --------------

    async def async_service_set_pixel(
        self, module_index: int, x: int, y: int, color: str
    ) -> None:
        await self._controller.async_set_pixel(module_index, x, y, color)

    async def async_service_set_pixels(self, pixels: list[dict[str, Any]]) -> None:
        edits = [(p["module_index"], p["x"], p["y"], p["color"]) for p in pixels]
        await self._controller.async_set_pixels(edits)

    async def async_service_set_module_color(self, module_index: int, color: str) -> None:
        await self._controller.async_set_module_color(module_index, color)

    async def async_service_set_module_colors(
        self, module_index: int, colors: list[str]
    ) -> None:
        await self._controller.async_set_module_grid(module_index, colors)

    async def async_service_set_image(
        self,
        start_module: int,
        max_modules: int,
        image_path: str | None = None,
        image_data: str | None = None,
    ) -> None:
        await self._controller.async_set_image(
            start_module, max_modules, image_path, image_data
        )

    async def async_service_clear(self) -> None:
        await self._controller.async_clear()

    async def async_service_set_fx_mode(self, mode: str) -> None:
        await self._controller.async_set_fx_mode(mode)


class YeelightMatrixLight(_MatrixEntity):
    """Whole-device light (power, brightness, colour) for the cube."""

    _attr_name = None  # use the device name
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        controller: YeelightMatrixController,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(controller, entry, device_info)
        self._attr_unique_id = entry.entry_id
        self._attr_is_on = True
        self._attr_brightness = 255
        self._attr_rgb_color = (255, 255, 255)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the module layout so custom cards can render the grid."""
        layout = self._controller.layout
        return {
            "orientation": layout.orientation.value,
            "base_position": layout.base.value,
            "modules": [module.type.value for module in layout.modules],
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally setting brightness/colour."""
        bulb = self._controller.cube.bulb
        await self.hass.async_add_executor_job(bulb.turn_on)
        self._attr_is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            brightness = max(1, round(kwargs[ATTR_BRIGHTNESS] * 100 / 255))
            await self.hass.async_add_executor_job(bulb.set_brightness, brightness)
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            await self.hass.async_add_executor_job(bulb.set_rgb, r, g, b)
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.hass.async_add_executor_job(self._controller.cube.bulb.turn_off)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll the bulb for power/brightness/colour."""
        properties = await self.hass.async_add_executor_job(
            self._controller.cube.bulb.get_properties
        )
        if not properties:
            return
        self._attr_is_on = properties.get("power") == "on"
        if properties.get("bright"):
            self._attr_brightness = round(int(properties["bright"]) * 255 / 100)
        rgb = properties.get("rgb")
        if isinstance(rgb, str) and len(rgb) == 6:
            self._attr_rgb_color = (
                int(rgb[0:2], 16),
                int(rgb[2:4], 16),
                int(rgb[4:6], 16),
            )
        elif isinstance(rgb, int):
            self._attr_rgb_color = ((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF)


class YeelightMatrixDot(_MatrixEntity):
    """A single addressable LED of the matrix, controllable from the UI."""

    _attr_should_poll = False
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        controller: YeelightMatrixController,
        entry: ConfigEntry,
        device_info: DeviceInfo,
        module_index: int,
        x: int,
        y: int,
    ) -> None:
        super().__init__(controller, entry, device_info)
        self._module_index = module_index
        self._x = x
        self._y = y
        self._attr_unique_id = f"{entry.entry_id}_m{module_index}_x{x}_y{y}"
        self._attr_name = f"Module {module_index} dot {x},{y}"
        self._refresh_from_layout()

    def _refresh_from_layout(self) -> None:
        from yeelight_matrix.color import to_rgb

        module = self._controller.layout.module_at(self._module_index)
        rgb = to_rgb(module.get_pixel(self._x, self._y))
        self._attr_rgb_color = rgb
        self._attr_is_on = rgb != BLACK_RGB

    async def async_added_to_hass(self) -> None:
        """Refresh when any draw happens so the dot stays in sync."""

        def _updated() -> None:
            self._refresh_from_layout()
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, updated_signal(self._entry.entry_id), _updated
            )
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Colour this dot (defaults to white if no colour is given)."""
        rgb = kwargs.get(ATTR_RGB_COLOR, (255, 255, 255))
        await self._controller.async_set_pixel(
            self._module_index, self._x, self._y, tuple(rgb)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn this dot off (black)."""
        await self._controller.async_set_pixel(
            self._module_index, self._x, self._y, BLACK_RGB
        )
