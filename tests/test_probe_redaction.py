"""Tests for the probe_ayla data redactor."""

from scripts.probe_ayla import _is_token_like, redact_data

# ---------------------------------------------------------------------------
# Original tests (updated for new DSN / name behaviour)
# ---------------------------------------------------------------------------


def test_redact_data_email():
    """Email addresses are scrubbed regardless of dict key."""
    data = {"user": "test@example.com", "other": "normal string"}
    redacted = redact_data(data)
    assert redacted["user"] == "***REDACTED_EMAIL***"
    assert redacted["other"] == "normal string"


def test_redact_data_ip():
    """IP addresses in sensitive keys are key-redacted; others hit the regex."""
    data = {"lan_ip": "192.168.1.100", "mask": "255.255.255.0"}
    redacted = redact_data(data)
    # 'lan_ip' contains 'ip' → key-based redaction
    assert redacted["lan_ip"] == "***REDACTED***"
    # 'mask' is not a sensitive key but the value matches the IPv4 regex
    assert redacted["mask"] == "***REDACTED_IP***"


def test_redact_data_mac():
    """MAC addresses are redacted by key match (key contains 'mac')."""
    data = {"mac": "00:1A:2B:3C:4D:5E", "mac_lower": "00:1a:2b:3c:4d:5e"}
    redacted = redact_data(data)
    assert redacted["mac"] == "***REDACTED***"
    assert redacted["mac_lower"] == "***REDACTED***"


def test_redact_data_sensitive_keys():
    """Values under sensitive key names are fully redacted."""
    data = {
        "access_token": "some_short_token",
        "wifi_password": "supersecretpassword",
        "dealer_name": "Bob's Plumbing",
        "customer_address": "123 Main St",
        "safe_field": "normal value",
    }
    redacted = redact_data(data)
    assert redacted["access_token"] == "***REDACTED***"
    assert redacted["wifi_password"] == "***REDACTED***"
    assert redacted["dealer_name"] == "***REDACTED***"
    assert redacted["customer_address"] == "***REDACTED***"
    assert redacted["safe_field"] == "normal value"


def test_redact_data_recursive():
    """Key-based and property-based redaction applies recursively."""
    data = {
        "devices": [
            {
                "dsn": "AC000W000",
                "lan_ip": "10.0.0.5",
                "properties": {"token": "abc", "value": 123},
            }
        ]
    }
    redacted = redact_data(data)
    # 'dsn' is now a sensitive key
    assert redacted["devices"][0]["dsn"] == "***REDACTED***"
    assert redacted["devices"][0]["lan_ip"] == "***REDACTED***"
    assert redacted["devices"][0]["properties"]["token"] == "***REDACTED***"
    assert redacted["devices"][0]["properties"]["value"] == 123


# ---------------------------------------------------------------------------
# New tests for the hardened redactor
# ---------------------------------------------------------------------------


def test_redact_dsn_by_key():
    """DSN values are redacted when the key is 'dsn'."""
    data = {"dsn": "AC000W123456789", "oem_model": "EWS123"}
    redacted = redact_data(data)
    assert redacted["dsn"] == "***REDACTED***"
    # oem_model is not sensitive
    assert redacted["oem_model"] == "EWS123"


def test_redact_serial_by_key():
    """serial / serial_number values are redacted."""
    data = {"serial_number": "SN-00012345", "serial": "SN-00012345"}
    redacted = redact_data(data)
    assert redacted["serial_number"] == "***REDACTED***"
    assert redacted["serial"] == "***REDACTED***"


def test_redact_uuid_by_key():
    """UUID values are redacted."""
    data = {"uuid": "550e8400-e29b-41d4-a716-446655440000"}
    redacted = redact_data(data)
    assert redacted["uuid"] == "***REDACTED***"


def test_redact_user_assigned_device_name():
    """User-assigned device names (key='name') are redacted."""
    data = {"name": "Andrew's Softener", "model": "EWS123"}
    redacted = redact_data(data)
    assert redacted["name"] == "***REDACTED***"
    assert redacted["model"] == "EWS123"


def test_redact_property_dict_ssid():
    """Ayla property dict: wifi_ssid value is redacted."""
    data = {
        "name": "wifi_ssid",
        "value": "My Home Wi-Fi",
        "data_updated_at": "2026-01-01T00:00:00Z",
    }
    redacted = redact_data(data)
    assert redacted["value"] == "***REDACTED***"
    # The property name key itself ('name') is NO LONGER redacted
    assert redacted["name"] == "wifi_ssid"


