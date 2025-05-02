"""Tests for the fetch content extraction functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
class TestContentExtraction:
    """Tests for the content extraction logic in fetch_url_with_playwright."""

    async def test_content_extraction_main_element_found(self, monkeypatch):
        """Test content extraction when a main element is found."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_element = MagicMock()
        mock_element.inner_html = AsyncMock(return_value="<h1>Main Content</h1><p>This is the main content</p>")

        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body><main>Main content</main></body></html>")
        mock_page.query_selector = AsyncMock()
        # Make query_selector return element only for "main" selector
        mock_page.query_selector.side_effect = lambda selector: mock_element if selector == "main" else None
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
        mock_html_to_markdown = MagicMock(return_value="# Main Content\n\nThis is the main content")

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify results
        assert content == "# Main Content\n\nThis is the main content"
        assert prefix == ""

        # Verify element extraction
        mock_page.query_selector.assert_called_with("main")
        mock_element.inner_html.assert_called_once()

        # Verify HTML to markdown was called with the main content
        mock_html_to_markdown.assert_called_once_with("<h1>Main Content</h1><p>This is the main content</p>")

    async def test_content_extraction_try_all_selectors(self, monkeypatch):
        """Test content extraction with multiple selector attempts."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_element = MagicMock()
        mock_element.inner_html = AsyncMock(return_value="<h1>Article Content</h1><p>This is article content</p>")

        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        html_content = "<html><body><article>Article content</article></body></html>"
        mock_page.content = AsyncMock(return_value=html_content)

        # Make selector find nothing for first few selectors, then find article
        def mock_query_selector(selector):
            if selector == "article":
                return mock_element
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
        mock_html_to_markdown = MagicMock(return_value="# Article Content\n\nThis is article content")

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify results
        assert content == "# Article Content\n\nThis is article content"
        assert prefix == ""

        # Verify HTML to markdown was called with the article content
        mock_html_to_markdown.assert_called_once_with("<h1>Article Content</h1><p>This is article content</p>")

    async def test_content_extraction_fallback_to_body(self, monkeypatch):
        """Test fallback to whole body when no specific content element is found."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        html_content = "<html><body><div>General content</div></body></html>"
        mock_page.content = AsyncMock(return_value=html_content)

        # Make all selectors return None
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

        # Mock HTML to markdown
        mock_html_to_markdown = MagicMock(return_value="General content")

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify results
        assert content == "General content"
        assert prefix == ""

        # Verify HTML to markdown was called with the full HTML
        mock_html_to_markdown.assert_called_once_with(html_content)

    async def test_content_extraction_error_with_fallback(self, monkeypatch):
        """Test fallback when there's an error during extraction."""
        # Import the server module
        from playwright.async_api import Error as PlaywrightError

        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        html_content = "<html><body><article>Content</article></body></html>"
        mock_page.content = AsyncMock(return_value=html_content)

        # Make inner_html fail with an error
        mock_element = MagicMock()
        mock_element.inner_html = AsyncMock(side_effect=PlaywrightError("Element error"))

        # First return the element that will fail, then return None for other selectors
        selector_calls = 0

        def mock_query_selector(selector):
            nonlocal selector_calls
            selector_calls += 1
            if selector_calls == 1:  # First call
                return mock_element
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
        mock_html_to_markdown = MagicMock(return_value="Fallback content")

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)
        monkeypatch.setattr(server_module, "PlaywrightError", PlaywrightError)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify results - should fall back to using the full HTML
        assert content == "Fallback content"
        assert prefix == ""

        # Verify HTML to markdown was called with the full HTML
        mock_html_to_markdown.assert_called_once_with(html_content)

    async def test_non_html_content_handling(self, monkeypatch):
        """Test handling of non-HTML content types."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "application/json"}
        mock_page.wait_for_load_state = AsyncMock()
        json_content = '{"key": "value", "items": [1, 2, 3]}'
        mock_page.content = AsyncMock(return_value=json_content)
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

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com/data.json",
            "TestUserAgent",
        )

        # Verify results - should return raw content with prefix
        assert content == json_content
        assert "application/json" in prefix
        assert "cannot be simplified to markdown" in prefix

    async def test_clean_up_markdown(self, monkeypatch):
        """Test the markdown cleanup process."""
        # Import the server module
        import mcp_server_fetch.server as server_module

        # Create mock objects
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.goto.return_value.headers = {"content-type": "text/html"}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body><div>Content</div></body></html>")
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

        # Create markdown with excess newlines
        markdown_with_newlines = "# Title\n\n\n\n\nParagraph\n\n\n\nAnother paragraph"
        mock_html_to_markdown = MagicMock(return_value=markdown_with_newlines)

        # Apply mocks
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
        )

        # Verify excess newlines were cleaned up
        assert content == "# Title\n\nParagraph\n\nAnother paragraph"
        assert prefix == ""
