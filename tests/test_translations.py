"""Tests for integration translation files."""

import json
from pathlib import Path


def test_translation_files_valid_json_and_no_key_references() -> None:
    """Enumerate every JSON file in translations/ and verify valid JSON with no [%key: references."""
    root_dir = Path(__file__).parent.parent
    translations_dir = (
        root_dir / "custom_components" / "ecowater_cloud" / "translations"
    )

    json_files = list(translations_dir.glob("*.json"))
    assert json_files, "No translation JSON files found"

    for json_file in json_files:
        content = json_file.read_text(encoding="utf-8")

        # Must parse as valid JSON
        data = json.loads(content)
        assert isinstance(data, dict), f"{json_file.name} must be a JSON object"

        # Must not contain [%key: references
        assert "[%key:" not in content, (
            f"{json_file.name} contains invalid core translation reference [%key:"
        )
