"""Test repairs logic for the EcoWater Cloud integration."""

import datetime
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ecowater_cloud.const import DOMAIN
from custom_components.ecowater_cloud.coordinator import (
    AccountCoordinator,
    CoordinatorErrorCategory,
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
    coordinator.last_error_category = CoordinatorErrorCategory.AUTHENTICATION

    from custom_components.ecowater_cloud.repairs import _check_auth_rejected

    _check_auth_rejected(hass, entry, coordinator)

    # Needs a small delay for async_create_issue to process
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_authentication_rejected"
    )
    assert issue is not None

    coordinator.last_error_category = None
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
    coordinator.last_error_category = CoordinatorErrorCategory.PROTOCOL

    from custom_components.ecowater_cloud.repairs import _check_protocol_changed

    _check_protocol_changed(hass, entry, coordinator)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_protocol_changed"
    )
    assert issue is not None

    coordinator.last_error_category = None
    _check_protocol_changed(hass, entry, coordinator)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_protocol_changed"
    )
    assert issue is None


@pytest.mark.asyncio
async def test_repair_isolation_between_entries(
    hass: HomeAssistant, mock_issue_registry
) -> None:
    """Test that repairs for two entries do not collide."""
    entry1 = MockConfigEntry(domain=DOMAIN, data={})
    entry1.add_to_hass(hass)

    entry2 = MockConfigEntry(domain=DOMAIN, data={})
    entry2.add_to_hass(hass)

    coord1 = AccountCoordinator(hass, entry1, AsyncMock())
    coord1.last_error_category = CoordinatorErrorCategory.AUTHENTICATION

    coord2 = AccountCoordinator(hass, entry2, AsyncMock())
    coord2.last_error_category = None

    from custom_components.ecowater_cloud.repairs import _check_auth_rejected

    _check_auth_rejected(hass, entry1, coord1)
    _check_auth_rejected(hass, entry2, coord2)
    await hass.async_block_till_done()

    issue1 = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry1.entry_id}_authentication_rejected"
    )
    assert issue1 is not None

    issue2 = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry2.entry_id}_authentication_rejected"
    )
    assert issue2 is None


@pytest.mark.asyncio
async def test_multi_device_repair_aggregation(
    hass: HomeAssistant, mock_issue_registry
) -> None:
    """Test that multiple devices with unknown salt models are aggregated."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    from unittest.mock import MagicMock

    dev1 = MagicMock()
    dev1.descriptor.name = "First Device"
    dev1.descriptor.model_id = "m1"
    dev1.capabilities.has_unmapped_salt_model = True

    dev2 = MagicMock()
    dev2.descriptor.name = "Second Device"
    dev2.descriptor.model_id = "m2"
    dev2.capabilities.has_unmapped_salt_model = True

    coord = AccountCoordinator(hass, entry, AsyncMock())
    coord.data = {"AC1": dev1, "AC2": dev2}

    from custom_components.ecowater_cloud.repairs import _check_unknown_salt_models

    _check_unknown_salt_models(hass, entry, coord)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_unknown_salt_model"
    )
    assert issue is not None
    assert "First Device" in issue.translation_placeholders["devices"]
    assert "Second Device" in issue.translation_placeholders["devices"]


@pytest.mark.asyncio
async def test_repairs_listener_registration(
    hass: HomeAssistant, mock_issue_registry
) -> None:
    """Test that async_register_repairs listens to the coordinator."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coord = AccountCoordinator(hass, entry, AsyncMock())
    coord.data = {}

    from custom_components.ecowater_cloud.repairs import async_register_repairs

    async_register_repairs(hass, entry, coord)
    await hass.async_block_till_done()

    # Trigger an error via coordinator update
    coord.last_error_category = CoordinatorErrorCategory.PROTOCOL
    coord.async_update_listeners()
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_protocol_changed"
    )
    assert issue is not None

    # Cleanup listener to avoid lingering timer
    if getattr(entry, "on_unload", None):
        for cb in entry.on_unload:
            cb()
    if getattr(coord, "_unsub_refresh", None):
        coord._unsub_refresh()


@pytest.mark.asyncio
async def test_stale_data_repair(hass: HomeAssistant, mock_issue_registry) -> None:
    """Test stale data repair issue is created and deleted."""
    from datetime import timedelta
    from unittest.mock import MagicMock

    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    dev = MagicMock()
    dev.descriptor.name = "Softener"
    dev.freshness.age = timedelta(hours=40)

    coord = AccountCoordinator(hass, entry, AsyncMock())
    coord.data = {"AC1": dev}

    from custom_components.ecowater_cloud.repairs import _check_stale_data

    _check_stale_data(hass, entry, coord)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(DOMAIN, f"{entry.entry_id}_data_stale")
    assert issue is not None
    assert "Softener (40h ago)" in issue.translation_placeholders["devices"]

    dev.freshness.age = timedelta(hours=10)
    _check_stale_data(hass, entry, coord)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(DOMAIN, f"{entry.entry_id}_data_stale")
    assert issue is None


@pytest.mark.asyncio
async def test_model_104703_no_repair(hass: HomeAssistant, mock_issue_registry) -> None:
    """Test that live-tested model 104703 does not trigger an unknown_salt_model repair."""
    from custom_components.ecowater_cloud.backends.ayla.models import (
        AylaDeviceData,
        AylaPropertyData,
    )
    from custom_components.ecowater_cloud.backends.ayla.normalization import (
        normalize_device,
    )
    from custom_components.ecowater_cloud.repairs import _check_unknown_salt_models

    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    dev_raw: AylaDeviceData = {
        "dsn": "AC000W000104703",
        "oem_model": "EWS3500",
        "product_name": "EWS ECR3700R30",
    }
    props_raw: list[AylaPropertyData] = [
        {"name": "model_id", "value": "104703", "type": "string"},
        {"name": "salt_level_tenths", "value": 30, "type": "integer"},
    ]
    received_at = datetime.datetime(2026, 8, 7, 11, 0, tzinfo=datetime.UTC)
    norm_dev = normalize_device(dev_raw, props_raw, received_at)

    coord = AccountCoordinator(hass, entry, AsyncMock())
    coord.data = {"AC000W000104703": norm_dev}

    _check_unknown_salt_models(hass, entry, coord)
    await hass.async_block_till_done()

    issue = mock_issue_registry.async_get_issue(
        DOMAIN, f"{entry.entry_id}_unknown_salt_model"
    )
    assert issue is None
