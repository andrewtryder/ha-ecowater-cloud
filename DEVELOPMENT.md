# Development Guide

This document covers everything you need to get started developing, testing, and contributing to the EcoWater Cloud integration.

For user-facing documentation, see the [README](README.md).

---

## Table of Contents

- [Development Environment](#development-environment)
- [Code Quality](#code-quality)
- [Running Tests](#running-tests)
- [Architecture Overview](#architecture-overview)
- [Directory Layout](#directory-layout)
- [Key Components](#key-components)
- [Identifier Policy](#identifier-policy)
- [Polling Strategy](#polling-strategy)
- [Backend Extensibility](#backend-extensibility)
- [Protocol Notes & Open Questions](#protocol-notes--open-questions)
- [Release Process](#release-process)
- [Further Reading](#further-reading)

---

## Development Environment

This repository uses a **devcontainer** and **[uv](https://docs.astral.sh/uv/)** for dependency management.

1. Open the repository in Visual Studio Code.
2. When prompted, select **Reopen in Container**.
3. Dependencies are automatically managed. Run commands via `uv run`.

## Code Quality

Before submitting any PR, all of these must pass:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy custom_components/ecowater_cloud
uv run pytest tests/ -v --tb=short
```

Tests must achieve **100% coverage** of all implemented behavior.

## Running Tests

```bash
# Full test suite with verbose output
uv run pytest tests/ -v --tb=short

# Single test file
uv run pytest tests/test_config_flow.py -v

# With coverage report
uv run pytest tests/ --cov=custom_components/ecowater_cloud --cov-report=term-missing
```

---

## Architecture Overview

`ha-ecowater-cloud` is a **multi-backend hub integration**: one config entry equals one cloud account, and a single `AccountCoordinator` manages all physical devices associated with that account.

### Directory Layout

```
ha-ecowater-cloud/
├── custom_components/
│   └── ecowater_cloud/
│       ├── __init__.py            # Entry-point: setup / teardown / migration
│       ├── manifest.json          # HA integration metadata
│       ├── const.py               # Domain, config keys, defaults
│       ├── exceptions.py          # Integration-wide exception taxonomy
│       ├── models.py              # Normalized device snapshot (frozen dataclass)
│       ├── coordinator.py         # AccountCoordinator (one per account)
│       ├── config_flow.py         # UI config flow + reauth flow
│       ├── diagnostics.py         # Diagnostics download handler
│       ├── strings.json           # UI string keys
│       ├── translations/
│       │   └── en.json            # English UI strings
│       ├── sensor.py              # Sensor entity platform
│       ├── binary_sensor.py       # Binary sensor entity platform
│       └── backends/
│           ├── __init__.py        # BackendAdapter abstract protocol
│           └── ayla/
│               ├── __init__.py    # AylaBackend (async Ayla HTTP client)
│               └── exceptions.py  # Ayla-specific exceptions → base taxonomy
├── tests/
├── scripts/
│   └── probe_ayla.py              # Device fixture generation script
└── docs/
```

### Key Components

#### Normalized Models (`models.py`)

`EcoWaterDeviceData` is a **frozen dataclass** that serves as the single contract between backends and the HA entity layer. Entities never import from `backends/` directly.

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

#### Exception Taxonomy (`exceptions.py`)

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

Callers catch **specific** exceptions. `ProtocolError` wraps the raw message without leaking token values.

#### AccountCoordinator (`coordinator.py`)

`AccountCoordinator(DataUpdateCoordinator[AccountInfo])` is instantiated once per config entry (one per account). Key behaviors:

- `_async_update_data` calls the backend adapter.
- `AuthenticationError` → raises `ConfigEntryAuthFailed` (triggers HA reauth flow).
- `ConnectivityError` → raises `UpdateFailed`.
- `UnsupportedDeviceError` for a single device → logs a warning and continues with remaining devices.

#### Config Flow (`config_flow.py`)

Schema version 1:

| Step | Trigger | Action |
|------|---------|--------|
| `user` | New setup | Collect username + password; create entry |
| `reauth_confirm` | `async_step_reauth` | Collect new password; update entry |

Credentials are stored in `entry.data` (encrypted by HA).

#### Entry-Point (`__init__.py`)

```python
type EcoWaterCloudConfigEntry = ConfigEntry[EcoWaterCloudData]


@dataclass
class EcoWaterCloudData:
    coordinator: AccountCoordinator
```

`async_setup_entry` flow:
1. Reads `entry.data["backend"]` to select the adapter (currently always `"ayla"`).
2. Creates `AccountCoordinator`.
3. Calls `coordinator.async_config_entry_first_refresh()`.
4. Stores `EcoWaterCloudData` in `entry.runtime_data`.
5. Calls `async_forward_entry_setups(entry, PLATFORMS)`.

### Identifier Policy

```python
# Device registry key
(DOMAIN, f"{backend}:{serial_number}")

# Entity unique_id
f"{backend}_{serial_number}_{entity_key}".lower()
```

No email, password, token, or mutable display name is ever used in an identifier.

### Config Entry Schema (version 1)

```python
{
    "backend": "ayla",  # str — backend identifier
    "username": "<email>",  # str — stored encrypted by HA
    "password": "<password>",  # str — stored encrypted by HA
}
```

### Polling Strategy

Default interval: **30 minutes** (`timedelta(minutes=30)`), configurable via options flow.

The old integration attempted a "force refresh" by posting to the `get_frequent_data` Ayla property and then sleeping. This is incompatible with async design — a non-blocking version may be evaluated in the future.

### Backend Extensibility

Adding a new backend (e.g. `hydrolink`) requires:

1. `backends/hydrolink/__init__.py` implementing `BackendAdapter`.
2. A new value `"hydrolink"` in `SUPPORTED_BACKENDS`.
3. `async_migrate_entry` handling any config-entry schema changes.
4. **No changes** to `coordinator.py`, `models.py`, or entities.

### Protocol Notes & Open Questions

- Exact token refresh endpoint and TTL for the Ayla backend.
- Whether `get_frequent_data` / force-refresh is safe without blocking sleep.
- Field presence variability across different EcoWater model numbers.
- Unit system returned by the Ayla API (assumed gallons/lbs; metric variants unknown).
- Whether the DSN serves as the stable serial number for all device types.

---

## Release Process

This project uses [Release Please](https://github.com/googleapis/release-please) with [Conventional Commits](https://www.conventionalcommits.org/).

### Versioning

Plain three-part semantic versions (e.g. `0.2.0`). No prerelease suffixes.

- **Patch** (e.g. `0.2.1`) — compatible fixes.
- **Minor** (e.g. `0.3.0`) — compatible features (while below 1.0).
- **1.0.0** — when the integration reaches its defined stability requirements.

### Pre-Release Checklist

| Area | Check |
|------|-------|
| **Clean Install** | Install from scratch via HACS. Config flow completes and entities appear. |
| **Upgrade** | Upgrade from the previous version. Entities resume without duplication. |
| **Unload / Reload** | Disabling and enabling the integration unloads/reloads cleanly. |
| **Restart** | Entities restore state and resume polling after an HA restart. |
| **Invalid Credentials** | Incorrect credentials during setup abort with `invalid_auth`. |
| **Reauth** | Password change triggers the reauth flow without duplicating the account. |
| **Temporary Outage** | Cloud API down / Wi-Fi dropout handled gracefully (no unhandled exceptions). |
| **Multiple Devices** | Multi-device accounts discover all devices and scope entities correctly. |
| **Diagnostics Redaction** | Diagnostics download contains no emails, passwords, tokens, or MACs. |
| **No Old Package** | Environment does not rely on `ecowater-softener` or `ayla_iot_unofficial`. |
| **CI** | `hassfest` and HACS validation pass in CI. |

### Tagging a Release

1. Update `CHANGELOG.md`.
2. Ensure `manifest.json` version matches the intended release.
3. Wait for all CI checks to pass on `main`.
4. Merge the Release Please PR (or manually draft a GitHub Release) to trigger the tag.

---

## Further Reading

- [Architecture deep-dive](docs/architecture.md)
- [Requirements & design decisions](docs/requirements.md)
- [Ayla protocol notes](docs/protocol-ayla.md)
- [Contributing guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
