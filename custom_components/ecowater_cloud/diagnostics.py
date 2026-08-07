"""Diagnostics support for EcoWater Cloud."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import EcoWaterCloudConfigEntry
from .const import CONF_BACKEND
from .models import EcoWaterDeviceData

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    "unique_id",
    "serial_number",
    "backend_id",
    "mac",
    "lan_ip",
}


def _redact_device_data(data: EcoWaterDeviceData) -> dict[str, Any]:
    """Redact sensitive fields from a device snapshot."""
    descriptor_dict = {
        "backend": data.descriptor.backend,
        "backend_id": "***REDACTED***",
        "serial_number": "***REDACTED***",
        "name": "***REDACTED***",
        "model": data.descriptor.model,
        "oem_model": data.descriptor.oem_model,
        "model_id": data.descriptor.model_id,
        "firmware_version": data.descriptor.firmware_version,
        "is_online": data.descriptor.is_online,
        "wifi_signal_strength_dbm": data.descriptor.wifi_signal_strength_dbm,
    }

    # Include capabilities and freshness for debugging polling issues
    capabilities_dict = {
        "has_water_usage_today": data.capabilities.has_water_usage_today,
        "has_water_usage_daily_avg": data.capabilities.has_water_usage_daily_avg,
        "has_water_available": data.capabilities.has_water_available,
        "has_total_water_used": data.capabilities.has_total_water_used,
        "has_flow_sensor": data.capabilities.has_flow_sensor,
        "has_salt_level": data.capabilities.has_salt_level,
        "has_salt_level_percentage": data.capabilities.has_salt_level_percentage,
        "has_out_of_salt_estimate": data.capabilities.has_out_of_salt_estimate,
        "has_salt_type": data.capabilities.has_salt_type,
        "has_regeneration_status": data.capabilities.has_regeneration_status,
        "has_days_since_regeneration": data.capabilities.has_days_since_regeneration,
        "has_rock_removed_daily_avg": data.capabilities.has_rock_removed_daily_avg,
        "has_rock_removed_since_regeneration": (
            data.capabilities.has_rock_removed_since_regeneration
        ),
        "has_total_rock_removed": data.capabilities.has_total_rock_removed,
        "has_peak_flow": data.capabilities.has_peak_flow,
        "has_capacity_remaining": data.capabilities.has_capacity_remaining,
        "has_regen_time_remaining": data.capabilities.has_regen_time_remaining,
        "has_valve_position": data.capabilities.has_valve_position,
        "has_avg_days_between_regens": data.capabilities.has_avg_days_between_regens,
        "has_avg_salt_per_regen": data.capabilities.has_avg_salt_per_regen,
        "has_total_regens": data.capabilities.has_total_regens,
        "has_total_salt_used": data.capabilities.has_total_salt_used,
        "has_low_salt_alert": data.capabilities.has_low_salt_alert,
        "has_depletion_alert": data.capabilities.has_depletion_alert,
        "has_excessive_water_use_alert": (
            data.capabilities.has_excessive_water_use_alert
        ),
        "has_flow_monitor_alert": data.capabilities.has_flow_monitor_alert,
        "has_service_reminder_alert": data.capabilities.has_service_reminder_alert,
        "has_error_code_alert": data.capabilities.has_error_code_alert,
        "has_error_code": data.capabilities.has_error_code,
        "has_unmapped_salt_model": data.capabilities.has_unmapped_salt_model,
        "total_water_source_property": data.total_water_source_property,
        "has_power_outage_count": getattr(
            data.capabilities, "has_power_outage_count", None
        ),
        "has_time_lost_events": getattr(
            data.capabilities, "has_time_lost_events", None
        ),
        "has_longest_rec_outage_mins": getattr(
            data.capabilities, "has_longest_rec_outage_mins", None
        ),
        "has_valve_reindex_count": getattr(
            data.capabilities, "has_valve_reindex_count", None
        ),
        "has_valve_motor_state_enum": getattr(
            data.capabilities, "has_valve_motor_state_enum", None
        ),
        "has_valve_pos_switch_enum": getattr(
            data.capabilities, "has_valve_pos_switch_enum", None
        ),
        "has_valve_pos_time_left_secs": getattr(
            data.capabilities, "has_valve_pos_time_left_secs", None
        ),
        "has_days_in_operation": getattr(
            data.capabilities, "has_days_in_operation", None
        ),
        "has_total_untreated_water_gals": getattr(
            data.capabilities, "has_total_untreated_water_gals", None
        ),
        "has_average_exhaustion_percent": getattr(
            data.capabilities, "has_average_exhaustion_percent", None
        ),
        "has_efficiency_mode_enum": getattr(
            data.capabilities, "has_efficiency_mode_enum", None
        ),
        "has_operating_capacity_grains": getattr(
            data.capabilities, "has_operating_capacity_grains", None
        ),
        "has_hardness_grains": getattr(data.capabilities, "has_hardness_grains", None),
        "has_iron_level_tenths_ppm": getattr(
            data.capabilities, "has_iron_level_tenths_ppm", None
        ),
        "has_flow_monitor_min_rate_gpm": getattr(
            data.capabilities, "has_flow_monitor_min_rate_gpm", None
        ),
        "has_flow_monitor_trip_sec": getattr(
            data.capabilities, "has_flow_monitor_trip_sec", None
        ),
        "has_manual_regens": getattr(data.capabilities, "has_manual_regens", None),
        "has_fill_secs": getattr(data.capabilities, "has_fill_secs", None),
        "has_backwash_secs": getattr(data.capabilities, "has_backwash_secs", None),
        "has_fast_rinse_secs": getattr(data.capabilities, "has_fast_rinse_secs", None),
        "has_second_backwash_cycles": getattr(
            data.capabilities, "has_second_backwash_cycles", None
        ),
        "has_second_backwash_secs": getattr(
            data.capabilities, "has_second_backwash_secs", None
        ),
    }

    import datetime

    freshness_dict: dict[str, Any] = {
        "received_at": data.freshness.received_at.isoformat()
        if data.freshness.received_at
        else None,
        "oldest_data_at": data.freshness.oldest_data_at.isoformat()
        if data.freshness.oldest_data_at
        else None,
        "newest_data_at": data.freshness.newest_data_at.isoformat()
        if data.freshness.newest_data_at
        else None,
    }

    if data.freshness.newest_data_at:
        freshness_dict["source_data_age_seconds"] = int(
            (
                datetime.datetime.now(datetime.UTC) - data.freshness.newest_data_at
            ).total_seconds()
        )
    else:
        freshness_dict["source_data_age_seconds"] = "unavailable_from_source"

    regeneration_dict = {
        "status": data.regeneration.status,
        "is_enabled": data.regeneration.is_enabled,
        "days_since_last": data.regeneration.days_since_last,
        "estimated_last_date": data.regeneration.estimated_last_date.isoformat()
        if data.regeneration.estimated_last_date
        else None,
    }

    return {
        "descriptor": descriptor_dict,
        "capabilities": capabilities_dict,
        "freshness": freshness_dict,
        "regeneration": regeneration_dict,
        "water_used_today_gallons": data.water_used_today_gallons,
        "water_used_daily_avg_gallons": data.water_used_daily_avg_gallons,
        "water_available_gallons": data.water_available_gallons,
        "total_water_used_gallons": data.total_water_used_gallons,
        "current_flow_gpm": data.current_flow_gpm,
        "salt_level_raw": data.salt_level_raw,
        "salt_level_percent": data.salt_level_percent,
        "days_until_out_of_salt": data.days_until_out_of_salt,
        "estimated_out_of_salt_date": data.estimated_out_of_salt_date.isoformat()
        if data.estimated_out_of_salt_date
        else None,
        "salt_type": data.salt_type,
        "rock_removed_since_regeneration_lbs": data.rock_removed_since_regeneration_lbs,
        "total_rock_removed_lbs": data.total_rock_removed_lbs,
        "rock_removed_daily_avg_lbs": data.rock_removed_daily_avg_lbs,
        "peak_water_flow_gpm": data.peak_water_flow_gpm,
        "capacity_remaining_percent": data.capacity_remaining_percent,
        "regen_time_rem_secs": data.regen_time_rem_secs,
        "current_valve_position": data.current_valve_position,
        "avg_days_between_regens": data.avg_days_between_regens,
        "avg_salt_per_regen_lbs": data.avg_salt_per_regen_lbs,
        "total_regens": data.total_regens,
        "total_salt_used_lbs": data.total_salt_used_lbs,
        "error_code": data.error_code,
        "low_salt_alert": data.low_salt_alert,
        "depletion_alert": data.depletion_alert,
        "excessive_water_use_alert": data.excessive_water_use_alert,
        "flow_monitor_alert": data.flow_monitor_alert,
        "service_reminder_alert": data.service_reminder_alert,
        "error_code_alert": data.error_code_alert,
        "power_outage_count": getattr(data, "power_outage_count", None),
        "time_lost_events": getattr(data, "time_lost_events", None),
        "longest_rec_outage_mins": getattr(data, "longest_rec_outage_mins", None),
        "valve_reindex_count": getattr(data, "valve_reindex_count", None),
        "valve_motor_state_enum": getattr(data, "valve_motor_state_enum", None),
        "valve_pos_switch_enum": getattr(data, "valve_pos_switch_enum", None),
        "valve_pos_time_left_secs": getattr(data, "valve_pos_time_left_secs", None),
        "days_in_operation": getattr(data, "days_in_operation", None),
        "total_untreated_water_gals": getattr(data, "total_untreated_water_gals", None),
        "average_exhaustion_percent": getattr(data, "average_exhaustion_percent", None),
        "efficiency_mode_enum": getattr(data, "efficiency_mode_enum", None),
        "operating_capacity_grains": getattr(data, "operating_capacity_grains", None),
        "hardness_grains": getattr(data, "hardness_grains", None),
        "iron_level_tenths_ppm": getattr(data, "iron_level_tenths_ppm", None),
        "flow_monitor_min_rate_gpm": getattr(data, "flow_monitor_min_rate_gpm", None),
        "flow_monitor_trip_sec": getattr(data, "flow_monitor_trip_sec", None),
        "manual_regens": getattr(data, "manual_regens", None),
        "fill_secs": getattr(data, "fill_secs", None),
        "backwash_secs": getattr(data, "backwash_secs", None),
        "fast_rinse_secs": getattr(data, "fast_rinse_secs", None),
        "second_backwash_cycles": getattr(data, "second_backwash_cycles", None),
        "second_backwash_secs": getattr(data, "second_backwash_secs", None),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EcoWaterCloudConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    backend_id = entry.data.get(CONF_BACKEND, "ayla")

    devices = {}
    for index, device_data in enumerate(coordinator.data.values(), start=1):
        devices[f"device_{index}"] = _redact_device_data(device_data)

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "backend": backend_id,
        "polling_interval": str(coordinator.update_interval),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": type(coordinator.last_exception).__name__
            if coordinator.last_exception
            else None,
            "devices_count": len(devices),
            "devices": devices,
        },
    }
