.PHONY: all clean install dev-setup test lint format ruff mypy security-check coverage run lock sync check-deps get-version bump-version docker-build docker-run docker-test docker-coverage build help

# Default target
all: clean install test lint

# Python settings
UV = uv
PYTHON_VERSION ?= 3.13.2
VENV = .venv

# Docker settings
IMAGE_NAME = threatflux/playwright-fetch
VERSION = $(shell grep -E "__version__ = \"[0-9]+\.[0-9]+\.[0-9]+\"" src/mcp_server_fetch/__init__.py | cut -d'"' -f2)
DOCKER_TAG = $(IMAGE_NAME):$(VERSION)
CONTAINER_NAME = playwright-fetch-test-container
HEALTH_CHECK_TIMEOUT = 30

# Version management
MAJOR = $(shell echo $(VERSION) | cut -d. -f1)
MINOR = $(shell echo $(VERSION) | cut -d. -f2)
PATCH = $(shell echo $(VERSION) | cut -d. -f3)
NEW_PATCH = $(shell expr $(PATCH) + 1)
NEW_VERSION = $(MAJOR).$(MINOR).$(NEW_PATCH)

# System detection
OS = $(shell uname -s)
ifeq ($(OS),Linux)
    PACKAGE_MANAGER = $(shell command -v apt-get >/dev/null 2>&1 && echo "apt" || (command -v yum >/dev/null 2>&1 && echo "yum" || echo "unknown"))
endif

# Check dependencies
check-deps:
	@echo "Checking system dependencies..."
	@if [ "$(OS)" = "Linux" ]; then \
		if [ "$(PACKAGE_MANAGER)" = "apt" ]; then \
			if ! dpkg -l | grep -q "python$(PYTHON_VERSION)-dev"; then \
				echo "Python $(PYTHON_VERSION) development package is missing. Installing..."; \
				sudo apt-get update && sudo apt-get install -y python$(PYTHON_VERSION)-dev; \
			else \
				echo "Python $(PYTHON_VERSION) development package is already installed."; \
			fi; \
			if ! dpkg -l | grep -q "build-essential"; then \
				echo "build-essential is missing. Installing..."; \
				sudo apt-get update && sudo apt-get install -y build-essential; \
			fi; \
			if ! dpkg -l | grep -q "libssl-dev"; then \
				echo "libssl-dev is missing. Installing..."; \
				sudo apt-get update && sudo apt-get install -y libssl-dev; \
			fi; \
		elif [ "$(PACKAGE_MANAGER)" = "yum" ]; then \
			if ! rpm -qa | grep -q "python$(PYTHON_VERSION)-devel"; then \
				echo "Python $(PYTHON_VERSION) development package is missing. Installing..."; \
				sudo yum install -y python$(PYTHON_VERSION)-devel; \
			else \
				echo "Python $(PYTHON_VERSION) development package is already installed."; \
			fi; \
			if ! rpm -qa | grep -q "gcc"; then \
				echo "gcc is missing. Installing..."; \
				sudo yum install -y gcc; \
			fi; \
			if ! rpm -qa | grep -q "openssl-devel"; then \
				echo "openssl-devel is missing. Installing..."; \
				sudo yum install -y openssl-devel; \
			fi; \
		else \
			echo "Unknown package manager. Please install Python $(PYTHON_VERSION) development package manually."; \
		fi; \
	elif [ "$(OS)" = "Darwin" ]; then \
		if ! command -v brew >/dev/null 2>&1; then \
			echo "Homebrew is not installed. Please install it from https://brew.sh/"; \
			exit 1; \
		fi; \
		if ! brew list python@$(PYTHON_VERSION) >/dev/null 2>&1; then \
			echo "Python $(PYTHON_VERSION) is missing. Installing..."; \
			brew install python@$(PYTHON_VERSION); \
		fi; \
		if ! brew list openssl >/dev/null 2>&1; then \
			echo "OpenSSL is missing. Installing..."; \
			brew install openssl; \
		fi; \
	else \
		echo "Unsupported OS. Please ensure you have Python $(PYTHON_VERSION) development packages installed."; \
	fi
	@echo "System dependency check complete."

