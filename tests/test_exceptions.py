"""Tests for the EcoWater Cloud exception taxonomy."""

from __future__ import annotations

import pytest

from custom_components.ecowater_cloud.backends.ayla.exceptions import (
    AylaAuthenticationError,
    AylaConnectivityError,
    AylaProtocolError,
    AylaRateLimitError,
)
from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    CommandError,
    ConnectivityError,
    EcoWaterError,
    ProtocolError,
    RateLimitError,
    ReauthenticationRequired,
    UnsupportedDeviceError,
)


class TestBaseException:
    def test_instantiable_with_message(self) -> None:
        err = EcoWaterError("something went wrong")
        assert str(err) == "something went wrong"

    def test_is_exception(self) -> None:
        assert issubclass(EcoWaterError, Exception)


class TestHierarchy:
    """All subclasses must be catchable as EcoWaterError."""

    @pytest.mark.parametrize(
        "cls",
        [
            AuthenticationError,
            ReauthenticationRequired,
            ConnectivityError,
            RateLimitError,
            ProtocolError,
            UnsupportedDeviceError,
            CommandError,
        ],
    )
    def test_subclass_of_ecowater_error(self, cls: type[EcoWaterError]) -> None:
        assert issubclass(cls, EcoWaterError)

    @pytest.mark.parametrize(
        "cls",
        [
            AuthenticationError,
            ReauthenticationRequired,
            ConnectivityError,
            RateLimitError,
            ProtocolError,
            UnsupportedDeviceError,
            CommandError,
        ],
    )
    def test_raiseable_and_catchable(self, cls: type[EcoWaterError]) -> None:
        with pytest.raises(EcoWaterError):
            raise cls("test")


class TestUnsupportedDeviceError:
    def test_serial_number_attribute_default_none(self) -> None:
        err = UnsupportedDeviceError("unsupported")
        assert err.serial_number is None

    def test_serial_number_attribute_set(self) -> None:
        err = UnsupportedDeviceError("unsupported", serial_number="DSN123")
        assert err.serial_number == "DSN123"

    def test_message_preserved(self) -> None:
        err = UnsupportedDeviceError(
            "device type XYZ not supported", serial_number="X1"
        )
        assert "XYZ" in str(err)


class TestCommandError:
    def test_status_attribute_default_none(self) -> None:
        err = CommandError("rejected")
        assert err.status is None

    def test_status_attribute_set(self) -> None:
        err = CommandError("rejected", status=400)
        assert err.status == 400


class TestAylaExceptions:
    """Ayla exceptions must subclass the base taxonomy."""

    def test_ayla_auth_is_authentication_error(self) -> None:
        assert issubclass(AylaAuthenticationError, AuthenticationError)

    def test_ayla_connectivity_is_connectivity_error(self) -> None:
        assert issubclass(AylaConnectivityError, ConnectivityError)

    def test_ayla_protocol_is_protocol_error(self) -> None:
        assert issubclass(AylaProtocolError, ProtocolError)

    def test_ayla_rate_limit_is_rate_limit_error(self) -> None:
        assert issubclass(AylaRateLimitError, RateLimitError)

    def test_ayla_auth_catchable_as_ecowater_error(self) -> None:
        with pytest.raises(EcoWaterError):
            raise AylaAuthenticationError("bad creds")
