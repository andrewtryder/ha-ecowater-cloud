#!/usr/bin/env bash
set -euo pipefail

# Portfolio Universal Local Validation Contract
# Repository: ha-ecowater-cloud
# Gate: 90% component branch coverage

echo "==> [1/8] Verifying toolchain and interpreter"
command -v uv >/dev/null 2>&1 || { echo "Error: uv is required but not installed"; exit 1; }
python_version=$(uv run --locked python --version)
echo "Using $python_version"

echo "==> [2/8] Verifying dependency lockfile freshness"
uv lock --check

echo "==> [3/8] Running pre-commit hooks on all files"
uv run --locked pre-commit run --all-files

echo "==> [4/8] Running Ruff lint and formatting checks"
uv run --locked ruff check .
uv run --locked ruff format --check .

echo "==> [5/8] Running Mypy strict type checks"
uv run --locked mypy custom_components/ecowater_cloud

echo "==> [6/8] Running actionlint workflow validation"
if command -v actionlint >/dev/null 2>&1; then
    actionlint .github/workflows/*.yml
else
    echo "actionlint not found in PATH, skipping workflow linting"
fi

echo "==> [7/8] Running Python test suite with branch coverage (>=90% gate)"
uv run --locked pytest --cov=custom_components/ecowater_cloud --cov-branch --cov-report=term-missing --cov-fail-under=90 tests/

echo "==> [8/8] Verifying clean git working tree"
git diff --exit-code

echo "==> Local validation passed successfully!"