# Installation
install: check-deps
	@echo "Creating virtual environment and installing dependencies..."
	@if command -v $(UV) >/dev/null 2>&1; then \
		echo "uv is already installed."; \
	else \
		echo "Installing uv..."; \
		if [ "$(OS)" = "Darwin" ] || [ "$(OS)" = "Linux" ]; then \
			curl -LsSf https://astral.sh/uv/install.sh | sh; \
		elif [ "$(OS)" = "Windows_NT" ]; then \
			powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"; \
		else \
			pip install uv; \
		fi; \
	fi
	$(UV) venv --python=$(PYTHON_VERSION)
	$(UV) pip install -e .
	@echo "Installation complete."

# Development setup
dev-setup: install
	@echo "Installing development dependencies..."
	$(UV) pip install -e ".[dev]"
	@if [ -f ".pre-commit-config.yaml" ]; then \
		$(UV) run pre-commit install; \
	fi
	@echo "Development setup complete."

# Generate lockfile for reproducible builds
lock:
	@echo "Generating lock file..."
	$(UV) lock
	@echo "Lock file generated."

# Sync dependencies from lockfile
sync:
	@echo "Syncing dependencies from lock file..."
	$(UV) sync
	@echo "Dependencies synced."

# Testing
test:
	@echo "Running tests..."
	@mkdir -p tests/unit tests/functional
	$(UV) run pytest -v tests/unit/ tests/functional/ -k "not skip"

