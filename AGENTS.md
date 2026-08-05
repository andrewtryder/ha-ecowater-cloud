# AGENTS.md — ha-ecowater-cloud

This file contains binding rules for any AI coding agent working in this repository.

## Permanent naming

| Item | Value |
|------|-------|
| Repository | `ha-ecowater-cloud` |
| Domain | `ecowater_cloud` |
| Integration directory | `custom_components/ecowater_cloud` |
| Ayla backend identifier | `ayla` |
| Future HydroLink backend | `hydrolink` |
| Integration display name | `EcoWater Cloud` |

## Non-negotiable implementation rules

1. **No old package.** Never import, install, or reference `ecowater_softener` or `ayla_iot_unofficial`.
2. **Reference only.** The repos `barleybobs/homeassistant-ecowater-softener` and `barleybobs/ecowater-softener` may be consulted as protocol references only. Do not copy their architecture.
3. **Async only.** No `requests`, `time.sleep`, background threads, or `websocket-client`. All HTTP uses injected `aiohttp.ClientSession`.
4. **HA session.** Home Assistant runtime HTTP must use the HA-managed client session (`async_get_clientsession`).
5. **One coordinator per account.** A single `AccountCoordinator` supports multiple physical devices.
6. **Normalized models.** Backend adapters convert raw cloud responses into frozen `DeviceSnapshot` dataclasses. Entities never access backend-specific dicts.
7. **Capability-driven entities.** Only create a sensor/entity if the corresponding `DeviceSnapshot` field is not `None`. Never convert missing values into fabricated zeros.
8. **Specific exceptions only.** No broad `except Exception`. Use the taxonomy in `exceptions.py`.
9. **Typed runtime data.** Use `entry.runtime_data` with a typed `ConfigEntry` alias. Never use `hass.data`.
10. **Schema versions from v1.** `async_migrate_entry` must exist from the first release.
11. **Reauth without deletion.** Implement `async_step_reauth` in `config_flow.py`.
12. **No date-format option.** Return real `datetime.date` and timezone-aware `datetime.datetime`. Let HA handle display.
13. **Conservative polling.** Default interval is 30 minutes.
14. **No control until verified.** Do not implement write/command operations until request payloads are confirmed by the repository owner.
15. **No credentials in logs.** Sanitize all log messages; never log username, password, token, or cookie.
16. **Minimal runtime deps.** Declare only packages not already shipped with Home Assistant.
17. **100% test coverage of behaviour.** All new logic must have corresponding tests.
18. **Stage discipline.** Do not implement Stage N+1 work unless the current prompt explicitly requests it.

## Identifier policy

```python
# Device registry
(DOMAIN, f"{backend}:{serial_number}")

# Entity unique ID
f"{backend}_{serial_number}_{entity_key}".lower()
```

Never include email, password, token, or mutable display name in an identifier.

## Config entry schema (version 1)

```python
{
    "backend": "ayla",  # str — backend identifier
    "username": "<email>",  # str — stored encrypted by HA
    "password": "<password>",  # str — stored encrypted by HA
}
```

## Verification (every stage)

Run in this order before declaring a stage complete:

```bash
ruff check .
ruff format --check .
mypy custom_components/ecowater_cloud
pytest tests/ -v --tb=short
# hassfest via devcontainer
```

Fix all failures; do not suppress them.

## Architecture docs

- [docs/requirements.md](docs/requirements.md)
- [docs/architecture.md](docs/architecture.md)
