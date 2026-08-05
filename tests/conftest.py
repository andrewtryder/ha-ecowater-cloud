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
            model_id="46904",
            firmware_version="1.2.3",
            is_online=True,
            wifi_signal_strength_dbm=-65,
        ),
        capabilities=DeviceCapabilities(
            has_water_usage=True,
            has_flow_sensor=True,
            has_salt_sensor=True,
            has_rock_sensor=True,
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
        current_flow_gpm=0.0,
        salt_level_raw=60.0,
        salt_level_percent=75.0,
        days_until_out_of_salt=42,
        estimated_out_of_salt_date=datetime.date(2026, 9, 16),
        salt_type="Solar Crystals",
        rock_removed_lbs=1500.0,
        rock_removed_daily_avg_lbs=3.2,
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
