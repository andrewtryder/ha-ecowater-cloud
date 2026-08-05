"""Tests for EcoWater Cloud sensors."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.ecowater_cloud.const import DOMAIN
from tests.conftest import MOCK_ENTRY_DATA


@pytest.mark.asyncio
async def test_all_sensors(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test all sensors setup and state."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    with patch(
        "custom_components.ecowater_cloud.AylaBackend", return_value=mock_ayla_backend
    ):
        entry = MockConfigEntry(
            version=2,
            minor_version=2,
            domain=DOMAIN,
            title="EcoWater Cloud",
            data=MOCK_ENTRY_DATA,
            source="user",
            options={},
            unique_id="user@example.com",
            discovery_keys={},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    # Test total water used (volume conversion check)
    state = hass.states.get("sensor.ecowater_softener_total_water_used")
    assert state is not None
    assert state.state == "56781.17676"  # 15000 gal -> L

    # Test salt level (percentage)
    state = hass.states.get("sensor.ecowater_softener_salt_level")
    assert state is not None
    assert state.state == "75.0"

    # Test regen status (enum)
    state = hass.states.get("sensor.ecowater_softener_regeneration_status")
    assert state is not None
    assert state.state == "standby"

    # Test out of salt date (date)
    state = hass.states.get("sensor.ecowater_softener_estimated_out_of_salt_date")
    assert state is not None
    assert state.state == "2026-09-16"

    # Test source last updated (datetime)
    state = hass.states.get("sensor.ecowater_softener_source_last_updated")
    assert state is not None
    assert state.state == "2026-08-05T13:59:00+00:00"

    # Test current water flow
    state = hass.states.get("sensor.ecowater_softener_current_water_flow")
    assert state is not None
    assert state.state == "0.0"


@pytest.mark.asyncio
async def test_sensor_missing_capability(
    hass: HomeAssistant, mock_ayla_backend
) -> None:
    """Test sensors are not created if capability is missing."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Modify mock to remove water usage capability
    account_info = await mock_ayla_backend.async_get_all_device_data()
    device = account_info.devices.get("ABC123456789")
    if device:
        from dataclasses import replace

        new_device = replace(
            device, capabilities=replace(device.capabilities, has_water_usage=False)
        )
        account_info.devices["ABC123456789"] = new_device

    with patch(
        "custom_components.ecowater_cloud.AylaBackend", return_value=mock_ayla_backend
    ):
        entry = MockConfigEntry(
            version=2,
            minor_version=2,
            domain=DOMAIN,
            title="EcoWater Cloud",
            data=MOCK_ENTRY_DATA,
            source="user",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Sensor should not be created
    state = hass.states.get("sensor.ecowater_softener_total_water_used")
    assert state is None