def test_redact_property_dict_ip():
    """Ayla property dict: lan_ip value is redacted via property-name lookup."""
    data = {"name": "lan_ip", "value": "192.168.1.50"}
    redacted = redact_data(data)
    assert redacted["value"] == "***REDACTED***"


def test_redact_property_dict_bearer_token():
    """Ayla property dict: access_token value is redacted via property-name lookup."""
    data = {"name": "access_token", "value": "eyJhbGciOiJIUzI1NiJ9.longtoken.signature"}
    redacted = redact_data(data)
    assert redacted["value"] == "***REDACTED***"


def test_redact_property_dict_non_sensitive_value_preserved():
    """Ayla property dict: safe numeric property values are preserved."""
    data = {"name": "gallons_used_today", "value": 42}
    redacted = redact_data(data)
    assert redacted["value"] == 42


def test_redact_property_dict_non_sensitive_string_preserved():
    """Ayla property dict: short non-sensitive string values are preserved."""
    data = {"name": "regen_status_enum", "value": "standby"}
    redacted = redact_data(data)
    assert redacted["value"] == "standby"


def test_redact_long_token_string():
    """Long opaque strings not under any key are redacted as tokens."""
    # Standalone token-like string (simulated as a bare value)
    token = "eyJhbGciOiJIUzI1NiJ9.Zm9vYmFy.U2lnbmF0dXJlSGVyZQ"
    assert _is_token_like(token)
    data = {"random_field": token}
    redacted = redact_data(data)
    # 'random_field' is not a sensitive key but the value is token-like
    assert redacted["random_field"] == "***REDACTED_TOKEN***"


def test_redact_short_string_not_token():
    """Short strings are not mistakenly redacted as tokens."""
    assert not _is_token_like("short")
    assert not _is_token_like("standby")


def test_redact_dealer_details():
    """Dealer-related fields are redacted."""
    data = {
        "dealer_name": "ABC Water",
        "dealer_code": "D12345",
        "installer_name": "Joe Smith",
    }
    redacted = redact_data(data)
    assert redacted["dealer_name"] == "***REDACTED***"
    assert redacted["dealer_code"] == "***REDACTED***"
    # installer_name: 'name' substring → key-based redaction
    assert redacted["installer_name"] == "***REDACTED***"


def test_redact_nested_device_name():
    """Device names in nested dicts are redacted."""
    data = {
        "device": {
            "dsn": "AC000W999",
            "name": "Kitchen Softener",
            "oem_model": "EWS456",
        }
    }
    redacted = redact_data(data)
    assert redacted["device"]["dsn"] == "***REDACTED***"
    assert redacted["device"]["name"] == "***REDACTED***"
    assert redacted["device"]["oem_model"] == "EWS456"


def test_redact_full_fixture_structure():
    """End-to-end: full Ayla fixture structure is properly sanitized."""
    fixture = {
        "devices": [
            {
                "device": {
                    "dsn": "AC000W000TEST",
                    "name": "My EcoWater",
                    "oem_model": "EWS123",
                    "lan_ip": "10.0.1.55",
                    "mac": "aa:bb:cc:dd:ee:ff",
                },
                "properties": [
                    {"name": "wifi_ssid", "value": "HomeNetwork"},
                    {"name": "gallons_used_today", "value": 30},
                    {"name": "current_water_flow_gpm", "value": 0},
                    {
                        "name": "access_token",
                        "value": "bearer_tok_abc123xyz_long_enough",
                    },
                ],
            }
        ]
    }
    redacted = redact_data(fixture)
    dev = redacted["devices"][0]["device"]
    props = redacted["devices"][0]["properties"]

    assert dev["dsn"] == "***REDACTED***"
    assert dev["name"] == "***REDACTED***"
    assert dev["oem_model"] == "EWS123"
    assert dev["lan_ip"] == "***REDACTED***"
    assert dev["mac"] == "***REDACTED***"

    ssid_prop = next(
        p for p in props if p["name"] == "wifi_ssid" and props.index(p) == 0
    )
    assert ssid_prop["value"] == "***REDACTED***"

    water_prop = props[1]
    assert water_prop["value"] == 30

    token_prop = props[3]
    assert token_prop["value"] == "***REDACTED***"
