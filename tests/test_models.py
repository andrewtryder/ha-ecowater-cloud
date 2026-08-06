"""Tests for the normalized models."""

import datetime

import pytest

from custom_components.ecowater_cloud.models import (
    DataFreshness,
    DeviceCapabilities,
    DeviceDescriptor,
    EcoWaterDeviceData,
    RegenerationState,
)
from tests.conftest import (
    BACKEND_AYLA,
    MOCK_SERIAL,
    make_full_device_snapshot,
)


class TestEcoWaterDeviceDataConstruction:
    def test_full_snapshot(self) -> None:
        snap = make_full_device_snapshot()
        assert snap.descriptor.model == "EcoWater ERR3700R"
        assert snap.salt_level_percent == 75.0
        assert snap.freshness.received_at is not None
        assert snap.freshness.received_at.tzinfo is not None


class TestEcoWaterDeviceDataImmutability:
    def test_frozen(self) -> None:
        snap = make_full_device_snapshot()
        with pytest.raises((AttributeError, TypeError)):
            snap.salt_level_percent = 50.0  # type: ignore[misc]

    def test_frozen_descriptor(self) -> None:
        snap = make_full_device_snapshot()
        with pytest.raises((AttributeError, TypeError)):
            snap.descriptor.model = "should fail"  # type: ignore[misc]


class TestEcoWaterDeviceDataValidation:
    def test_naive_datetime_raises(self) -> None:
        naive_dt = datetime.datetime(2026, 1, 1, 12, 0, 0)  # no tzinfo
        with pytest.raises(ValueError, match="timezone-aware"):
            EcoWaterDeviceData(
                descriptor=DeviceDescriptor(
                    backend=BACKEND_AYLA,
                    backend_id=MOCK_SERIAL,
                    serial_number=MOCK_SERIAL,
                    name="Test",
                    model="Test Model",
                ),
                capabilities=DeviceCapabilities(*[True] * 17),
                freshness=DataFreshness(received_at=naive_dt),
                regeneration=RegenerationState(status="None"),
            )

    def test_salt_level_above_100_raises(self) -> None:
        with pytest.raises(ValueError, match="salt_level_percent"):
            EcoWaterDeviceData(
                descriptor=DeviceDescriptor(
                    backend=BACKEND_AYLA,
                    backend_id=MOCK_SERIAL,
                    serial_number=MOCK_SERIAL,
                    name="Test",
                    model="Test Model",
                ),
                capabilities=DeviceCapabilities(*[True] * 17),
                freshness=DataFreshness(
                    received_at=datetime.datetime.now(datetime.UTC)
                ),
                regeneration=RegenerationState(status="None"),
                salt_level_percent=101.0,
            )

    def test_salt_level_below_0_raises(self) -> None:
        with pytest.raises(ValueError, match="salt_level_percent"):
            EcoWaterDeviceData(
                descriptor=DeviceDescriptor(
                    backend=BACKEND_AYLA,
                    backend_id=MOCK_SERIAL,
                    serial_number=MOCK_SERIAL,
                    name="Test",
                    model="Test Model",
                ),
                capabilities=DeviceCapabilities(*[True] * 17),
                freshness=DataFreshness(
                    received_at=datetime.datetime.now(datetime.UTC)
                ),
                regeneration=RegenerationState(status="None"),
                salt_level_percent=-1.0,
            )

    def test_salt_level_boundary_values_ok(self) -> None:
        for val in (0.0, 50.0, 100.0):
            snap = EcoWaterDeviceData(
                descriptor=DeviceDescriptor(
                    backend=BACKEND_AYLA,
                    backend_id=MOCK_SERIAL,
                    serial_number=MOCK_SERIAL,
                    name="Test",
                    model="Test Model",
                ),
                capabilities=DeviceCapabilities(*[True] * 17),
                freshness=DataFreshness(
                    received_at=datetime.datetime.now(datetime.UTC)
                ),
                regeneration=RegenerationState(status="None"),
                salt_level_percent=val,
            )
            assert snap.salt_level_percent == val


class TestEcoWaterDeviceDataEquality:
    def test_equal_snapshots(self) -> None:
        a = make_full_device_snapshot()
        b = make_full_device_snapshot()
        assert a == b

    def test_different_serial_not_equal(self) -> None:
        a = make_full_device_snapshot()
        b_desc = DeviceDescriptor(
            backend=BACKEND_AYLA,
            backend_id="BBB",
            serial_number="BBB",
            name="Test",
            model="Test",
        )
        b = EcoWaterDeviceData(
            descriptor=b_desc,
            capabilities=a.capabilities,
            freshness=a.freshness,
            regeneration=a.regeneration,
        )
        assert a != b

    def test_hashable(self) -> None:
        snap = make_full_device_snapshot()
        # frozen dataclasses are hashable
        s: set[EcoWaterDeviceData] = {snap}
        assert snap in s
