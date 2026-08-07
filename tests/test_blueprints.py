"""Tests for automation blueprints."""

from pathlib import Path

import yaml


def test_blueprints_valid_yaml_and_schema() -> None:
    """Verify all blueprint YAML files load, contain required metadata, and set min_version."""
    root_dir = Path(__file__).parent.parent
    blueprints_dir = root_dir / "blueprints" / "automation" / "ecowater_cloud"

    yaml_files = list(blueprints_dir.glob("*.yaml"))
    assert len(yaml_files) >= 4, (
        f"Expected at least 4 blueprints, found {len(yaml_files)}"
    )

    class HALoader(yaml.SafeLoader):
        pass

    HALoader.add_constructor("!input", lambda loader, node: node.value)

    for file_path in yaml_files:
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.load(f, Loader=HALoader)  # noqa: S506

        assert isinstance(data, dict), (
            f"Blueprint {file_path.name} must be a dictionary"
        )
        assert "blueprint" in data, (
            f"Blueprint {file_path.name} missing 'blueprint' section"
        )

        bp = data["blueprint"]
        assert "name" in bp, f"Blueprint {file_path.name} missing name"
        assert "description" in bp, f"Blueprint {file_path.name} missing description"
        assert bp.get("domain") == "automation", (
            f"Blueprint {file_path.name} domain must be automation"
        )
        assert bp.get("author") == "Andrew Ryder", (
            f"Blueprint {file_path.name} author mismatch"
        )

        ha_meta = bp.get("homeassistant", {})
        assert ha_meta.get("min_version") == "2026.3.0", (
            f"Blueprint {file_path.name} min_version must be 2026.3.0"
        )


async def test_blueprints_validate_in_home_assistant(hass) -> None:
    """Validate all blueprints against Home Assistant's blueprint schema and parser."""
    from homeassistant.components.blueprint import models
    from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
    from homeassistant.util.yaml import load_yaml

    root_dir = Path(__file__).parent.parent
    blueprints_dir = root_dir / "blueprints" / "automation" / "ecowater_cloud"

    for file_path in blueprints_dir.glob("*.yaml"):
        yaml_dict = load_yaml(str(file_path))
        validated = BLUEPRINT_SCHEMA(yaml_dict)
        bp = models.Blueprint(
            validated,
            expected_domain="automation",
            path=str(file_path),
            schema=BLUEPRINT_SCHEMA,
        )
        assert bp.name
        assert bp.domain == "automation"
