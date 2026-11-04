# Automations and dashboard

These examples use data reported by your device. Return to the [README](../README.md) for setup and compatibility.

## Companion Automation Blueprints

Easily import pre-built automation blueprints into Home Assistant to stay alerted on salt levels, flow, telemetry freshness, and regeneration status.

| Blueprint | Description | Import |
|---|---|---|
| **Low Salt Notification** | Alert when salt level drops below a target percentage or low-salt alert triggers | [![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fandrewtryder%2Fha-ecowater-cloud%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fecowater_cloud%2Flow_salt_notification.yaml) |
| **High Water Flow Alert** | Warn if continuous water flow exceeds a threshold (e.g. 5 GPM) for N minutes | [![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fandrewtryder%2Fha-ecowater-cloud%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fecowater_cloud%2Fhigh_flow_alert.yaml) |
| **Stale Data Warning** | Alert when EcoWater cloud telemetry has not synced for over 24 hours | [![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fandrewtryder%2Fha-ecowater-cloud%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fecowater_cloud%2Fstale_data_notification.yaml) |
| **Regeneration Notification** | Notify when a regeneration cycle starts or completes | [![Open your Home Assistant instance and show the blueprint import dialog.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fandrewtryder%2Fha-ecowater-cloud%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fecowater_cloud%2Fregeneration_notification.yaml) |

## Maintenance Dashboard Helper

Add a concise, formatted device-health view to your Lovelace dashboard by copying the YAML snippet below into an **Entities** card. Replace the example entity IDs below with the corresponding entities from your EcoWater device:

```yaml
type: entities
title: EcoWater Device Health
entities:
  - entity: binary_sensor.ecowater_softener_system_problem
    name: System Status
  - entity: binary_sensor.ecowater_softener_data_stale
    name: Cloud Telemetry Freshness
  - entity: sensor.ecowater_softener_salt_level
    name: Salt Level
  - entity: sensor.ecowater_softener_days_until_out_of_salt
    name: Days Until Empty
  - entity: sensor.ecowater_softener_monthly_salt_use_estimate
    name: Monthly Salt Use Estimate
  - entity: sensor.ecowater_softener_regeneration_status
    name: Regeneration Status
  - entity: sensor.ecowater_softener_days_since_last_regeneration
    name: Days Since Last Regen
  - entity: binary_sensor.ecowater_softener_low_salt_alert
    name: Low Salt Alert
  - entity: binary_sensor.ecowater_softener_service_reminder_alert
    name: Service Reminder Alert
  - entity: sensor.ecowater_softener_wifi_signal_strength
    name: Wi-Fi Signal
```
