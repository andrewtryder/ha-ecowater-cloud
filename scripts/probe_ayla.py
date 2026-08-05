"""Safe Ayla API probe and fixture generator."""

import argparse
import asyncio
import json
import logging
import os
import re

# We must run this from the repo root so we can import custom_components
import sys
from pathlib import Path
from typing import Any

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.ecowater_cloud.backends.ayla.api import AylaApi
from custom_components.ecowater_cloud.backends.ayla.exceptions import (
    AylaAuthenticationError,
    AylaConnectivityError,
    AylaProtocolError,
    AylaRateLimitError,
)

# Standard logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sensitive dict-key substrings (checked on parent key, not property name)
# ---------------------------------------------------------------------------
_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "email",
        "password",
        "token",
        "cookie",
        "ip",
        "mac",
        "dealer",
        "customer",
        "address",
        "phone",
        "zip",
        "lat",
        "lng",
        "ssid",
        "wifi",
        "auth",
        # Identifiers that must be redacted before public upload
        "dsn",
        "serial",
        "device_id",
        "uuid",
        "key",
        "name",
    }
)

# ---------------------------------------------------------------------------
# Ayla property names whose *value* is sensitive (SSID, bearer, IP, etc.)
# These are matched when the enclosing dict has the shape {"name": ..., "value": ...}
# ---------------------------------------------------------------------------
_SENSITIVE_PROPERTY_NAMES: frozenset[str] = frozenset(
    {
        "wifi_ssid",
        "wifi_password",
        "wifi_bssid",
        "lan_ip",
        "wan_ip",
        "gateway",
        "dns",
        "access_token",
        "refresh_token",
        "dsn",
        "serial_number",
        "device_name",
        "user_defined_name",
        "dealer_name",
        "dealer_code",
        "installer_name",
    }
)

# Long-string detection: strings longer than this that look like tokens get scrubbed
_TOKEN_MIN_LEN = 24
# Characters common in tokens / JWTs / hex IDs
_TOKEN_CHARS = re.compile(r"^[A-Za-z0-9+/=._\-]+$")


def _is_token_like(value: str) -> bool:
    """Return True if *value* looks like an opaque bearer token or ID."""
    return len(value) >= _TOKEN_MIN_LEN and bool(_TOKEN_CHARS.match(value))


def redact_data(
    data: Any,
    _parent_key: str | None = None,
    _property_name: str | None = None,
) -> Any:
    """Recursively scrub sensitive information from data.

    Three layers of protection:

    1. **Key-based**: if the enclosing dict key matches a sensitive keyword
       the entire string value is replaced with ``***REDACTED***``.
    2. **Property-name-based**: Ayla API responses wrap each sensor as
       ``{"name": "wifi_ssid", "value": "My Network"}``.  When a dict of
       that shape is detected the *value* field is checked against
       :data:`_SENSITIVE_PROPERTY_NAMES` and redacted if it matches.
    3. **Pattern-based**: email addresses, IPv4, MAC addresses, and long
       token-like strings are scrubbed from every remaining string.
    """
    if isinstance(data, dict):
        # Detect Ayla property dict: {"name": str, "value": ...}
        if (
            "name" in data
            and "value" in data
            and isinstance(data["name"], str)
        ):
            property_name = data["name"]

            result = {
                key: redact_data(value, _parent_key=key)
                for key, value in data.items()
                if key not in {"name", "value"}
            }
            result["name"] = property_name
            result["value"] = redact_data(
                data["value"],
                _parent_key="value",
                _property_name=property_name.lower(),
            )
            return result

        result: dict[str, Any] = {}
        for k, v in data.items():
            result[k] = redact_data(v, _parent_key=k)
        return result

    elif isinstance(data, list):
        return [redact_data(item) for item in data]

    elif isinstance(data, str):
        # --- Layer 1: key-based redaction ---
        if _parent_key is not None:
            key_lower = _parent_key.lower()
            if any(x in key_lower for x in _SENSITIVE_KEYS):
                return "***REDACTED***"

        # --- Layer 2: property-name-based redaction ---
        if _property_name is not None and _property_name in _SENSITIVE_PROPERTY_NAMES:
            return "***REDACTED***"

        # --- Layer 3: pattern-based redaction ---
        # Email
        if "@" in data:
            data = re.sub(
                r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
                "***REDACTED_EMAIL***",
                data,
            )
        # IPv4
        data = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "***REDACTED_IP***", data)
        # MAC
        data = re.sub(
            r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
            "***REDACTED_MAC***",
            data,
        )
        # Long token-like strings (bearer tokens, UUIDs, opaque IDs)
        if _is_token_like(data):
            return "***REDACTED_TOKEN***"

        return data

    else:
        return data


