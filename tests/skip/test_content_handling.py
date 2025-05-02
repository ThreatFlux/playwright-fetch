"""Tests for content handling in the MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_fetch.server import fetch_url_with_playwright, html_to_markdown


class TestContentHandling:
    """Tests for content extraction and transformation."""

    def test_html_to_markdown(self, mock_html_content, mock_markdown_content):
        """Test HTML to Markdown conversion."""
        # Test with a sample HTML content
        result = html_to_markdown(mock_html_content)
        # Clean up whitespace in both strings for comparison
        expected = "\n".join(line.strip() for line in mock_markdown_content.split("\n") if line.strip())
        result_cleaned = "\n".join(line.strip() for line in result.split("\n") if line.strip())
        assert expected in result_cleaned

    @pytest.mark.asyncio
    async def test_fetch_with_main_content(self, monkeypatch):
        """Test that the fetch function extracts main content when available."""
        # Mock response, page, and element
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.headers = {"content-type": "text/html"}

        element_mock = AsyncMock()
        element_mock.inner_html = AsyncMock(return_value="<p>Main content</p>")

        page_mock = AsyncMock()
        page_mock.goto = AsyncMock(return_value=response_mock)
        page_mock.content = AsyncMock(return_value="<html><body><main><p>Main content</p></main></body></html>")
        page_mock.query_selector = AsyncMock(return_value=element_mock)
        page_mock.wait_for_load_state = AsyncMock()

        context_mock = AsyncMock()
        context_mock.new_page = AsyncMock(return_value=page_mock)
        context_mock.close = AsyncMock()

        browser_mock = AsyncMock()
        browser_mock.new_context = AsyncMock(return_value=context_mock)
        browser_mock.close = AsyncMock()

        playwright_mock = MagicMock()
        playwright_mock.chromium = MagicMock()
        playwright_mock.chromium.launch = AsyncMock(return_value=browser_mock)

        # Setup monkeypatching for async_playwright
        class MockPlaywright:
            def __init__(self):
                pass

            async def __aenter__(self):
                return playwright_mock

            async def __aexit__(self, *args, **kwargs):
                pass

        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: MockPlaywright())

        # Test fetch
        content, prefix = await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify content extraction
        assert "Main content" in content
        assert prefix == ""
        assert page_mock.query_selector.called
        page_mock.query_selector.assert_any_call("main")

    @pytest.mark.asyncio
    async def test_fetch_non_html_content(self, monkeypatch):
        """Test fetching non-HTML content."""
        # Mock response, page, and browser
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.headers = {"content-type": "application/json"}

        page_mock = AsyncMock()
        page_mock.goto = AsyncMock(return_value=response_mock)
        page_mock.content = AsyncMock(return_value='{"key": "value"}')
        page_mock.wait_for_load_state = AsyncMock()

        context_mock = AsyncMock()
        context_mock.new_page = AsyncMock(return_value=page_mock)
        context_mock.close = AsyncMock()

        browser_mock = AsyncMock()
        browser_mock.new_context = AsyncMock(return_value=context_mock)
        browser_mock.close = AsyncMock()

        playwright_mock = MagicMock()
        playwright_mock.chromium = MagicMock()
        playwright_mock.chromium.launch = AsyncMock(return_value=browser_mock)

        # Setup monkeypatching for async_playwright
        class MockPlaywright:
            def __init__(self):
                pass

            async def __aenter__(self):
                return playwright_mock

            async def __aexit__(self, *args, **kwargs):
                pass

        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: MockPlaywright())

        # Test fetch
        content, prefix = await fetch_url_with_playwright("https://example.com/data.json", "TestUserAgent")

        # Verify content handling
        assert '{"key": "value"}' in content
        assert "application/json" in prefix
        assert "cannot be simplified to markdown" in prefix

    @pytest.mark.asyncio
    async def test_fetch_with_proxy(self, monkeypatch):
        """Test fetching with a proxy server."""
        # Track if proxy was used
        proxy_used = False

        # Mock response, page, and browser
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.headers = {"content-type": "text/html"}

        page_mock = AsyncMock()
        page_mock.goto = AsyncMock(return_value=response_mock)
        page_mock.content = AsyncMock(return_value="<html><body><p>Test content</p></body></html>")
        page_mock.query_selector = AsyncMock(return_value=None)
        page_mock.wait_for_load_state = AsyncMock()

        context_mock = AsyncMock()
        context_mock.new_page = AsyncMock(return_value=page_mock)
        context_mock.close = AsyncMock()

        browser_mock = AsyncMock()
        browser_mock.new_context = AsyncMock(return_value=context_mock)
        browser_mock.close = AsyncMock()

        playwright_mock = MagicMock()
        playwright_mock.chromium = MagicMock()

        # Custom launch function that checks for proxy
        async def mock_launch(**kwargs):
            nonlocal proxy_used
            if "proxy" in kwargs:
                proxy_used = True
            return browser_mock

        playwright_mock.chromium.launch = mock_launch

        # Setup monkeypatching for async_playwright
        class MockPlaywright:
            def __init__(self):
                pass

            async def __aenter__(self):
                return playwright_mock

            async def __aexit__(self, *args, **kwargs):
                pass

        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: MockPlaywright())

        # Test fetch with proxy
        await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            proxy_url="http://proxy.example.com:8080",
        )

        # Verify proxy was used
        assert proxy_used is True
