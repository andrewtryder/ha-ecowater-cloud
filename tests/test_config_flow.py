"""Test the EcoWater Cloud config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ecowater_cloud.const import (
    BACKEND_AYLA,
    CONF_POLLING_INTERVAL,
    DOMAIN,
)
from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    ConnectivityError,
    RateLimitError,
)

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "test-password"


@pytest.mark.asyncio
async def test_form_user(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test we get the form and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

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
                "username": MOCK_USERNAME,
                "password": MOCK_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "EcoWater Cloud"
    assert result2["data"] == {
        "backend": BACKEND_AYLA,
        "username": "test@example.com",
        "password": MOCK_PASSWORD,
        "region": "us",
    }
    mock_setup_entry.assert_awaited_once()


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
        minor_version=3,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={
            "backend": BACKEND_AYLA,
            "username": MOCK_USERNAME,
            "password": MOCK_PASSWORD,
            "region": "us",
        },
        source="user",
        options={},
        unique_id=f"ayla:us:{MOCK_USERNAME}",
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
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
        minor_version=3,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={
            "backend": BACKEND_AYLA,
            "username": MOCK_USERNAME,
            "password": MOCK_PASSWORD,
            "region": "us",
        },
        source="user",
        options={},
        unique_id=f"ayla:us:{MOCK_USERNAME}",
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

    with (
        patch(
            "custom_components.ecowater_cloud.config_flow.AylaBackend",
            return_value=mock_ayla_backend,
        ),
        patch(
            "custom_components.ecowater_cloud.async_setup_entry",
            return_value=True,
        ),
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
        minor_version=3,
        domain=DOMAIN,
        title="EcoWater Cloud",
        data={
            "backend": BACKEND_AYLA,
            "username": MOCK_USERNAME,
            "password": MOCK_PASSWORD,
            "region": "us",
        },
        source="user",
        options={},
        unique_id=f"ayla:us:{MOCK_USERNAME}",
        discovery_keys={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_POLLING_INTERVAL: 15,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_POLLING_INTERVAL: 15,
    }


@pytest.mark.asyncio
async def test_reauth_confirm_exceptions(hass: HomeAssistant) -> None:
    """Test reauth confirm handles exceptions."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ecowater_cloud.exceptions import (
        AuthenticationError,
        ConnectivityError,
        RateLimitError,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: "old-password"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": "reauth",
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )

    exceptions = [
        (AuthenticationError("auth"), "invalid_auth"),
        (ConnectivityError("conn"), "cannot_connect"),
        (RateLimitError("rate"), "rate_limit"),
        (ValueError("unknown"), "unknown"),
    ]

    for exc, expected_error in exceptions:
        with patch(
            "custom_components.ecowater_cloud.config_flow.validate_input",
            side_effect=exc,
        ):
            res = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {"password": "new-password"},
            )
            assert res["type"] is FlowResultType.FORM
            assert res["errors"]["base"] == expected_error
