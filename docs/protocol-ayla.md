# EcoWater Cloud — Ayla Protocol Notes

## Introduction

This document details the observed behaviour of the Ayla Networks API used by legacy EcoWater Wi-Fi connected devices. The information was gathered by inspecting the `barleybobs/ecowater-softener` (and `ayla-iot-unofficial`) repositories and confirming via probes.

## Architecture

The Ayla API is an HTTPS REST API. The app uses long-lived credentials (email/password) to fetch an `access_token` and `refresh_token`. The `access_token` is passed via the `Authorization` header on subsequent requests.

Endpoints are split into different services, typically:
- `user-field` service for authentication.
- `ads-field` service for device data and commands.

There are also regional deployments.
**US Region:**
- User: `https://user-field.aylanetworks.com`
- ADS: `https://ads-field.aylanetworks.com`

**EU Region:**
- User: `https://user-field-eu.aylanetworks.com`
- ADS: `https://ads-eu.aylanetworks.com`

EcoWater mobile apps appear to use the US region by default, but EU devices may be pinned to the EU endpoints. The App ID and Secret appear to be global constants:
- **App ID**: `ecowater-mobile-id`
- **App Secret**: `ecowater-mobile-9026832`

## Endpoints

### 1. Authentication (Sign In)

**Method**: `POST`
**URL**: `{user_url}/users/sign_in.json`
**Payload**:
```json
{
  "user": {
    "email": "user@example.com",
    "password": "password",
    "application": {
      "app_id": "ecowater-mobile-id",
      "app_secret": "ecowater-mobile-9026832"
    }
  }
}
```
**Response**:
```json
{
  "access_token": "token_string",
  "refresh_token": "refresh_string",
  "expires_in": 3600
}
```
*Note: A 404 response often indicates an invalid App ID/Secret or invalid account, whereas 401 is typically an invalid password.*

### 2. Authentication (Refresh)

**Method**: `POST`
**URL**: `{user_url}/users/refresh_token.json`
**Payload**:
```json
{
  "user": {
    "refresh_token": "refresh_string"
  }
}
```
**Response**: Similar to Sign In.

### 3. Authentication (Sign Out)

**Method**: `POST`
**URL**: `{user_url}/users/sign_out.json`
**Payload**:
```json
{
  "user": {
    "access_token": "token_string"
  }
}
```

### 4. List Devices

**Method**: `GET`
**URL**: `{ads_url}/apiv1/devices.json`
**Headers**: `Authorization: auth_token <access_token>`
**Response**:
A list of nested device objects.
```json
[
  {
    "device": {
      "dsn": "AC000W000...",
      "key": 123456,
      "product_name": "Softener",
      "oem_model": "EWS...",
      "mac": "00:00:00:00:00:00",
      "lan_ip": "192.168.1.5",
      "connection_status": "Online"
    }
  }
]
```
*Note: EcoWater softeners typically have an `oem_model` starting with `EWS`. Reverse osmosis monitors report `oem_model` `SHERO` and `product_class` `RO`.*

### 5. Get Device Properties

**Method**: `GET`
**URL**: `{ads_url}/apiv1/dsns/{dsn}/properties.json`
**Headers**: `Authorization: auth_token <access_token>`
**Response**:
A list of nested property objects.
```json
[
  {
    "property": {
      "name": "gallons_used_today",
      "value": 150,
      "data_updated_at": "2026-08-05T12:00:00Z",
      "type": "integer"
    }
  }
]
```

#### Reverse osmosis properties

Observed on one `SHERO` / `HERO-385Plus` device. The device read `connection_status: Offline` with `connected_at` and telemetry timestamps from earlier the same day, and its properties share a single daily check-in time, so it appears to sleep between check-ins. That cadence comes from one capture.

| Property | Interpretation | Basis |
|----------|----------------|-------|
| `avg_daily_gal_tenths` | Average gallons per day, in tenths | 10 (1.0 gal/day) matches 41 gal over 43 days |
| `dispensed_gal` | Gallons dispensed | Unknown whether it resets on filter or membrane replacement |
| `filter_life_remaining_days` | Days of filter life | Property name |
| `tds_removal_percent` | TDS removal percentage | Property name |
| `supply_voltage_tenths` | Supply voltage, in tenths of a volt | Property name; 51 read as 5.1 V |
| `rf_signal_bars` | Wi-Fi signal bars | Property name; scale unknown |
| `replace_filter_alert`, `replace_membrane_alert`, `replace_batteries_alert`, `no_ro_system_found_alert` | 0/1 alert flags | All observed as 0; active value is inferred |
| `host_software_version` | Device firmware | Softeners use `base_software_version` |
| `connection_details` | Comma-separated values that include the Wi-Fi SSID and MAC | Sensitive; not used |

### 6. Set Device Property

**Method**: `POST`
**URL**: `{ads_url}/apiv1/dsns/{dsn}/properties/{property_name}/datapoints.json`
**Headers**: `Authorization: auth_token <access_token>`
**Payload**:
```json
{
  "datapoint": {
    "value": 1
  }
}
```
*Note: Certain properties (e.g. `get_frequent_data`) can be written to trigger the device to send a fresh state update.*
