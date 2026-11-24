# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

[AGENTS.md](AGENTS.md) holds the binding project rules (naming, async-only HTTP, no write/command operations, no HydroLink, identifier policy). Read it first; this file does not repeat it.

## Commands

Requires Python >=3.14.2 and [uv](https://docs.astral.sh/uv/). Install dependencies with the `dev` extra, because Home Assistant and the test plugin live there:

```bash
uv sync --frozen --extra dev
```

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy custom_components/ecowater_cloud
uv run pytest tests/ -v --tb=short

# Single test
uv run pytest tests/test_version.py::test_versions_match_and_are_stable -v

# Same coverage gate as CI (90% floor, branch coverage)
uv run pytest --cov=custom_components/ecowater_cloud --cov-branch --cov-report=term-missing --cov-fail-under=90 tests/
```

Pytest runs with `filterwarnings = error` and `asyncio_mode = auto`, so any new warning fails the suite. Hassfest and HACS validation run only in CI.

`scripts/probe_ayla.py` hits the live Ayla API using `ECOWATER_USERNAME` / `ECOWATER_PASSWORD` and writes a redacted fixture. Live captures belong in `.private/`, which is gitignored.

## Architecture

One config entry is one cloud account. One `AccountCoordinator` serves every device on that account.

Data flows one way, and each layer depends only on the contract below it:

1. `backends/ayla/api.py` (`AylaApi`): HTTP, token handling, and refresh-then-retry on a 401. Maps HTTP failures to Ayla exceptions, which subclass the taxonomy in `exceptions.py`.
2. `backends/ayla/backend.py` (`AylaBackend`): implements the `BackendAdapter` protocol from `backends/__init__.py`. Falls back to a full re-login when refresh fails, keeps only `EWS*` OEM models, and skips individual devices that raise `UnsupportedDeviceError`.
3. `backends/ayla/normalization.py` (`normalize_device`): the only place that interprets raw Ayla property names, scales, and enums. It builds frozen `EcoWaterDeviceData` (`models.py`), including `DeviceCapabilities` flags derived from which properties are present. `SALT_TENTHS_MAX` maps `model_id` to salt capacity; an unmapped model gets no salt percentage and raises a Repairs issue.
4. `coordinator.py`: stores `dict[serial, EcoWaterDeviceData]` in `coordinator.data`. Converts exceptions to `ConfigEntryAuthFailed` / `UpdateFailed` and records `last_error_category`, which `repairs.py` reads.
5. `sensor.py` / `binary_sensor.py`: tables of entity descriptions, each with `value_fn` and `supported_fn`. A coordinator listener re-runs discovery, so entities appear when a device or capability shows up later.

`repairs.py` registers a coordinator listener that creates and resolves HA Repairs issues (auth rejected, no devices, unknown salt model, stale data, protocol change). Stale-data detection uses timestamps from `TELEMETRY_PROPERTIES` in `normalization.py`, not from all properties.

### Adding a telemetry entity

A single new value touches all of these:

1. Value field on `EcoWaterDeviceData` and a `has_*` flag on `DeviceCapabilities` in `models.py`. Capability flags have no defaults, so every constructor must set them.
2. Value and flag in `normalize_device`.
3. Description in `sensor.py` or `binary_sensor.py`, with `supported_fn` reading the flag.
4. `entity` strings in `translations/en.json`. There is no `strings.json`.
5. `capabilities_dict` in `diagnostics.py`, an explicit allowlist that does not pick up new fields.
6. `make_full_device_snapshot()` in `tests/conftest.py`.

### Config entries

The current schema is `VERSION = 2`, `MINOR_VERSION = 3`, and entry data also includes `region` (`us` or `eu`). The entry unique ID is `ayla:{region}:{normalized_email}`. Schema changes go in `async_migrate_entry` and need matching version bumps in `config_flow.py`. Flow steps are `user`, `reauth`, and `reconfigure`, plus an options flow for the polling interval (default 30 minutes).

## Commits and releases

Commits and PR titles must follow Conventional Commits; CI and the `commit-msg` pre-commit hook enforce this. Release Please derives versions from them and bumps `pyproject.toml`, `manifest.json`, and `uv.lock` together, so do not edit versions by hand. `tests/test_version.py` requires the first two to match as plain `X.Y.Z`.
