"""Comprehensive tests for the fetch_url_with_playwright function."""

import asyncio
import os

# Import the browser fixture
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError

from mcp_server_fetch.server import fetch_url_with_playwright

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tests.fixtures.browser_fixture import PlaywrightMockFactory

pytestmark = pytest.mark.asyncio


class TestFetchUrlComplete:
    """Comprehensive tests for fetch_url_with_playwright."""

    async def test_successful_html_fetch_with_main_selector(self, monkeypatch):
        """Test successful fetch of HTML content with main content selector."""
        # Setup mock
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <header>Header</header>
            <main><p>Main content here</p></main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        mock_setup = PlaywrightMockFactory.setup_full_mock(html_content=html_content)

        # Set up the element mock to return main content
        element_mock = mock_setup["element"]
        element_mock.inner_html.return_value = "<p>Main content here</p>"

        # Ensure query_selector returns the element for 'main' but not for other selectors
        page_mock = mock_setup["page"]

        async def mock_query_selector(selector):
            if selector == "main":
                return element_mock
            return None

        page_mock.query_selector = AsyncMock(side_effect=mock_query_selector)

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify
        assert "Main content here" in content
        assert prefix == ""
        assert page_mock.goto.called
        assert page_mock.content.called
        assert page_mock.query_selector.called
        assert element_mock.inner_html.called

    async def test_html_fetch_without_main_selector(self, monkeypatch):
        """Test fetch of HTML where no main content selector matches."""
        # Setup mock
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <div>Just some generic content</div>
        </body>
        </html>
        """
        mock_setup = PlaywrightMockFactory.setup_full_mock(html_content=html_content)

        # Make query_selector return None for all selectors
        page_mock = mock_setup["page"]
        page_mock.query_selector.return_value = None

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify it falls back to using the whole HTML
        assert content is not None
        assert prefix == ""
        # All selectors should have been tried
        assert page_mock.query_selector.call_count >= 9

    async def test_fetch_non_html_content(self, monkeypatch):
        """Test fetching non-HTML content."""
        # Setup mock with JSON content type
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        mock_setup["response"].headers = {"content-type": "application/json"}

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://api.example.com/data.json",
            "TestUserAgent",
        )

        # Verify it returns raw content with a prefix
        assert content is not None
        assert "application/json" in prefix
        assert "cannot be simplified to markdown" in prefix

    async def test_force_raw_parameter(self, monkeypatch):
        """Test that force_raw=True returns raw content even for HTML."""
        # Setup mock
        html_content = "<html><body><p>Test content</p></body></html>"
        mock_setup = PlaywrightMockFactory.setup_full_mock(html_content=html_content)

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function with force_raw=True
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            force_raw=True,
        )

        # Verify raw content is returned
        assert html_content in content
        assert "cannot be simplified to markdown" in prefix

    async def test_fetch_with_proxy(self, monkeypatch):
        """Test fetch with proxy configuration."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()

        # Track if proxy was configured
        proxy_configured = False
        browser_type_mock = mock_setup["playwright"].chromium

        async def mock_launch(**kwargs):
            nonlocal proxy_configured
            if "proxy" in kwargs:
                proxy_configured = True
            return mock_setup["browser"]

        browser_type_mock.launch = AsyncMock(side_effect=mock_launch)

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function with proxy
        await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            proxy_url="http://proxy.example.com:8080",
        )

        # Verify proxy was configured
        assert proxy_configured

    async def test_fetch_with_headless_false(self, monkeypatch):
        """Test fetch with headless=False."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()

        # Track browser launch parameters
        browser_config = {}
        browser_type_mock = mock_setup["playwright"].chromium

        async def mock_launch(**kwargs):
            nonlocal browser_config
            browser_config = kwargs
            return mock_setup["browser"]

        browser_type_mock.launch = AsyncMock(side_effect=mock_launch)

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function with headless=False
        await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            headless=False,
        )

        # Verify headless parameter
        assert "headless" in browser_config
        assert browser_config["headless"] is False

    async def test_fetch_error_no_response(self, monkeypatch):
        """Test error handling when no response is received."""
        # Setup mock with no response
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]
        page_mock.goto.return_value = None

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Verify the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        assert "no response received" in str(exc_info.value)

    async def test_fetch_error_status_code(self, monkeypatch):
        """Test error handling for HTTP error status codes."""
        # Setup mock with error status code
        mock_setup = PlaywrightMockFactory.setup_full_mock(status=404)

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Verify the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        assert "status code 404" in str(exc_info.value)

    async def test_fetch_error_playwright_exception(self, monkeypatch):
        """Test error handling for Playwright exceptions."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        browser_type_mock = mock_setup["playwright"].chromium

        # Make launch raise a PlaywrightError
        from playwright.async_api import Error as PlaywrightError

        browser_type_mock.launch = AsyncMock(side_effect=PlaywrightError("Connection failed"))

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Verify the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        assert "Failed to fetch" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    async def test_fetch_error_timeout(self, monkeypatch):
        """Test error handling for timeout errors."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]

        # Make goto raise a TimeoutError
        page_mock.goto = AsyncMock(side_effect=asyncio.TimeoutError())

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Verify the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        assert "Timeout when fetching" in str(exc_info.value)

    async def test_fetch_error_extraction_failure(self, monkeypatch):
        """Test handling of content extraction failures."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]
        element_mock = mock_setup["element"]

        # Make content extraction fail but allow the function to continue
        element_mock.inner_html = AsyncMock(side_effect=Exception("Extraction failed"))

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # This should not raise but fall back to using the full HTML
        content, prefix = await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify content was still returned using the fallback
        assert content is not None
        assert page_mock.content.called

    async def test_fetch_with_different_wait_until(self, monkeypatch):
        """Test fetch with different wait_until values."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]

        # Patch the async_playwright function
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Call the function with a different wait_until value
        await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            wait_until="domcontentloaded",
        )

        # Verify the wait_until parameter was passed correctly
        assert page_mock.goto.called
        call_args = page_mock.goto.call_args
        assert call_args.kwargs.get("wait_until") == "domcontentloaded"
