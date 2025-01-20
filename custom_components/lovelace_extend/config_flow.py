from .const import DOMAIN
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import config_validation as cv
from typing import Any, Dict
from voluptuous import Schema, Optional


def get_schema(hass: HomeAssistant) -> Schema:

    dashboards: Dict[str, str] = {}

    for key, value in hass.data['lovelace']['dashboards'].items():
        if value.config is not None:
            dashboards.update({
                key: value.config['title'] if 'title' in value.config else value.config['url_path']
            })

    return Schema({
        Optional('dashboards'): cv.multi_select(dashboards),
    })


class LovelaceExtendConfigFlow(ConfigFlow, domain=DOMAIN):
    """Lovelace Extend config flow."""
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: Dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="Lovelace Extension", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=get_schema(self.hass), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    async def async_step_init(self, input: Dict[str, Any]|None = None) -> Dict[str, Any]:

        if input is not None:

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=input
            )

            return self.async_create_entry(data=input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                get_schema(self.hass), self.config_entry.data
            ),
        )