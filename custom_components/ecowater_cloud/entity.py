"""Base entity for the EcoWater Cloud integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AccountCoordinator
from .models import EcoWaterDeviceData


class EcoWaterEntity(CoordinatorEntity[AccountCoordinator]):
    """Base class for all EcoWater entities.

    Attributes
    ----------
    coordinator : AccountCoordinator
        The account coordinator managing updates for all devices on this account.
    serial_number : str
        The unique serial number of the physical device this entity belongs to.
    """

    def __init__(
        self,
        coordinator: AccountCoordinator,
        serial_number: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.serial_number = serial_number

    @property
    def device_data(self) -> EcoWaterDeviceData | None:
        """Get the current telemetry for this device, if any."""
        return self.coordinator.data.get(self.serial_number)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the device registry.

        The first time this is evaluated, the device data must be present.
        """
        data = self.device_data
        if not data:
            # Fallback if somehow called when data is entirely missing.
            return DeviceInfo(
                identifiers={(DOMAIN, f"ayla:{self.serial_number}")},
            )

        descriptor = data.descriptor
        return DeviceInfo(
            identifiers={(DOMAIN, f"{descriptor.backend}:{descriptor.serial_number}")},
            name=descriptor.name,
            manufacturer="EcoWater",
            model=descriptor.model,
            sw_version=descriptor.firmware_version,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Consider available if coordinator poll succeeded AND we have data for this serial.
        return super().available and self.device_data is not None
