"""End-to-end HTTP tests for the AylaBackend interacting with AylaApi."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
        json=[
            {
                "property": {
                    "name": "current_water_flow_gpm",
                    "value": 50
                }
            }
        ],
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

