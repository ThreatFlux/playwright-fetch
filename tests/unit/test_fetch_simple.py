"""Simple unit tests for the fetch_url_with_playwright function."""

import asyncio
import re
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData


# Class for async context manager mocking
class AsyncContextManagerMock:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
class TestFetchUrlSimple:
    """Basic tests for the fetch functionality with simplified mocking approach."""

    async def test_html_to_markdown(self):
        """Test the HTML to Markdown conversion function."""
        from mcp_server_fetch.server import html_to_markdown

        # Test basic conversion
        html = "<h1>Test</h1><p>This is a test</p>"
        markdown = html_to_markdown(html)

        assert "# Test" in markdown
        assert "This is a test" in markdown

    async def test_fetch_with_mocks(self, monkeypatch):
        """Test fetch_url_with_playwright with complete mocking."""
        # Import the server first to get a reference to the original modules
        import mcp_server_fetch.server as server_module

        # Create all our mocks first
        html_content = "<html><body><h1>Test</h1><p>Sample content</p></body></html>"
        mock_html_to_markdown = MagicMock(return_value="# Test\n\nSample content")

        # Create a mock for Playwright's Page object
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=html_content)
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        # Create a mock for browser context
        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        # Create a mock for the browser
        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        # Create a mock for Playwright instance
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Set up our mocks using monkeypatch
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Now call the function
        content, prefix = await server_module.fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify the result
        assert content == "# Test\n\nSample content"
        assert prefix == ""

        # Verify the mocks were called correctly
        mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until="networkidle",
            timeout=30000,
        )
        mock_page.wait_for_load_state.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_non_html(self, monkeypatch):
        """Test fetching non-HTML content (like JSON)."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create all our mocks first
        json_content = '{"key": "value", "items": [1, 2, 3]}'

        # Create a mock for Playwright's Page object
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "application/json"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=json_content)
        mock_page.close = AsyncMock()

        # Create mock objects for the rest of the chain
        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Set up our mocks using monkeypatch
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call the function with force_raw=True
        content, prefix = await server_module.fetch_url_with_playwright(
            "https://example.com/api",
            "TestUserAgent",
            force_raw=True,
        )

        # Verify the result
        assert content == json_content
        assert "application/json" in prefix

    async def test_fetch_with_proxy(self, monkeypatch):
        """Test fetch with proxy settings."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create all our mocks first
        html_content = "<html><body><p>Test content</p></body></html>"
        mock_html_to_markdown = MagicMock(return_value="Test content")

        # Mock ProxySettings class
        mock_proxy_settings = MagicMock()
        mock_proxy_settings_class = MagicMock(return_value=mock_proxy_settings)

        # Create mocks for the Playwright objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=html_content)
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Set up our mocks using monkeypatch
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)
        monkeypatch.setattr(server_module, "ProxySettings", mock_proxy_settings_class)
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call the function with a proxy
        await server_module.fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            proxy_url="http://proxy.example.com",
        )

        # Verify proxy settings were created correctly
        mock_proxy_settings_class.assert_called_once_with(server="http://proxy.example.com")

        # Verify the proxy was passed to chromium.launch
        mock_playwright.chromium.launch.assert_called_once()
        assert mock_playwright.chromium.launch.call_args[1]["proxy"] == mock_proxy_settings

    async def test_fetch_error_handling(self, monkeypatch):
        """Test error handling during fetch."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create a mock exception class
        class MockPlaywrightError(Exception):
            pass

        # Create the browser mocks
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(side_effect=MockPlaywrightError("Test error"))
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Set up our mocks using monkeypatch
        monkeypatch.setattr(server_module, "PlaywrightError", MockPlaywrightError)
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call the function and expect a McpError
        with pytest.raises(McpError) as excinfo:
            await server_module.fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify the error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "Test error" in str(excinfo.value)

        # Verify cleanup happened despite the error
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_different_wait_until_options(self, monkeypatch):
        """Test different wait_until options."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create shared mocks
        html_content = "<html><body><p>Test content</p></body></html>"
        mock_html_to_markdown = MagicMock(return_value="Test content")

        # Set up the html_to_markdown mock
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Test each wait_until option
        for option in ["commit", "domcontentloaded", "load", "networkidle"]:
            # Create fresh mocks for each iteration
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()
            mock_page.goto.return_value.status = 200
            mock_page.goto.return_value.headers = {"content-type": "text/html"}
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.content = AsyncMock(return_value=html_content)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.close = AsyncMock()

            mock_context = MagicMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

            # Create a function that captures the current mock_playwright instance
            def create_context_manager_factory(playwright_instance):
                def factory():
                    return AsyncContextManagerMock(playwright_instance)

                return factory

            # Set up async_playwright mock for this iteration with properly captured variable
            monkeypatch.setattr(
                server_module,
                "async_playwright",
                create_context_manager_factory(mock_playwright),
            )

            # Call the function with this wait_until option
            await server_module.fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
                wait_until=option,
            )

            # Verify wait_until was passed correctly
            mock_page.goto.assert_called_once_with(
                "https://example.com",
                wait_until=option,
                timeout=30000,
            )
