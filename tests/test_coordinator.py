"""Tests for AccountCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ecowater_cloud.coordinator import AccountCoordinator
from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    ConnectivityError,
    ProtocolError,
    RateLimitError,
    ReauthenticationRequired,
)
from tests.conftest import MOCK_SERIAL


def _make_coordinator(
    hass: HomeAssistant,
    backend: MagicMock,
) -> AccountCoordinator:
    return AccountCoordinator(
        hass=hass,
        backend=backend,
        entry_title="test-account",
    )


class TestCoordinatorUpdate:
    async def test_returns_account_snapshot_on_success(
        self, hass: HomeAssistant, mock_ayla_backend: MagicMock
    ) -> None:
        coordinator = _make_coordinator(hass, mock_ayla_backend)
        result = await coordinator._async_update_data()
        assert MOCK_SERIAL in result

        dev = result[MOCK_SERIAL]
        assert dev.descriptor.serial_number == MOCK_SERIAL

    async def test_connectivity_error_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_get_all_device_data = AsyncMock(
            side_effect=ConnectivityError("network down")
        )
        coordinator = _make_coordinator(hass, backend)

        with pytest.raises(UpdateFailed, match="network down"):
            await coordinator._async_update_data()

    async def test_authentication_error_raises_config_entry_auth_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_get_all_device_data = AsyncMock(
            side_effect=AuthenticationError("bad token")
        )
        coordinator = _make_coordinator(hass, backend)

        with pytest.raises(ConfigEntryAuthFailed, match="bad token"):
            await coordinator._async_update_data()

    async def test_reauth_required_raises_config_entry_auth_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_get_all_device_data = AsyncMock(
            side_effect=ReauthenticationRequired("session expired")
        )
        coordinator = _make_coordinator(hass, backend)

        with pytest.raises(ConfigEntryAuthFailed, match="session expired"):
            await coordinator._async_update_data()

    async def test_rate_limit_error_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_get_all_device_data = AsyncMock(
            side_effect=RateLimitError("too many requests")
        )
        coordinator = _make_coordinator(hass, backend)

        with pytest.raises(UpdateFailed, match="EcoWater rate limit reached"):
            await coordinator._async_update_data()

    async def test_protocol_error_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_get_all_device_data = AsyncMock(
            side_effect=ProtocolError("bad payload")
        )
        coordinator = _make_coordinator(hass, backend)

        with pytest.raises(UpdateFailed, match="Unexpected EcoWater response"):
            await coordinator._async_update_data()


class TestCoordinatorSetup:
    """Tests for _async_setup (authentication before first refresh)."""

    async def test_setup_authenticates_backend(
        self, hass: HomeAssistant, mock_ayla_backend: MagicMock
    ) -> None:
        """_async_setup must call async_authenticate on the backend."""
        coordinator = _make_coordinator(hass, mock_ayla_backend)
        await coordinator._async_setup()
        mock_ayla_backend.async_authenticate.assert_awaited_once()

    async def test_setup_auth_error_raises_config_entry_auth_failed(
        self, hass: HomeAssistant
    ) -> None:
        backend = MagicMock()
        backend.async_authenticate = AsyncMock(
            side_effect=AuthenticationError("bad credentials")
        )
        coordinator = _make_coordinator(hass, backend)
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_setup()

    async def test_setup_connectivity_error_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        from custom_components.ecowater_cloud.exceptions import ConnectivityError

        backend = MagicMock()
        backend.async_authenticate = AsyncMock(
            side_effect=ConnectivityError("no network")
        )
        coordinator = _make_coordinator(hass, backend)
        with pytest.raises(UpdateFailed, match="Unable to connect"):
            await coordinator._async_setup()

    async def test_setup_rate_limit_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        from custom_components.ecowater_cloud.exceptions import RateLimitError

        backend = MagicMock()
        backend.async_authenticate = AsyncMock(side_effect=RateLimitError("slow down"))
        coordinator = _make_coordinator(hass, backend)
        with pytest.raises(UpdateFailed, match="rate limit"):
            await coordinator._async_setup()

    async def test_setup_protocol_error_raises_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        from custom_components.ecowater_cloud.exceptions import ProtocolError

        backend = MagicMock()
        backend.async_authenticate = AsyncMock(
            side_effect=ProtocolError("unexpected response")
        )
        coordinator = _make_coordinator(hass, backend)
        with pytest.raises(UpdateFailed, match="authentication response"):
            await coordinator._async_setup()


class TestCoordinatorConfiguration:
    def test_default_scan_interval_is_30_minutes(
        self, hass: HomeAssistant, mock_ayla_backend: MagicMock
    ) -> None:
        from datetime import timedelta

        coordinator = _make_coordinator(hass, mock_ayla_backend)
        assert coordinator.update_interval == timedelta(minutes=30)

    def test_custom_scan_interval(
        self, hass: HomeAssistant, mock_ayla_backend: MagicMock
    ) -> None:
        from datetime import timedelta

        coordinator = AccountCoordinator(
            hass=hass,
            backend=mock_ayla_backend,
            entry_title="test",
            scan_interval=timedelta(hours=1),
        )
        assert coordinator.update_interval == timedelta(hours=1)
