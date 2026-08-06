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
        "has_salt_sensor": data.capabilities.has_salt_sensor,
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
