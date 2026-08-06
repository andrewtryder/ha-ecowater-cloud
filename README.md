# EcoWater Cloud for Home Assistant

![Experimental](https://img.shields.io/badge/status-experimental-red.svg)
![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom-orange.svg)

A modern, async, standalone Home Assistant integration for EcoWater Cloud connected water treatment devices.

> **⚠️ EXPERIMENTAL STATUS**: This integration is currently in early experimental testing. Do not submit this repository to the default HACS store yet. It should be used exclusively as a custom repository while it undergoes stabilization and verification.

> **⚠️ WARNING**: Do not run the old `ecowater_softener` integration and this new `ecowater_cloud` integration on the same account simultaneously! Doing so may cause aggressive polling, resulting in account lockouts or temporary IP bans from the cloud service.

**Note on Migration**: The old integration’s registry data will **not** be migrated automatically. This new integration uses a fresh domain (`ecowater_cloud`) and will create new entities.

## Features & Limitations

- **Backend Support**:
  - **Ayla Wi-Fi Backend**: Experimental Ayla support (Read-Only). (Full support pending live account verification). For the first alpha, only US Ayla accounts are documented/supported unless live testing confirms the US endpoint works globally.
  - **HydroLink Home Backend**: Not supported in this repository. For HydroLink devices, please use [ha-ecowater-hydrolink](https://github.com/Roeli1996/ha-ecowater-hydrolink).
- **Read-Only**: This integration is currently read-only. No control capabilities (like triggering a regeneration) are implemented yet.
- **Standalone Architecture**: This integration uses a fully standalone, async API client built directly into the component. It does **not** rely on the old `ecowater-softener` Python package or any third-party unmaintained libraries.

## Supported Capabilities

The integration supports reading the following capabilities, dynamically enabled based on your specific water treatment device (unsupported models may expose fewer entities):

- **Water Usage**: Total used, daily average, treated water available, and current flow rate.
- **Salt / Rock**: Current salt level percentage, days until out of salt, estimated empty date, salt type, and rock removed metrics.
- **Regeneration**: Current status (Standby, Regenerating, Scheduled), days since last regeneration, and estimated date of last regeneration.
- **Diagnostic / Network**: Device online status, Wi-Fi signal strength, and timestamps indicating when the device last synced with the cloud.

### Polling & Stale Data Policy

The integration natively polls the cloud every 30 minutes.

**Important:** Water softeners are extremely conservative with telemetry uploads to save power and bandwidth. When no water is flowing, the device may not sync data to the cloud for 12–24 hours. The integration handles this natively by showing the `source_last_updated` diagnostic timestamp.

Unless the `device_reported_online` binary sensor explicitly drops, long periods without data updates are expected behavior and not a bug with the integration.

## Installation

### HACS Custom Repository (Recommended)
1. Open HACS in your Home Assistant instance.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this repository: `https://github.com/andrewtryder/ha-ecowater-cloud`
4. Select the category **Integration**.
5. Click **Add**.
6. Close the dialog, search for "EcoWater Cloud" in HACS, and click **Download**.
7. Restart Home Assistant.

### Manual Installation
1. Download the latest release from the Releases page.
2. Extract the `custom_components/ecowater_cloud` folder.
3. Copy it to your Home Assistant `config/custom_components/` directory.
4. Restart Home Assistant.

## Setup Steps

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **EcoWater Cloud**.
4. Enter your EcoWater username (email) and password.
5. Your supported devices will automatically be discovered and added.

## Upgrades & Removal

**To Upgrade**: Use HACS to download the latest version and restart Home Assistant. Entities will seamlessly resume polling.
**To Remove**:
1. Delete the integration instance from Settings -> Devices & Services.
2. Remove the custom repository from HACS.
3. Restart Home Assistant.

## Troubleshooting & Diagnostics

If you encounter issues:
1. Ensure your device is online in the official EcoWater app.
2. Check the `source_last_updated` diagnostic sensor to see when the cloud last received data.
3. Download the integration diagnostics file: Go to **Settings** -> **Devices & Services** -> **EcoWater Cloud** -> **Download diagnostics**.

### Collecting a Sanitized Fixture

If you have an unsupported device, or your device exhibits missing entities, you can safely generate a sanitized API fixture to help us build support for it.

**Never post your credentials or raw, unredacted API responses in public issues.**

To safely collect a fixture:
1. Clone this repository locally to a machine with Python installed.
2. Run the included probe script:
   ```bash
   ECOWATER_USERNAME="your-email@example.com" ECOWATER_PASSWORD="yourpassword" python3 scripts/probe_ayla.py --write-fixture my_device_fixture.json
   ```
3. The script will automatically redact your email, IP addresses, MAC addresses, device tokens, and dealer information.
4. **Manually review** `my_device_fixture.json` to ensure no sensitive personal data leaked.
5. Attach the JSON file to your GitHub Issue.

## Privacy and Security Notes

- This integration communicates directly and exclusively with the EcoWater Ayla cloud servers via HTTPS.
- Your credentials are stored and managed by Home Assistant.
- No personal data or telemetry is transmitted back to the integration developer.
