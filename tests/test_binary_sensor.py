"""Tests for EcoWater Cloud binary sensors."""

from unittest.mock import patch

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.ecowater_cloud.const import DOMAIN
from tests.conftest import MOCK_ENTRY_DATA


@pytest.mark.asyncio
async def test_binary_sensors(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test binary sensors setup and state."""
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

    # Test device_reported_online
    state = hass.states.get("binary_sensor.ecowater_softener_device_reported_online")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["device_class"] == BinarySensorDeviceClass.CONNECTIVITY

    # Test recharge_enabled
    state = hass.states.get("binary_sensor.ecowater_softener_recharge_enabled")
    assert state is not None
    assert state.state == "on"

    # Test regenerating (should be off since status is Standby)
    state = hass.states.get("binary_sensor.ecowater_softener_regenerating")
    assert state is not None
    assert state.state == "off"


@pytest.mark.asyncio
async def test_dynamic_binary_sensor_addition(
    hass: HomeAssistant, mock_ayla_backend
) -> None:
    """Test that new devices discovered after setup create new binary sensors."""
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
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Simulate update adding a new device
        account_info = await mock_ayla_backend.async_get_all_device_data()

        from dataclasses import replace

        first_device = next(iter(account_info.devices.values()))
        new_device = replace(
            first_device,
            descriptor=replace(
                first_device.descriptor,
                serial_number="NEW_DEVICE",
                name="New Filter",
            ),
        )
        account_info.devices["NEW_DEVICE"] = new_device

        # Trigger coordinator refresh
        # Wait, the coordinator fetches from backend, so we need to trigger it
        coordinator = entry.runtime_data.coordinator
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.new_filter_device_reported_online")
        assert state is not None
        assert state.state == "on"
