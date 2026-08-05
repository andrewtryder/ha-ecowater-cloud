# EcoWater Cloud — Architecture

## Overview

`ha-ecowater-cloud` is a Home Assistant custom integration that retrieves telemetry
from EcoWater cloud-connected water treatment devices. It is structured as a
multi-backend hub integration: one config entry = one cloud account; one coordinator
per account manages all physical devices associated with that account.

---

## Directory layout

```
ha-ecowater-cloud/
├── custom_components/
│   └── ecowater_cloud/
│       ├── __init__.py            # Entry-point: setup / teardown / migration
│       ├── manifest.json          # HA integration metadata
│       ├── const.py               # Domain, config keys, defaults
│       ├── exceptions.py          # Integration-wide exception taxonomy
│       ├── models.py              # Typed normalized device snapshot (frozen dataclass)
│       ├── coordinator.py         # AccountCoordinator (one per account)
│       ├── config_flow.py         # UI config flow + reauth flow
│       ├── strings.json           # UI string keys
│       ├── translations/
│       │   └── en.json            # English UI strings
│       └── backends/
│           ├── __init__.py        # BackendAdapter abstract protocol
│           └── ayla/
│               ├── __init__.py    # AylaBackend (async Ayla HTTP client)
│               └── exceptions.py  # Ayla-specific exceptions → base taxonomy
├── tests/
│   ├── conftest.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   ├── test_config_flow.py
│   └── test_coordinator.py
├── docs/
│   ├── requirements.md
│   └── architecture.md            # (this file)
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── validate.yml
├── AGENTS.md
├── README.md
├── hacs.json
└── pyproject.toml
```

---

## Layer responsibilities

- `app_id = "ecowater-mobile-id"`
- `app_secret = "ecowater-mobile-9026832"`
- user-supplied email + password

Retrieves device list from `https://ads.aylanetworks.com/apiv1/devices.json`.
Retrieves per-device properties from `https://ads.aylanetworks.com/apiv1/dsns/<dsn>/properties.json`.

Token refresh is handled transparently inside the backend.

### `models.py` — Normalized snapshots

`EcoWaterDeviceData` is a **frozen dataclass** that serves as the root telemetry object, wrapping granular sub-models: `DeviceDescriptor`, `DeviceCapabilities`, `DataFreshness`, and `RegenerationState`. It is the single contract between backends and the HA layer. Entities never import from `backends/`.

```
EcoWaterDeviceData
  descriptor: DeviceDescriptor
  capabilities: DeviceCapabilities
  freshness: DataFreshness
  regeneration: RegenerationState
  water_used_today_gallons: float | None
  water_used_daily_avg_gallons: float | None
  water_available_gallons: float | None
  total_water_used_gallons: float | None
  current_flow_gpm: float | None
  salt_level_raw: float | None
  salt_level_percent: float | None
  days_until_out_of_salt: int | None
  estimated_out_of_salt_date: datetime.date | None
  salt_type: str | None
  rock_removed_lbs: float | None
  rock_removed_daily_avg_lbs: float | None
```

### `exceptions.py` — Exception taxonomy

```
EcoWaterError                  # base
├── AuthenticationError        # 401 / bad credentials
├── ReauthenticationRequired   # password changed; session invalid
├── ConnectivityError          # network, timeout, DNS
├── RateLimitError             # 429
├── ProtocolError              # unexpected response shape
├── UnsupportedDeviceError     # device not mappable to DeviceSnapshot
└── CommandError               # write rejected by cloud
```

Callers catch specific exceptions. `ProtocolError` wraps the raw message without
leaking token values.

### `coordinator.py` — AccountCoordinator

`AccountCoordinator(DataUpdateCoordinator[AccountInfo])` is
instantiated once per config entry (= once per account). Its `data` attribute
is an `AccountInfo` containing a `devices` dict keyed by serial number.

- `_async_update_data` calls the backend adapter.
- On `AuthenticationError` → raises `ConfigEntryAuthFailed` (triggers HA reauth).
- On `ConnectivityError` → raises `UpdateFailed`.
- On `UnsupportedDeviceError` for a single device → logs a warning and continues
  updating remaining devices; that device's previous snapshot is preserved.

### `config_flow.py` — Configuration UI

Schema version 1. Steps:

| Step | Trigger | Action |
|------|---------|--------|
| `user` | New setup | Collect username + password; create entry |
| `reauth_confirm` | `async_step_reauth` | Collect new password; update entry |

Credentials are stored in `entry.data` (encrypted by HA).

### `__init__.py` — Entry-point

```python
type EcoWaterCloudConfigEntry = ConfigEntry[EcoWaterCloudData]


@dataclass
class EcoWaterCloudData:
    coordinator: AccountCoordinator
```

`async_setup_entry`:
1. Reads `entry.data["backend"]` to select adapter (currently always `"ayla"`).
2. Creates `AccountCoordinator`.
3. Calls `coordinator.async_config_entry_first_refresh()`.
4. Stores `EcoWaterCloudData` in `entry.runtime_data`.
5. Calls `async_forward_entry_setups(entry, PLATFORMS)`.

`async_unload_entry`: calls `async_unload_platforms`.

`async_migrate_entry`: handles version upgrades; version 1 → stub (no-op).

---

## Identifier policy

```python
# Device registry key
(DOMAIN, f"{backend}:{serial_number}")

# Entity unique_id
f"{backend}_{serial_number}_{entity_key}".lower()
```

No email, password, token, or mutable display name ever appears in an identifier.

---

## Polling strategy

Default interval: **30 minutes** (`timedelta(minutes=30)`).

The old integration attempted a "force refresh" by posting to the `get_frequent_data`
Ayla property and then sleeping 30 seconds. This is incompatible with async design.
Stage 2 will evaluate whether a non-blocking version is safe and worth implementing.

---

## Backend extensibility

Adding the future `hydrolink` backend requires:

1. `backends/hydrolink/__init__.py` implementing `BackendAdapter`.
2. A new value `"hydrolink"` in `SUPPORTED_BACKENDS`.
3. `async_migrate_entry` handling any config-entry schema changes.
4. No changes to `coordinator.py`, `models.py`, or entities.

---

## Protocol uncertainties (to be resolved in Stage 2)

- Exact token refresh endpoint and TTL for the Ayla backend.
- Whether `get_frequent_data` / force-refresh is safe without `time.sleep`.
- Field presence variability across different EcoWater model numbers.
- Unit system returned by the Ayla API (assumed gallons/lbs; metric variants unknown).
- Whether the DSN serves as the stable serial number for all device types.
