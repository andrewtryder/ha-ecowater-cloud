"""Normalized, immutable device data models for the EcoWater Cloud integration.

All backend adapters must convert their cloud-specific responses into
these normalized models before returning data to the coordinator.
No entity or coordinator code may import from ``backends/``.

Design notes
------------
- All models are **frozen dataclasses** — instances are immutable.
- All telemetry fields that can legitimately be missing are ``Optional``;
  an absent field means the cloud did not report a value for that property.
  Missing values must *never* be fabricated as zero.
- Date/Time fields are always timezone-aware (UTC) when they represent an exact instant.
- Volume fields are in **US gallons**; mass fields are in **pounds**. Unit
  conversion to SI is handled by Home Assistant entities.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DeviceDescriptor:
    """Basic identity and metadata for a device."""

    backend: str
    backend_id: str
    serial_number: str
    name: str
    model: str | None = field(default=None)
    oem_model: str | None = field(default=None)
    model_id: str | None = field(default=None)
    firmware_version: str | None = field(default=None)
    is_online: bool | None = field(default=None)
    wifi_signal_strength_dbm: int | None = field(default=None)


@dataclass(frozen=True, slots=True)
class DeviceCapabilities:
    """Flags indicating which features are present on this specific device."""

    has_water_usage_today: bool
    has_water_usage_daily_avg: bool
    has_water_available: bool
    has_total_water_used: bool
    has_flow_sensor: bool
    has_salt_sensor: bool
    has_rock_removed_daily_avg: bool
    has_rock_removed_since_regeneration: bool
    has_total_rock_removed: bool
    has_peak_flow: bool
    has_capacity_remaining: bool
    has_regen_time_remaining: bool
    has_valve_position: bool
    has_avg_days_between_regens: bool
    has_avg_salt_per_regen: bool
    has_total_regens: bool
    has_total_salt_used: bool
    has_low_salt_alert: bool
    has_depletion_alert: bool
    has_excessive_water_use_alert: bool
    has_flow_monitor_alert: bool
    has_service_reminder_alert: bool
    has_error_code_alert: bool
    has_error_code: bool


@dataclass(frozen=True, slots=True)
class DataFreshness:
    """Timestamps tracking the freshness of the device telemetry."""

    received_at: datetime.datetime
    oldest_data_at: datetime.datetime | None = field(default=None)
    newest_data_at: datetime.datetime | None = field(default=None)

    @property
    def age(self) -> datetime.timedelta:
        """The age of the data based on newest timestamp or received_at."""
        target = self.newest_data_at or self.received_at
        return self.received_at - target

    @property
    def is_stale(self) -> bool:
        """Return True if the data is older than 24 hours."""
        return self.age > datetime.timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class RegenerationState:
    """Telemetry related to device regeneration/recharge cycles."""

    status: str | None
    is_enabled: bool | None = field(default=None)
    days_since_last: int | None = field(default=None)
    estimated_last_date: datetime.date | None = field(default=None)


@dataclass(frozen=True, slots=True)
class EcoWaterDeviceData:
    """The root normalized telemetry payload for a single device."""

    descriptor: DeviceDescriptor
    capabilities: DeviceCapabilities
    freshness: DataFreshness
    regeneration: RegenerationState

    # --- Water Usage ---
    water_used_today_gallons: float | None = field(default=None)
    water_used_daily_avg_gallons: float | None = field(default=None)
    water_available_gallons: float | None = field(default=None)
    total_water_used_gallons: float | None = field(default=None)
    total_water_source_property: str | None = field(default=None)
    current_flow_gpm: float | None = field(default=None)

    # --- Salt & Rock ---
    salt_level_raw: float | None = field(default=None)
    salt_level_percent: float | None = field(default=None)
    days_until_out_of_salt: int | None = field(default=None)
    estimated_out_of_salt_date: datetime.date | None = field(default=None)
    salt_type: str | None = field(default=None)
    rock_removed_since_regeneration_lbs: float | None = field(default=None)
    total_rock_removed_lbs: float | None = field(default=None)
    rock_removed_daily_avg_lbs: float | None = field(default=None)

    # --- High-Value Advanced Metrics ---
    peak_water_flow_gpm: float | None = field(default=None)
    capacity_remaining_percent: float | None = field(default=None)
    regen_time_rem_secs: float | None = field(default=None)
    current_valve_position: str | None = field(default=None)
    avg_days_between_regens: float | None = field(default=None)
    avg_salt_per_regen_lbs: float | None = field(default=None)
    total_regens: int | None = field(default=None)
    total_salt_used_lbs: float | None = field(default=None)
    error_code: str | None = field(default=None)

    # --- Alerts ---
    low_salt_alert: bool | None = field(default=None)
    depletion_alert: bool | None = field(default=None)
    excessive_water_use_alert: bool | None = field(default=None)
    flow_monitor_alert: bool | None = field(default=None)
    service_reminder_alert: bool | None = field(default=None)
    error_code_alert: bool | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if self.salt_level_percent is not None and not (
            0.0 <= self.salt_level_percent <= 100.0
        ):
            raise ValueError(
                f"salt_level_percent must be in [0, 100], got {self.salt_level_percent}"
            )
        if self.freshness.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AccountInfo:
    """The full state of all devices belonging to an account."""

    devices: Mapping[str, EcoWaterDeviceData]
