"""Tests for the probe_ayla data redactor."""

from scripts.probe_ayla import redact_data


def test_redact_data_email():
    """Test redaction of emails."""
    data = {"user": "test@example.com", "other": "normal string"}
    redacted = redact_data(data)
    assert redacted["user"] == "***REDACTED_EMAIL***"
    assert redacted["other"] == "normal string"


def test_redact_data_ip():
    """Test redaction of IP addresses."""
    # Since 'lan_ip' and 'mask' trigger the key-based redaction, they become ***REDACTED***
    data = {"lan_ip": "192.168.1.100", "mask": "255.255.255.0"}
    redacted = redact_data(data)
    assert redacted["lan_ip"] == "***REDACTED***"
    # Mask doesn't hit key redaction, but it hits the IP regex
    assert redacted["mask"] == "***REDACTED_IP***"


def test_redact_data_mac():
    """Test redaction of MAC addresses."""
    data = {"mac": "00:1A:2B:3C:4D:5E", "mac_lower": "00:1a:2b:3c:4d:5e"}
    redacted = redact_data(data)
    assert redacted["mac"] == "***REDACTED***"
    assert redacted["mac_lower"] == "***REDACTED***"


def test_redact_data_sensitive_keys():
    """Test redaction of values based on sensitive keys."""
    data = {
        "access_token": "some_short_token",
        "wifi_password": "supersecretpassword",
        "dealer_name": "Bob's Plumbing",
        "customer_address": "123 Main St",
        "normal_key": "normal value",
    }
    redacted = redact_data(data)
    assert redacted["access_token"] == "***REDACTED***"
    assert redacted["wifi_password"] == "***REDACTED***"
    assert redacted["dealer_name"] == "***REDACTED***"
    assert redacted["customer_address"] == "***REDACTED***"
    assert redacted["normal_key"] == "normal value"


def test_redact_data_recursive():
    """Test recursive redaction."""
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
    assert redacted["devices"][0]["lan_ip"] == "***REDACTED***"
    assert redacted["devices"][0]["properties"]["token"] == "***REDACTED***"
    assert redacted["devices"][0]["properties"]["value"] == 123
    assert redacted["devices"][0]["dsn"] == "AC000W000"
