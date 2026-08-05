"""Tests for Ayla data normalization."""

import datetime
import json
from pathlib import Path

from custom_components.ecowater_cloud.backends.ayla.models import (
    AylaDeviceData,
    AylaPropertyData,
)
from custom_components.ecowater_cloud.backends.ayla.normalization import (
    normalize_device,
)


def load_fixture(name: str) -> dict:
    """Load a JSON fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "ayla" / name
    return json.loads(fixture_path.read_text())


def test_normalize_synthetic_device():
    """Test normalization of a fully-featured synthetic device."""
    data = load_fixture("synthetic_device.json")
    dev: AylaDeviceData = data["device"]
    props: list[AylaPropertyData] = [p["property"] for p in data["properties"]]
    received_at = datetime.datetime(2026, 8, 5, 12, 10, tzinfo=datetime.UTC)

    normalized = normalize_device(dev, props, received_at)

    assert normalized.descriptor.serial_number == "AC000W000123456"
    assert normalized.descriptor.model == "EWS3500"
    assert normalized.descriptor.model_id == "46904"
    assert normalized.descriptor.firmware_version == "V1.02"
    assert normalized.descriptor.is_online is True
    assert normalized.descriptor.wifi_signal_strength_dbm == -65

    # Water usage (no scaling)
    assert normalized.water_used_today_gallons == 150.0
    assert normalized.water_used_daily_avg_gallons == 200.0
    assert normalized.water_available_gallons == 1500.0
    assert normalized.total_water_used_gallons == 15000.0

    # Current flow (divide by 10)
    assert normalized.current_flow_gpm == 2.5

    # Salt
    assert normalized.salt_type == "NaCl"
    assert normalized.salt_level_raw == 40.0
    # Model 46904 max tenths is 80. (40 * 100) / 80 = 50.0%
    assert normalized.salt_level_percent == 50.0
    assert normalized.days_until_out_of_salt == 30
    assert normalized.estimated_out_of_salt_date == datetime.date(2026, 9, 4)

    # Rock (scaling)
    assert normalized.rock_removed_lbs == 105.0  # 1050 / 10
    assert normalized.rock_removed_daily_avg_lbs == 2.5  # 25000 / 10000

    # Regeneration
    assert normalized.regeneration.status == "None"
    assert normalized.regeneration.is_enabled is True
    assert normalized.regeneration.days_since_last == 5
    assert normalized.regeneration.estimated_last_date == datetime.date(2026, 7, 31)

    # Freshness
    assert normalized.freshness.received_at == received_at
    assert normalized.freshness.oldest_data_at == datetime.datetime(2026, 8, 5, 10, 0, tzinfo=datetime.UTC)
    assert normalized.freshness.newest_data_at == datetime.datetime(2026, 8, 5, 12, 6, tzinfo=datetime.UTC)

    # Capabilities
    assert normalized.capabilities.has_water_usage is True
    assert normalized.capabilities.has_flow_sensor is True
    assert normalized.capabilities.has_salt_sensor is True
    assert normalized.capabilities.has_rock_sensor is True


def test_normalize_edge_cases():
    """Test normalization with missing fields, nulls, invalid types, and unknown salt models."""
    dev: AylaDeviceData = {
        "dsn": "AC0001",
        # Missing model and status
    }
    props: list[AylaPropertyData] = [
        {"name": "gallons_used_today", "value": None, "data_updated_at": "2026-08-05T12:00:00Z", "type": "integer"},
        {"name": "current_water_flow_gpm", "value": "invalid", "data_updated_at": "invalid-time", "type": "integer"},
        {"name": "salt_level_tenths", "value": "40.5", "data_updated_at": "2026-08-05T12:00:00Z", "type": "string"},
        {"name": "model_id", "value": "99999", "data_updated_at": "2026-08-05T12:00:00Z", "type": "string"},
    ]
    received_at = datetime.datetime(2026, 8, 5, 12, 10, tzinfo=datetime.UTC)

    normalized = normalize_device(dev, props, received_at)

    # Missing string fields fallback gracefully
    assert normalized.descriptor.model == "Unknown Model"
    assert normalized.descriptor.is_online is None

    # Missing / Null values
    assert normalized.water_used_today_gallons is None

    # Type conversion errors
    assert normalized.current_flow_gpm is None

    # String numeric conversion
    assert normalized.salt_level_raw == 40.5

    # Unknown salt model id (99999 is not in SALT_TENTHS_MAX)
    assert normalized.salt_level_percent is None

    # Timestamps skipping invalid
    assert normalized.freshness.oldest_data_at == datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC)

    # Capabilities
    assert normalized.capabilities.has_water_usage is True
    assert normalized.capabilities.has_flow_sensor is True
    assert normalized.capabilities.has_salt_sensor is True
    assert normalized.capabilities.has_rock_sensor is False


def test_missing_property_name():
    """Test that properties without a name are safely ignored."""
    dev: AylaDeviceData = {"dsn": "A"}
    props: list[AylaPropertyData] = [{"value": 100}]  # type: ignore[typeddict-item]
    received_at = datetime.datetime(2026, 8, 5, 12, 10, tzinfo=datetime.UTC)

    normalized = normalize_device(dev, props, received_at)
    assert normalized.water_used_today_gallons is None
