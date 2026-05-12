"""Config flow for Nova Poshta integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import API_KEY, DOMAIN, TRACKING_NUMBERS, PHONE
from .coordinator import NovaPoshtaCoordinator, InvalidAuth

_LOGGER = logging.getLogger(__name__)

TTN_PATTERN = r"^\d{14}(,\s*\d{14})*$"


def _parse_ttns(raw: str) -> list[str]:
    """Parse comma-separated TTN string into a clean list."""
    return [t.strip() for t in raw.split(",") if t.strip()]


class NovaPoshtaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nova Poshta."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[API_KEY].strip()
            phone = user_input[PHONE].strip()
            ttns = _parse_ttns(user_input[TRACKING_NUMBERS])

            if not ttns:
                errors[TRACKING_NUMBERS] = "invalid_ttns"
            else:
                try:
                    coordinator = NovaPoshtaCoordinator(
                        {API_KEY: api_key, PHONE: phone, TRACKING_NUMBERS: ttns},
                        self.hass,
                    )
                    await coordinator.async_validate_input()
                except InvalidAuth:
                    errors[API_KEY] = "invalid_auth"
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(api_key[:8])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Nova Poshta ({phone})",
                        data={
                            API_KEY: api_key,
                            PHONE: phone,
                            TRACKING_NUMBERS: ttns,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(API_KEY): str,
                    vol.Required(PHONE): str,
                    vol.Required(TRACKING_NUMBERS): str,
                }
            ),
            description_placeholders={
                "ttns_example": "20451424853965, 20451420857213",
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NovaPoshtaOptionsFlow(config_entry)


class NovaPoshtaOptionsFlow(OptionsFlow):
    """Handle options — allows adding/removing TTNs without re-setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        current_ttns = self._config_entry.data.get(TRACKING_NUMBERS, [])
        current_ttns_str = ", ".join(current_ttns)

        if user_input is not None:
            ttns = _parse_ttns(user_input[TRACKING_NUMBERS])
            if not ttns:
                errors[TRACKING_NUMBERS] = "invalid_ttns"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, TRACKING_NUMBERS: ttns},
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(TRACKING_NUMBERS, default=current_ttns_str): str,
                }
            ),
            description_placeholders={
                "ttns_example": "20451424853965, 20451420857213",
            },
            errors=errors,
        )
