# Contributing to EcoWater Cloud

Thank you for your interest in contributing! Whether it's a bug report, a device fixture, or a code improvement — all contributions are welcome.

## Getting Started

See the [Development Guide](DEVELOPMENT.md) for environment setup, architecture overview, and code quality requirements.

## Pull Requests

1. All commits must follow [Conventional Commits](https://www.conventionalcommits.org/).
2. Keep PRs focused on a single feature or bug fix.
3. Ensure all checks pass before submitting (see [Code Quality](DEVELOPMENT.md#code-quality)).
4. If you are adding support for a new model or new capabilities, include a sanitized fixture from `scripts/probe_ayla.py` as proof.

## Submitting Device Fixtures

If your device has features not yet supported, you can submit a fixture to help us add support. Run the `probe_ayla.py` script with your credentials — it automatically redacts emails, tokens, IPs, MACs, passwords, and dealer info.

**Always manually review** the generated JSON before sharing it in a GitHub issue or PR. Never share your password or live auth tokens.

See the [README](README.md#submitting-a-device-fixture) for step-by-step instructions.

## Reporting Issues

When filing a bug report, please include:

1. Your Home Assistant version.
2. The integration version (from `manifest.json` or HACS).
3. The integration diagnostics file (Settings → Devices & Services → EcoWater Cloud → Download diagnostics).
4. Relevant log entries from **Settings → System → Logs** (filtered to `ecowater_cloud`).
