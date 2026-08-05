# EcoWater Home Assistant — New Codebase Requirements Register

**Assessment date:** 2026-08-05  
**Primary source:** `barleybobs/homeassistant-ecowater-softener` issue and pull-request history  
**Purpose:** Preserve the requirements needed to write a later Codex CLI implementation prompt for a new maintained repository.

---

## 1. Executive decision

Build a **new codebase with compatibility goals**, rather than continuing to patch the existing implementation.

The new repository should:

1. Preserve the existing Home Assistant domain and legacy entity unique IDs where technically safe.
2. Replace the current synchronous, per-device polling architecture.
3. Support multiple EcoWater cloud generations through backend adapters.
4. Treat device capabilities and missing properties explicitly.
5. implement current Home Assistant config-entry, entity, diagnostics, migration, localization, testing, and release practices.
6. Initially prioritize reliable read-only monitoring, then add verified control operations.

Do not merge the existing open pull requests as the foundation. Extract the valid requirements from them and implement those requirements cleanly.

---

## 2. Backend families discovered

### 2.1 Legacy Ayla backend

Used by the current v4 integration and the `ecowater-softener` Python package.

Known characteristics:

- EcoWater devices are discovered through an Ayla account.
- Properties are model-dependent and sometimes absent.
- The existing library performs synchronous calls and can sleep for 30 seconds while requesting a device refresh.
- Salt percentage conversion depends on the device model.
- Some cloud properties can remain stale or report plausible but incorrect values.

**MVP requirement:** Supported with feature parity for known legacy entities.

### 2.2 HydroLink Home backend

Used by newer systems, including reports for ERR3700/ERR3700R20 and newer ECR models.

Known characteristics:

- HydroLink credentials are distinct from legacy EcoWater Wi-Fi Manager credentials.
- EU and US/other regions may use different hosts.
- Device lookup uses an internal cloud UUID, not only the physical serial number.
- Fresh data may require a wake sequence:
  1. request `/devices/{uuid}/live`;
  2. wait asynchronously for the device/cloud update;
  3. request `/devices/{uuid}/detail-or-summary`;
  4. verify source timestamps or changed data.
- Existing community integrations provide useful protocol research but have incomplete multi-device, migration, and calculated-state handling.

**MVP requirement:** Supported as a first-class backend, not bolted onto the Ayla data structures.

### 2.3 EcoWater OEM / IQUA backend

Reported for IQUA and some rebranded systems such as Viessmann AquaHome. Community research references `apioem.ecowater.com/v1`.

Known characteristics:

- It appears distinct from both Ayla and HydroLink.
- Existing third-party support has become unreliable.
- Supported brands and models are not established.

**Initial requirement:** Define the backend interface and configuration model so this provider can be added later. Do not claim support until authenticated fixtures and device testing exist.

---

## 3. Core architecture requirements

### ARCH-001 — Account-level runtime

Use one config entry and one runtime client/coordinator per cloud account and backend, unless a backend technically requires otherwise.

The coordinator should return a mapping such as:

```python
dict[str, EcoWaterDeviceData]
```

where the key is the backend device ID.

This avoids logging in and retrieving every account device separately for every configured device.

### ARCH-002 — Backend adapter interface

Define a typed asynchronous interface similar to:

```python
class EcoWaterBackend(Protocol):
    async def async_authenticate(self) -> AccountInfo: ...
    async def async_list_devices(self) -> list[DeviceDescriptor]: ...
    async def async_get_devices(
        self, *, force_refresh: bool = False
    ) -> list[RawDeviceData]: ...
    async def async_start_regeneration(self, device_id: str) -> None: ...
    async def async_close(self) -> None: ...
```

Control methods must be capability-dependent and may be unsupported by some adapters.

### ARCH-003 — Normalized immutable model

Convert backend responses into frozen dataclasses or equivalent immutable typed models.

Suggested models:

- `AccountInfo`
- `DeviceDescriptor`
- `EcoWaterDeviceData`
- `EcoWaterCapabilities`
- `DataFreshness`
- `RegenerationState`
- `BackendDiagnosticData`

The normalized model must retain:

- backend/provider;
- internal backend device ID;
- serial number when present;
- model and firmware;
- common measurements;
- source timestamps;
- capabilities;
- sanitized raw-property metadata for diagnostics.

### ARCH-004 — Explicit exception taxonomy

Do not collapse all failures into `Exception` or one generic update error.

At minimum:

- `EcoWaterAuthError`
- `EcoWaterConnectionError`
- `EcoWaterRateLimitError`
- `EcoWaterProtocolError`
- `EcoWaterUnsupportedDeviceError`
- `EcoWaterCommandError`

