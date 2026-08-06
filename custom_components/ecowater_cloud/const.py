"""Constants for the EcoWater Cloud integration."""

import logging
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ecowater_cloud"
LOGGER = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Configuration Keys
CONF_BACKEND: Final = "backend"
CONF_REGION: Final = "region"
CONF_POLLING_INTERVAL: Final = "polling_interval_minutes"
CONF_FREQUENT_DATA_INTERVAL: Final = "frequent_data_interval"

# Supported Backends
BACKEND_AYLA: Final = "ayla"

SUPPORTED_BACKENDS: Final = [BACKEND_AYLA]

# Regions
REGION_US: Final = "us"
REGION_EU: Final = "eu"
SUPPORTED_REGIONS: Final = [REGION_US, REGION_EU]

# Polling defaults
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=30)
MIN_SCAN_INTERVAL: Final = timedelta(minutes=5)
MAX_SCAN_INTERVAL: Final = timedelta(hours=24)
