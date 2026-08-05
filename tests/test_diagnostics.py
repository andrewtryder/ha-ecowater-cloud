"""Tests for EcoWater Cloud diagnostics."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ecowater_cloud.const import DOMAIN
from custom_components.ecowater_cloud.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.conftest import MOCK_ENTRY_DATA, MOCK_PASSWORD, MOCK_USERNAME


@pytest.mark.asyncio
async def test_diagnostics_redaction(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test that diagnostics properly redact sensitive information."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ecowater_cloud import EcoWaterCloudConfigEntry

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

    # The setup transforms it to EcoWaterCloudConfigEntry via type alias
    typed_entry: EcoWaterCloudConfigEntry = hass.config_entries.async_get_entry(
        entry.entry_id
    )
    assert typed_entry is not None

    diagnostics = await async_get_config_entry_diagnostics(hass, typed_entry)

    # Check config entry redaction
    assert diagnostics["entry"]["data"]["username"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["password"] == "**REDACTED**"
    assert MOCK_USERNAME not in str(diagnostics)
    assert MOCK_PASSWORD not in str(diagnostics)

    # Check coordinator / device redaction
    assert "devices" in diagnostics["coordinator"]
    devices = diagnostics["coordinator"]["devices"]
    assert len(devices) == 1
    assert "device_1" in devices

    device_data = devices["device_1"]
    assert device_data["descriptor"]["serial_number"] == "***REDACTED***"
    assert device_data["descriptor"]["backend_id"] == "***REDACTED***"

    # Safe fields should be exposed
    assert device_data["descriptor"]["model"] == "EcoWater ERR3700R"
    assert device_data["total_water_used_gallons"] == 15000.0
    assert device_data["capabilities"]["has_water_usage_today"] is True
    assert device_data["capabilities"]["has_water_usage_daily_avg"] is True
    assert device_data["capabilities"]["has_water_available"] is True
    assert device_data["capabilities"]["has_total_water_used"] is True
    assert (
        device_data["capabilities"]["total_water_source_property"]
        == "total_water_used_gals"
    )