async def async_main() -> int:
    """Run the probe."""
    parser = argparse.ArgumentParser(description="Ayla API Probe for EcoWater Cloud")
    parser.add_argument("--device", help="Specific DSN to query properties for")
    parser.add_argument(
        "--list-properties",
        action="store_true",
        help=(
            "Print redacted property names and values to the terminal. "
            "Sensitive values (SSIDs, IPs, tokens) are masked. "
            "To see raw values for local debugging only, use --raw-properties instead."
        ),
    )
    parser.add_argument(
        "--raw-properties",
        action="store_true",
        help=(
            "[DEVELOPMENT ONLY] Print raw, unredacted property values to the terminal. "
            "NEVER share this output publicly."
        ),
    )
    parser.add_argument(
        "--write-fixture",
        metavar="PATH",
        help="Write sanitized JSON to this path",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite fixture if it exists",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    username = os.environ.get("ECOWATER_USERNAME")
    password = os.environ.get("ECOWATER_PASSWORD")

    if not username or not password:
        _LOGGER.error(
            "ECOWATER_USERNAME and ECOWATER_PASSWORD environment variables "
            "are required."
        )
        return 1

    _LOGGER.info("Starting probe...")

    async with aiohttp.ClientSession() as session:
        api = AylaApi(session)
        try:
            await api.async_authenticate(username, password)
            _LOGGER.info("Authenticated successfully.")

            devices = await api.async_list_devices()
            _LOGGER.info(f"Found {len(devices)} device(s).")

            fixture_data: dict[str, Any] = {"devices": []}

            for dev in devices:
                dsn = dev.get("dsn", "UNKNOWN")
                model = dev.get("model", "UNKNOWN")
                oem = dev.get("oem_model", "UNKNOWN")

                # Safe print summary
                safe_dsn = f"{dsn[:4]}...{dsn[-4:]}" if len(dsn) > 8 else "***"
                _LOGGER.info(f"Device: DSN={safe_dsn}, Model={model}, OEM={oem}")

                # Fetch properties
                if args.device and dsn != args.device:
                    continue

                props = await api.async_get_device_properties(dsn)

                if args.list_properties or args.raw_properties:
                    _LOGGER.info("Properties for %s:", safe_dsn)
                    redacted_props = redact_data(props)
                    for raw_p, red_p in zip(props, redacted_props, strict=True):
                        prop_name_str = raw_p.get("name", "?")
                        if args.raw_properties:
                            val: Any = raw_p.get("value")
                            _LOGGER.warning(
                                "  [RAW] %s: %s (%s) updated at %s",
                                prop_name_str,
                                val,
                                type(val).__name__,
                                raw_p.get("data_updated_at"),
                            )
                        else:
                            safe_val = red_p.get("value")
                            _LOGGER.info(
                                "  - %s: %s updated at %s",
                                prop_name_str,
                                safe_val,
                                raw_p.get("data_updated_at"),
                            )
                else:
                    _LOGGER.info("  Available properties: %d", len(props))

                fixture_data["devices"].append({"device": dev, "properties": props})

            if args.write_fixture:
                path = Path(args.write_fixture)
                if path.exists() and not args.force:
                    _LOGGER.error(
                        f"Fixture path {path} exists! Use --force to overwrite."
                    )
                else:
                    _LOGGER.warning(
                        "Writing sanitized fixture. "
                        "PLEASE REVIEW IT MANUALLY BEFORE COMMITTING."
                    )
                    sanitized = redact_data(fixture_data)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(sanitized, indent=2))
                    _LOGGER.info(f"Wrote fixture to {path}")

        except AylaAuthenticationError as e:
            _LOGGER.error(f"Authentication failed: {e}")
            return 1
        except AylaRateLimitError as e:
            _LOGGER.error(f"Rate limited: {e}")
            return 1
        except AylaConnectivityError as e:
            _LOGGER.error(f"Connection failed: {e}")
            return 1
        except AylaProtocolError as e:
            _LOGGER.error(f"Protocol error: {e}")
            return 1
        finally:
            await api.async_clear_authentication()

    return 0


def main() -> None:
    """Entry point."""
    sys.exit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
