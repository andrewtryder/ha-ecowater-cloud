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
    ApplicationNotFoundError,
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
        (ApplicationNotFoundError("no app"), "application_not_found"),
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
        (ApplicationNotFoundError("no app"), "application_not_found"),
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


@pytest.mark.asyncio
async def test_form_user_rejects_eu_region(hass: HomeAssistant) -> None:
    """The removed EU region is no longer accepted by the user step."""
    from homeassistant.data_entry_flow import InvalidData

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": MOCK_PASSWORD,
                "region": "eu",
            },
        )


@pytest.mark.asyncio
async def test_reconfigure_flow(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test reconfigure moves a legacy EU entry to the North America server."""
    from homeassistant.config_entries import SOURCE_RECONFIGURE
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
            "region": "eu",
        },
        source="user",
        unique_id=f"ayla:eu:{MOCK_USERNAME}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

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
            {
                "username": MOCK_USERNAME,
                "password": "new-password",
                "region": "us",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data["username"] == MOCK_USERNAME
    assert entry.data["password"] == "new-password"
    assert entry.data["region"] == "us"
    assert entry.unique_id == f"ayla:us:{MOCK_USERNAME}"


@pytest.mark.asyncio
async def test_reconfigure_same_region_password(
    hass: HomeAssistant, mock_ayla_backend
) -> None:
    """Test reconfigure updates password when region is unchanged."""
    from homeassistant.config_entries import SOURCE_RECONFIGURE
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
        unique_id=f"ayla:us:{MOCK_USERNAME}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

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
            {
                "username": MOCK_USERNAME,
                "password": "new-password",
                "region": "us",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data["password"] == "new-password"
    assert entry.data["region"] == "us"
    assert entry.unique_id == f"ayla:us:{MOCK_USERNAME}"


@pytest.mark.asyncio
async def test_reconfigure_account_mismatch(hass: HomeAssistant) -> None:
    """Test reconfigure fails when switching account email."""
    from homeassistant.config_entries import SOURCE_RECONFIGURE
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: "old-password",
            "region": "us",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
        data=entry.data,
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "different@example.com",
            "password": "new-password",
            "region": "us",
        },
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "account_mismatch"


@pytest.mark.asyncio
async def test_reconfigure_errors(hass: HomeAssistant) -> None:
    """Test reconfigure handles errors."""
    from homeassistant.config_entries import SOURCE_RECONFIGURE
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: "old-password",
            "region": "us",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    with patch(
        "custom_components.ecowater_cloud.config_flow.validate_input",
        side_effect=AuthenticationError("auth"),
    ):
        res = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": "wrong-password",
                "region": "us",
            },
        )
        assert res["type"] is FlowResultType.FORM
        assert res["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_reconfigure_duplicate(hass: HomeAssistant, mock_ayla_backend) -> None:
    """Test reconfigure duplicate account is aborted."""
    from homeassistant.config_entries import SOURCE_RECONFIGURE
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry1 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: "pw", "region": "us"},
        unique_id=f"ayla:us:{MOCK_USERNAME}",
    )
    entry1.add_to_hass(hass)

    # A legacy EU entry for the same account cannot move onto entry1's server.
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: "pw", "region": "eu"},
        unique_id=f"ayla:eu:{MOCK_USERNAME}",
    )
    entry2.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry2.entry_id,
        },
    )

    with patch(
        "custom_components.ecowater_cloud.config_flow.AylaBackend",
        return_value=mock_ayla_backend,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": MOCK_USERNAME,
                "password": "new-password",
                "region": "us",
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


def test_schema_compatibility_and_validation() -> None:
    """Test _as_form_schema helper and schema validation semantics."""
    import voluptuous as vol

    from custom_components.ecowater_cloud.config_flow import (
        STEP_USER_DATA_SCHEMA,
        _as_form_schema,
    )

    # Verify _as_form_schema returns the identical schema object
    schema = vol.Schema({vol.Required("test"): str})
    wrapped = _as_form_schema(schema)
    assert wrapped is schema
    assert wrapped({"test": "value"}) == {"test": "value"}
    with pytest.raises(vol.Invalid):
        wrapped({"test": 123})

    # Verify STEP_USER_DATA_SCHEMA accepts valid and rejects invalid inputs
    user_schema = _as_form_schema(STEP_USER_DATA_SCHEMA)
    valid_data = user_schema(
        {
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "secret-password",
            "region": "us",
        }
    )
    assert valid_data[CONF_USERNAME] == "user@example.com"
    assert valid_data["region"] == "us"

    with pytest.raises(vol.Invalid):
        user_schema({CONF_USERNAME: "user@example.com"})
