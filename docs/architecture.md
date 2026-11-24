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
│       ├── diagnostics.py         # Diagnostics download handler
│       ├── repairs.py             # HA Repairs issue tracking
│       ├── translations/
│       │   └── en.json            # English UI strings
│       ├── entity.py              # Base entity
│       ├── sensor.py              # Sensor entity platform
│       ├── binary_sensor.py       # Binary sensor entity platform
│       └── backends/
│           ├── __init__.py        # BackendAdapter abstract protocol
│           └── ayla/
│               ├── __init__.py    # Re-exports AylaBackend
│               ├── api.py         # Async Ayla HTTP client (AylaApi)
│               ├── backend.py     # AylaBackend (BackendAdapter implementation)
│               ├── models.py      # Raw Ayla payload types
│               ├── normalization.py # Raw Ayla payloads → EcoWaterDeviceData
│               └── exceptions.py  # Ayla-specific exceptions → base taxonomy
├── tests/
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

### `backends/ayla/` — Ayla backend

Authenticates with:

- `app_id = "ecowater-mobile-id"`
- `app_secret = "ecowater-mobile-9026832"`
- user-supplied email + password

Retrieves device list from `{ads_url}/apiv1/devices.json`.
Retrieves per-device properties from `{ads_url}/apiv1/dsns/<dsn>/properties.json`.
`{ads_url}` depends on the region; see [protocol-ayla.md](protocol-ayla.md).

Token refresh is handled transparently inside the backend. If the refresh token
expires or is rejected, the backend automatically attempts full reauthentication
using the credentials saved in the config entry before prompting for user
reauthentication in Home Assistant.

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
├── UnsupportedDeviceError     # device not mappable to EcoWaterDeviceData
└── CommandError               # write rejected by cloud
```

Callers catch specific exceptions. `ProtocolError` wraps the raw message without
leaking token values.

### `coordinator.py` — AccountCoordinator

`AccountCoordinator(DataUpdateCoordinator[dict[str, EcoWaterDeviceData]])` is
instantiated once per config entry (= once per account). Its `data` attribute
is a dict keyed by serial number.

- `_async_update_data` calls the backend adapter.
- On `AuthenticationError` or `ReauthenticationRequired` → raises
  `ConfigEntryAuthFailed` (triggers HA reauth).
- On `ConnectivityError`, `RateLimitError`, or `ProtocolError` → raises
  `UpdateFailed`.
- The failure type is recorded in `last_error_category`, which `repairs.py` reads.

`UnsupportedDeviceError` for a single device is handled in the backend, which logs
a warning and continues with the remaining devices. The skipped device is absent
from that update, so its entities become unavailable.

### `config_flow.py` — Configuration UI

Schema version 2.3. Steps:

| Step | Trigger | Action |
|------|---------|--------|
| `user` | New setup | Collect username + password + region; create entry |
| `reauth_confirm` | `async_step_reauth` | Collect new password; update entry |
| `reconfigure` | `async_step_reconfigure` | Update password or region; a different email aborts with `account_mismatch` |

The options flow sets the polling interval. Credentials are stored in `entry.data`
(encrypted by HA).

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

`async_migrate_entry`: handles version upgrades to 2.3, stamping `backend` and
`region` and rewriting the entry unique ID to `ayla:{region}:{normalized_email}`.

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

---

## Protocol uncertainties (to be resolved in Stage 2)

- Exact token refresh endpoint and TTL for the Ayla backend.
- Whether `get_frequent_data` / force-refresh is safe without `time.sleep`.
- Field presence variability across different EcoWater model numbers.
- Unit system returned by the Ayla API (assumed gallons/lbs; metric variants unknown).
- Whether the DSN serves as the stable serial number for all device types.