coverage:
	@echo "Generating coverage report..."
	@mkdir -p tests/unit tests/functional
	rm -f .coverage htmlcov/* coverage.xml || true
	$(UV) pip install pytest-cov
	$(UV) run pytest --cov=src/mcp_server_fetch --cov-report=term --cov-report=html --cov-report=xml:coverage.xml --cov-branch tests/unit/ tests/functional/ -k "not skip"
	@echo "Coverage report generated in htmlcov/ and coverage.xml"

# Code quality
lint: ruff mypy
	@echo "Linting complete."

ruff:
	@echo "Running ruff linter..."
	$(UV) run ruff check --line-length 120 src tests
	@echo "Ruff linting complete."

format:
	@echo "Formatting code..."
	$(UV) run ruff format --line-length 120 src tests
	@echo "Formatting complete."

mypy:
	@echo "Running type checker..."
	$(UV) pip install types-setuptools types-toml
	@echo "Using custom stubs for missing type packages..."
	# Create MYPYPATH environment variable to find our stubs
	cd src && MYPYPATH=../stubs $(UV) run mypy --ignore-missing-imports mcp_server_fetch
	@echo "Type checking complete for source files."
	@echo "Skipping type checking for test files due to known issues."

security-check:
	@echo "Running security checks..."
	$(UV) pip install bandit safety
	$(UV) run bandit -r src/mcp_server_fetch --quiet --format json --output security-report.json
	$(UV) run bandit -r src/mcp_server_fetch
	$(UV) run safety check --full-report --output json --output-file safety-report.json
	$(UV) run safety check --full-report
	@echo "Security checks complete. Reports saved as security-report.json and safety-report.json"

# Cleaning
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV) *.egg-info dist build __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

# Docker
docker-build:
	@echo "Building Docker image $(DOCKER_TAG)..."
	docker build -t $(DOCKER_TAG) .
	docker tag $(DOCKER_TAG) $(IMAGE_NAME):latest
	@echo "Docker build complete."

docker-run:
	@echo "Running Docker container..."
	docker run -i --rm $(DOCKER_TAG)

# Docker test with health check
docker-test:
	@echo "Testing Docker container..."
	docker stop $(CONTAINER_NAME) >/dev/null 2>&1 || true
	docker rm $(CONTAINER_NAME) >/dev/null 2>&1 || true

	@echo "Starting test container in detached mode..."
	docker run -d --name $(CONTAINER_NAME) $(DOCKER_TAG)

	@echo "Waiting $(HEALTH_CHECK_TIMEOUT) seconds for container to initialize..."
	sleep $(HEALTH_CHECK_TIMEOUT)

	@echo "Stopping and removing test container..."
	docker logs $(CONTAINER_NAME)
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

	@echo "✅ Docker test completed"

# Docker test with full checks
docker-coverage:
	@echo "Running tests, coverage, format, lint and type checks in Docker..."
	docker build --target=test -t $(IMAGE_NAME):test .
	docker run --rm $(IMAGE_NAME):test bash -c "cd /app && \
	 uv pip install -e '.[dev]' && \
	 uv lock && \
	 uv run ruff format --line-length 120 /app/src/ /app/tests/ && \
	 uv run ruff check --line-length 120 /app/src/ /app/tests/ && \
	 mkdir -p /app/stubs && cp -r stubs/* /app/stubs/ 2>/dev/null || true && \
	 cd /app/src && MYPYPATH=/app/stubs uv run mypy --ignore-missing-imports mcp_server_fetch && \
	 uv run bandit -r /app/src/mcp_server_fetch && \
	 uv run pytest --cov=/app/src/mcp_server_fetch --cov-report=term --cov-report=html --cov-report=xml /app/tests/ && \
	 uv run safety check"

# Development
run:
	@echo "Running development server..."
	$(UV) run -m mcp_server_fetch --headless=true

# Version management commands
get-version:
	@echo "Current version: $(VERSION)"
	@echo "Version components: MAJOR=$(MAJOR), MINOR=$(MINOR), PATCH=$(PATCH)"
	@echo "Next version will be: $(NEW_VERSION)"

bump-version:
	@echo "Bumping version from $(VERSION) to $(NEW_VERSION)"

	@if [ -f "pyproject.toml" ]; then \
		sed -i.bak '/^\[project\]/,/^[[]/ s/^version = "[0-9]*\.[0-9]*\.[0-9]*"/version = "$(NEW_VERSION)"/' pyproject.toml && rm -f pyproject.toml.bak; \
		echo "Updated pyproject.toml"; \
	fi

	@if [ -f "src/mcp_server_fetch/__init__.py" ]; then \
		sed -i.bak 's/__version__ = "[0-9]*\.[0-9]*\.[0-9]*"/__version__ = "$(NEW_VERSION)"/' src/mcp_server_fetch/__init__.py && rm -f src/mcp_server_fetch/__init__.py.bak; \
		echo "Updated __init__.py"; \
	fi

	@echo "Version bump complete. New version: $(NEW_VERSION)"
	@echo "To commit this change, run:"
	@echo "  git add pyproject.toml src/mcp_server_fetch/__init__.py"
	@echo "  git commit -m \"chore: bump version to $(NEW_VERSION)\""
	@echo "  git tag -a \"v$(NEW_VERSION)\" -m \"Version $(NEW_VERSION)\""

# Build package
build:
	@echo "Building Python package..."
	$(UV) pip install build
	$(UV) run python -m build
	@echo "Package built successfully. See dist/ directory."

help:
	@echo "Playwright Fetch MCP Server Makefile"
	@echo ""
	@echo "Available targets:"
	@echo " all            : Clean, install, test, and lint"
	@echo " clean          : Clean up build artifacts and caches"
	@echo " check-deps     : Check and install system dependencies"
	@echo " install        : Install dependencies in a virtual environment"
	@echo " dev-setup      : Set up development environment"
	@echo " lock           : Generate lock file for reproducible builds"
	@echo " sync           : Sync dependencies from lock file"
	@echo " test           : Run tests"
	@echo " coverage       : Generate test coverage report"
	@echo " lint           : Run all linters"
	@echo " ruff           : Run ruff linter"
	@echo " format         : Format code using ruff"
	@echo " mypy           : Run type checker"
	@echo " security-check : Run security checks"
	@echo " docker-build   : Build Docker image"
	@echo " docker-run     : Run Docker container"
	@echo " docker-test    : Test Docker container"
	@echo " docker-coverage: Run all tests and checks in Docker"
	@echo " build          : Build Python package"
	@echo " get-version    : Show current and next version"
	@echo " bump-version   : Bump version number"