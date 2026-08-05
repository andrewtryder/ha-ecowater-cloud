"""Raw data models for the Ayla backend responses.

These models map 1:1 to the JSON payloads returned by the Ayla API.
"""

from typing import TypedDict


class AylaDeviceData(TypedDict, total=False):
    """Inner dictionary for a device in the Ayla devices endpoint."""

    dsn: str
    product_name: str
    oem_model: str
    mac: str
    lan_ip: str
    connection_status: str


class AylaDeviceDict(TypedDict):
    """Wrapper dictionary for an Ayla device."""

    device: AylaDeviceData


class AylaPropertyData(TypedDict, total=False):
    """Inner dictionary for a property in the Ayla properties endpoint."""

    name: str
    value: int | float | str | None
    data_updated_at: str
    type: str


class AylaPropertyDict(TypedDict):
    """Wrapper dictionary for an Ayla property."""

    property: AylaPropertyData
