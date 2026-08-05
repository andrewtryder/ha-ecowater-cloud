# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha.1] - 2026-08-05

### Added
- **Initial Alpha Release**: A complete rewrite of the EcoWater integration built as a standalone Home Assistant component without third-party dependencies.
- **Ayla Backend Support**: Full read-only support for legacy EcoWater Wi-Fi softeners and filters via the Ayla IoT cloud.
- **Sensors**: Comprehensive capability-driven sensors for water usage (today, average, treated available, total used, current flow), salt levels, days until empty, and regeneration status.
- **Binary Sensors**: Status indicators for device connectivity, regeneration state, and recharge enablement.
- **Diagnostics**: Specialized diagnostic entities (`source_last_updated`, `wifi_signal_strength`) to help identify and trace the conservative telemetry polling behavior of EcoWater devices.
- **Robust Architecture**: Centralized `AccountCoordinator` handles polling for all devices on an account via one coordinated account poll, preventing rate limiting.
- **Reauthentication**: Added support for changing passwords via standard HA re-auth flows.
- **Community Standards**: Implemented issue templates, bug report forms, and fully configured a HACS compliant custom repository structure.
- **Sanitization Tools**: Included `scripts/probe_ayla.py` to allow users to securely generate redacted API fixtures for reporting missing features without leaking PII.
