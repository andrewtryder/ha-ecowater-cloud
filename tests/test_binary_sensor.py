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

    # Test system_problem (should be off when device is online and no alerts are active)
    state = hass.states.get("binary_sensor.ecowater_softener_system_problem")
    assert state is not None
    assert state.state == "off"
    assert state.attributes["device_class"] == BinarySensorDeviceClass.PROBLEM


@pytest.mark.asyncio
async def test_system_problem_evaluates_true_on_alerts() -> None:
    """Test that system_problem binary sensor evaluates to True when any alert is active."""
    from unittest.mock import MagicMock

    from custom_components.ecowater_cloud.binary_sensor import (
        BINARY_SENSORS,
        EcoWaterBinarySensor,
    )

    desc = next(b for b in BINARY_SENSORS if b.key == "system_problem")

    # Healthy device
    dev = MagicMock()
    dev.descriptor.backend = "ayla"
    dev.descriptor.is_online = True
    dev.freshness.age = None
    dev.low_salt_alert = False
    dev.depletion_alert = False
    dev.service_reminder_alert = False
    dev.error_code_alert = False
    dev.excessive_water_use_alert = False
    dev.flow_monitor_alert = False

    coord = MagicMock()
    coord.data = {"AC1": dev}

    sensor = EcoWaterBinarySensor(coord, "AC1", desc)
    assert sensor.is_on is False

    # Low salt alert triggers system_problem
    dev.low_salt_alert = True
    assert sensor.is_on is True

    # Offline device triggers system_problem
    dev.low_salt_alert = False
    dev.descriptor.is_online = False
    assert sensor.is_on is True

    # All unknown signals return None (unknown)
    dev.descriptor.is_online = None
    dev.freshness.age = None
    dev.low_salt_alert = None
    dev.depletion_alert = None
    dev.service_reminder_alert = None
    dev.error_code_alert = None
    dev.excessive_water_use_alert = None
    dev.flow_monitor_alert = None
    assert sensor.is_on is None


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


@pytest.mark.asyncio
async def test_data_stale_binary_sensor_unknown_freshness() -> None:
    """Test that data_stale binary sensor returns None (unknown) when freshness timestamp is missing."""
    from unittest.mock import MagicMock

    from custom_components.ecowater_cloud.binary_sensor import (
        BINARY_SENSORS,
        EcoWaterBinarySensor,
    )

    data_stale_desc = next(b for b in BINARY_SENSORS if b.key == "data_stale")

    dev_no_freshness = MagicMock()
    dev_no_freshness.descriptor.backend = "ayla"
    dev_no_freshness.freshness.age = None

    coord = MagicMock()
    coord.data = {"AC1": dev_no_freshness}

    sensor = EcoWaterBinarySensor(coord, "AC1", data_stale_desc)
    assert sensor.is_on is None
