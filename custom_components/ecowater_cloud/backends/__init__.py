"""Backend adapter protocol for the EcoWater Cloud integration.

Each cloud backend (Ayla, HydroLink, …) must implement :class:`BackendAdapter`.
The coordinator interacts exclusively with this protocol; it has no knowledge
of any specific cloud's HTTP API.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from custom_components.ecowater_cloud.models import (
    AccountInfo,
    DeviceDescriptor,
    EcoWaterDeviceData,
)


@runtime_checkable
class BackendAdapter(Protocol):
    """Async protocol that all backend adapters must satisfy.

    All methods are async. Implementations must:
    - Map all HTTP/cloud errors to the integration's exception taxonomy.
    - Never log credentials, tokens, or cookies.
    """

    async def async_authenticate(self) -> None:
        """Authenticate with the cloud backend and store session credentials."""
        ...

    async def async_clear_authentication(self) -> None:
        """Clear session credentials (e.g. sign out)."""
        ...

    async def async_list_devices(self) -> list[DeviceDescriptor]:
        """Fetch basic descriptors for all supported devices."""
        ...

    async def async_get_device_data(self, serial_number: str) -> EcoWaterDeviceData:
        """Fetch all telemetry for a specific device."""
        ...

    async def async_get_all_device_data(self) -> AccountInfo:
        """Fetch all supported devices and their current telemetry.

        Returns
        -------
        AccountInfo
            Contains mapping of ``serial_number → EcoWaterDeviceData``.
        """
        ...
