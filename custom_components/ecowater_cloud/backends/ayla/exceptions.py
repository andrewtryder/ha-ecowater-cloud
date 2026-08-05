"""Ayla-specific exceptions.

These are raised internally within the Ayla backend adapter and are
re-raised as (or mapped to) the integration's base exception taxonomy
before they leave the ``backends/ayla`` package.

In most cases the Ayla adapter catches these, performs any sanitisation
needed (e.g. stripping token values from error messages), and re-raises the
appropriate base class from
:mod:`~custom_components.ecowater_cloud.exceptions`.
"""

from custom_components.ecowater_cloud.exceptions import (
    AuthenticationError,
    ConnectivityError,
    ProtocolError,
    RateLimitError,
)

__all__ = [
    "AylaAuthenticationError",
    "AylaConnectivityError",
    "AylaProtocolError",
    "AylaRateLimitError",
]


class AylaAuthenticationError(AuthenticationError):
    """Raised when the Ayla user-service rejects the supplied credentials."""


class AylaConnectivityError(ConnectivityError):
    """Raised when the Ayla service endpoints cannot be reached."""


class AylaProtocolError(ProtocolError):
    """Raised when an Ayla API response is invalid or structurally unexpected."""


class AylaRateLimitError(RateLimitError):
    """Raised when the Ayla API returns HTTP 429."""
