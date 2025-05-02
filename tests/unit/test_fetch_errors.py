"""Tests for error handling in fetch functionality."""

import asyncio
from typing import Any, Dict, Literal, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

from mcp_server_fetch.server import fetch_url_with_playwright


class AsyncContextManagerMock:
    """Mock for async context manager pattern."""

    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
class TestFetchErrors:
    """Test error handling in the fetch functionality."""

    async def test_fetch_no_response(self, monkeypatch):
        """Test handling when there's no response."""
        # Import the server module
        from playwright.async_api import Error as PlaywrightError

        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        # Return None for goto to simulate no response
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call function and expect error
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "no response received" in str(excinfo.value)

        # In the error cases, page.close is never called because we raise before it
        # but context and browser are closed in the finally block
        # No need to verify mock_page.close here
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_http_error(self, monkeypatch):
        """Test handling when there's an HTTP error code."""
        # Import the server module
        from playwright.async_api import Error as PlaywrightError

        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        # Return response with error status
        mock_response = MagicMock()
        mock_response.status = 404
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call function and expect error
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "status code 404" in str(excinfo.value)

        # In the error cases, page.close is never called because we raise before it
        # but context and browser are closed in the finally block
        # No need to verify mock_page.close here
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_playwright_error(self, monkeypatch):
        """Test handling when Playwright raises an error."""
        # Import the server module
        from playwright.async_api import Error as PlaywrightError

        import mcp_server_fetch.server as server_module

        # Create PlaywrightError for testing
        class TestPlaywrightError(PlaywrightError):
            pass

        # Create mock objects
        mock_page = MagicMock()
        # Make goto raise a PlaywrightError
        mock_page.goto = AsyncMock(side_effect=TestPlaywrightError("Browser error"))
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call function and expect error
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "Browser error" in str(excinfo.value)

        # Verify cleanup was called
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_timeout_error(self, monkeypatch):
        """Test handling when there's a timeout error."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        # Make goto raise a timeout error
        mock_page.goto = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call function and expect error
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify error message
        assert "Timeout when fetching" in str(excinfo.value)

        # Verify cleanup was called
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_generic_error(self, monkeypatch):
        """Test handling when there's a generic error."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        # Make goto raise a generic error
        mock_page.goto = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call function and expect error
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright(
                "https://example.com",
                "TestUserAgent",
            )

        # Verify error message
        assert "Error fetching" in str(excinfo.value)
        assert "Unexpected error" in str(excinfo.value)

        # Verify cleanup was called
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

    async def test_fetch_content_extraction_error(self, monkeypatch):
        """Test handling when there's an error during content extraction."""
        # Import the server module
        from playwright.async_api import Error as PlaywrightError

        import mcp_server_fetch.server as server_module

        # Create mock objects
        html_content = "<html><body><main>Content</main></body></html>"

        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=html_content)

        # Define an error message to avoid TRY003 linting error
        element_error = "Element error"

        # Make query_selector raise an error for specific selectors
        def mock_query_selector(selector):
            if selector == "main":
                raise PlaywrightError(element_error)
            return None

        mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        # Mock HTML to markdown
        mock_html_to_markdown = MagicMock(return_value="Converted content")

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Should still succeed but with fallback to the whole content
        assert content == "Converted content"
        assert prefix == ""

        # HTML to markdown should be called with the full HTML
        mock_html_to_markdown.assert_called_with(html_content)

        # In the error cases, page.close is never called because we raise before it
        # but context and browser are closed in the finally block
        # No need to verify mock_page.close here
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
