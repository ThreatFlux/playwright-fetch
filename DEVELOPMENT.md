# Development Guide

This document provides information for developers who want to contribute to the Playwright Fetch MCP Server project.

## Project Structure

```
playwright-fetch/
├── .github/workflows/        # GitHub Actions workflows
├── src/                      # Source code
│   └── mcp_server_fetch/
│       ├── __init__.py       # Package initialization and CLI entry point
│       ├── __main__.py       # Module execution entry point
│       └── server.py         # Core server implementation
├── tests/                    # Test suite
│   ├── conftest.py           # Test fixtures and configuration
│   ├── functional/           # Functional/integration tests
│   └── unit/                 # Unit tests
├── .coveragerc               # Coverage configuration
├── .ruff.toml                # Ruff linter configuration
├── bandit.yaml               # Bandit security scanner configuration
├── codecov.yml               # Codecov configuration
├── mypy.ini                  # Type checking configuration
├── pyproject.toml            # Project metadata and dependencies
├── Dockerfile                # Docker build configuration
└── Makefile                  # Make targets for common operations
```

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/threatflux/playwright-fetch
   cd playwright-fetch
   ```

2. Install dependencies with uv:
   ```bash
   # Using uv (recommended)
   uv pip install -e ".[dev]"
   uv run playwright install --with-deps chromium
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run the test suite with:

```bash
# Run all tests
make test

# Generate coverage report
make coverage
```

## Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Linting and formatting
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning

Run these checks with:

```bash
# Run all linters
make lint

# Format the code
make format

# Run type checker
make mypy

# Run security checks
make security-check
```

## Building and Running

```bash
# Build package
make build

# Run the server locally
make run

# Build Docker image
make docker-build

# Run Docker container
make docker-run
```

## Release Process

1. Update version in `src/mcp_server_fetch/__init__.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a pull request
4. Once merged, tag the release:
   ```bash
   git tag -a v0.1.x -m "Version 0.1.x"
   git push origin v0.1.x
   ```
5. The GitHub Actions release workflow will build and publish the package and Docker image.

## CI/CD

The project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow**: Runs on all pushes and pull requests to the main branch
  - Runs linters, type checker, security scans, and tests
  - Builds Docker image (only on pushes to main, not on PRs)

- **Release Workflow**: Runs when a tag is pushed
  - Validates version match between tag and code
  - Runs tests and checks
  - Creates GitHub release with built packages
  - Builds and pushes Docker image to Docker Hub