Map these to Home Assistant behavior:

- authentication failure → reauthentication;
- temporary connection/service failure → coordinator update failure;
- malformed or changed response → protocol error with diagnostics;
- unsupported model/backend → user-visible abort or repair guidance;
- command failure → translated action error.

### ARCH-005 — Fully asynchronous I/O

Use Home Assistant’s managed HTTP session. Do not use:

- `requests`;
- `websocket-client` threads;
- `time.sleep`;
- executor-wrapped long-lived clients as the target architecture.

Any wake delay must use `await asyncio.sleep(...)` and have a bounded overall timeout.

### ARCH-006 — Conservative polling

Default polling must be backend-specific and conservative.

Requirements:

- enforce a safe minimum interval;
- do not default to one-minute polling without evidence that it is safe;
- support retry backoff for temporary failures;
- honor rate-limit responses;
- avoid waking devices unnecessarily;
- optionally add small jitter if multiple entries could poll simultaneously;
- log transitions into and out of failure, not every repeated failure.

### ARCH-007 — Multi-device and dynamic-device support

All devices under an account should be represented.

Requirements:

- do not select only the first returned device;
- add entities for devices discovered after initial setup;
- retain entities for temporarily missing devices while marking them unavailable;
- define a policy for devices permanently removed from the account;
- device identifiers must remain stable.

---

## 4. Configuration-entry requirements

### CFG-001 — Provider-aware setup flow

The config flow should collect:

1. backend/provider;
2. backend-specific region when required;
3. username/email;
4. password;
5. optional advanced settings only when justified.

Do not ask users to select a date display format.

### CFG-002 — Real authentication validation

Setup must distinguish:

- invalid credentials;
- account valid but no supported devices;
- network/service unavailable;
- rate limiting;
- malformed response;
- unsupported region/provider.

A wrong password must never produce a successful empty integration.

### CFG-003 — Stable unique IDs

Use a stable account identifier supplied by the backend where available.

Fallbacks must be documented and must not expose secrets. A normalized email may be used only if no stable account ID exists.

Prevent duplicate account/provider entries.

### CFG-004 — Reauthentication

Implement a complete reauthentication flow that updates credentials without removing the config entry or recreating entity registry records.

This directly addresses issue #67.

### CFG-005 — Reconfiguration

Provide reconfiguration for settings that define the connection, such as HydroLink region or provider-specific endpoints, where changing them is safe.

Use an options flow only for genuine operational preferences, such as a bounded polling interval.

### CFG-006 — Versioned migration

Set and maintain config-entry `VERSION` and `MINOR_VERSION`.

Implement `async_migrate_entry` with tests for:

- legacy entries containing username/password/device serial;
- entries missing `device_serial_number`;
- any future account-level transition;
- provider and region defaults;
- preserving entity/device identifiers.

Never directly mutate config entry data.

### CFG-007 — Runtime data

Store the coordinator/client in typed config-entry runtime data instead of copying credentials and mutable dictionaries into `hass.data`.

### CFG-008 — Avoid reload-listener anti-patterns

Use current Home Assistant config-flow/options behavior. Avoid maintaining an entry update listener whose only purpose is to reload while the flow helper also reloads the entry.

---

## 5. Device and entity requirements

### ENT-001 — Capability-driven entity creation

Never create every possible entity unconditionally.

Build entities from:

- backend capabilities;
- device capabilities;
- available property metadata;
- supported model mappings.

A missing optional flow property must not prevent salt, usage, or device entities from being created.

### ENT-002 — Preserve legacy identifiers

Where semantics are unchanged, preserve the existing unique-ID form:

```text
ecowater_<serial-lowercase>_<legacy-property-key>
```

Create an explicit migration mapping for renamed or moved entities.

Do not depend on automatically generated entity IDs for compatibility.

### ENT-003 — Correct platform selection

Use appropriate platforms:

- `sensor`: numeric, enum, date, and timestamp data;
- `binary_sensor`: online, regenerating, low-salt, leak, and problem states;
- `button`: start regeneration, when verified and supported;
- future `select`, `number`, or `time`: only for verified writable settings;
- device information/diagnostics: model, firmware, serial, backend, and region.

### ENT-004 — Translation keys

Use translated entity names and translated enum states.

Do not hard-code English entity names in Python.

Initial language parity should at least retain existing English, French, and German translations. Spanish content from PR #74 can be used as a translation reference after review.

### ENT-005 — Missing versus unavailable

Differentiate:

- coordinator refresh failed → entities unavailable;
- coordinator refresh succeeded but one property is absent → that entity unknown, or not created when the property is unsupported;
- property temporarily returns `None` → do not crash platform setup;
- programming/schema error → log and test; do not silently swallow every exception.

