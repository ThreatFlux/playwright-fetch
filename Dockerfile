FROM python:3.13.2-slim AS base

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app:/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
# Add security-related environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/browser-data
ENV NODE_OPTIONS=--max-old-space-size=2048
ENV PYTHONHASHSEED=random
# Specify the user ID explicitly for security
ENV USER_ID=1000
ENV GROUP_ID=1000

# Install dependencies needed for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Create a non-root user with specific UID/GID
    && groupadd -g ${GROUP_ID} appuser \
    && useradd -m -u ${USER_ID} -g appuser -s /bin/bash appuser \
    # Create browser data directory with proper permissions
    && mkdir -p ${PLAYWRIGHT_BROWSERS_PATH} \
    && chown -R appuser:appuser ${PLAYWRIGHT_BROWSERS_PATH}

FROM base AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what's needed for dependency installation
COPY pyproject.toml setup.py MANIFEST.in /app/

# Install dependencies only (not project)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system playwright && \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright python -m playwright install --with-deps chromium

# Copy the rest of the project
COPY . /app/

# Install project directly instead of in editable mode
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .

FROM base AS test

# Install dependencies for testing
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright
COPY --from=builder /app /app

WORKDIR /app

# Install development dependencies for testing
ENTRYPOINT ["/bin/bash"]

FROM base AS final

# Install Playwright browser dependencies in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-liberation \
    fonts-noto-color-emoji \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Playwright browser binaries and project files
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

WORKDIR /app

# Make run.py executable and set permissions
RUN chmod +x /app/run.py && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add health check - a more thorough check that tests the application's basic functionality
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import os, sys, asyncio, json; \
    sys.path.append('/app'); \
    from src.mcp_server_fetch.server import get_robots_txt_url; \
    try: \
        result = get_robots_txt_url('https://example.com'); \
        if result == 'https://example.com/robots.txt': sys.exit(0); \
        else: sys.exit(1); \
    except Exception as e: \
        sys.stderr.write(str(e)); \
        sys.exit(1);"

# Set secure permissions for runtime
RUN chmod -R o-w /app

# Use the direct run script with a process supervisor signal handler
ENTRYPOINT ["python", "-u", "/app/run.py"]