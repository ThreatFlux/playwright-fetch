# Playwright-Fetch MCP Server Installation Guide

This guide provides instructions for setting up and using the Playwright-Fetch MCP server, which uses Playwright for browser automation to fetch web content with JavaScript support.

## Using with Docker (Recommended)

The Docker image contains all necessary dependencies including Python, Playwright, and browser binaries.

### 1. Build the Docker Image

```bash
# Clone the repository
git clone https://github.com/yourusername/playwright-fetch.git
cd playwright-fetch

# Build the Docker image
docker build -t mcp/playwright-fetch .
```

### 2. Configure Your MCP Client

#### For Claude.app

Add this to your Claude settings:

```json
"mcpServers": {
  "playwright-fetch": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "mcp/playwright-fetch"]
  }
}
```

#### For VS Code

Add this to your `.vscode/mcp.json` file or User Settings:

```json
{
  "mcp": {
    "servers": {
      "playwright-fetch": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "mcp/playwright-fetch"]
      }
    }
  }
}
```

## Local Installation (Advanced)

If you prefer to install locally rather than using Docker:

### 1. Requirements

- Python 3.13.2 or newer
- uv package manager (`pip install uv`)

### 2. Installation Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/playwright-fetch.git
cd playwright-fetch

# Create and activate a virtual environment
uv venv --seed
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package and dependencies
uv pip install -e .

# Install Playwright browsers
python -m playwright install --with-deps chromium
```

### 3. Configure Your MCP Client for Local Installation

#### For Claude.app

```json
"mcpServers": {
  "playwright-fetch": {
    "command": "/path/to/.venv/bin/python",
    "args": ["-m", "mcp_server_fetch"]
  }
}
```

#### For VS Code

```json
{
  "mcp": {
    "servers": {
      "playwright-fetch": {
        "command": "/path/to/.venv/bin/python",
        "args": ["-m", "mcp_server_fetch"]
      }
    }
  }
}
```

## Using the Server

Once configured, you can use the server with the following tools:

- `playwright-fetch` - Fetches a URL using Playwright browser automation
  - `url` (string, required): URL to fetch
  - `max_length` (integer, optional): Maximum characters to return (default: 5000)
  - `start_index` (integer, optional): Start at this character index (default: 0)
  - `raw` (boolean, optional): Get raw HTML without conversion (default: false)
  - `wait_for_js` (boolean, optional): Wait for JavaScript execution (default: true)

### Example Usage in Claude

```
Use the playwright-fetch tool to visit example.com
```

## Command Line Options

The server supports these command-line options:

- `--user-agent`: Custom User-Agent string
- `--ignore-robots-txt`: Ignore robots.txt restrictions
- `--proxy-url`: Proxy URL for requests
- `--headless`: Run browser in headless mode (default: True)
- `--wait-until`: When to consider navigation succeeded (choices: "load", "domcontentloaded", "networkidle", "commit", default: "networkidle")