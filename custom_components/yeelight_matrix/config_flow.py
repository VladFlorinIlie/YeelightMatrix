"""Config flow for Yeelight Matrix."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from yeelight_matrix.enums import BasePosition, ModuleType, Orientation

from .const import (
    CONF_BASE_POSITION,
    CONF_DOT_ENTITIES,
    CONF_LAYOUT_ORIENTATION,
    CONF_MODULES,
    DEFAULT_DOT_ENTITIES,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_VALID_MODULE_TYPES = {item.value for item in ModuleType}
_VALID_BASES = {
    Orientation.VERTICAL.value: {BasePosition.TOP.value, BasePosition.BOTTOM.value},
    Orientation.HORIZONTAL.value: {BasePosition.LEFT.value, BasePosition.RIGHT.value},
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)

STEP_LAYOUT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LAYOUT_ORIENTATION, default=Orientation.VERTICAL.value): vol.In(
            [item.value for item in Orientation]
        ),
        vol.Required(CONF_BASE_POSITION, default=BasePosition.BOTTOM.value): vol.In(
            [item.value for item in BasePosition]
        ),
        vol.Required(CONF_MODULES): str,
        vol.Required(CONF_DOT_ENTITIES, default=DEFAULT_DOT_ENTITIES): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yeelight Matrix."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the connection step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            self.data.update(user_input)
            return await self.async_step_layout()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def async_step_layout(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the layout configuration step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            orientation = user_input[CONF_LAYOUT_ORIENTATION]
            base = user_input[CONF_BASE_POSITION]
            modules = [m.strip() for m in user_input[CONF_MODULES].split(",") if m.strip()]

            if not modules:
                errors[CONF_MODULES] = "no_modules"
            elif any(m not in _VALID_MODULE_TYPES for m in modules):
                errors[CONF_MODULES] = "invalid_module"
            elif base not in _VALID_BASES[orientation]:
                errors[CONF_BASE_POSITION] = "invalid_base"

            if not errors:
                self.data[CONF_LAYOUT_ORIENTATION] = orientation
                self.data[CONF_BASE_POSITION] = base
                self.data[CONF_MODULES] = modules
                self.data[CONF_DOT_ENTITIES] = user_input[CONF_DOT_ENTITIES]
                return self.async_create_entry(title=self.data[CONF_HOST], data=self.data)

        return self.async_show_form(
            step_id="layout", data_schema=STEP_LAYOUT_DATA_SCHEMA, errors=errors
        )
