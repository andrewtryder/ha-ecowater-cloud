"""Config flow for EcoWater Cloud."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .backends.ayla import AylaBackend
from .const import (
    BACKEND_AYLA,
    CONF_BACKEND,
    CONF_POLLING_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .exceptions import AuthenticationError, ConnectivityError, RateLimitError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    backend = AylaBackend(session, data[CONF_USERNAME], data[CONF_PASSWORD])

    await backend.async_authenticate()

    # Retrieve devices to ensure they have at least one supported device
    devices = await backend.async_list_devices()

    if not devices:
        raise NoDevicesError("No devices found on this account")

    return {"title": "EcoWater Cloud"}


class EcoWaterCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the EcoWater Cloud config flow."""

    VERSION = 2
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_email = user_input[CONF_USERNAME].lower().strip()
            await self.async_set_unique_id(normalized_email)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectivityError:
                errors["base"] = "cannot_connect"
            except RateLimitError:
                errors["base"] = "rate_limit"
            except NoDevicesError:
                errors["base"] = "no_devices"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                data = {
                    CONF_BACKEND: BACKEND_AYLA,
                    CONF_USERNAME: normalized_email,
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }
                return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            try:
                test_data = {
                    CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }
                await validate_input(self.hass, test_data)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectivityError:
                errors["base"] = "cannot_connect"
            except RateLimitError:
                errors["base"] = "rate_limit"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={
                        **reauth_entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> EcoWaterCloudOptionsFlow:
        """Create the options flow."""
        return EcoWaterCloudOptionsFlow(config_entry)


class EcoWaterCloudOptionsFlow(OptionsFlow):
    """Handle options for EcoWater Cloud."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        default_polling = self.config_entry.options.get(
            CONF_POLLING_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60)
        )
        min_polling = int(MIN_SCAN_INTERVAL.total_seconds() / 60)
        max_polling = int(MAX_SCAN_INTERVAL.total_seconds() / 60)

        schema = vol.Schema(
            {
                vol.Required(CONF_POLLING_INTERVAL, default=default_polling): vol.All(
                    vol.Coerce(int), vol.Clamp(min=min_polling, max=max_polling)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


class NoDevicesError(Exception):
    """Error to indicate no devices were found."""
