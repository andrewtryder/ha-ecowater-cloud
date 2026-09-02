"""End-to-end HTTP tests for the AylaBackend interacting with AylaApi."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMockResponse,
)

from custom_components.ecowater_cloud.backends.ayla.backend import AylaBackend

USER_URL = "https://user-field.aylanetworks.com"
ADS_URL = "https://ads-field.aylanetworks.com"


@pytest.mark.asyncio
async def test_ayla_backend_e2e_successful_update(hass, aioclient_mock):
    """Test full e2e flow from AylaBackend to AylaApi mocked HTTP responses."""
    # 1. Mock authentication
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"},
        status=200,
    )

    # 2. Mock list_devices (Ayla wraps devices in {"device": {...}})
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        json=[
            {
                "device": {
                    "dsn": "AC0001",
                    "oem_model": "EWS123",
                    "connection_status": "Online",
                    "mac": "00:11:22:33:44:55",
                }
            }
        ],
        status=200,
    )

    # 3. Mock get_device_properties (Ayla wraps properties in {"property": {...}})
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/AC0001/properties.json",
        json=[{"property": {"name": "current_water_flow_gpm", "value": 50}}],
        status=200,
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "password")

    # Perform the flow
    await backend.async_authenticate()
    account_info = await backend.async_get_all_device_data()

    assert len(account_info.devices) == 1
    device_data = account_info.devices["AC0001"]

    # Verify normalization worked all the way from the raw HTTP response
    assert device_data.descriptor.serial_number == "AC0001"
    assert device_data.descriptor.model == "EWS123"

    # 50 gpm from API, divided by 10 as per EcoWater normalization rules -> 5.0
    assert device_data.current_flow_gpm == 5.0


@pytest.mark.asyncio
async def test_ayla_backend_e2e_expired_access_token_refresh_succeeds(
    hass, aioclient_mock
):
    """Test expired access token refreshed via refresh token without full login."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={
            "access_token": "expired_access",
            "refresh_token": "valid_refresh",
        },
        status=200,
    )

    devices_calls = 0

    async def devices_response(method, url, data):
        nonlocal devices_calls
        devices_calls += 1
        if devices_calls == 1:
            return AiohttpClientMockResponse(method, url, status=401)
        return AiohttpClientMockResponse(
            method,
            url,
            json=[
                {
                    "device": {
                        "dsn": "AC0001",
                        "oem_model": "EWS123",
                        "connection_status": "Online",
                    }
                }
            ],
            status=200,
        )

    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        side_effect=devices_response,
    )
    aioclient_mock.post(
        f"{USER_URL}/users/refresh_token.json",
        json={
            "access_token": "refreshed_access",
            "refresh_token": "new_refresh",
        },
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/AC0001/properties.json",
        json=[{"property": {"name": "current_water_flow_gpm", "value": 50}}],
        status=200,
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "password")

    await backend.async_authenticate()
    account_info = await backend.async_get_all_device_data()

    assert len(account_info.devices) == 1
    assert account_info.devices["AC0001"].current_flow_gpm == 5.0
    # sign_in called only once for initial auth; refresh_token handled the expiration
    sign_in_calls_count = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if str(c[1]).endswith("/users/sign_in.json")
        ]
    )
    refresh_calls_count = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if str(c[1]).endswith("/users/refresh_token.json")
        ]
    )
    assert sign_in_calls_count == 1
    assert refresh_calls_count == 1