### ENT-006 — Dates and timestamps

Return real Python `date` values for date sensors and timezone-aware `datetime` values for timestamp sensors.

Let Home Assistant’s frontend apply locale formatting.

Do not provide a `dd/mm/yyyy` versus `mm/dd/yyyy` option.

For derived dates:

- prefer an authoritative backend date;
- otherwise label the value as estimated;
- use the backend/device timezone when known;
- do not infer correctness from local midnight alone.

### ENT-007 — Units

Expose correct native units and device classes, then rely on Home Assistant’s unit conversion wherever supported.

Do not store formatted strings or duplicate alternative-unit attributes unless Home Assistant cannot perform the conversion.

Raw backend units must be recorded in fixtures and normalization tests.

### ENT-008 — Statistics and water dashboard

Validate every sensor’s state class semantically.

Examples requiring deliberate tests:

- current flow → measurement;
- daily usage that resets → total-increasing semantics when appropriate;
- lifetime total → cumulative total semantics;
- remaining treated-water capacity → not a cumulative consumption total;
- averages → generally not totals.

Ensure at least one authoritative cumulative consumption entity is compatible with Home Assistant’s water/energy dashboard.

### ENT-009 — Status and freshness

Provide diagnostic information without inventing an “online” state.

Recommended fields:

- last successful coordinator update;
- backend source update timestamp;
- data age;
- device-reported online state, if the backend supplies one;
- integration availability;
- optional stale-data binary sensor or repair warning after a documented threshold.

A prior successful API call alone must not permanently classify the device as online.

### ENT-010 — Device information

Device registry information should include, when available:

- manufacturer;
- model;
- serial number;
- firmware version;
- backend/provider;
- configuration URL only when stable and safe.

Diagnostic entities such as RSSI should default to disabled where appropriate.

---

## 6. Protocol and data-quality requirements

### DATA-001 — Safe optional-property normalization

All backend conversion functions must tolerate missing and null values.

Examples:

- `None / 10` must never occur;
- an unknown salt model must not fabricate a percentage;
- absent salt properties on filters must not become zero salt;
- absent flow support must not create a broken flow entity.

### DATA-002 — Model-specific salt conversion

Preserve and validate known model-specific salt-capacity conversion data.

Requirements:

- fixture tests for confirmed eVOLUTION 500 Power and 600 Power behavior;
- expose raw salt property and model ID in redacted diagnostics;
- unknown model mapping → percentage unknown, with a debug/warning diagnostic;
- make model mappings data-driven rather than scattered conditionals.

### DATA-003 — Stale and frozen cloud data

The cloud may return a valid HTTP response and plausible values that are stale.

Track:

- response receipt time;
- source property update time;
- last value-change time where useful;
- whether a force-refresh was attempted;
- data age.

Do not automatically replace source values with calculated values without clearly distinguishing them.

### DATA-004 — HydroLink wake sequence

Implement wake-and-fetch as an asynchronous state machine:

1. obtain/cache internal device UUID;
2. decide whether a wake is needed;
3. request `/live`;
4. wait with bounded polling or delay;
5. request `/detail-or-summary`;
6. verify source timestamp/freshness;
7. retain the last good data on temporary failure while marking availability appropriately.

Test timeout, unauthorized, rate-limited, partial, stale, and successful responses.

### DATA-005 — Daily usage calculation

A calculated daily usage sensor may be useful when the backend’s daily counter freezes, but it is not required for the first release.

If implemented:

- derive it from an authoritative monotonic total;
- persist calculation state across Home Assistant restarts;
- reset using Home Assistant/local timezone deliberately;
- handle counter reset and rollover;
- distinguish it from the manufacturer-reported daily usage;
- mark it experimental until validated.

### DATA-006 — Regeneration-derived calculations

“Water used in last regeneration,” remaining time, and valve stage are valuable but must be based on verified properties.

Do not implement a derived regeneration-water sensor that loses its start value on restart without documenting or restoring state.

---

## 7. Control-operation requirements

### CTRL-001 — Start regeneration

Implement only after the endpoint/property has been verified for each backend.

Requirements:

- capability-gated button/action;
- translated error handling;
- refresh after successful command;
- no command retries that could trigger the action twice;
- tests proving the exact request and handling of ambiguous responses.

### CTRL-002 — Scheduled regeneration

Treat scheduling as a later feature until writable properties, allowed values, timezone behavior, and idempotency are verified.

### CTRL-003 — Regeneration telemetry

Expose when available:

