"""Common test fixtures for Playwright Fetch MCP Server tests."""

import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from playwright.async_api import Browser, BrowserContext, Page, Response

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Set asyncio fixture default scope to function
pytestmark = pytest.mark.asyncio(scope="function")


@pytest.fixture
def mock_html_content():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta charset="utf-8">
    </head>
    <body>
        <header>
            <h1>Test Website</h1>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
        </header>
        <main>
            <article>
                <h2>Main Content</h2>
                <p>This is the main content of the page.</p>
                <p>It contains some <strong>important</strong> information.</p>
            </article>
        </main>
        <footer>
            <p>© 2025 Test Website</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def mock_markdown_content():
    """Expected markdown output for the mock HTML."""
    return """# Test Website

* [Home](/)
* [About](/about)

## Main Content

This is the main content of the page.

It contains some **important** information.

© 2025 Test Website"""


@pytest_asyncio.fixture
async def mock_playwright():
    """Mock Playwright components for testing."""
    # Mock Response
    response_mock = AsyncMock(spec=Response)
    response_mock.status = 200
    response_mock.headers = {"content-type": "text/html"}

    # Mock Page
    page_mock = AsyncMock(spec=Page)
    page_mock.goto.return_value = response_mock
    page_mock.content.return_value = "<html><body><main><p>Test content</p></main></body></html>"
    page_mock.query_selector.return_value = AsyncMock()
    page_mock.query_selector.return_value.inner_html.return_value = "<p>Test content</p>"

    # Mock Browser Context
    context_mock = AsyncMock(spec=BrowserContext)
    context_mock.new_page.return_value = page_mock

    # Mock Browser
    browser_mock = AsyncMock(spec=Browser)
    browser_mock.new_context.return_value = context_mock

    # Mock Playwright
    playwright_mock = AsyncMock()
    playwright_mock.chromium = AsyncMock()
    playwright_mock.chromium.launch.return_value = browser_mock

    # Create a patch for async_playwright
    @asynccontextmanager
    async def mock_async_playwright():
        try:
            yield playwright_mock
        finally:
            pass

    with patch("playwright.async_api.async_playwright", return_value=mock_async_playwright()):
        yield {
            "playwright": playwright_mock,
            "browser": browser_mock,
            "context": context_mock,
            "page": page_mock,
            "response": response_mock,
        }


@pytest.fixture
def mock_httpx_response():
    """Mock for HTTPX Response."""
    response = Mock()
    response.status_code = 200
    response.text = """
    User-agent: *
    Allow: /
    """
    return response


@pytest_asyncio.fixture
async def mock_httpx_client():
    """Mock for HTTPX AsyncClient."""
    client_mock = AsyncMock()
    client_mock.get.return_value = mock_httpx_response()

    @asynccontextmanager
    async def mock_async_client(*args, **kwargs):
        try:
            yield client_mock
        finally:
            pass

    with patch("httpx.AsyncClient", return_value=mock_async_client()):
        yield client_mock
