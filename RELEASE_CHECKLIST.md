# Release Checklist

Before tagging and publishing a new release, maintainers must verify the following scenarios manually to ensure a stable experience for users.

## Core Scenarios
- [ ] **Clean Installation**: Install from scratch via HACS. Config flow completes successfully and entities appear.
- [ ] **Upgrade**: Upgrade from the previous version. Existing entities continue updating without duplication.
- [ ] **Unload / Reload**: Disabling and enabling the integration in Home Assistant UI unloads and reloads entities cleanly without tracebacks.
- [ ] **Restart**: Entities restore their states and correctly resume polling after a Home Assistant restart.

## Edge Cases
- [ ] **Invalid Credentials**: Entering incorrect credentials during setup correctly aborts with `invalid_auth`.
- [ ] **Password Change / Reauth**: If the cloud password is changed, the integration triggers a Reauth flow and correctly updates the credentials without duplicating the account.
- [ ] **Temporary Outage**: If the cloud API goes down or the device drops off Wi-Fi, the integration handles it gracefully (entities may become unavailable but no unhandled exceptions are thrown).
- [ ] **Multiple Devices**: Verify that an account with multiple devices discovers all devices and scopes entities correctly to each device.

## Safety & Compliance
- [ ] **Diagnostics Redaction**: Download the integration diagnostics file and confirm no emails, passwords, tokens, or MAC addresses are present.
- [ ] **No Old Package**: Ensure the environment does not rely on `ecowater-softener` or `ayla_iot_unofficial` libraries.
- [ ] **HACS / Hassfest**: Confirm the CI pipeline passes `hassfest` and HACS validation.

## Release Process
- Update the `CHANGELOG.md` with relevant changes.
- Ensure `manifest.json` version matches the intended release.
- Wait for all CI checks to pass on `main`.
- Merge the Release Please PR (or manually draft a GitHub Release) to trigger the tag.

## Versioning Policy
This project uses plain three-part semantic versions (e.g., `0.2.0`). Prerelease suffixes (like `-alpha` or `-beta`) are not used. Project maturity is described in the README and release notes.

Future versions will use:
- **Patch releases** (e.g., `0.2.1`) for compatible fixes.
- **Minor releases** (e.g., `0.3.0`) for compatible features while below 1.0.
- **1.0.0** when the integration reaches its defined stability requirements.
