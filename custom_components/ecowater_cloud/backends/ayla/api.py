"""Ayla API client.

Low-level client for the Ayla Networks API used by legacy EcoWater Wi-Fi
connected softeners.
This module does not import Home Assistant and is strictly for protocol interaction.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .exceptions import (
    AylaAuthenticationError,
    AylaConnectivityError,
    AylaProtocolError,
    AylaRateLimitError,
)

_LOGGER = logging.getLogger(__name__)

AYLA_APP_ID = "ecowater-mobile-id"
AYLA_APP_SECRET = "ecowater-mobile-9026832"  # noqa: S105

REGION_US = "us"
REGION_EU = "eu"

URL_BASES = {
    REGION_US: {
        "user": "https://user-field.aylanetworks.com",
        "ads": "https://ads-field.aylanetworks.com",
    },
    REGION_EU: {
        "user": "https://user-field-eu.aylanetworks.com",
        "ads": "https://ads-eu.aylanetworks.com",
    },
}

DEFAULT_TIMEOUT = 10.0


class AylaApi:
    """Async client for Ayla Networks API."""

    def __init__(self, session: ClientSession, region: str = REGION_US) -> None:
        """Initialise the API client."""
        self._session = session
        self._region = region
        self._user_url = URL_BASES[region]["user"]
        self._ads_url = URL_BASES[region]["ads"]

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        # We don't automatically retry authentication, but we keep state.

    @property
    def _auth_headers(self) -> dict[str, str]:
        """Headers required for authenticated requests."""
        if not self._access_token:
            raise AylaAuthenticationError(
                "Not authenticated; no access token available"
            )
        return {"Authorization": f"auth_token {self._access_token}"}

    async def _async_request(
        self, method: str, url: str, authenticate: bool = True, **kwargs: Any
    ) -> dict[str, Any] | list[Any]:
        """Perform an HTTP request and handle Ayla-specific error mapping."""
        headers = kwargs.pop("headers", {})
        if authenticate:
            headers.update(self._auth_headers)

        # Merge bounded timeout. We don't override if caller explicitly passed one.
        if "timeout" not in kwargs:
            kwargs["timeout"] = DEFAULT_TIMEOUT

        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                if response.status == 401:
                    raise AylaAuthenticationError(
                        "Authentication rejected by Ayla API (HTTP 401)"
                    )
                if response.status == 404:
                    if url.endswith("sign_in.json"):
                        raise AylaAuthenticationError(
                            "Authentication rejected by Ayla API (HTTP 404)"
                        )
                    raise AylaProtocolError("HTTP error 404: Resource not found")

                if response.status == 429:
                    raise AylaRateLimitError("Ayla API rate limit exceeded")

                response.raise_for_status()

                # Some endpoints (like sign_out) might return empty 204 or no JSON
                if response.status == 204:
                    return {}

                try:
                    from typing import cast

                    return cast("dict[str, Any] | list[Any]", await response.json())
                except ValueError as ex:
                    raise AylaProtocolError(f"Malformed JSON response: {ex}") from ex

        except ClientResponseError as ex:
            # Catch HTTP errors not handled above
            raise AylaProtocolError(f"HTTP error {ex.status}: {ex.message}") from ex
        except ClientError as ex:
            # Network-level connectivity errors or timeouts
            raise AylaConnectivityError(f"Connection failed: {ex}") from ex
        except TimeoutError as ex:
            raise AylaConnectivityError("Request timed out") from ex

    async def async_authenticate(self, email: str, password: str) -> None:
        """Authenticate with the Ayla API."""
        _LOGGER.debug("Authenticating with Ayla API for account (email redacted)")
        url = f"{self._user_url}/users/sign_in.json"

        payload = {
            "user": {
                "email": email,
                "password": password,
                "application": {
                    "app_id": AYLA_APP_ID,
                    "app_secret": AYLA_APP_SECRET,
                },
            }
        }

        response = await self._async_request(
            "POST", url, authenticate=False, json=payload
        )

        if not isinstance(response, dict) or "access_token" not in response:
            raise AylaProtocolError("Invalid authentication response format")

        self._access_token = response["access_token"]
        self._refresh_token = response.get("refresh_token")

        _LOGGER.debug("Successfully authenticated with Ayla API")

    async def async_list_devices(self) -> list[dict[str, Any]]:
        """List all devices available to the authenticated account."""
        _LOGGER.debug("Fetching device list from Ayla API")
        url = f"{self._ads_url}/apiv1/devices.json"
        response = await self._async_request("GET", url)

        if not isinstance(response, list):
            raise AylaProtocolError("Expected a list of devices")

        # Ayla wraps devices: [{"device": {...}}, {"device": {...}}]
        devices = []
        for item in response:
            if isinstance(item, dict) and "device" in item:
                devices.append(item["device"])
            else:
                raise AylaProtocolError("Malformed device entry in list")

        _LOGGER.debug("Found %d device(s)", len(devices))
        return devices

    async def async_get_device_properties(self, dsn: str) -> list[dict[str, Any]]:
        """Fetch all properties for a specific device serial number (DSN)."""
        _LOGGER.debug("Fetching properties for device (DSN redacted)")
        url = f"{self._ads_url}/apiv1/dsns/{dsn}/properties.json"
        response = await self._async_request("GET", url)

        if not isinstance(response, list):
            raise AylaProtocolError("Expected a list of properties")

        # Ayla wraps properties: [{"property": {...}}, {"property": {...}}]
        properties = []
        for item in response:
            if isinstance(item, dict) and "property" in item:
                properties.append(item["property"])
            else:
                raise AylaProtocolError("Malformed property entry in list")

        return properties

    async def async_clear_authentication(self) -> None:
        """Sign out and clear internal token state."""
        _LOGGER.debug("Signing out of Ayla API")
        if not self._access_token:
            return

        url = f"{self._user_url}/users/sign_out.json"
        payload = {"user": {"access_token": self._access_token}}

        try:
            # We don't care if sign-out fails on the server, we just want to attempt it.
            await self._async_request("POST", url, json=payload)
        except (
            AylaConnectivityError,
            AylaProtocolError,
            AylaAuthenticationError,
            AylaRateLimitError,
        ) as ex:
            _LOGGER.debug("Sign out request failed, ignoring: %s", ex)
        finally:
            self._access_token = None
            self._refresh_token = None
