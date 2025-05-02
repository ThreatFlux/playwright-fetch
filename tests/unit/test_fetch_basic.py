"""Basic tests for URL fetching with Playwright."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import markdownify
import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

# Import the function only - not the whole module
# This allows us to properly patch dependencies
from mcp_server_fetch.server import html_to_markdown


@pytest.mark.asyncio
class TestFetchBasic:
    """Basic tests for the fetch_url_with_playwright functionality."""

    async def test_fetch_url_basic(self, monkeypatch):
        """Test basic fetch functionality with HTML content."""
        # Import the function here after patching
        from mcp_server_fetch.server import fetch_url_with_playwright

        # Sample HTML content
        html_content = "<html><body><h1>Example</h1><p>Content</p></body></html>"
        markdown_result = "# Example\n\nContent"

        # Mock objects
        mock_element = MagicMock()
        mock_element.inner_html = AsyncMock(return_value="<h1>Example</h1><p>Content</p>")

        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=html_content)
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        # Create a mock for the context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_playwright

            async def __aexit__(self, *args):
                pass

        # Create a mock for the html_to_markdown function
        mock_html_to_markdown = MagicMock(return_value=markdown_result)

        # Patch the dependencies
        with patch("playwright.async_api.async_playwright", return_value=MockAsyncContextManager()):
            with patch("mcp_server_fetch.server.html_to_markdown", mock_html_to_markdown):
                # Call the function
                content, prefix = await fetch_url_with_playwright(
                    "https://example.com",
                    "TestAgent",
                )

                # Verify results
                assert content == markdown_result
                assert prefix == ""

                # Verify calls
                mock_page.goto.assert_called_once_with(
                    "https://example.com",
                    wait_until="networkidle",
                    timeout=30000,
                )
                mock_page.wait_for_load_state.assert_called_once()
                mock_context.close.assert_called_once()
                mock_browser.close.assert_called_once()

    async def test_fetch_url_non_html(self, monkeypatch):
        """Test fetching non-HTML content."""
        # Import the function here after patching
        from mcp_server_fetch.server import fetch_url_with_playwright

        # Sample JSON content
        json_content = '{"key": "value", "items": [1, 2, 3]}'

        # Mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "application/json"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value=json_content)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        # Create a mock for the context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_playwright

            async def __aexit__(self, *args):
                pass

        # Patch the dependencies
        with patch("playwright.async_api.async_playwright", return_value=MockAsyncContextManager()):
            # Call the function with force_raw=True
            content, prefix = await fetch_url_with_playwright(
                "https://example.com/api",
                "TestAgent",
                force_raw=True,
            )

            # Verify results
            assert content == json_content
            assert "application/json" in prefix

            # Verify calls were made correctly
            mock_page.goto.assert_called_once()
            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()

    async def test_fetch_url_with_proxy(self, monkeypatch):
        """Test fetching with proxy configuration."""
        # Import the function here after patching
        from playwright.async_api import ProxySettings

        from mcp_server_fetch.server import fetch_url_with_playwright

        # Mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        # Create mock for ProxySettings
        mock_proxy_settings = MagicMock()

        # Create a mock for the context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_playwright

            async def __aexit__(self, *args):
                pass

        # Patch the dependencies
        with patch("playwright.async_api.async_playwright", return_value=MockAsyncContextManager()):
            with patch("playwright.async_api.ProxySettings", return_value=mock_proxy_settings):
                # Call the function with proxy
                await fetch_url_with_playwright(
                    "https://example.com",
                    "TestAgent",
                    proxy_url="http://proxy.example.com",
                )

                # Verify the proxy was used in the browser launch
                mock_chromium.launch.assert_called_once()
                # Check if proxy was included in kwargs
                assert "proxy" in mock_chromium.launch.call_args[1]

    async def test_fetch_url_error_handling(self, monkeypatch):
        """Test error handling during fetch."""
        # Import the function here after patching
        from playwright.async_api import Error as PlaywrightError

        from mcp_server_fetch.server import fetch_url_with_playwright

        # Mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(side_effect=Exception("Navigation failed"))
        mock_page.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        # Create a mock for the context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_playwright

            async def __aexit__(self, *args):
                pass

        # Create a fake PlaywrightError for testing
        mock_playwright_error = MagicMock(spec=PlaywrightError)

        # Patch the dependencies
        with patch("playwright.async_api.async_playwright", return_value=MockAsyncContextManager()):
            with patch("playwright.async_api.Error", mock_playwright_error):
                # Call the function and expect an error
                with pytest.raises(McpError) as excinfo:
                    await fetch_url_with_playwright("https://example.com", "TestAgent")

                # Verify error
                assert "Error fetching" in str(excinfo.value)
                mock_context.close.assert_called_once()
                mock_browser.close.assert_called_once()

    async def test_fetch_url_different_wait_until(self, monkeypatch):
        """Test different wait_until options."""
        # Import the function here after patching
        from mcp_server_fetch.server import fetch_url_with_playwright

        # Test each wait_until option
        for option in ["commit", "domcontentloaded", "load", "networkidle"]:
            # Mock objects
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()
            mock_page.goto.return_value.status = 200
            mock_page.goto.return_value.headers = {"content-type": "text/html"}
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.close = AsyncMock()

            mock_context = MagicMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()

            mock_chromium = MagicMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright = MagicMock()
            mock_playwright.chromium = mock_chromium

            # Create a mock for the context manager with a captured playwright instance
            # This avoids the B023 linting issue by capturing the variable in the closure
            def create_context_manager(playwright_instance):
                class MockAsyncContextManager:
                    async def __aenter__(self):
                        return playwright_instance

                    async def __aexit__(self, *args):
                        pass

                return MockAsyncContextManager()

            mock_context_manager = create_context_manager(mock_playwright)

            # Create a mock for the html_to_markdown function
            mock_html_to_markdown = MagicMock(return_value="Test")

            # Patch the dependencies
            with patch("playwright.async_api.async_playwright", return_value=mock_context_manager):
                with patch("mcp_server_fetch.server.html_to_markdown", mock_html_to_markdown):
                    # Call the function with the wait_until option
                    await fetch_url_with_playwright(
                        "https://example.com",
                        "TestAgent",
                        wait_until=option,
                    )

                    # Verify wait_until was used
                    mock_page.goto.assert_called_once_with(
                        "https://example.com",
                        wait_until=option,
                        timeout=30000,
                    )
