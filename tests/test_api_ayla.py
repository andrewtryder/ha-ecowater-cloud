"""Tests for the Ayla API client."""


import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.ecowater_cloud.backends.ayla.api import AylaApi
from custom_components.ecowater_cloud.backends.ayla.exceptions import (
    AylaAuthenticationError,
    AylaConnectivityError,
    AylaProtocolError,
    AylaRateLimitError,
)

USER_URL = "https://user-field.aylanetworks.com"
ADS_URL = "https://ads-field.aylanetworks.com"


async def test_successful_authentication(hass, aioclient_mock):
    """Test successful login flow."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access", "refresh_token": "mocked_refresh", "expires_in": 3600},
        status=200,
    )

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("test@example.com", "password123")

    assert api._access_token == "mocked_access"
    assert api._refresh_token == "mocked_refresh"


async def test_authentication_failure(hass, aioclient_mock):
    """Test login failure (HTTP 401)."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        status=401,
        json={"error": "Unauthorized"}
    )

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    with pytest.raises(AylaAuthenticationError):
        await api.async_authenticate("test@example.com", "wrong")


async def test_rate_limit(hass, aioclient_mock):
    """Test rate limit handling."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"},
        status=200,
    )
    aioclient_mock.get(f"{ADS_URL}/apiv1/devices.json", status=429)

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("test@example.com", "pass")

    with pytest.raises(AylaRateLimitError):
        await api.async_list_devices()


async def test_list_devices(hass, aioclient_mock):
    """Test listing devices."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"},
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/devices.json",
        json=[
            {"device": {"dsn": "DEV1", "model": "EWS1"}},
            {"device": {"dsn": "DEV2", "model": "EWS2"}},
        ],
        status=200,
    )

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("t@e.com", "p")
    devices = await api.async_list_devices()

    assert len(devices) == 2
    assert devices[0]["dsn"] == "DEV1"


async def test_get_device_properties(hass, aioclient_mock):
    """Test getting properties."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"},
        status=200,
    )
    aioclient_mock.get(
        f"{ADS_URL}/apiv1/dsns/MYDSN123/properties.json",
        json=[
            {"property": {"name": "water_use", "value": 100}},
            {"property": {"name": "salt_level", "value": 50}},
        ],
        status=200,
    )

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("t@e.com", "p")
    props = await api.async_get_device_properties("MYDSN123")

    assert len(props) == 2
    assert props[0]["name"] == "water_use"
    assert props[1]["value"] == 50


async def test_sign_out(hass, aioclient_mock):
    """Test sign out clears token."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"}
    )
    aioclient_mock.post(f"{USER_URL}/users/sign_out.json", status=204)

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("t@e.com", "p")
    assert api._access_token == "mocked_access"

    await api.async_clear_authentication()
    assert api._access_token is None


async def test_protocol_error_malformed_json(hass, aioclient_mock):
    """Test catching invalid JSON from Ayla."""
    aioclient_mock.post(
        f"{USER_URL}/users/sign_in.json",
        json={"access_token": "mocked_access"}
    )
    aioclient_mock.get(f"{ADS_URL}/apiv1/devices.json", text="not valid json", status=200)

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    await api.async_authenticate("t@e.com", "p")

    with pytest.raises(AylaProtocolError, match="Malformed JSON"):
        await api.async_list_devices()


async def test_connectivity_error_timeout(hass, aioclient_mock):
    """Test catching timeout."""
    aioclient_mock.get(f"{ADS_URL}/apiv1/devices.json", exc=TimeoutError())

    session = async_get_clientsession(hass)
    api = AylaApi(session)
    api._access_token = "mocked"

    with pytest.raises(AylaConnectivityError, match="Request timed out"):
        await api.async_list_devices()
