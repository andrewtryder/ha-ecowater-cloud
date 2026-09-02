"""Tests for the AylaBackend."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ecowater_cloud.backends.ayla.backend import AylaBackend
from custom_components.ecowater_cloud.backends.ayla.exceptions import (
    AylaAuthenticationError,
    AylaConnectivityError,
    AylaProtocolError,
    AylaRateLimitError,
)
from custom_components.ecowater_cloud.models import EcoWaterDeviceData


@pytest.fixture
def mock_ayla_api(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock the underlying AylaApi."""
    api = MagicMock()
    api.async_authenticate = AsyncMock()
    api.async_clear_authentication = AsyncMock()

    # Return some raw data matching the synthetic device
    api.async_list_devices = AsyncMock(
        return_value=[
            {"dsn": "AC0001", "oem_model": "EWS123", "connection_status": "Online"},
            {"dsn": "IGNORE_ME", "oem_model": "OTHER_BRAND"},
        ]
    )

    api.async_get_device_properties = AsyncMock(
        return_value=[{"name": "current_water_flow_gpm", "value": 50}]
    )

    # Patch AylaBackend to use this API
    monkeypatch.setattr(
        "custom_components.ecowater_cloud.backends.ayla.backend.AylaApi",
        lambda session, region="us": api,
    )
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

    assert len(devices) == 1  # OTHER_BRAND is filtered out
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
async def test_ayla_backend_get_device_data_not_found_in_list(
    mock_ayla_api: MagicMock,
) -> None:
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


@pytest.mark.asyncio
async def test_ayla_backend_reauthenticates_on_auth_error(
    mock_ayla_api: MagicMock,
) -> None:
    """Test that an AuthenticationError triggers full reauth and retries the operation."""
    backend = AylaBackend(MagicMock(), "user@example.com", "saved_pass")

    # list_devices fails with AuthenticationError first time, succeeds second time
    mock_ayla_api.async_list_devices.side_effect = [
        AylaAuthenticationError("token expired"),
        [{"dsn": "AC0001", "oem_model": "EWS123", "connection_status": "Online"}],
    ]

    devices = await backend.async_list_devices()

    assert len(devices) == 1
    assert devices[0].serial_number == "AC0001"
    mock_ayla_api.async_authenticate.assert_awaited_once_with(
        "user@example.com", "saved_pass"
    )
    assert mock_ayla_api.async_list_devices.await_count == 2


@pytest.mark.asyncio
async def test_ayla_backend_reauth_failure_propagates(
    mock_ayla_api: MagicMock,
) -> None:
    """Test that if full credential reauth fails, AuthenticationError propagates."""
    backend = AylaBackend(MagicMock(), "user@example.com", "wrong_pass")

    mock_ayla_api.async_list_devices.side_effect = AylaAuthenticationError(
        "token expired"
    )
    mock_ayla_api.async_authenticate.side_effect = AylaAuthenticationError(
        "invalid credentials"
    )

    with pytest.raises(AylaAuthenticationError, match="invalid credentials"):
        await backend.async_list_devices()

    mock_ayla_api.async_authenticate.assert_awaited_once_with(
        "user@example.com", "wrong_pass"
    )


@pytest.mark.asyncio
async def test_ayla_backend_bounded_retry_on_repeated_auth_error(
    mock_ayla_api: MagicMock,
) -> None:
    """Test that retry after reauth is bounded to a single retry (no infinite loop)."""
    backend = AylaBackend(MagicMock(), "user@example.com", "saved_pass")

    # Both initial and retried list_devices fail with AuthenticationError
    mock_ayla_api.async_list_devices.side_effect = AylaAuthenticationError(
        "token expired"
    )

    with pytest.raises(AylaAuthenticationError, match="token expired"):
        await backend.async_list_devices()

    # Reauth should only be called once, list_devices called twice total
    mock_ayla_api.async_authenticate.assert_awaited_once_with(
        "user@example.com", "saved_pass"
    )
    assert mock_ayla_api.async_list_devices.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_cls", "error_msg"),
    [
        (AylaConnectivityError, "network unreachable"),
        (AylaRateLimitError, "rate limit exceeded"),
        (AylaProtocolError, "malformed response"),
    ],
)
async def test_ayla_backend_non_auth_errors_do_not_trigger_reauth(
    mock_ayla_api: MagicMock,
    error_cls: type[Exception],
    error_msg: str,
) -> None:
    """Test that connectivity, rate-limit, and protocol errors do not trigger credential reauth."""
    backend = AylaBackend(MagicMock(), "user@example.com", "saved_pass")
    mock_ayla_api.async_list_devices.side_effect = error_cls(error_msg)

    with pytest.raises(error_cls, match=error_msg):
        await backend.async_list_devices()

    mock_ayla_api.async_authenticate.assert_not_called()
    assert mock_ayla_api.async_list_devices.await_count == 1


@pytest.mark.asyncio
async def test_ayla_backend_get_device_data_reauthenticates(
    mock_ayla_api: MagicMock,
) -> None:
    """Test async_get_device_data reauthenticates on auth error."""
    backend = AylaBackend(MagicMock(), "user@example.com", "saved_pass")

    # First attempt at getting properties fails with 401
    mock_ayla_api.async_get_device_properties.side_effect = [
        AylaAuthenticationError("token expired"),
        [{"name": "current_water_flow_gpm", "value": 50}],
    ]

    data = await backend.async_get_device_data("AC0001")
    assert data.descriptor.serial_number == "AC0001"
    assert data.current_flow_gpm == 5.0
    mock_ayla_api.async_authenticate.assert_awaited_once_with(
        "user@example.com", "saved_pass"
    )


@pytest.mark.asyncio
async def test_ayla_backend_get_all_device_data_reauthenticates(
    mock_ayla_api: MagicMock,
) -> None:
    """Test async_get_all_device_data reauthenticates on auth error."""
    backend = AylaBackend(MagicMock(), "user@example.com", "saved_pass")

    # First attempt at list_devices fails with auth error
    mock_ayla_api.async_list_devices.side_effect = [
        AylaAuthenticationError("token expired"),
        [
            {
                "dsn": "AC0001",
                "oem_model": "EWS123",
                "connection_status": "Online",
            }
        ],
    ]

    account = await backend.async_get_all_device_data()
    assert "AC0001" in account.devices
    mock_ayla_api.async_authenticate.assert_awaited_once_with(
        "user@example.com", "saved_pass"
    )
