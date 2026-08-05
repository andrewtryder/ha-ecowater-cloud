"""HydroLink backend implementation."""

from __future__ import annotations

import logging

from aiohttp import ClientSession

from ..models import AccountInfo, DeviceDescriptor, EcoWaterDeviceData
from . import BackendAdapter

_LOGGER = logging.getLogger(__name__)


class HydroLinkBackend(BackendAdapter):
    """Adapter for the future HydroLink Home backend."""

    def __init__(
        self, session: ClientSession, username: str, password: str, region: str
    ) -> None:
        """Initialize the HydroLink backend.

        Args:
            session: The aiohttp ClientSession to use.
            username: The account username.
            password: The account password.
            region: The region (e.g. 'us', 'eu').
        """
        self._session = session
        self._username = username
        self._password = password
        self._region = region

    async def async_authenticate(self) -> None:
        """Authenticate with the HydroLink backend."""
        raise NotImplementedError(
            "HydroLink protocol details missing: require sanitized fixtures to implement. "
            "Missing evidence for token structure and authentication endpoints."
        )

    async def async_clear_authentication(self) -> None:
        """Clear cached authentication tokens."""
        raise NotImplementedError(
            "HydroLink protocol details missing: require sanitized fixtures to implement."
        )

    async def async_list_devices(self) -> list[DeviceDescriptor]:
        """List all supported devices on the account."""
        raise NotImplementedError(
            "HydroLink protocol details missing: require sanitized fixtures to implement. "
            "Missing evidence for multi-device payloads."
        )

    async def async_get_device_data(self, serial_number: str) -> EcoWaterDeviceData:
        """Fetch all telemetry for a specific device."""
        raise NotImplementedError(
            "HydroLink protocol details missing: require sanitized fixtures to implement. "
            "Missing evidence for the wake sequence endpoints, UUID extraction, and payload."
        )

    async def async_get_all_device_data(self) -> AccountInfo:
        """Fetch all supported devices and their current telemetry."""
        raise NotImplementedError(
            "HydroLink protocol details missing: require sanitized fixtures to implement. "
            "Missing evidence for mapping raw HydroLink data to AccountInfo."
        )
