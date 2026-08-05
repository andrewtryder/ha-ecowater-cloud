"""Test scaffolding for the HydroLink API client."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.ecowater_cloud.backends.hydrolink import HydroLinkBackend


async def test_eu_region(hass):
    """Test authentication against the EU region."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "eu")
    with pytest.raises(NotImplementedError):
        await backend.async_authenticate()


async def test_us_region(hass):
    """Test authentication against the US region."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_authenticate()


async def test_multiple_devices(hass):
    """Test parsing multiple devices on one account."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_list_devices()


async def test_stale_data(hass):
    """Test handling of stale telemetry data without waking the device."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_get_device_data("test_id")


async def test_wake_success(hass):
    """Test successful wake sequence."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_get_device_data("test_id")


async def test_wake_timeout(hass):
    """Test wake sequence timeout."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_get_device_data("test_id")


async def test_unauthorized(hass):
    """Test handling of unauthorized errors during polling."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_list_devices()


async def test_rate_limit(hass):
    """Test handling of rate limit errors."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_list_devices()


async def test_partial_properties(hass):
    """Test normalization of devices lacking certain capabilities (e.g. no water sensor)."""
    session = async_get_clientsession(hass)
    backend = HydroLinkBackend(session, "test@test.com", "pass", "us")
    with pytest.raises(NotImplementedError):
        await backend.async_get_all_device_data()