@pytest.mark.asyncio
async def test_ayla_backend_e2e_rejected_refresh_token_auto_reauthenticates(
    hass, aioclient_mock
):
    """Test rejected refresh token triggers full username/password reauth and retries."""
    sign_in_calls = 0

    async def sign_in_response(method, url, data):
        nonlocal sign_in_calls
        sign_in_calls += 1
        if sign_in_calls == 1:
            return AiohttpClientMockResponse(
                method,
                url,
                json={
                    "access_token": "initial_access",
                    "refresh_token": "expired_refresh",
                },
                status=200,
            )
        return AiohttpClientMockResponse(
            method,
            url,
            json={
                "access_token": "reauth_access",
                "refresh_token": "fresh_refresh",
            },
            status=200,
        )

    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        side_effect=sign_in_response,
    )

    devices_calls = 0

    async def devices_response(method, url, data):
        nonlocal devices_calls
        devices_calls += 1
        if devices_calls == 1:
            return AiohttpClientMockResponse(method, url, status=401)
        return AiohttpClientMockResponse(
            method,
            url,
            json=[
                {
                    "device": {
                        "dsn": "AC0001",
                        "oem_model": "EWS123",
                        "connection_status": "Online",
                    }
                }
            ],
            status=200,
        )

    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        side_effect=devices_response,
    )
    # Refresh token endpoint rejects the expired refresh token (401)
    aioclient_mock.post(
        f"{USER_URL}/users/refresh_token.json",
        status=401,
        json={"error": "Invalid refresh token"},
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/AC0001/properties.json",
        json=[{"property": {"name": "current_water_flow_gpm", "value": 50}}],
        status=200,
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "saved_password")

    await backend.async_authenticate()
    account_info = await backend.async_get_all_device_data()

    assert len(account_info.devices) == 1
    assert account_info.devices["AC0001"].current_flow_gpm == 5.0

    # sign_in called twice: 1 for initial auth, 1 for auto re-auth
    assert sign_in_calls == 2
    # refresh_token attempted once
    refresh_calls_count = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if str(c[1]).endswith("/users/refresh_token.json")
        ]
    )
    assert refresh_calls_count == 1
    # devices.json called twice: 1st got 401, 2nd after reauth got 200
    assert devices_calls == 2


@pytest.mark.asyncio
async def test_ayla_backend_e2e_rejected_refresh_and_failed_reauth_propagates_error(
    hass, aioclient_mock
):
    """Test that when refresh fails and full login also fails, AuthenticationError propagates."""
    sign_in_calls = 0

    async def sign_in_response(method, url, data):
        nonlocal sign_in_calls
        sign_in_calls += 1
        if sign_in_calls == 1:
            return AiohttpClientMockResponse(
                method,
                url,
                json={
                    "access_token": "initial_access",
                    "refresh_token": "expired_refresh",
                },
                status=200,
            )
        return AiohttpClientMockResponse(
            method,
            url,
            json={"error": "Unauthorized"},
            status=401,
        )

    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        side_effect=sign_in_response,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        status=401,
    )
    aioclient_mock.post(
        f"{USER_URL}/users/refresh_token.json",
        status=401,
        json={"error": "Invalid refresh token"},
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "changed_password")

    await backend.async_authenticate()

    from custom_components.ecowater_cloud.backends.ayla.exceptions import (
        AylaAuthenticationError,
    )

    with pytest.raises(AylaAuthenticationError):
        await backend.async_get_all_device_data()

    # Total sign_in calls: 1 initial, 1 failed reauth (no loop)
    assert sign_in_calls == 2


@pytest.mark.asyncio
async def test_ayla_backend_e2e_refresh_connectivity_error_does_not_reauth(
    hass, aioclient_mock
):
    """Test that connectivity error during refresh does not trigger username/password login."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={
            "access_token": "initial_access",
            "refresh_token": "valid_refresh",
        },
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        status=401,
    )
    aioclient_mock.post(
        f"{USER_URL}/users/refresh_token.json",
        exc=TimeoutError(),
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "password")

    await backend.async_authenticate()

    from custom_components.ecowater_cloud.backends.ayla.exceptions import (
        AylaConnectivityError,
    )

    with pytest.raises(AylaConnectivityError, match="Request timed out"):
        await backend.async_get_all_device_data()

    # sign_in was NOT called a second time
    sign_in_calls_count = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if str(c[1]).endswith("/users/sign_in.json")
        ]
    )
    assert sign_in_calls_count == 1


@pytest.mark.asyncio
async def test_ayla_backend_e2e_refresh_rate_limit_error_does_not_reauth(
    hass, aioclient_mock
):
    """Test that rate limit error during refresh does not trigger username/password login."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={
            "access_token": "initial_access",
            "refresh_token": "valid_refresh",
        },
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        status=401,
    )
    aioclient_mock.post(
        f"{USER_URL}/users/refresh_token.json",
        status=429,
    )

    session = async_get_clientsession(hass)
    backend = AylaBackend(session, "test@example.com", "password")

    await backend.async_authenticate()

    from custom_components.ecowater_cloud.backends.ayla.exceptions import (
        AylaRateLimitError,
    )

    with pytest.raises(AylaRateLimitError):
        await backend.async_get_all_device_data()

    # sign_in was NOT called a second time
    sign_in_calls_count = len(
        [
            c
            for c in aioclient_mock.mock_calls
            if str(c[1]).endswith("/users/sign_in.json")
        ]
    )
    assert sign_in_calls_count == 1
