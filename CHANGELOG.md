# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.1.0...v0.2.0) (2026-08-06)


### Features

* add salt capacity mapping for model 104703 ([21300c3](https://github.com/andrewtryder/ha-ecowater-cloud/commit/21300c311d7234afdf20e7394401034ac1c2bf46))
* implement high-value properties ([#6](https://github.com/andrewtryder/ha-ecowater-cloud/issues/6)) ([d14d39d](https://github.com/andrewtryder/ha-ecowater-cloud/commit/d14d39de30155cba1effe7295e2baca78b4b0527))
* implement specific rock removal entities ([57bef93](https://github.com/andrewtryder/ha-ecowater-cloud/commit/57bef937019b507684895e6d6d540457a03ffd21))
* initial commit for EcoWater Cloud ([21dabb4](https://github.com/andrewtryder/ha-ecowater-cloud/commit/21dabb45edcbd9f7470f5e761d6a0c2c19754b5e))
* support model-specific aliases for total water used ([fe241ad](https://github.com/andrewtryder/ha-ecowater-cloud/commit/fe241ad2b48ee72ac53538a9ef49020c7c31711b))


### Bug Fixes

* address important, non-immediate blockers ([7b4ebb3](https://github.com/andrewtryder/ha-ecowater-cloud/commit/7b4ebb35cfb586ab1023ba88cdd3444b0510c3a5))
* authenticate backend before first refresh via _async_setup ([c213c0b](https://github.com/andrewtryder/ha-ecowater-cloud/commit/c213c0b3233c9356fc2facdfb145dd8ed39a79eb))
* correct Ayla API response unwrapping and error handling ([abaecea](https://github.com/andrewtryder/ha-ecowater-cloud/commit/abaecea6b9629dfa2a7b525a62ff9cb966502626))
* correct sensor device class and enum values ([2550775](https://github.com/andrewtryder/ha-ecowater-cloud/commit/2550775ea0a6249379209b3d4ec2baf9dabc6d21))
* correctly map rock removal properties ([62ea7a2](https://github.com/andrewtryder/ha-ecowater-cloud/commit/62ea7a2b189e772473511389861d44b07f17fcc3))
* harden probe redactor for safe public issue uploads ([f5a24aa](https://github.com/andrewtryder/ha-ecowater-cloud/commit/f5a24aa6a01c64ea37aab7efa8958d2b1e4a1dab))
* preserve property names in redacted ayla fixtures ([f5d1f80](https://github.com/andrewtryder/ha-ecowater-cloud/commit/f5d1f80915fc3546821dbc4d2fe26d411b1cc0fc))
* sort manifest.json keys according to Home Assistant standards ([f583e38](https://github.com/andrewtryder/ha-ecowater-cloud/commit/f583e38253a480c536600545bbf31e95c78ed646))
* use correct Ayla property names for water capabilities ([279cf30](https://github.com/andrewtryder/ha-ecowater-cloud/commit/279cf30c9692e027396bcb1795cc2845c47f9028))
* version consistency, supported-device filtering, ConfigEntryError ([7a23064](https://github.com/andrewtryder/ha-ecowater-cloud/commit/7a2306416452361cd782e269ab1781ce79c4547f))


### Documentation

* add MIT license ([8f1f5d2](https://github.com/andrewtryder/ha-ecowater-cloud/commit/8f1f5d2f125201c6f55fc5f0051d477eb017fad8))

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
