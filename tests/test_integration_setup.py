"""Integration-level test: full async_setup_entry call chain via mocked HTTP.

Covers:
  async_setup_entry
    → coordinator._async_setup (authenticate)
    → coordinator._async_update_data (list devices + fetch properties)
    → coordinator.data populated
    → sensor / binary_sensor entities registered
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ecowater_cloud.backends.ayla.backend import AylaBackend
from custom_components.ecowater_cloud.const import DOMAIN
from tests.conftest import MOCK_ENTRY_DATA

USER_URL = "https://user-field.aylanetworks.com"
ADS_URL = "https://ads-field.aylanetworks.com"

DEVICE_DSN = "SN9999TEST"

_AUTH_RESPONSE = {"access_token": "tok_test_abc123"}

_DEVICE_LIST = [
    {
        "device": {
            "dsn": DEVICE_DSN,
            "oem_model": "EWS123",
            "connection_status": "Online",
            "mac": "aa:bb:cc:dd:ee:ff",
        }
    }
]

_PROPERTIES = [
    {"property": {"name": "gallons_used_today", "value": 55}},
    {"property": {"name": "avg_daily_use_gals", "value": 40}},
    {"property": {"name": "treated_water_avail_gals", "value": 1200}},
    {"property": {"name": "total_water_used_gals", "value": 20000}},
    {"property": {"name": "current_water_flow_gpm", "value": 0}},
    {"property": {"name": "salt_level_tenths", "value": 700}},
    {"property": {"name": "out_of_salt_estimate_days", "value": 30}},
    {"property": {"name": "regen_status_enum", "value": 0}},
    {"property": {"name": "salt_type_enum", "value": 0}},
    # model_id "1601" → SALT_TENTHS_MAX = 800, so 700/800*100 = 87.5
    {"property": {"name": "model_id", "value": "1601"}},
]


@pytest.mark.asyncio
async def test_backend_full_http_chain(hass: HomeAssistant, aioclient_mock) -> None:
    """Test authenticate → list devices → fetch properties via mocked HTTP."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json=_AUTH_RESPONSE,
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        json=_DEVICE_LIST,
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/{DEVICE_DSN}/properties.json",
        json=_PROPERTIES,
        status=200,
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "s3cr3t")

    await backend.async_authenticate()
    account_info = await backend.async_get_all_device_data()

    assert len(account_info.devices) == 1
    device = account_info.devices[DEVICE_DSN]

    assert device.descriptor.serial_number == DEVICE_DSN
    assert device.descriptor.model == "EWS123"
    assert device.descriptor.is_online is True
    assert device.water_used_today_gallons == 55.0
    assert device.water_used_daily_avg_gallons == 40.0
    assert device.water_available_gallons == 1200.0
    assert device.total_water_used_gallons == 20000.0
    assert device.current_flow_gpm == 0.0
    assert device.salt_level_raw == 700.0
    assert device.salt_level_percent is not None
    # model_id "1601" → SALT_TENTHS_MAX["1601"] = 80; 700 tenths / 80 * 100 = 875 → clamped to 100.0
    assert device.salt_level_percent == 100.0
    assert device.days_until_out_of_salt == 30
    assert device.regeneration.status == "standby"
    assert device.salt_type == "sodium_chloride"
    assert device.capabilities.has_water_usage is True
    assert device.capabilities.has_salt_sensor is True


@pytest.mark.asyncio
async def test_setup_entry_via_real_backend_http(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test the complete async_setup_entry call chain with mocked HTTP.

    Verifies:
      1. _async_setup calls async_authenticate on the backend.
      2. _async_update_data fetches device data.
      3. coordinator.data contains the expected device.
      4. Sensor entities are registered in HA state machine.
    """
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json=_AUTH_RESPONSE,
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        json=_DEVICE_LIST,
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/{DEVICE_DSN}/properties.json",
        json=_PROPERTIES,
        status=200,
    )

    session = async_get_clientsession(hass)
    real_backend = AylaBackend(session, "test@example.com", "s3cr3t")

    with patch(
        "custom_components.ecowater_cloud.AylaBackend",
        return_value=real_backend,
    ):
        entry = MockConfigEntry(
            version=2,
            minor_version=2,
            domain=DOMAIN,
            title="EcoWater Cloud",
            data=MOCK_ENTRY_DATA,
            source="user",
            options={},
            unique_id="test@example.com",
            discovery_keys={},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    coordinator = entry.runtime_data.coordinator
    assert coordinator is not None
    assert DEVICE_DSN in coordinator.data

    device = coordinator.data[DEVICE_DSN]
    assert device.descriptor.serial_number == DEVICE_DSN
    assert device.regeneration.status == "standby"
    assert device.salt_type == "sodium_chloride"

    # Sensor entities must be registered in HA's state machine
    entity_ids = [s.entity_id for s in hass.states.async_all()]
    water_today = [e for e in entity_ids if "water_used_today" in e]
    assert water_today, f"Expected water_used_today entity; found: {entity_ids}"
