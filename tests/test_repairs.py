"""Test repairs logic for the EcoWater Cloud integration."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ecowater_cloud.const import DOMAIN
from custom_components.ecowater_cloud.coordinator import AccountCoordinator
from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    ProtocolError,
)


@pytest.fixture
def mock_issue_registry(hass: HomeAssistant):
    """Fixture to easily check the issue registry."""
    from homeassistant.helpers.issue_registry import async_get

    return async_get(hass)


@pytest.mark.asyncio
async def test_auth_rejected_repair(hass: HomeAssistant, mock_issue_registry) -> None:
    """Test auth rejected repair is created and deleted."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coordinator = AccountCoordinator(hass, entry, AsyncMock())
    coordinator.last_exception = AuthenticationError("Auth failed")

    from custom_components.ecowater_cloud.repairs import _check_auth_rejected

    _check_auth_rejected(hass, entry, coordinator)

    # Needs a small delay for async_create_issue to process
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_authentication_rejected"
    )
    assert issue is not None

    coordinator.last_exception = None
    _check_auth_rejected(hass, entry, coordinator)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_authentication_rejected"
    )
    assert issue is None


@pytest.mark.asyncio
async def test_protocol_changed_repair(
    hass: HomeAssistant, mock_issue_registry
) -> None:
    """Test protocol changed repair is created and deleted."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coordinator = AccountCoordinator(hass, entry, AsyncMock())
    coordinator.last_exception = ProtocolError("Protocol changed")

    from custom_components.ecowater_cloud.repairs import _check_protocol_changed

    _check_protocol_changed(hass, entry, coordinator)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_protocol_changed"
    )
    assert issue is not None

    coordinator.last_exception = None
    _check_protocol_changed(hass, entry, coordinator)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_protocol_changed"
    )
    assert issue is None