- scheduled/running state;
- remaining duration;
- valve position/stage;
- start and completion timestamps.

Use translated enum states rather than arbitrary strings.

---

## 8. Diagnostics, repairs, and supportability

### DIAG-001 — Diagnostics download

Implement Home Assistant diagnostics with strict redaction.

Redact:

- username/email when appropriate;
- password;
- access tokens;
- cookies;
- authorization headers;
- Wi-Fi SSID and IP address unless explicitly justified;
- dealer/customer personally identifiable information.

Include:

- integration version;
- Home Assistant version compatibility data;
- provider and region;
- device model/serial in suitably redacted form;
- capabilities;
- source timestamps/data ages;
- sanitized property names/types;
- recent normalized values where non-sensitive;
- last exception category.

### DIAG-002 — Repairs

Create repair issues for actionable persistent conditions, such as:

- unsupported/unknown provider migration;
- repeated authentication failure;
- device data stale beyond a conservative threshold;
- unknown salt conversion model where salt percentage would otherwise be wrong;
- no supported devices on a valid account.

Avoid repairs for transient cloud outages.

### DIAG-003 — Logging

Requirements:

- debug logs for request flow without credentials or raw authorization data;
- one warning when updates begin failing;
- one recovery message when updates resume;
- protocol-change errors must identify the missing/changed field without dumping sensitive payloads;
- no broad `except` that silently converts programming errors to `None`.

---

## 9. Testing and quality requirements

### TEST-001 — Fixture-based backend tests

Maintain sanitized response fixtures for:

- Ayla legacy salt softener;
- Ayla non-salt/filter system;
- Ayla device missing flow;
- known salt model variants;
- HydroLink EU device;
- HydroLink US device;
- multiple devices under one account;
- partial/missing properties;
- stale source timestamp;
- authentication expiry;
- rate limit;
- malformed JSON/schema;
- no devices;
- unsupported device.

### TEST-002 — Config-flow coverage

Test:

- successful setup for each implemented provider;
- invalid auth;
- cannot connect;
- no supported devices;
- duplicate account;
- reauth success/failure;
- reconfigure success/failure;
- options bounds;
- every migration path;
- abort and retry behavior.

### TEST-003 — Entity coverage

Test:

- expected entities per capability set;
- stable unique IDs;
- device registry linkage;
- missing optional values;
- unavailable versus unknown behavior;
- translation keys and enum states;
- units, device classes, and state classes;
- entity migration from legacy IDs.

### TEST-004 — Coordinator coverage

Test:

- first refresh;
- repeated success;
- outage and recovery;
- token renewal;
- backoff/rate limiting;
- source staleness;
- HydroLink wake timeout and success;
- multi-device updates;
- newly discovered and removed devices.

### TEST-005 — Command coverage

For each control operation:

- successful request;
- unsupported device;
- authentication failure;
- connection failure;
- ambiguous response;
- ensure no unsafe duplicate retry.

### TEST-006 — CI

CI should run:

- Ruff;
- formatting check;
- mypy or equivalent strict type check where practical;
- pytest with coverage;
- hassfest;
- HACS validation;
- supported Python/Home Assistant test environment;
- dependency/security update automation.

Pin GitHub Actions to maintained major versions or immutable SHAs according to repository policy.

---

## 10. Open pull-request disposition

### PR #51 — no-salt systems and one-minute flow polling

**Extract:**

- non-salt/filter devices are real supported-device candidates;
- flow is optional;
- entities must be capability-driven.

**Reject as implementation:**

- manual “uses salt” checkbox as the main capability model;
- representing unsupported salt fields as zero or empty strings;
- one-minute default polling;
- old code base and merge conflicts.

### PR #74 — translated entity names

**Extract:**

- entity `translation_key` usage;
- translated names and states;
- Spanish translation material.

**Reject as implementation:**

- broad stale branch;
- unrelated date-format changes;
- test-package dependency;
- mixing status and last-update behavior into a translation PR.

### PR #86 — catch data access errors

**Extract:**

- missing/null properties must not crash all entities.

**Reject as implementation:**

- broad `except Exception`;
- silently setting every error to `None`;
- solving capability discovery at entity construction time.

---

## 11. Issue-to-requirement matrix

