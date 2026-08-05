"""Binary sensor platform for the EcoWater Cloud integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EcoWaterCloudConfigEntry
from .coordinator import AccountCoordinator
from .entity import EcoWaterEntity
from .models import EcoWaterDeviceData


@dataclass(frozen=True, kw_only=True)
class EcoWaterBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an EcoWater binary sensor entity."""

    is_on_fn: Callable[[EcoWaterDeviceData], bool | None]
    supported_fn: Callable[[EcoWaterDeviceData], bool] = lambda _: True


BINARY_SENSORS: tuple[EcoWaterBinarySensorEntityDescription, ...] = (
    EcoWaterBinarySensorEntityDescription(
        key="device_reported_online",
        translation_key="device_reported_online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        supported_fn=lambda d: d.descriptor.is_online is not None,
        is_on_fn=lambda d: d.descriptor.is_online,
    ),
    EcoWaterBinarySensorEntityDescription(
        key="regenerating",
        translation_key="regenerating",
        device_class=BinarySensorDeviceClass.RUNNING,
        supported_fn=lambda d: d.regeneration.status is not None,
        is_on_fn=lambda d: bool(
            d.regeneration.status and d.regeneration.status.lower() == "regenerating"
        ),
    ),
    EcoWaterBinarySensorEntityDescription(
        key="recharge_enabled",
        translation_key="recharge_enabled",
        # no specific device class, standard boolean state
        supported_fn=lambda d: d.regeneration.is_enabled is not None,
        is_on_fn=lambda d: d.regeneration.is_enabled,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcoWaterCloudConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EcoWater binary sensor platform."""
    coordinator = entry.runtime_data.coordinator

    added_entities: set[tuple[str, str]] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add binary sensors for new devices discovered."""
        new_entities: list[EcoWaterBinarySensor] = []
        for serial_number, device_data in coordinator.data.items():
            for description in BINARY_SENSORS:
                entity_key = (serial_number, description.key)
                if entity_key not in added_entities and description.supported_fn(
                    device_data
                ):
                    added_entities.add(entity_key)
                    new_entities.append(
                        EcoWaterBinarySensor(coordinator, serial_number, description)
                    )
        if new_entities:
            async_add_entities(new_entities)

    # Initial addition
    _async_add_new_devices()

    # Register listener for future discovery
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))


class EcoWaterBinarySensor(EcoWaterEntity, BinarySensorEntity):
    """A generic EcoWater binary sensor entity."""

    entity_description: EcoWaterBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AccountCoordinator,
        serial_number: str,
        description: EcoWaterBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, serial_number)
        self.entity_description = description

        # Calculate unique id based on the backend and serial
        data = coordinator.data.get(serial_number)
        backend = data.descriptor.backend if data else "ayla"
        self._attr_unique_id = f"{backend}_{serial_number}_{description.key}".lower()

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        if not self.device_data:
            return None
        return self.entity_description.is_on_fn(self.device_data)
