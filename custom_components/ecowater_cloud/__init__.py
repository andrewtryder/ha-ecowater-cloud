"""The EcoWater Cloud integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .backends.ayla import AylaBackend
from .const import (
    BACKEND_AYLA,
    CONF_BACKEND,
    CONF_POLLING_INTERVAL,
    CONF_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    REGION_US,
)
from .coordinator import AccountCoordinator

_LOGGER = logging.getLogger(__name__)

type EcoWaterCloudConfigEntry = ConfigEntry[EcoWaterCloudData]


@dataclass
class EcoWaterCloudData:
    """Runtime data for the EcoWater Cloud integration."""

    coordinator: AccountCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: EcoWaterCloudConfigEntry
) -> bool:
    """Set up EcoWater Cloud from a config entry."""
    backend_id = entry.data.get(CONF_BACKEND, BACKEND_AYLA)

    if backend_id != BACKEND_AYLA:
        raise ConfigEntryError(
            f"Unsupported EcoWater backend: '{backend_id}'. "
            "Remove this entry and re-add with a supported backend."
        )

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    region = entry.data.get(CONF_REGION, REGION_US)

    session = async_get_clientsession(hass)

    backend = AylaBackend(session, username, password, region=region)

    polling_mins = entry.options.get(CONF_POLLING_INTERVAL)
    if polling_mins is not None:
        scan_interval = timedelta(minutes=polling_mins)
    else:
        scan_interval = DEFAULT_SCAN_INTERVAL

    coordinator = AccountCoordinator(
        hass=hass,
        backend=backend,
        entry_title=entry.title,
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = EcoWaterCloudData(coordinator=coordinator)

    # Register Repairs issue tracking (must happen after first refresh)
    from .repairs import async_register_repairs

    async_register_repairs(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EcoWaterCloudConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        new_data = {**entry.data}
        # Stamp backend as ayla if it doesn't exist (it should, but just in case)
        new_data.setdefault(CONF_BACKEND, BACKEND_AYLA)
        new_data.setdefault(CONF_REGION, REGION_US)

        hass.config_entries.async_update_entry(
            entry, data=new_data, version=2, minor_version=2
        )
    elif entry.version == 2 and entry.minor_version < 2:
        new_data = {**entry.data}
        new_data.setdefault(CONF_REGION, REGION_US)
        hass.config_entries.async_update_entry(
            entry, data=new_data, version=2, minor_version=2
        )
    if entry.version == 2 and entry.minor_version < 3:
        new_data = {**entry.data}
        region = new_data.setdefault(CONF_REGION, REGION_US)
        username = new_data.get(CONF_USERNAME, "").lower().strip()
        new_unique_id = f"{BACKEND_AYLA}:{region}:{username}"
        hass.config_entries.async_update_entry(
            entry, data=new_data, unique_id=new_unique_id, version=2, minor_version=3
        )
    if entry.version == 2 and entry.minor_version < 4:
        # Only the North America Ayla cloud has the EcoWater app registered, so
        # any stored non-US region (the former "eu" option) is rewritten to US.
        new_data = {**entry.data}
        migrated_unique_id: str | None = entry.unique_id
        if new_data.get(CONF_REGION) != REGION_US:
            new_data[CONF_REGION] = REGION_US
            username = new_data.get(CONF_USERNAME, "").lower().strip()
            candidate = f"{BACKEND_AYLA}:{REGION_US}:{username}"
            existing = hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, candidate
            )
            if existing is None or existing.entry_id == entry.entry_id:
                migrated_unique_id = candidate
            else:
                _LOGGER.warning(
                    "Another EcoWater Cloud entry already uses this account on "
                    "the North America server; keeping this entry's unique ID"
                )
        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            unique_id=migrated_unique_id,
            version=2,
            minor_version=4,
        )

    _LOGGER.info("Migration to version %s successful", entry.version)
    return True
