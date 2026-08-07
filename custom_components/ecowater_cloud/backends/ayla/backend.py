"""Ayla IoT Platform backend adapter."""

import datetime
import logging
from typing import TYPE_CHECKING, cast

from custom_components.ecowater_cloud.backends import BackendAdapter
from custom_components.ecowater_cloud.exceptions import UnsupportedDeviceError
from custom_components.ecowater_cloud.models import (
    AccountInfo,
    DeviceDescriptor,
    EcoWaterDeviceData,
)

from .api import AylaApi
from .models import AylaDeviceData, AylaPropertyData
from .normalization import normalize_device

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)


class AylaBackend(BackendAdapter):
    """Async client for the Ayla IoT Platform."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        region: str = "us",
    ) -> None:
        self._username = username
        self._password = password
        self._api = AylaApi(session, region=region)

    async def async_authenticate(self) -> None:
        """Authenticate with the Ayla user service."""
        await self._api.async_authenticate(self._username, self._password)

    async def async_clear_authentication(self) -> None:
        """Clear the current Ayla session."""
        await self._api.async_clear_authentication()

    async def async_list_devices(self) -> list[DeviceDescriptor]:
        """Fetch basic descriptors for supported EcoWater devices only.

        Only devices whose OEM model starts with ``EWS`` are considered
        supported. Unsupported models are silently skipped, matching the
        behaviour of :meth:`async_get_all_device_data`.
        """
        raw_devices = await self._api.async_list_devices()
        descriptors = []
        for dev in raw_devices:
            oem_model = dev.get("oem_model", "")
            if not oem_model.startswith("EWS"):
                _LOGGER.debug(
                    "async_list_devices: skipping unsupported model '%s'", oem_model
                )
                continue
            descriptors.append(
                DeviceDescriptor(
                    backend="ayla",
                    backend_id=dev.get("dsn", ""),
                    serial_number=dev.get("dsn", ""),
                    name=dev.get("product_name", "EcoWater Device"),
                    model=oem_model,
                    is_online=(dev.get("connection_status") == "Online")
                    if "connection_status" in dev
                    else None,
                )
            )
        return descriptors

    async def async_get_device_data(self, serial_number: str) -> EcoWaterDeviceData:
        """Fetch all telemetry for a specific device.

        Note: The Ayla backend requires the basic device metadata (model, name)
        which is only returned in the list_devices endpoint. To satisfy getting
        a single device robustly, we first list devices to get the metadata,
        then fetch properties.
        """
        raw_devices = await self._api.async_list_devices()
        target_dev = None
        for dev in raw_devices:
            if dev.get("dsn") == serial_number:
                target_dev = dev
                break

        if not target_dev:
            # Note: Ayla api handles unknown devices by 404, but here we can't
            # find the metadata. We construct a synthetic minimal metadata if not found
            target_dev = {"dsn": serial_number}

        raw_props = await self._api.async_get_device_properties(serial_number)

        # Unwrap the property wrappers
        unwrapped_props: list[AylaPropertyData] = [
            cast(AylaPropertyData, p) for p in raw_props
        ]

        received_at = datetime.datetime.now(datetime.UTC)
        return normalize_device(
            cast(AylaDeviceData, target_dev), unwrapped_props, received_at
        )

    async def async_get_all_device_data(self) -> AccountInfo:
        """Fetch all supported devices and their current telemetry."""
        raw_devices = await self._api.async_list_devices()

        devices_data = {}
        received_at = datetime.datetime.now(datetime.UTC)

        for d in raw_devices:
            dev = cast(AylaDeviceData, d)
            dsn = dev.get("dsn")
            if not dsn:
                continue

            # Filter for EcoWater devices only, as per reference repo logic
            oem_model = dev.get("oem_model", "")
            if not oem_model.startswith("EWS"):
                _LOGGER.warning("Ignoring unsupported device model: %s", oem_model)
                continue

            try:
                raw_props = await self._api.async_get_device_properties(dsn)
                unwrapped_props: list[AylaPropertyData] = [
                    cast(AylaPropertyData, p) for p in raw_props
                ]
                devices_data[dsn] = normalize_device(dev, unwrapped_props, received_at)
            except UnsupportedDeviceError as err:
                redacted_dsn = f"{dsn[:3]}...{dsn[-3:]}" if len(dsn) > 6 else "***"
                _LOGGER.warning("Skipping unsupported device %s: %s", redacted_dsn, err)

        return AccountInfo(devices=devices_data)
