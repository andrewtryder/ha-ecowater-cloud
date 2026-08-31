# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.7.1...v0.7.2) (2026-08-31)


### Bug Fixes

* configure dependabot cooldown period ([0add764](https://github.com/andrewtryder/ha-ecowater-cloud/commit/0add764420a1b0c99d19ade87d93e8dc27122e35))
* configure dependabot cooldown period ([401de18](https://github.com/andrewtryder/ha-ecowater-cloud/commit/401de180005aeb20edcf0603a8385e22a2a814ce))

## [0.7.1](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.7.0...v0.7.1) (2026-08-12)


### Bug Fixes

* refresh expired Ayla access tokens ([429a3d1](https://github.com/andrewtryder/ha-ecowater-cloud/commit/429a3d1f4133bae8b562f312880d0d9d3812aa44))

## [0.7.0](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.6.2...v0.7.0) (2026-08-07)


### Features

* add EcoWater system_problem binary sensor ([#42](https://github.com/andrewtryder/ha-ecowater-cloud/issues/42)) ([093695a](https://github.com/andrewtryder/ha-ecowater-cloud/commit/093695aeca7f0313499febf080b1d934e81ddadd))
* add initial automation blueprints and README import links ([#41](https://github.com/andrewtryder/ha-ecowater-cloud/issues/41)) ([7a323c7](https://github.com/andrewtryder/ha-ecowater-cloud/commit/7a323c70b8d8adff4e5bb20cd8fda3561cac1c7c))
* add monthly salt use estimate sensor and dashboard card helper ([#43](https://github.com/andrewtryder/ha-ecowater-cloud/issues/43)) ([1070c7e](https://github.com/andrewtryder/ha-ecowater-cloud/commit/1070c7ebb6147400724520e501097ad71f8bc7a1))
* enable wifi_signal_strength and data_stale by default ([#39](https://github.com/andrewtryder/ha-ecowater-cloud/issues/39)) ([b06be03](https://github.com/andrewtryder/ha-ecowater-cloud/commit/b06be038a162f1fc46a2c4deb854f7d46c4364b0))


### Bug Fixes

* address 0.7.0 readiness findings in blueprints, error handling, freshness, and sensors ([#44](https://github.com/andrewtryder/ha-ecowater-cloud/issues/44)) ([841954d](https://github.com/andrewtryder/ha-ecowater-cloud/commit/841954d73b969cbdb9d3cbbf6faad5952ee1538e))
* remove invalid VOLUME state_class and restore model 104703 salt mapping ([#45](https://github.com/andrewtryder/ha-ecowater-cloud/issues/45)) ([f3b210a](https://github.com/andrewtryder/ha-ecowater-cloud/commit/f3b210a6052cf71af7bbca1f8ead387746951a65))

## [0.6.2](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.6.1...v0.6.2) (2026-08-07)


### Bug Fixes

* replace core translation key references with literal text in translations ([#38](https://github.com/andrewtryder/ha-ecowater-cloud/issues/38)) ([77c36af](https://github.com/andrewtryder/ha-ecowater-cloud/commit/77c36af517350d4ca6726075bfd5af426fe86c44))


### Documentation

* add device overview screenshot to README ([#36](https://github.com/andrewtryder/ha-ecowater-cloud/issues/36)) ([745813a](https://github.com/andrewtryder/ha-ecowater-cloud/commit/745813a8a4661acc05793ec30af44461dfaf2199))

## [0.6.1](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.6.0...v0.6.1) (2026-08-07)


### Bug Fixes

* pre-submission cleanups for binary sensor freshness and repair strings ([#34](https://github.com/andrewtryder/ha-ecowater-cloud/issues/34)) ([f96299d](https://github.com/andrewtryder/ha-ecowater-cloud/commit/f96299df3f21ae20c6a1cb50fe7733656e07be3c))

## [0.6.0](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.5.2...v0.6.0) (2026-08-07)


### Features

* refine salt/regen capabilities, telemetry freshness, per-device error isolation, and attribution ([e8f0a13](https://github.com/andrewtryder/ha-ecowater-cloud/commit/e8f0a138df356be3aeff27a1a90dd067a6999589))


### Bug Fixes

* resolve final v1.0 translation, nullability, repair text, and abort issues ([878eb67](https://github.com/andrewtryder/ha-ecowater-cloud/commit/878eb67ce15c987b39f1af4bcc9b286e97303d60))

## [0.5.2](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.5.1...v0.5.2) (2026-08-07)


### Bug Fixes

* lock down workflow permissions and update dependencies in uv.lock ([ab3e1f1](https://github.com/andrewtryder/ha-ecowater-cloud/commit/ab3e1f196410252797db11c281cb23babc43308b))
* resolve zizmor security alerts ([00c08f4](https://github.com/andrewtryder/ha-ecowater-cloud/commit/00c08f48b78005a4cff77b778a3bdd2ac88cbe8f))
* **security:** override vulnerable transitive cryptography dependency to &gt;=50.0.0 ([45108ff](https://github.com/andrewtryder/ha-ecowater-cloud/commit/45108ff4b3df65171b0aa6653bd1e04ab0282095))

## [0.5.1](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.5.0...v0.5.1) (2026-08-06)


### Bug Fixes

* resolve ruff lint errors ([0206e7a](https://github.com/andrewtryder/ha-ecowater-cloud/commit/0206e7a85e14852cc2d96d0ff01c8b766c6977d4))

## [0.3.0](https://github.com/andrewtryder/ha-ecowater-cloud/compare/v0.2.0...v0.3.0) (2026-08-06)


### Features

* add ayla region selection (US/EU) ([#14](https://github.com/andrewtryder/ha-ecowater-cloud/issues/14)) ([a70aa90](https://github.com/andrewtryder/ha-ecowater-cloud/commit/a70aa90ddca02938662073883248d15c5bc845e8))
* add read-only diagnostic sensors ([825cbe0](https://github.com/andrewtryder/ha-ecowater-cloud/commit/825cbe027441ee56b7fab575e917c01adcdefea7))
* add read-only diagnostic sensors ([#11](https://github.com/andrewtryder/ha-ecowater-cloud/issues/11)) ([fb8a0ef](https://github.com/andrewtryder/ha-ecowater-cloud/commit/fb8a0ef0a71e70ecb23b1bcc79ac6fd8c1ebf891))
* add stale data, repairs, and unknown model support ([#10](https://github.com/andrewtryder/ha-ecowater-cloud/issues/10)) ([a34e16d](https://github.com/andrewtryder/ha-ecowater-cloud/commit/a34e16d61e9648b441841b44941a9f1a98d29d93))
* add stale-data detection ([648e89a](https://github.com/andrewtryder/ha-ecowater-cloud/commit/648e89af9c896f60e1c9b07517c8b5d0012a70fb))
* add stale-data detection ([#12](https://github.com/andrewtryder/ha-ecowater-cloud/issues/12)) ([a4f22ff](https://github.com/andrewtryder/ha-ecowater-cloud/commit/a4f22ff6ddf141644a395e586f3f9076fed1da62))


### Documentation

* add HACS button and uninstall instructions ([922a9ad](https://github.com/andrewtryder/ha-ecowater-cloud/commit/922a9addd17e031f4fc80043db90f7e4c9b3ad98))
* remove hydrolink support references ([fb70cd4](https://github.com/andrewtryder/ha-ecowater-cloud/commit/fb70cd47e5bd33acf50c61180701bc8aa786c221))

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
