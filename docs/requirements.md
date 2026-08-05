# EcoWater Cloud — Functional Requirements

## Background

EcoWater water treatment systems (softeners, filters) have Wi-Fi modules that phone
home to EcoWater's cloud infrastructure. The legacy Wi-Fi module uses the **Ayla IoT
platform** (`user.aylanetworks.com` / `ads.aylanetworks.com`) as its cloud backend.
A future product line, **HydroLink Home**, uses a separate backend.

This integration fetches device telemetry from the cloud and exposes it as read-only
Home Assistant entities. Control operations are explicitly **out of scope** until the
command payloads are independently verified and tested.

---

## Functional requirements

### FR-01 — Cloud account setup

The user provides an EcoWater cloud **email** and **password** once through the HA
UI config flow. The integration authenticates to the cloud backend and stores the
credentials encrypted in the config entry.

### FR-02 — Automatic device discovery

All supported devices associated with the account are added to Home Assistant
automatically. The user does not select individual devices.

### FR-03 — Read-only telemetry

The integration fetches and exposes (where available per device):

| Property | HA entity type | Unit |
|----------|---------------|------|
| Water available (remaining capacity) | Sensor | gal / L |
| Water usage today | Sensor | gal / L |
| Water usage daily average | Sensor | gal / L |
| Current water flow rate | Sensor | gal/min |
| Salt level percentage | Sensor | % |
| Days until out of salt | Sensor | days |
| Salt type | Sensor | — |
| Last recharge date | Sensor | date |
| Days since last recharge | Sensor | days |
| Recharge enabled | Binary sensor | — |
| Recharge status | Sensor | — |
| Total hardness removed | Sensor | lbs / kg |
| Hardness removed daily average | Sensor | lbs / kg |
| Model description | Device attribute | — |
| Software/firmware version | Device attribute | — |

### FR-04 — Capability-driven entity creation

An entity is created only if the corresponding property is present in the device
snapshot. A missing optional property must never prevent other entities from loading.
Missing values must not be fabricated as zero.

### FR-05 — Conservative polling

Default update interval: **30 minutes**. The user may configure this via integration
options (future stage).

### FR-06 — Reauth without deletion

If cloud credentials expire or are rejected the integration transitions to a
"reauth required" state. The user can re-enter credentials from the integration
settings page without removing and re-adding the integration.

### FR-07 — Schema migration

The config entry uses schema version 1 from initial release. Migration functions
must be present and tested from the beginning.

### FR-08 — Error transparency

- `AuthenticationError` → triggers HA reauth flow automatically.
- `ConnectivityError` → integration becomes "unavailable"; entities show unavailable.
- `RateLimitError` → backs off; logged at WARNING level.
- `ProtocolError` → logged at ERROR; integration becomes unavailable.
- `UnsupportedDeviceError` → device is skipped; all other devices continue loading.

### FR-09 — No credentials in diagnostics

The integration's diagnostic dump must sanitize username, password, tokens, and
cookies. Only non-PII fields (model, DSN, property names) may appear.

### FR-10 — No control operations (Stage 1–2)

Write/command operations (e.g., triggering a recharge) are deferred until their
request payloads are confirmed by the repository owner.

---

## Non-functional requirements

### NFR-01 — Minimum Home Assistant version

`2026.3.0` (introduces Python 3.14 support).

### NFR-02 — Python version

`>=3.14` (matching HA 2026.3.0 minimum).

### NFR-03 — Async-only HTTP

All HTTP must use `aiohttp`. No synchronous HTTP libraries.

### NFR-04 — No third-party backend wrapper

The Ayla client is implemented directly using `aiohttp`. No dependency on
`ecowater-softener`, `ayla-iot-unofficial`, or any derivative package.

### NFR-05 — Minimal runtime dependencies

Only packages not already bundled with Home Assistant may be declared in
`manifest.json` `requirements`. `aiohttp` and standard library modules are
already available.

### NFR-06 — HACS compliance

The repository must pass all HACS default store checks (public, `hacs.json`,
`manifest.json`, single integration per repo).

### NFR-07 — CI validation

Every PR must pass: `ruff check`, `ruff format --check`, `mypy`, `pytest`,
and `hassfest`.
