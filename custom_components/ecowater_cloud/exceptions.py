"""Exception taxonomy for the EcoWater Cloud integration.

All integration-specific exceptions derive from :class:`EcoWaterError`.
Callers must catch specific subclasses; catching the base class is only
appropriate at integration boundaries (e.g. coordinator → UpdateFailed).

Hierarchy
---------
EcoWaterError
├── AuthenticationError        — 401 / bad credentials
├── ReauthenticationRequired   — session invalid, password changed
├── ConnectivityError          — network unreachable, timeout, DNS failure
├── RateLimitError             — 429 Too Many Requests
├── ProtocolError              — unexpected response shape / parse failure
├── UnsupportedDeviceError     — device type cannot be mapped to DeviceSnapshot
└── CommandError               — cloud rejected a write/command request
"""


class EcoWaterError(Exception):
    """Base class for all EcoWater Cloud integration errors."""


class AuthenticationError(EcoWaterError):
    """Raised when the cloud rejects the supplied credentials (HTTP 401).

    Triggers an automatic reauth flow in Home Assistant.
    """


class ReauthenticationRequired(EcoWaterError):
    """Raised when the current session is permanently invalid.

    This differs from :class:`AuthenticationError` in that the stored
    credentials themselves are likely still valid — the session token has
    been invalidated (e.g. after a password change on another client).
    Handling is identical to :class:`AuthenticationError` from HA's
    perspective: trigger the reauth flow.
    """


class ConnectivityError(EcoWaterError):
    """Raised when the cloud cannot be reached.

    Covers: TCP connection refused, DNS resolution failure, TLS errors,
    and request timeouts. The integration should mark all entities as
    unavailable and retry on the next poll cycle.
    """


class RateLimitError(EcoWaterError):
    """Raised when the cloud returns HTTP 429 Too Many Requests."""


class ProtocolError(EcoWaterError):
    """Raised when a cloud response cannot be parsed or is structurally unexpected.

    The raw error message is stored in ``args[0]``. Sensitive values (tokens,
    email addresses) must be stripped from the message before raising.
    """


class UnsupportedDeviceError(EcoWaterError):
    """Raised when a device cannot be mapped to a :class:`~.models.DeviceSnapshot`.

    The coordinator skips the device and continues loading all other devices
    rather than failing the whole account update.

    Attributes
    ----------
    serial_number : str | None
        The device's serial number or DSN if known at raise time.
    """

    def __init__(self, message: str, serial_number: str | None = None) -> None:
        super().__init__(message)
        self.serial_number = serial_number


class CommandError(EcoWaterError):
    """Raised when the cloud rejects a write or command request.

    Includes the HTTP status code and a sanitized description from the
    response body when available.

    Attributes
    ----------
    status : int | None
        HTTP status code returned by the cloud, if applicable.
    """

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
