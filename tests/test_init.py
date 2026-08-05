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
        patch("custom_components.ecowater_cloud.AylaBackend", return_value=mock_ayla_backend),
        patch("custom_components.ecowater_cloud.PLATFORMS", []),
    ):
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
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data.coordinator is not None

        # Unload
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_setup_unsupported_backend(hass: HomeAssistant) -> None:
    """Test setting up with an unsupported backend aborts gracefully."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"backend": "unsupported", "username": "user", "password": "pwd"},
        source="user",
        options={},
        unique_id="user@example.com",
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    # setup should return False
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

    # Run the setup which triggers migration internally
    # For now migration just logs success and returns True
    from custom_components.ecowater_cloud import async_migrate_entry
    assert await async_migrate_entry(hass, entry)
