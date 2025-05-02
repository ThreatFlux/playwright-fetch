"""Tests for the core server functionality."""

import asyncio
from typing import Literal, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, ErrorData

from mcp_server_fetch.server import Fetch, serve


class AsyncContextManagerMock:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
class TestServerFunctions:
    """Test the server functionality."""

    async def test_fetch_model_validation(self):
        """Test validation of the Fetch model."""
        # Valid arguments
        valid_args = {"url": "https://example.com", "max_length": 1000}
        fetch = Fetch(**valid_args)
        assert str(fetch.url) == "https://example.com/"
        assert fetch.max_length == 1000
        assert fetch.start_index == 0
        assert fetch.raw is False
        assert fetch.wait_for_js is True

        # Test default values
        fetch = Fetch(url="https://example.com")
        assert fetch.max_length == 5000
        assert fetch.start_index == 0
        assert fetch.raw is False
        assert fetch.wait_for_js is True

        # Override defaults
        fetch = Fetch(
            url="https://example.com",
            max_length=10000,
            start_index=500,
            raw=True,
            wait_for_js=False,
        )
        assert fetch.max_length == 10000
        assert fetch.start_index == 500
        assert fetch.raw is True
        assert fetch.wait_for_js is False

        # Test validation error for URLs
        with pytest.raises(ValueError):
            Fetch(url="not-a-url")

        # Test validation for max_length
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=0)

        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=2000000)

        # Test validation for start_index
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", start_index=-1)

    async def test_server_setup(self, monkeypatch):
        """Test the server setup with basic configuration."""
        # Import the server module
        from mcp.server import Server

        import mcp_server_fetch.server as server_module

        # Mock server instance
        mock_server = MagicMock()
        mock_server.list_tools = MagicMock(return_value=MagicMock())
        mock_server.list_prompts = MagicMock(return_value=MagicMock())
        mock_server.call_tool = MagicMock(return_value=MagicMock())
        mock_server.get_prompt = MagicMock(return_value=MagicMock())
        mock_server.create_initialization_options = MagicMock(return_value={})

        # Mock Server constructor
        mock_server_constructor = MagicMock(return_value=mock_server)

        # Mock stdio_server
        mock_stdio_server = MagicMock()
        mock_stdio_server.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_stdio_server.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock run
        mock_run = AsyncMock()
        mock_server.run = mock_run

        # Set up mocks
        monkeypatch.setattr(server_module, "Server", mock_server_constructor)
        monkeypatch.setattr(server_module, "stdio_server", mock_stdio_server)

        # Call serve function
        await serve(
            custom_user_agent="TestUserAgent",
            ignore_robots_txt=True,
            proxy_url="http://proxy.example.com",
            headless=False,
            wait_until="domcontentloaded",
        )

        # Verify server creation
        mock_server_constructor.assert_called_once_with("mcp-playwright-fetch")

        # Verify decorators were used
        assert mock_server.list_tools.called
        assert mock_server.list_prompts.called
        assert mock_server.call_tool.called
        assert mock_server.get_prompt.called

        # Verify server was run
        assert mock_run.called

    async def test_get_robots_txt_url_with_various_urls(self):
        """Test get_robots_txt_url function with various URLs."""
        from mcp_server_fetch.server import get_robots_txt_url

        # Basic URL
        assert get_robots_txt_url("https://example.com") == "https://example.com/robots.txt"

        # URL with path
        assert get_robots_txt_url("https://example.com/page.html") == "https://example.com/robots.txt"

        # URL with query parameters
        assert get_robots_txt_url("https://example.com/search?q=test") == "https://example.com/robots.txt"

        # URL with fragment
        assert get_robots_txt_url("https://example.com/page#section") == "https://example.com/robots.txt"

        # URL with port
        assert get_robots_txt_url("https://example.com:8080/api") == "https://example.com:8080/robots.txt"

        # URL with subdomain
        assert get_robots_txt_url("https://blog.example.com") == "https://blog.example.com/robots.txt"

    async def test_html_to_markdown_conversion(self):
        """Test the HTML to markdown conversion function."""
        from mcp_server_fetch.server import html_to_markdown

        # Simple HTML
        html = "<h1>Test Heading</h1><p>Test paragraph with <strong>bold</strong> and <em>italic</em> text.</p>"
        markdown = html_to_markdown(html)

        assert "# Test Heading" in markdown
        assert "Test paragraph with" in markdown
        assert "**bold**" in markdown
        assert "*italic*" in markdown

        # Lists
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """
        markdown = html_to_markdown(html)

        assert "* Item 1" in markdown
        assert "* Item 2" in markdown
        assert "* Item 3" in markdown

        # Links
        html = "<p>Visit <a href='https://example.com'>Example</a> website</p>"
        markdown = html_to_markdown(html)

        assert "Visit [Example](https://example.com)" in markdown

    async def test_fetch_url_with_playwright_basic(self, monkeypatch):
        """Test the fetch_url_with_playwright function with basic parameters."""
        # Import the necessary components
        import mcp_server_fetch.server as server_module
        from mcp_server_fetch.server import fetch_url_with_playwright

        # Create mock objects
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"

        # Mock the async_playwright and related objects
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

        # Setup the mock HTML to markdown function
        mock_html_to_markdown = MagicMock(return_value="# Test\n\nContent")

        # Apply mocks
        monkeypatch.setattr(server_module, "html_to_markdown", mock_html_to_markdown)
        monkeypatch.setattr(server_module, "async_playwright", lambda: AsyncContextManagerMock(mock_playwright))

        # Call the function
        content, prefix = await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            force_raw=False,
            proxy_url=None,
            headless=True,
            wait_until="networkidle",
        )

        # Verify results
        assert content == "# Test\n\nContent"
        assert prefix == ""

        # Verify playwright usage
        mock_browser.new_context.assert_called_once_with(user_agent="TestUserAgent")
        mock_context.new_page.assert_called_once()
        mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until="networkidle",
            timeout=30000,
        )
        mock_page.wait_for_load_state.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

        # Verify HTML to markdown conversion
        mock_html_to_markdown.assert_called_once()
