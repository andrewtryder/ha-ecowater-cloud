"""Shared pytest fixtures for ha-ecowater-cloud tests."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.ecowater_cloud.const import (
    BACKEND_AYLA,
    CONF_BACKEND,
)
from custom_components.ecowater_cloud.models import (
    AccountInfo,
    DataFreshness,
    DeviceCapabilities,
    DeviceDescriptor,
    EcoWaterDeviceData,
    RegenerationState,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

MOCK_USERNAME = "user@example.com"
MOCK_PASSWORD = "test-password-not-real"
MOCK_SERIAL = "ABC123456789"

MOCK_ENTRY_DATA = {
    CONF_BACKEND: BACKEND_AYLA,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
}


def make_full_device_snapshot() -> EcoWaterDeviceData:
    """Build a fully-populated :class:`EcoWaterDeviceData` for testing."""
    return EcoWaterDeviceData(
        descriptor=DeviceDescriptor(
            backend=BACKEND_AYLA,
            backend_id=MOCK_SERIAL,
            serial_number=MOCK_SERIAL,
            name="EcoWater Softener",
            model="EcoWater ERR3700R",
            oem_model="EWS3700",
            model_id="46904",
            firmware_version="1.2.3",
            is_online=True,
            wifi_signal_strength_dbm=-65,
        ),
        capabilities=DeviceCapabilities(
            has_water_usage_today=True,
            has_water_usage_daily_avg=True,
            has_water_available=True,
            has_total_water_used=True,
            has_flow_sensor=True,
            has_salt_sensor=True,
            has_rock_removed_daily_avg=True,
            has_rock_removed_since_regeneration=True,
            has_total_rock_removed=True,
            has_peak_flow=True,
            has_capacity_remaining=True,
            has_regen_time_remaining=True,
            has_valve_position=True,
            has_avg_days_between_regens=True,
            has_avg_salt_per_regen=True,
            has_total_regens=True,
            has_total_salt_used=True,
            has_low_salt_alert=True,
            has_depletion_alert=True,
            has_excessive_water_use_alert=True,
            has_flow_monitor_alert=True,
            has_service_reminder_alert=True,
            has_error_code_alert=True,
            has_error_code=True,
            has_unmapped_salt_model=False,
            has_power_outage_count=True,
            has_time_lost_events=True,
            has_longest_rec_outage_mins=True,
            has_valve_reindex_count=True,
            has_valve_motor_state_enum=True,
            has_valve_pos_switch_enum=True,
            has_valve_pos_time_left_secs=True,
            has_days_in_operation=True,
            has_total_untreated_water_gals=True,
            has_average_exhaustion_percent=True,
            has_efficiency_mode_enum=True,
            has_operating_capacity_grains=True,
            has_hardness_grains=True,
            has_iron_level_tenths_ppm=True,
            has_flow_monitor_min_rate_gpm=True,
            has_flow_monitor_trip_sec=True,
            has_manual_regens=True,
            has_fill_secs=True,
            has_backwash_secs=True,
            has_fast_rinse_secs=True,
            has_second_backwash_cycles=True,
            has_second_backwash_secs=True,
        ),
        freshness=DataFreshness(
            received_at=datetime.datetime(2026, 8, 5, 14, 0, 0, tzinfo=datetime.UTC),
            oldest_data_at=datetime.datetime(2026, 8, 5, 13, 0, 0, tzinfo=datetime.UTC),
            newest_data_at=datetime.datetime(
                2026, 8, 5, 13, 59, 0, tzinfo=datetime.UTC
            ),
        ),
        regeneration=RegenerationState(
            status="Standby",
            is_enabled=True,
            days_since_last=21,
            estimated_last_date=datetime.date(2026, 7, 15),
        ),
        water_used_today_gallons=45.0,
        water_used_daily_avg_gallons=38.7,
        water_available_gallons=1234.5,
        total_water_used_gallons=15000.0,
        total_water_source_property="total_water_used_gals",
        current_flow_gpm=0.0,
        salt_level_raw=60.0,
        salt_level_percent=75.0,
        days_until_out_of_salt=42,
        estimated_out_of_salt_date=datetime.date(2026, 9, 16),
        salt_type="sodium_chloride",
        rock_removed_since_regeneration_lbs=3.25,
        total_rock_removed_lbs=42.0,
        rock_removed_daily_avg_lbs=1.5,
        peak_water_flow_gpm=12.0,
        capacity_remaining_percent=50.0,
        regen_time_rem_secs=0,
        current_valve_position="Service",
        avg_days_between_regens=10.0,
        avg_salt_per_regen_lbs=5.0,
        total_regens=120,
        total_salt_used_lbs=600.0,
        error_code=None,
        low_salt_alert=False,
        depletion_alert=False,
        excessive_water_use_alert=False,
        flow_monitor_alert=False,
        service_reminder_alert=False,
        error_code_alert=False,
        power_outage_count=2,
        time_lost_events=1,
        longest_rec_outage_mins=120,
        valve_reindex_count=1,
        valve_motor_state_enum=0,
        valve_pos_switch_enum=1,
        valve_pos_time_left_secs=0,
        days_in_operation=365,
        total_untreated_water_gals=20000.0,
        average_exhaustion_percent=85.0,
        efficiency_mode_enum=1,
        operating_capacity_grains=30000,
        hardness_grains=15,
        iron_level_tenths_ppm=0,
        flow_monitor_min_rate_gpm=2.0,
        flow_monitor_trip_sec=120,
        manual_regens=2,
        fill_secs=300,
        backwash_secs=600,
        fast_rinse_secs=180,
        second_backwash_cycles=0,
        second_backwash_secs=0,
    )


# ---------------------------------------------------------------------------
# Mock backend
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ayla_backend() -> MagicMock:
    """Return a mock AylaBackend that satisfies BackendAdapter."""
    backend = MagicMock()
    backend.async_authenticate = AsyncMock(return_value=None)
    backend.async_get_all_device_data = AsyncMock(
        return_value=AccountInfo(devices={MOCK_SERIAL: make_full_device_snapshot()})
    )
    backend.async_list_devices = AsyncMock(return_value=[MOCK_SERIAL])
    return backend


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
