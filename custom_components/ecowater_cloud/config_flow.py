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
from .backends.hydrolink import HydroLinkBackend
from .const import (
    BACKEND_AYLA,
    BACKEND_HYDROLINK,
    CONF_BACKEND,
    CONF_POLLING_INTERVAL,
    CONF_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .exceptions import AuthenticationError, ConnectivityError, RateLimitError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BACKEND, default=BACKEND_AYLA): vol.In(
            {
                BACKEND_AYLA: "Legacy EcoWater Wi-Fi",
                BACKEND_HYDROLINK: "HydroLink Home",
            }
        ),
    }
)

STEP_AYLA_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_HYDROLINK_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION, default="us"): vol.In(
            {
                "us": "United States",
                "eu": "Europe",
            }
        ),
    }
)


async def validate_input(hass: HomeAssistant, backend_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    from .backends import BackendAdapter
    session = async_get_clientsession(hass)

    backend: BackendAdapter
    if backend_type == BACKEND_AYLA:
        backend = AylaBackend(session, data[CONF_USERNAME], data[CONF_PASSWORD])
    elif backend_type == BACKEND_HYDROLINK:
        backend = HydroLinkBackend(
            session, data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_REGION]
        )
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    await backend.async_authenticate()

    # Retrieve devices to ensure they have at least one supported device
    devices = await backend.async_list_devices()

    if not devices:
        raise NoDevicesError("No devices found on this account")

    return {"title": "EcoWater Cloud"}


class EcoWaterCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EcoWater Cloud."""

    VERSION = 2
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._backend: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self._backend = user_input[CONF_BACKEND]
            if self._backend == BACKEND_AYLA:
                return await self.async_step_ayla()
            if self._backend == BACKEND_HYDROLINK:
                return await self.async_step_hydrolink()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA
        )

    async def async_step_ayla(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Ayla credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_email = user_input[CONF_USERNAME].lower().strip()
            await self.async_set_unique_id(normalized_email)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, BACKEND_AYLA, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectivityError:
                errors["base"] = "cannot_connect"
            except RateLimitError:
                errors["base"] = "rate_limit"
            except NoDevicesError:
                errors["base"] = "no_devices"
            except NotImplementedError:
                errors["base"] = "not_implemented"
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
            step_id="ayla", data_schema=STEP_AYLA_DATA_SCHEMA, errors=errors
        )

    async def async_step_hydrolink(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle HydroLink credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_email = user_input[CONF_USERNAME].lower().strip()
            await self.async_set_unique_id(normalized_email)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, BACKEND_HYDROLINK, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectivityError:
                errors["base"] = "cannot_connect"
            except RateLimitError:
                errors["base"] = "rate_limit"
            except NoDevicesError:
                errors["base"] = "no_devices"
            except NotImplementedError:
                errors["base"] = "not_implemented"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                data = {
                    CONF_BACKEND: BACKEND_HYDROLINK,
                    CONF_USERNAME: normalized_email,
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_REGION: user_input[CONF_REGION],
                }
                return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="hydrolink", data_schema=STEP_HYDROLINK_DATA_SCHEMA, errors=errors
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
        backend_type = reauth_entry.data.get(CONF_BACKEND, BACKEND_AYLA)

        if user_input is not None:
            try:
                test_data = {
                    CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }
                if CONF_REGION in reauth_entry.data:
                    test_data[CONF_REGION] = reauth_entry.data[CONF_REGION]

                await validate_input(self.hass, backend_type, test_data)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectivityError:
                errors["base"] = "cannot_connect"
            except RateLimitError:
                errors["base"] = "rate_limit"
            except NotImplementedError:
                errors["base"] = "not_implemented"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={**reauth_entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]},
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

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLLING_INTERVAL, default=default_polling
                ): vol.All(vol.Coerce(int), vol.Clamp(min=min_polling)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


class NoDevicesError(Exception):
    """Error to indicate no devices were found."""
