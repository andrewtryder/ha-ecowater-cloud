# Contributing to ha-ecowater-cloud

Thank you for your interest in contributing to the EcoWater Cloud integration! 

## Development Environment

This repository uses a `devcontainer` setup and `uv` for dependency management.

1. Open the repository in Visual Studio Code.
2. When prompted, select **Reopen in Container**.
3. Inside the container, dependencies are automatically managed via `uv`. You can run commands directly using `uv run`.

## Pull Requests

1. All commits must follow [Conventional Commits](https://www.conventionalcommits.org/).
2. Keep pull requests focused on a single feature or bug fix.
3. Ensure all tests pass before submitting.
4. If you are adding a new model or new capabilities, please provide a sanitized fixture from the `scripts/probe_ayla.py` script as proof.

## Code Quality and Tests

Before submitting a PR, ensure you run:
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy custom_components/ecowater_cloud`
- `uv run pytest tests/`

Tests must achieve 100% coverage of all implemented behavior.

## Submitting Fixtures

If your device has features not yet supported, you can submit a fixture. 
Run the `probe_ayla.py` script provided in this repository using your credentials. **The script will automatically redact your email, tokens, IPs, MAC addresses, passwords, and dealer information.**

Always manually review the generated JSON fixture to ensure no PII is leaked before sharing it in a GitHub issue or PR. Never share your password or live auth tokens.
