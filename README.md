<p align="center">
  <img src="docs/images/ecowater-cloud-header.png" alt="EcoWater Cloud for Home Assistant" width="600">
</p>

<h1 align="center">EcoWater Cloud for Home Assistant</h1>

<p align="center">
  A modern, async Home Assistant integration for EcoWater cloud-connected water treatment devices.
</p>

<p align="center">
  <a href="https://github.com/andrewtryder/ha-ecowater-cloud/releases"><img src="https://img.shields.io/github/v/release/andrewtryder/ha-ecowater-cloud?style=flat-square" alt="Release"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square" alt="HACS Custom Repository">
  <a href="https://github.com/andrewtryder/ha-ecowater-cloud/blob/main/LICENSE"><img src="https://img.shields.io/github/license/andrewtryder/ha-ecowater-cloud?style=flat-square" alt="License"></a>
</p>

---

## What It Does

This integration connects your EcoWater Wi-Fi-enabled water softener to Home Assistant via the EcoWater cloud, giving you Cloud-reported visibility into your EcoWater system without leaving your dashboard.

**Sensors include:**

| Category | Entities |
|---|---|
| **Water Usage** | Total used, daily average, treated water available, current flow rate |
| **Salt & Rock** | Salt level %, days until out of salt, estimated empty date, salt type, rock removed |
| **Regeneration** | Status (Standby / Regenerating / Scheduled), days since last, estimated last date |
| **Diagnostics** | Device online status, Wi-Fi signal strength, last cloud sync timestamp |

Entities are created dynamically — only capabilities your specific device reports will appear.

## Device Compatibility

The following backends and models are known to this integration:

| Backend | Region | OEM model | Display model | Status |
|---|---|---|---|---|
| Ayla | US | EWS3500 | EWS ECR3700R30 | Live tested |
| Ayla | EU | — | — | Endpoint implemented, untested |
| HydroLink | — | — | — | Not supported |

It should work with other Ayla-connected EcoWater devices, but we can't guarantee it until we have fixture data from more models.

**Have a different model?** We'd love your help — see [Submitting a Device Fixture](#submitting-a-device-fixture) below.

> **HydroLink devices** are not supported here. If your softener uses HydroLink Home, check out [ha-ecowater-hydrolink](https://github.com/Roeli1996/ha-ecowater-hydrolink) instead.

## Important Notes

> **⚠️** Do **not** run the old `ecowater_softener` integration and this `ecowater_cloud` integration on the same account at the same time. Doing so can cause aggressive polling that may lead to account lockouts or temporary IP bans from the cloud service.

- This integration is **read-only** — no control actions (e.g. triggering a regeneration) are implemented.
- If you are migrating from the old integration, entities will **not** transfer automatically. This integration uses a separate domain (`ecowater_cloud`) and creates fresh entities.

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrewtryder&repository=ha-ecowater-cloud&category=integration)

1. Click the button above to open HACS on your Home Assistant instance.
2. Click **Download** on the repository page.
3. **Restart Home Assistant.**

*(If the button doesn't work)*
1. Open **HACS** in your Home Assistant instance.
2. Tap the **⋮** menu (top-right) → **Custom repositories**.
3. Paste the repository URL: `https://github.com/andrewtryder/ha-ecowater-cloud`
4. Set the category to **Integration** and click **Add**.
5. Close the dialog, search for **EcoWater Cloud**, and click **Download**.
6. **Restart Home Assistant.**

### Manual

1. Download the latest release from the [Releases](https://github.com/andrewtryder/ha-ecowater-cloud/releases) page.
2. Copy the `custom_components/ecowater_cloud` folder into your `config/custom_components/` directory.
3. **Restart Home Assistant.**

## Setup

1. Go to **Settings → Devices & Services**.
2. Click **Add Integration**.
3. Search for **EcoWater Cloud**.
4. Enter your EcoWater account email and password.
5. Your devices will be discovered and added automatically.

## Upgrading & Uninstalling

| Action | Steps |
|---|---|
| **Upgrade** | Open HACS → download the latest version → restart Home Assistant. |
| **Uninstall** | 1. Delete the integration from Settings → Devices & Services.<br>2. Open HACS → find EcoWater Cloud → click **⋮** → **Remove**.<br>3. Remove the custom repository from HACS.<br>4. Restart Home Assistant. |

## How Polling Works

The integration polls the cloud every **30 minutes** by default (configurable in the options flow).

Water softeners are conservative with telemetry — when no water is flowing, your device may not push data to the cloud for 12–24 hours. This is **normal**. Check the `source_last_updated` diagnostic sensor to see when the cloud last received fresh data from your device. An online state confirms cloud connectivity but does not guarantee that every telemetry value is current.

## Troubleshooting

1. **Device not responding?** Open the official EcoWater app and confirm the device shows as online.
2. **Stale data?** Check the `source_last_updated` diagnostic sensor — it tells you the last time the device actually synced with the cloud.
3. **Need help?** Download the integration diagnostics file: **Settings → Devices & Services → EcoWater Cloud → Download diagnostics**, and attach it to a [GitHub Issue](https://github.com/andrewtryder/ha-ecowater-cloud/issues).

## Submitting a Device Fixture

If your device model isn't fully supported — or entities are missing — you can generate a **sanitized API fixture** to help us add support.

1. Clone this repository to a machine with Python installed.
2. Run the probe script:
   ```bash
   ECOWATER_USERNAME="your-email@example.com" \
   ECOWATER_PASSWORD="yourpassword" \
   python3 scripts/probe_ayla.py --write-fixture my_device.json
   ```
3. The script automatically redacts emails, IPs, MACs, tokens, and dealer info.
4. **Review the output file** to verify no personal data remains.
5. Attach the JSON to a [GitHub Issue](https://github.com/andrewtryder/ha-ecowater-cloud/issues).

> **Never post your credentials or raw API responses in public issues.**

## Privacy & Security

- Communicates exclusively with the EcoWater Ayla cloud servers over HTTPS.
- Credentials are stored and managed by Home Assistant.
- No telemetry or personal data is sent to the integration developer.

## Contributing

Contributions, bug reports, and device fixtures are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

For architecture details, protocol notes, and development setup, see the [Development Guide](DEVELOPMENT.md).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
