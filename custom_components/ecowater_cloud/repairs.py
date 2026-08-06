"""Home Assistant Repairs support for the EcoWater Cloud integration.

Creates and resolves HA Repairs issues for conditions that require user attention,
such as authentication failures, no recognized devices, unknown salt models,
stale cloud data, and unexpected protocol changes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)

from .const import DOMAIN, STALE_DATA_THRESHOLD
from .coordinator import CoordinatorErrorCategory

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import AccountCoordinator

_LOGGER = logging.getLogger(__name__)


def async_register_repairs(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    """Register a coordinator listener that creates/resolves Repairs issues.

    Must be called after the coordinator's first successful refresh.
    """

    @callback_safe
    def _update_repairs() -> None:
        _check_auth_rejected(hass, entry, coordinator)
        _check_no_devices(hass, entry, coordinator)
        _check_unknown_salt_models(hass, entry, coordinator)
        _check_stale_data(hass, entry, coordinator)
        _check_protocol_changed(hass, entry, coordinator)

    # Run once immediately, then on every coordinator update.
    _update_repairs()
    entry.async_on_unload(coordinator.async_add_listener(_update_repairs))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def callback_safe(fn: Callable[[], None]) -> Callable[[], None]:
    """Thin wrapper so the listener does not propagate exceptions into HA core."""

    def _wrapped() -> None:
        try:
            fn()
        except Exception:
            _LOGGER.exception("Error while evaluating Repairs issues")

    return _wrapped


def _issue(
    hass: HomeAssistant,
    issue_id: str,
    severity: IssueSeverity,
    translation_placeholders: dict[str, str] | None = None,
) -> None:
    async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=severity,
        translation_key=issue_id,
        translation_placeholders=translation_placeholders or {},
    )


def _resolve(hass: HomeAssistant, issue_id: str) -> None:
    async_delete_issue(hass, DOMAIN, issue_id)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_auth_rejected(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    issue_id = "authentication_rejected"
    if coordinator.last_error_category == CoordinatorErrorCategory.AUTHENTICATION:
        _issue(hass, issue_id, IssueSeverity.ERROR)
    else:
        _resolve(hass, issue_id)


def _check_no_devices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    issue_id = "no_devices"
    data = coordinator.data
    # Only fire if we have a successful fetch (data is not None) but it's empty.
    if data is not None and len(data) == 0:
        _issue(hass, issue_id, IssueSeverity.WARNING)
    else:
        _resolve(hass, issue_id)


def _check_unknown_salt_models(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    issue_id = "unknown_salt_model"
    if coordinator.data is None:
        _resolve(hass, issue_id)
        return

    unmapped = [
        f"{d.descriptor.name} (model {d.descriptor.model_id})"
        for d in coordinator.data.values()
        if d.capabilities.has_unmapped_model
    ]
    if unmapped:
        _issue(
            hass,
            issue_id,
            IssueSeverity.WARNING,
            {"devices": ", ".join(unmapped)},
        )
    else:
        _resolve(hass, issue_id)


def _check_stale_data(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    """Create a Repairs issue if ANY device has stale source data."""
    issue_id = "data_stale"
    if coordinator.data is None:
        _resolve(hass, issue_id)
        return

    import datetime

    now = datetime.datetime.now(datetime.UTC)
    stale_devices = []
    for d in coordinator.data.values():
        newest = d.freshness.newest_data_at
        if newest is not None and (now - newest) > STALE_DATA_THRESHOLD:
            age_hours = int((now - newest).total_seconds() / 3600)
            stale_devices.append(f"{d.descriptor.name} ({age_hours}h ago)")

    if stale_devices:
        _issue(
            hass,
            issue_id,
            IssueSeverity.WARNING,
            {"devices": ", ".join(stale_devices)},
        )
    else:
        _resolve(hass, issue_id)


def _check_protocol_changed(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AccountCoordinator,
) -> None:
    issue_id = "protocol_changed"
    if coordinator.last_error_category == CoordinatorErrorCategory.PROTOCOL:
        _issue(hass, issue_id, IssueSeverity.ERROR)
    else:
        _resolve(hass, issue_id)
