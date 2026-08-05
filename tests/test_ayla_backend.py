"""Tests for the AylaBackend."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ecowater_cloud.backends.ayla.backend import AylaBackend
from custom_components.ecowater_cloud.models import EcoWaterDeviceData


@pytest.fixture
def mock_ayla_api(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock the underlying AylaApi."""
    api = MagicMock()
    api.async_authenticate = AsyncMock()
    api.async_clear_authentication = AsyncMock()

    # Return some raw data matching the synthetic device
    api.async_list_devices = AsyncMock(return_value=[
        {
            "dsn": "AC0001",
            "oem_model": "EWS123",
            "connection_status": "Online"
        },
        {
            "dsn": "IGNORE_ME",
            "oem_model": "OTHER_BRAND"
        }
    ])

    api.async_get_device_properties = AsyncMock(return_value=[
        {"name": "current_water_flow_gpm", "value": 50}
    ])

    # Patch AylaBackend to use this API
    monkeypatch.setattr("custom_components.ecowater_cloud.backends.ayla.backend.AylaApi", lambda session: api)
    return api


@pytest.mark.asyncio
async def test_ayla_backend_authenticate(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    await backend.async_authenticate()
    mock_ayla_api.async_authenticate.assert_awaited_once_with("user", "pass")


@pytest.mark.asyncio
async def test_ayla_backend_clear_authentication(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    await backend.async_clear_authentication()
    mock_ayla_api.async_clear_authentication.assert_awaited_once()


@pytest.mark.asyncio
async def test_ayla_backend_list_devices(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    devices = await backend.async_list_devices()

    assert len(devices) == 2
    assert devices[0].serial_number == "AC0001"
    assert devices[0].model == "EWS123"


@pytest.mark.asyncio
async def test_ayla_backend_get_device_data_found(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    data = await backend.async_get_device_data("AC0001")

    assert isinstance(data, EcoWaterDeviceData)
    assert data.descriptor.serial_number == "AC0001"
    assert data.current_flow_gpm == 5.0  # 50 / 10


@pytest.mark.asyncio
async def test_ayla_backend_get_device_data_not_found_in_list(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    data = await backend.async_get_device_data("UNKNOWN")

    assert isinstance(data, EcoWaterDeviceData)
    assert data.descriptor.serial_number == "UNKNOWN"
    assert data.current_flow_gpm == 5.0  # mock properties return 50


@pytest.mark.asyncio
async def test_ayla_backend_get_all_device_data(mock_ayla_api: MagicMock) -> None:
    backend = AylaBackend(MagicMock(), "user", "pass")
    account = await backend.async_get_all_device_data()

    assert len(account.devices) == 1  # Should ignore "OTHER_BRAND"
    assert "AC0001" in account.devices

    dev = account.devices["AC0001"]
    assert dev.descriptor.serial_number == "AC0001"
    assert dev.current_flow_gpm == 5.0
