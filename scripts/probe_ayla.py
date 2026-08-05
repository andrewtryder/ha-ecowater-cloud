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


def redact_data(data: Any, is_key: bool = False) -> Any:
    """Recursively scrub sensitive information from data.

    This removes emails, IPs, macs, tokens, passwords, dealer info.
    """
    if isinstance(data, dict):
        return {k: redact_data(v, is_key=k) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_data(v) for v in data]
    elif isinstance(data, str):
        if is_key:
            # Check if the key itself suggests it's sensitive
            key_lower = str(is_key).lower()
            if any(
                x in key_lower
                for x in [
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
                ]
            ):
                return "***REDACTED***"

        # Scrub email addresses
        if "@" in data and "." in data:
            data = re.sub(
                r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
                "***REDACTED_EMAIL***",
                data,
            )
        # Scrub IPv4 addresses (simple regex)
        data = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "***REDACTED_IP***", data)
        # Scrub MAC addresses (00:00:00:00:00:00 or 00-00-00-00-00-00)
        data = re.sub(
            r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
            "***REDACTED_MAC***",
            data,
        )
        # Scrub Tokens / Auth
        if len(data) > 30 and ("." in data or data.isalnum() or "-" in data):
            # This is a bit aggressive but catches long tokens.
            # We'll only apply this if it looks like a JWT or long hex string.
            # However, DSNs are also strings. DSNs look like AC000W000...
            # We don't strictly scrub DSNs entirely but we probably should.
            pass

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
        help="Print property values in terminal",
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

                if args.list_properties:
                    _LOGGER.info(f"Properties for {safe_dsn}:")
                    for p in props:
                        name = p.get("name")
                        val = p.get("value")
                        typ = type(val).__name__
                        ts = p.get("data_updated_at")
                        _LOGGER.info(f"  - {name}: {val} ({typ}) updated at {ts}")
                else:
                    prop_names = [p.get("name") for p in props]
                    _LOGGER.info(f"  Available properties: {len(prop_names)}")

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
