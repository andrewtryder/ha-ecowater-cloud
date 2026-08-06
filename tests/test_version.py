import json
import re
import tomllib
from pathlib import Path


def test_versions_match_and_are_stable() -> None:
    """Test that manifest.json and pyproject.toml have matching, stable versions."""
    root_dir = Path(__file__).parent.parent

    manifest_path = root_dir / "custom_components" / "ecowater_cloud" / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        manifest_version = manifest_data["version"]

    pyproject_path = root_dir / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)
        pyproject_version = pyproject_data["project"]["version"]

    assert manifest_version == pyproject_version, (
        f"Version mismatch: manifest ({manifest_version}) != pyproject ({pyproject_version})"
    )

    stable_version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    assert stable_version_pattern.match(manifest_version), (
        f"Version must be plain X.Y.Z, but was: {manifest_version}"
    )
