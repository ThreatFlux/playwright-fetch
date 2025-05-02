# Playwright Fetch MCP Server

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/ThreatFlux/playwright-fetch)](https://github.com/ThreatFlux/playwright-fetch/releases)
[![CI](https://github.com/ThreatFlux/playwright-fetch/workflows/CI/badge.svg)](https://github.com/ThreatFlux/playwright-fetch/actions)
[![codecov](https://codecov.io/gh/ThreatFlux/playwright-fetch/branch/main/graph/badge.svg)](https://codecov.io/gh/ThreatFlux/playwright-fetch)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40.0-4ead85)](https://playwright.dev/)
[![MCP](https://img.shields.io/badge/MCP-Integrated-blueviolet)](https://docs.anthropic.com/claude/docs/model-context-protocol)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Model Context Protocol server that provides web content fetching capabilities using Playwright for browser automation. This server enables LLMs to retrieve and process JavaScript-rendered content from web pages, converting HTML to markdown for easier consumption.

<a href="https://glama.ai/mcp/servers/@ThreatFlux/playwright-fetch">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@ThreatFlux/playwright-fetch/badge" alt="Playwright Fetch Server MCP server" />
</a>

## Author

Created by [Wyatt Roersma](https://github.com/wyroersma) with assistance from Claude Code.

## Key Features

- **Browser Automation**: Uses Playwright to render web pages with full JavaScript support
- **Content Extraction**: Automatically identifies and extracts main content areas from web pages
- **Markdown Conversion**: Converts HTML to clean, readable markdown
- **Pagination Support**: Handles large content through pagination
- **Robots.txt Compliance**: Respects robots.txt directives for autonomous fetching
- **Proxy Support**: Allows routing requests through a proxy server
- **Docker Ready**: Available as pre-built Docker images via [Docker Hub](https://hub.docker.com/r/threatflux/playwright-fetch) and [GitHub Container Registry](https://github.com/threatflux/playwright-fetch/pkgs/container/playwright-fetch)

## Available Tools

- `playwright-fetch` - Fetches a URL using Playwright browser automation and extracts its contents as markdown.
  - `url` (string, required): URL to fetch
  - `max_length` (integer, optional): Maximum number of characters to return (default: 5000)
  - `start_index` (integer, optional): Start content from this character index (default: 0)
  - `raw` (boolean, optional): Get raw content without markdown conversion (default: false)
  - `wait_for_js` (boolean, optional): Wait for JavaScript to execute (default: true)

## Prompts

- **playwright-fetch**
  - Fetch a URL using Playwright and extract its contents as markdown
  - Arguments:
    - `url` (string, required): URL to fetch

## Requirements

- Python 3.13.2 or newer
- [uv](https://docs.astral.sh/uv/) package manager
- Playwright browsers installed

## Installation

### 1. Install with uv (recommended)

```bash
uv pip install git+https://github.com/ThreatFlux/playwright-fetch.git
# Install Playwright browsers
uv pip exec playwright install
```

Alternatively, clone the repository and install:

```bash
git clone https://github.com/ThreatFlux/playwright-fetch.git
cd playwright-fetch
uv pip install -e .
# Install Playwright browsers
uv pip exec playwright install
```

### 2. Using Docker

You can use our pre-built Docker images from Docker Hub or GitHub Container Registry:

```bash
# From Docker Hub
docker pull threatflux/playwright-fetch:latest

# From GitHub Container Registry
docker pull ghcr.io/threatflux/playwright-fetch:latest
```

Or build it yourself:

```bash
docker build -t threatflux/playwright-fetch .
```

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "playwright-fetch": {
    "command": "uvx",
    "args": ["mcp-server-playwright-fetch"]
  }
}
```
</details>

<details>
<summary>Using docker</summary>

```json
"mcpServers": {
  "playwright-fetch": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "threatflux/playwright-fetch"]
  }
}
```
</details>

### Configure for VS Code

For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code.

<details>
<summary>Using uvx</summary>

```json
{
  "mcp": {
    "servers": {
      "playwright-fetch": {
        "command": "uvx",
        "args": ["mcp-server-playwright-fetch"]
      }
    }
  }
}
```
</details>

<details>
<summary>Using Docker</summary>

```json
{
  "mcp": {
    "servers": {
      "playwright-fetch": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "threatflux/playwright-fetch"]
      }
    }
  }
}
```
</details>

## Command Line Options

The server supports these command-line options:

- `--user-agent`: Custom User-Agent string
- `--ignore-robots-txt`: Ignore robots.txt restrictions
- `--proxy-url`: Proxy URL to use for requests
- `--headless`: Run browser in headless mode (default: True)
- `--wait-until`: When to consider navigation succeeded (choices: "load", "domcontentloaded", "networkidle", "commit", default: "networkidle")

## Example Usage

```bash
# Run with default settings
uv run mcp-server-playwright-fetch

# Run with a custom user agent and proxy
uv run mcp-server-playwright-fetch --user-agent="MyCustomAgent/1.0" --proxy-url="http://myproxy:8080"

# Run with visible browser for debugging
uv run mcp-server-playwright-fetch --headless=false
```

## Debugging

You can use the MCP inspector to debug the server:

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-playwright-fetch
```

## Differences from Standard Fetch Server

This implementation differs from the standard fetch MCP server in these ways:

1. **Browser Automation**: Uses Playwright to render JavaScript-heavy pages
2. **Content Extraction**: Attempts to extract main content from common page structures
3. **Wait Options**: Configurable page loading strategy (wait for load, DOM content, network idle)
4. **Visible Browser Option**: Can run with a visible browser for debugging

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.