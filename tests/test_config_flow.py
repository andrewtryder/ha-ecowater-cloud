"""Tests for the EcoWater Cloud config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ecowater_cloud.const import (
    BACKEND_AYLA,
    BACKEND_HYDROLINK,
    CONF_BACKEND,
    CONF_POLLING_INTERVAL,
    CONF_REGION,
    DOMAIN,
)
from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    ConnectivityError,
    RateLimitError,
)
from tests.conftest import MOCK_PASSWORD, MOCK_USERNAME


@pytest.mark.asyncio
async def test_form_user_ayla(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test we get the form and create an entry via Ayla."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BACKEND: BACKEND_AYLA},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ayla"

    with (
        patch(
            "custom_components.ecowater_cloud.config_flow.AylaBackend",
            return_value=mock_ayla_backend,
        ),
        patch(
            "custom_components.ecowater_cloud.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": " Test@Example.com ",
                "password": MOCK_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "EcoWater Cloud"
    assert result2["data"] == {
        "backend": BACKEND_AYLA,
        "username": "test@example.com",  # Should be normalized
        "password": MOCK_PASSWORD,
    }
    mock_setup_entry.assert_awaited_once()


@pytest.mark.asyncio
async def test_form_user_hydrolink_not_implemented(hass: HomeAssistant) -> None:
    """Test we get the form and handle HydroLink not implemented error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BACKEND: BACKEND_HYDROLINK},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hydrolink"

    # HydroLinkBackend throws NotImplementedError on authenticate
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": MOCK_USERNAME,
            "password": MOCK_PASSWORD,
            CONF_REGION: "eu",
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "not_implemented"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "expected_error"),
    [
        (AuthenticationError("auth failed"), "invalid_auth"),
        (ConnectivityError("connect failed"), "cannot_connect"),
        (RateLimitError("too many requests"), "rate_limit"),
        (RuntimeError("unknown"), "unknown"),
    ],
)
async def test_form_user_errors(
    hass: HomeAssistant, exception: Exception, expected_error: str
) -> None:
    """Test we handle errors during user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BACKEND: BACKEND_AYLA},
    )

    with patch(
        "custom_components.ecowater_cloud.config_flow.AylaBackend",
    ) as mock_backend_cls:
        mock_backend = mock_backend_cls.return_value
        mock_backend.async_authenticate = AsyncMock(side_effect=exception)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": MOCK_PASSWORD,
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}


@pytest.mark.asyncio
async def test_form_user_no_devices(hass: HomeAssistant) -> None:
    """Test handling of an account with no supported devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BACKEND: BACKEND_AYLA},
    )

    with patch(
        "custom_components.ecowater_cloud.config_flow.AylaBackend",
    ) as mock_backend_cls:
        mock_backend = mock_backend_cls.return_value
        mock_backend.async_authenticate = AsyncMock(return_value=None)
        mock_backend.async_list_devices = AsyncMock(return_value=[])

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": MOCK_PASSWORD,
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "no_devices"}


@pytest.mark.asyncio
async def test_duplicate_account(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test duplicate account is aborted."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Pre-create entry
    entry = MockConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"backend": BACKEND_AYLA, "username": MOCK_USERNAME, "password": MOCK_PASSWORD},
        source="user",
        options={},
        unique_id=MOCK_USERNAME,
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BACKEND: BACKEND_AYLA},
    )

    with patch(
        "custom_components.ecowater_cloud.config_flow.AylaBackend",
        return_value=mock_ayla_backend,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": MOCK_PASSWORD,
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_reauth_flow(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test the reauth flow."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"backend": BACKEND_AYLA, "username": MOCK_USERNAME, "password": MOCK_PASSWORD},
        source="user",
        options={},
        unique_id=MOCK_USERNAME,
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "custom_components.ecowater_cloud.config_flow.AylaBackend",
        return_value=mock_ayla_backend,
    ), patch(
        "custom_components.ecowater_cloud.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "new-password"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data["password"] == "new-password"


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"backend": BACKEND_AYLA, "username": MOCK_USERNAME, "password": MOCK_PASSWORD},
        source="user",
        options={},
        unique_id=MOCK_USERNAME,
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_POLLING_INTERVAL: 15},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {CONF_POLLING_INTERVAL: 15}


@pytest.mark.asyncio
async def test_migration(hass: HomeAssistant) -> None:
    """Test migration from version 1 to version 2."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={"username": MOCK_USERNAME, "password": MOCK_PASSWORD},
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ecowater_cloud.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.version == 2
    assert entry.data["backend"] == "ayla"
