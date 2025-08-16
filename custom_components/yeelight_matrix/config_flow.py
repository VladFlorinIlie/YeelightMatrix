"""Config flow for Yeelight Matrix."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BASE_POSITION,
    CONF_LAYOUT_ORIENTATION,
    CONF_MODULES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=55443): int,
    }
)

STEP_LAYOUT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LAYOUT_ORIENTATION, default="vertical"): vol.In(
            ["vertical", "horizontal"]
        ),
        vol.Required(CONF_BASE_POSITION, default="bottom"): vol.In(
            ["top", "bottom", "left", "right"]
        ),
        vol.Required(CONF_MODULES): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yeelight Matrix."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_layout()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_layout(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the layout configuration step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            modules_str = user_input[CONF_MODULES]
            modules_list = [module.strip() for module in modules_str.split(",")]

            self.data[CONF_MODULES] = modules_list
            self.data[CONF_LAYOUT_ORIENTATION] = user_input[CONF_LAYOUT_ORIENTATION]
            self.data[CONF_BASE_POSITION] = user_input[CONF_BASE_POSITION]

            return self.async_create_entry(title=self.data[CONF_HOST], data=self.data)

        return self.async_show_form(
            step_id="layout", data_schema=STEP_LAYOUT_DATA_SCHEMA, errors=errors
        )
