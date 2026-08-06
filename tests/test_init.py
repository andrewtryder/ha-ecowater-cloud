"""Tests for the EcoWater Cloud integration setup and unload."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.ecowater_cloud.const import DOMAIN
from tests.conftest import MOCK_ENTRY_DATA


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test setting up and unloading the integration."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Mock the backend creation in __init__
    with (
        patch(
            "custom_components.ecowater_cloud.AylaBackend",
            return_value=mock_ayla_backend,
        ),
        patch("custom_components.ecowater_cloud.PLATFORMS", []),
    ):
        entry = MockConfigEntry(
            version=2,
            minor_version=1,
            domain=DOMAIN,
            title="EcoWater Cloud",
            data=MOCK_ENTRY_DATA,
            source="user",
            options={},
            unique_id="ayla:us:user@example.com",
            discovery_keys={},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data.coordinator is not None

        # Verify the full call chain: authenticate → get_all_device_data
        mock_ayla_backend.async_authenticate.assert_awaited_once()
        mock_ayla_backend.async_get_all_device_data.assert_awaited_once()

        # Unload
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_setup_unsupported_backend(hass: HomeAssistant) -> None:
    """Test setting up with an unsupported backend aborts gracefully."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"backend": "unsupported", "username": "user", "password": "pwd"},
        source="user",
        options={},
        unique_id="ayla:us:user@example.com",
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    # ConfigEntryError is raised → HA marks entry as SETUP_ERROR
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.asyncio
async def test_migrate_entry(hass: HomeAssistant) -> None:
    """Test config entry migration."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data=MOCK_ENTRY_DATA,
        source="user",
        options={},
        unique_id="user@example.com",
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    from custom_components.ecowater_cloud import async_migrate_entry
    from custom_components.ecowater_cloud.const import (
        BACKEND_AYLA,
        CONF_BACKEND,
        CONF_REGION,
        REGION_US,
    )

    assert await async_migrate_entry(hass, entry)

    # Migration must bump version to 2.3 and stamp backend, region, and unique_id
    assert entry.version == 2
    assert entry.minor_version == 3
    assert entry.data[CONF_BACKEND] == BACKEND_AYLA
    assert entry.data[CONF_REGION] == REGION_US
    assert entry.unique_id == "ayla:us:user@example.com"