| Issue(s) | Finding | Required response |
|---|---|---|
| #1, #6, #39, #42, #77, #78 | Date strings, locale, “Today/Yesterday,” midnight inconsistencies | Typed dates/timestamps; no date-format option; authoritative source dates or clearly estimated dates |
| #5, #12, #21, #66 | Setup/update exceeds 10 seconds; updates stall; optional property crashes setup | Async client, no blocking sleeps, one account coordinator, capability-driven entities |
| #8, #22–#25, #30, #33, #41, #46, #47 | Entity model and state-class problems | Correct platforms, state classes, statistics tests, water dashboard compatibility |
| #16, #17, #20, #43, #44, #52 | Endpoint/page/schema changes break scraper | Backend clients, typed errors, fixtures, protocol diagnostics |
| #31, #34, #54, #65, #68, #79 | Intermittent outage, stale/frozen data, reinstall/power-cycle recovery | Retry/backoff, freshness tracking, diagnostics, reauth/reconfigure, no forced reinstall |
| #37, #38 | Regeneration controls and telemetry | Capability-gated button/actions; status, remaining time, stage when verified |
| #40, #51, #66, #73 | Different models and non-salt systems have different properties | Capability model, tested support matrix, missing properties do not break setup |
| #57, PR #74 | Incomplete localization | Translation keys for entity names and enum states |
| #67 | Password cannot be changed cleanly | Reauthentication flow preserving registry/history |
| #72 | Metric/imperial concern | Correct native units and Home Assistant conversion; avoid unnecessary custom unit system |
| #75 | Salt scaling differs by model | Data-driven model conversion table and raw diagnostics |
| #76 | Status and last successful call requested | Diagnostic timestamps and truthful device/API status model |
| #80 | IQUA/Viessmann OEM API | Third backend interface; defer support until verified |
| #81, #83, #85 | HydroLink accounts/devices, migration crash, stale cache | First-class HydroLink backend, async wake sequence, config migration |
| #82 | Flow remains zero/stale | Optional flow capability; freshness metadata; no “real-time” guarantee |

---

## 12. Recommended delivery phases

### Phase 0 — Protocol evidence

- collect and sanitize Ayla and HydroLink fixtures;
- enumerate known model IDs and capabilities;
- verify HydroLink authentication, regions, wake behavior, and multi-device payloads;
- verify regeneration command endpoints separately.

### Phase 1 — Repository skeleton

- current Home Assistant custom-integration structure;
- typed runtime data;
- backend protocol and normalized dataclasses;
- config flow, reauth, reconfigure, migration;
- diagnostics;
- CI, lint, types, tests.

### Phase 2 — Legacy Ayla read-only parity

- device discovery;
- legacy entity-ID preservation;
- common sensors;
- model salt conversion;
- non-salt/filter support;
- multi-device account coordinator.

### Phase 3 — HydroLink read-only support

- EU/US regions;
- token lifecycle;
- UUID discovery;
- wake-and-detail refresh;
- HydroLink-specific entities and binary sensors;
- source freshness.

### Phase 4 — Verified controls

- start regeneration;
- status refresh;
- remaining time/stage when available;
- command tests and documentation.

### Phase 5 — OEM/IQUA research and adapter

- authenticated API capture;
- supported-brand matrix;
- adapter implementation only after fixtures and testers exist.

---

## 13. Initial release acceptance criteria

A first maintained release is acceptable only when:

1. Existing supported Ayla users can migrate without deleting the integration.
2. Legacy entity unique IDs remain stable for semantically identical entities.
3. Password changes can be repaired through reauthentication.
4. A missing optional property cannot prevent all entities from loading.
5. Multiple devices under one account are supported.
6. Temporary cloud failure makes entities unavailable and automatically recovers.
7. Successful but stale source data is visible in diagnostics.
8. Dates are typed and locale formatting is delegated to Home Assistant.
9. Known salt percentage model mappings are fixture-tested.
10. HydroLink EU and US setup, refresh, wake, and token renewal are fixture-tested.
11. Unsupported or non-salt devices expose only applicable entities.
12. The cumulative water entity is accepted by Home Assistant statistics/water-dashboard validation.
13. Diagnostics redact all credentials and tokens.
14. HACS validation, hassfest, lint, type checks, and tests pass in CI.
15. Documentation contains an explicit tested backend/model matrix and known limitations.

---

## 14. Inputs still needed before generating the Codex implementation prompt

The later Codex prompt should not ask the coding agent to guess protocol contracts. Before implementation, provide or explicitly authorize it to derive:

- sanitized Ayla responses for at least two model families;
- sanitized HydroLink EU and US responses;
- known model-ID-to-salt-capacity mappings;
- old config-entry examples for migration tests;
- the exact new repository name and GitHub owner;
- whether to preserve the domain `ecowater_softener`;
- minimum supported Home Assistant release;
- whether HydroLink support is required in the first implementation pass;
- whether regeneration controls are in scope for the first release;
- license and attribution text for reused protocol research.

Until those decisions are made, the architecture should include the extension points but avoid speculative endpoint behavior.
