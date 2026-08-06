"""Coordinator for the EcoWater Cloud integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .exceptions import (
    AuthenticationError,
    ConnectivityError,
    ProtocolError,
    RateLimitError,
    ReauthenticationRequired,
)
from .models import EcoWaterDeviceData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .backends import BackendAdapter

_LOGGER = logging.getLogger(__name__)


class CoordinatorErrorCategory(StrEnum):
    """Categorized errors for diagnostics and repairs."""

    AUTHENTICATION = "authentication"
    CONNECTIVITY = "connectivity"
    RATE_LIMIT = "rate_limit"
    PROTOCOL = "protocol"


class AccountCoordinator(DataUpdateCoordinator[dict[str, EcoWaterDeviceData]]):
    """Coordinator that fetches data for all devices on a single account.

    Parameters
    ----------
    hass:
        The Home Assistant instance.
    backend:
        A :class:`~.backends.BackendAdapter` implementation (e.g.
        :class:`~.backends.ayla.AylaBackend`).
    entry_title:
        A display-safe label for this coordinator (used in log messages).
        Must not contain credentials or tokens.
    scan_interval:
        How often to poll the cloud.  Defaults to
        :data:`~.const.DEFAULT_SCAN_INTERVAL` (30 minutes).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        backend: BackendAdapter,
        entry_title: str,
        scan_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}:{entry_title}",
            update_interval=scan_interval,
        )
        self._backend = backend
        self.last_error_category: CoordinatorErrorCategory | None = None

    async def _async_setup(self) -> None:
        """Authenticate before the first account refresh.

        ``DataUpdateCoordinator._async_setup`` is called automatically by
        ``async_config_entry_first_refresh()`` before the first data fetch.
        Raising here prevents setup from completing and lets HA surface the
        correct error (auth failure vs. connectivity failure).
        """
        try:
            await self._backend.async_authenticate()
            self.last_error_category = None
        except AuthenticationError as err:
            self.last_error_category = CoordinatorErrorCategory.AUTHENTICATION
            raise ConfigEntryAuthFailed from err
        except ConnectivityError as err:
            self.last_error_category = CoordinatorErrorCategory.CONNECTIVITY
            raise UpdateFailed("Unable to connect to EcoWater") from err
        except RateLimitError as err:
            self.last_error_category = CoordinatorErrorCategory.RATE_LIMIT
            raise UpdateFailed("EcoWater rate limit reached") from err
        except ProtocolError as err:
            self.last_error_category = CoordinatorErrorCategory.PROTOCOL
            raise UpdateFailed("Unexpected EcoWater authentication response") from err

    async def _async_update_data(self) -> dict[str, EcoWaterDeviceData]:
        """Fetch the latest snapshots for all account devices.

        Returns
        -------
        dict[str, EcoWaterDeviceData]
            Mapping of ``serial_number → EcoWaterDeviceData``.

        Raises
        ------
        ConfigEntryAuthFailed
            When :class:`~.exceptions.AuthenticationError` or
            :class:`~.exceptions.ReauthenticationRequired` is raised by the
            backend.  Home Assistant will automatically trigger the reauth
            flow.
        UpdateFailed
            When :class:`~.exceptions.ConnectivityError` is raised.  Home
            Assistant will mark entities as unavailable until the next
            successful poll.
        """
        try:
            account_info = await self._backend.async_get_all_device_data()
            self.last_error_category = None
            return dict(account_info.devices)
        except (AuthenticationError, ReauthenticationRequired) as err:
            self.last_error_category = CoordinatorErrorCategory.AUTHENTICATION
            raise ConfigEntryAuthFailed(str(err)) from err
        except ConnectivityError as err:
            self.last_error_category = CoordinatorErrorCategory.CONNECTIVITY
            raise UpdateFailed(str(err)) from err
        except RateLimitError as err:
            self.last_error_category = CoordinatorErrorCategory.RATE_LIMIT
            raise UpdateFailed("EcoWater rate limit reached") from err
        except ProtocolError as err:
            self.last_error_category = CoordinatorErrorCategory.PROTOCOL
            raise UpdateFailed("Unexpected EcoWater response") from err
