"""Sensor platform for the EcoWater Cloud integration."""

from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EcoWaterCloudConfigEntry
from .coordinator import AccountCoordinator
from .entity import EcoWaterEntity
from .models import EcoWaterDeviceData


@dataclass(frozen=True, kw_only=True)
class EcoWaterSensorEntityDescription(SensorEntityDescription):
    """Describes an EcoWater sensor entity."""

    value_fn: Callable[
        [EcoWaterDeviceData],
        float | int | str | datetime.date | datetime.datetime | None,
    ]
    supported_fn: Callable[[EcoWaterDeviceData], bool] = lambda _: True


SENSORS: tuple[EcoWaterSensorEntityDescription, ...] = (
    # --- Water Usage ---
    EcoWaterSensorEntityDescription(
        key="water_used_today",
        translation_key="water_used_today",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_water_usage_today,
        value_fn=lambda d: d.water_used_today_gallons,
    ),
    EcoWaterSensorEntityDescription(
        key="average_daily_water_use",
        translation_key="average_daily_water_use",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        supported_fn=lambda d: d.capabilities.has_water_usage_daily_avg,
        value_fn=lambda d: d.water_used_daily_avg_gallons,
    ),
    EcoWaterSensorEntityDescription(
        key="treated_water_available",
        translation_key="treated_water_available",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        supported_fn=lambda d: d.capabilities.has_water_available,
        value_fn=lambda d: d.water_available_gallons,
    ),
    EcoWaterSensorEntityDescription(
        key="total_water_used",
        translation_key="total_water_used",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_total_water_used,
        value_fn=lambda d: d.total_water_used_gallons,
    ),
    EcoWaterSensorEntityDescription(
        key="current_water_flow",
        translation_key="current_water_flow",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement="gal/min",
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_flow_sensor,
        value_fn=lambda d: d.current_flow_gpm,
    ),
    EcoWaterSensorEntityDescription(
        key="peak_water_flow",
        translation_key="peak_water_flow",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement="gal/min",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        supported_fn=lambda d: d.capabilities.has_peak_flow,
        value_fn=lambda d: d.peak_water_flow_gpm,
    ),
    # --- Salt & Rock ---
    EcoWaterSensorEntityDescription(
        key="salt_level",
        translation_key="salt_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_salt_level_percentage,
        value_fn=lambda d: d.salt_level_percent,
    ),
    EcoWaterSensorEntityDescription(
        key="capacity_remaining",
        translation_key="capacity_remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_capacity_remaining,
        value_fn=lambda d: d.capacity_remaining_percent,
    ),
    EcoWaterSensorEntityDescription(
        key="total_salt_used",
        translation_key="total_salt_used",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_total_salt_used,
        value_fn=lambda d: d.total_salt_used_lbs,
    ),
    EcoWaterSensorEntityDescription(
        key="days_until_out_of_salt",
        translation_key="days_until_out_of_salt",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_out_of_salt_estimate,
        value_fn=lambda d: d.days_until_out_of_salt,
    ),
    EcoWaterSensorEntityDescription(
        key="estimated_out_of_salt_date",
        translation_key="estimated_out_of_salt_date",
        device_class=SensorDeviceClass.DATE,
        supported_fn=lambda d: d.capabilities.has_out_of_salt_estimate,
        value_fn=lambda d: d.estimated_out_of_salt_date,
    ),
    EcoWaterSensorEntityDescription(
        key="salt_type",
        translation_key="salt_type",
        device_class=SensorDeviceClass.ENUM,
        supported_fn=lambda d: d.capabilities.has_salt_type,
        value_fn=lambda d: (
            d.salt_type.lower().replace(" ", "_") if d.salt_type else None
        ),
        options=["sodium_chloride", "potassium_chloride"],
    ),
    # --- Regeneration ---
    EcoWaterSensorEntityDescription(
        key="regeneration_status",
        translation_key="regeneration_status",
        device_class=SensorDeviceClass.ENUM,
        options=["standby", "regenerating", "scheduled"],
        supported_fn=lambda d: d.capabilities.has_regeneration_status,
        value_fn=lambda d: (
            d.regeneration.status.lower() if d.regeneration.status else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="regeneration_time_remaining",
        translation_key="regeneration_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_regen_time_remaining,
        value_fn=lambda d: d.regen_time_rem_secs,
    ),
    EcoWaterSensorEntityDescription(
        key="current_valve_position",
        translation_key="current_valve_position",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "service",
            "fill",
            "brine_slow_rinse",
            "backwash",
            "fast_rinse",
        ],
        supported_fn=lambda d: d.capabilities.has_valve_position,
        value_fn=lambda d: (
            d.current_valve_position.lower() if d.current_valve_position else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="average_days_between_regenerations",
        translation_key="average_days_between_regenerations",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_avg_days_between_regens,
        value_fn=lambda d: d.avg_days_between_regens,
    ),
    EcoWaterSensorEntityDescription(
        key="average_salt_per_regeneration",
        translation_key="average_salt_per_regeneration",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_avg_salt_per_regen,
        value_fn=lambda d: d.avg_salt_per_regen_lbs,
    ),
    EcoWaterSensorEntityDescription(
        key="monthly_salt_use_estimate",
        translation_key="monthly_salt_use_estimate",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        supported_fn=lambda d: (
            d.capabilities.has_avg_salt_per_regen
            and d.capabilities.has_avg_days_between_regens
            and d.avg_days_between_regens is not None
            and d.avg_days_between_regens > 0
            and d.avg_salt_per_regen_lbs is not None
        ),
        value_fn=lambda d: (
            (d.avg_salt_per_regen_lbs / d.avg_days_between_regens) * 30.4375
            if (
                d.avg_salt_per_regen_lbs is not None
                and d.avg_days_between_regens is not None
                and d.avg_days_between_regens > 0
            )
            else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="total_regenerations",
        translation_key="total_regenerations",
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_total_regens,
        value_fn=lambda d: d.total_regens,
    ),
    EcoWaterSensorEntityDescription(
        key="days_since_last_regeneration",
        translation_key="days_since_last_regeneration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        supported_fn=lambda d: d.capabilities.has_days_since_regeneration,
        value_fn=lambda d: d.regeneration.days_since_last,
    ),
    EcoWaterSensorEntityDescription(
        key="estimated_last_regeneration_date",
        translation_key="estimated_last_regeneration_date",
        device_class=SensorDeviceClass.DATE,
        supported_fn=lambda d: d.capabilities.has_days_since_regeneration,
        value_fn=lambda d: d.regeneration.estimated_last_date,
    ),
    EcoWaterSensorEntityDescription(
        key="rock_removed_since_regeneration",
        translation_key="rock_removed_since_regeneration",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=4,
        supported_fn=lambda d: d.capabilities.has_rock_removed_since_regeneration,
        value_fn=lambda d: d.rock_removed_since_regeneration_lbs,
    ),
    EcoWaterSensorEntityDescription(
        key="total_rock_removed",
        translation_key="total_rock_removed",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
        supported_fn=lambda d: d.capabilities.has_total_rock_removed,
        value_fn=lambda d: d.total_rock_removed_lbs,
    ),
    EcoWaterSensorEntityDescription(
        key="average_rock_removal",
        translation_key="average_rock_removal",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        supported_fn=lambda d: d.capabilities.has_rock_removed_daily_avg,
        value_fn=lambda d: d.rock_removed_daily_avg_lbs,
    ),
    EcoWaterSensorEntityDescription(
        key="total_untreated_water",
        translation_key="total_untreated_water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_total_untreated_water_gals,
        value_fn=lambda d: d.total_untreated_water_gals,
    ),
    EcoWaterSensorEntityDescription(
        key="average_exhaustion",
        translation_key="average_exhaustion",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_average_exhaustion_percent,
        value_fn=lambda d: d.average_exhaustion_percent,
    ),
    EcoWaterSensorEntityDescription(
        key="salt_efficiency_mode_raw",
        translation_key="salt_efficiency_mode_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_efficiency_mode_enum,
        value_fn=lambda d: (
            str(d.efficiency_mode_enum) if d.efficiency_mode_enum is not None else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="operating_capacity_raw",
        translation_key="operating_capacity_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_operating_capacity_grains,
        value_fn=lambda d: d.operating_capacity_grains,
    ),
    EcoWaterSensorEntityDescription(
        key="hardness_setting_raw",
        translation_key="hardness_setting_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_hardness_grains,
        value_fn=lambda d: d.hardness_grains,
    ),
    EcoWaterSensorEntityDescription(
        key="iron_setting_raw",
        translation_key="iron_setting_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_iron_level_tenths_ppm,
        value_fn=lambda d: d.iron_level_tenths_ppm,
    ),
    EcoWaterSensorEntityDescription(
        key="flow_monitor_minimum_rate",
        translation_key="flow_monitor_minimum_rate",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement="gal/min",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_flow_monitor_min_rate_gpm,
        value_fn=lambda d: d.flow_monitor_min_rate_gpm,
    ),
    EcoWaterSensorEntityDescription(
        key="excessive_flow_trip_duration",
        translation_key="excessive_flow_trip_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_flow_monitor_trip_sec,
        value_fn=lambda d: d.flow_monitor_trip_sec,
    ),
    # --- Diagnostics ---
    EcoWaterSensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        supported_fn=lambda d: d.capabilities.has_error_code,
        value_fn=lambda d: d.error_code,
    ),
    EcoWaterSensorEntityDescription(
        key="integration_last_successful_update",
        translation_key="integration_last_successful_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.freshness.received_at,
    ),
    EcoWaterSensorEntityDescription(
        key="source_last_updated",
        translation_key="source_last_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.freshness.telemetry_newest_data_at,
    ),
    EcoWaterSensorEntityDescription(
        key="source_oldest_data",
        translation_key="source_oldest_data",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.freshness.oldest_data_at,
    ),
    EcoWaterSensorEntityDescription(
        key="source_data_age",
        translation_key="source_data_age",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (
            d.freshness.age.total_seconds() / 3600
            if d.freshness.age is not None
            else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="wifi_signal_strength",
        translation_key="wifi_signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.descriptor.wifi_signal_strength_dbm,
    ),
    # --- Unknown-model diagnostics ---
    # Disabled by default, gated on has_unmapped_salt_model
    EcoWaterSensorEntityDescription(
        key="raw_salt_level",
        translation_key="raw_salt_level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_unmapped_salt_model,
        value_fn=lambda d: d.salt_level_raw,
    ),
    EcoWaterSensorEntityDescription(
        key="model_id",
        translation_key="model_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_unmapped_salt_model,
        value_fn=lambda d: d.descriptor.model_id,
    ),
    EcoWaterSensorEntityDescription(
        key="oem_model",
        translation_key="oem_model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_unmapped_salt_model,
        value_fn=lambda d: d.descriptor.oem_model,
    ),
    EcoWaterSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_unmapped_salt_model,
        value_fn=lambda d: d.descriptor.firmware_version,
    ),
    EcoWaterSensorEntityDescription(
        key="total_water_source_property",
        translation_key="total_water_source_property",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_unmapped_salt_model,
        value_fn=lambda d: d.total_water_source_property,
    ),
    EcoWaterSensorEntityDescription(
        key="power_outage_count",
        translation_key="power_outage_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_power_outage_count,
        value_fn=lambda d: d.power_outage_count,
    ),
    EcoWaterSensorEntityDescription(
        key="time_lost_event_count",
        translation_key="time_lost_event_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_time_lost_events,
        value_fn=lambda d: d.time_lost_events,
    ),
    EcoWaterSensorEntityDescription(
        key="longest_recent_outage",
        translation_key="longest_recent_outage",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_longest_rec_outage_mins,
        value_fn=lambda d: d.longest_rec_outage_mins,
    ),
    EcoWaterSensorEntityDescription(
        key="valve_reindex_count",
        translation_key="valve_reindex_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_valve_reindex_count,
        value_fn=lambda d: d.valve_reindex_count,
    ),
    EcoWaterSensorEntityDescription(
        key="motor_state_raw",
        translation_key="motor_state_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_valve_motor_state_enum,
        value_fn=lambda d: (
            str(d.valve_motor_state_enum)
            if d.valve_motor_state_enum is not None
            else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="valve_position_switch_state_raw",
        translation_key="valve_position_switch_state_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_valve_pos_switch_enum,
        value_fn=lambda d: (
            str(d.valve_pos_switch_enum)
            if d.valve_pos_switch_enum is not None
            else None
        ),
    ),
    EcoWaterSensorEntityDescription(
        key="remaining_valve_position_time",
        translation_key="remaining_valve_position_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_valve_pos_time_left_secs,
        value_fn=lambda d: d.valve_pos_time_left_secs,
    ),
    EcoWaterSensorEntityDescription(
        key="days_in_operation",
        translation_key="days_in_operation",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_days_in_operation,
        value_fn=lambda d: d.days_in_operation,
    ),
    EcoWaterSensorEntityDescription(
        key="manual_regeneration_count",
        translation_key="manual_regeneration_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported_fn=lambda d: d.capabilities.has_manual_regens,
        value_fn=lambda d: d.manual_regens,
    ),
    EcoWaterSensorEntityDescription(
        key="fill_duration",
        translation_key="fill_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_fill_secs,
        value_fn=lambda d: d.fill_secs,
    ),
    EcoWaterSensorEntityDescription(
        key="backwash_duration",
        translation_key="backwash_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_backwash_secs,
        value_fn=lambda d: d.backwash_secs,
    ),
    EcoWaterSensorEntityDescription(
        key="rinse_duration",
        translation_key="rinse_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_fast_rinse_secs,
        value_fn=lambda d: d.fast_rinse_secs,
    ),
    EcoWaterSensorEntityDescription(
        key="second_backwash_cycles_raw",
        translation_key="second_backwash_cycles_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_second_backwash_cycles,
        value_fn=lambda d: d.second_backwash_cycles,
    ),
    EcoWaterSensorEntityDescription(
        key="second_backwash_duration",
        translation_key="second_backwash_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        supported_fn=lambda d: d.capabilities.has_second_backwash_secs,
        value_fn=lambda d: d.second_backwash_secs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcoWaterCloudConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EcoWater sensor platform."""
    coordinator = entry.runtime_data.coordinator

    added_entities: set[tuple[str, str]] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add sensors for new devices discovered."""
        new_entities: list[EcoWaterSensor] = []
        for serial_number, device_data in coordinator.data.items():
            for description in SENSORS:
                entity_key = (serial_number, description.key)
                if entity_key not in added_entities and description.supported_fn(
                    device_data
                ):
                    added_entities.add(entity_key)
                    new_entities.append(
                        EcoWaterSensor(coordinator, serial_number, description)
                    )
        if new_entities:
            async_add_entities(new_entities)

    # Initial addition
    _async_add_new_devices()

    # Register listener for future discovery
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))


class EcoWaterSensor(EcoWaterEntity, SensorEntity):
    """A generic EcoWater sensor entity."""

    entity_description: EcoWaterSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AccountCoordinator,
        serial_number: str,
        description: EcoWaterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, serial_number)
        self.entity_description = description

        # Calculate unique id based on the backend and serial
        data = coordinator.data.get(serial_number)
        backend = data.descriptor.backend if data else "ayla"
        self._attr_unique_id = f"{backend}_{serial_number}_{description.key}".lower()

    @property
    def native_value(
        self,
    ) -> float | int | str | datetime.date | datetime.datetime | None:
        """Return the native value of the sensor."""
        if not self.device_data:
            return None
        return self.entity_description.value_fn(self.device_data)
