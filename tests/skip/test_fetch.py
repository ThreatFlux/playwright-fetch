"""Tests for the fetch_url_with_playwright function."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from playwright.async_api import Error as PlaywrightError

from mcp_server_fetch.server import fetch_url_with_playwright


class TestFetchUrlWithPlaywright:
    """Tests for the fetch_url_with_playwright function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_playwright):
        """Test a successful URL fetch."""
        # Configure the mock page content
        mock_playwright["page"].content.return_value = """
        <html>
            <body>
                <main>
                    <h1>Test Page</h1>
                    <p>This is some test content.</p>
                </main>
            </body>
        </html>
        """

        # Mock the main content element
        main_element = AsyncMock()
        main_element.inner_html.return_value = """
            <h1>Test Page</h1>
            <p>This is some test content.</p>
        """
        mock_playwright["page"].query_selector.return_value = main_element

        # Run the fetch function
        content, prefix = await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the results
        assert prefix == ""  # Successful markdown conversion has no prefix
        assert "# Test Page" in content
        assert "This is some test content." in content

        # Verify the browser was launched with expected arguments
        mock_playwright["playwright"].chromium.launch.assert_called_with(headless=True)

        # Verify the context was created with the user agent
        mock_playwright["browser"].new_context.assert_called_with(user_agent="TestUserAgent")

        # Verify the page was navigated to the URL with expected options
        mock_playwright["page"].goto.assert_called_with("https://example.com", wait_until="networkidle", timeout=30000)

    @pytest.mark.asyncio
    async def test_fetch_with_proxy(self, mock_playwright):
        """Test fetching with a proxy configuration."""
        # Run the fetch function with a proxy
        await fetch_url_with_playwright(
            "https://example.com",
            "TestUserAgent",
            proxy_url="http://proxy.example.com:8080",
        )

        # Verify the browser was launched with proxy settings
        launch_call = mock_playwright["playwright"].chromium.launch.call_args
        assert "proxy" in launch_call[1]
        assert launch_call[1]["proxy"].server == "http://proxy.example.com:8080"

    @pytest.mark.asyncio
    async def test_visible_browser(self, mock_playwright):
        """Test fetching with a visible (non-headless) browser."""
        # Run the fetch function with headless=False
        await fetch_url_with_playwright("https://example.com", "TestUserAgent", headless=False)

        # Verify the browser was launched with headless=False
        mock_playwright["playwright"].chromium.launch.assert_called_with(headless=False)

    @pytest.mark.asyncio
    async def test_fetch_non_html(self, mock_playwright):
        """Test fetching non-HTML content."""
        # Configure the mock response to indicate non-HTML content
        mock_playwright["response"].headers = {"content-type": "application/json"}
        mock_playwright["page"].content.return_value = '{"key": "value"}'

        # Run the fetch function
        content, prefix = await fetch_url_with_playwright("https://example.com/data.json", "TestUserAgent")

        # Verify the results
        assert "Content type application/json cannot be simplified to markdown" in prefix
        assert '{"key": "value"}' in content

    @pytest.mark.asyncio
    async def test_fetch_force_raw(self, mock_playwright):
        """Test fetching with force_raw=True."""
        # Configure the mock response
        mock_playwright["response"].headers = {"content-type": "text/html"}
        mock_playwright["page"].content.return_value = "<html><body><p>Raw HTML</p></body></html>"

        # Run the fetch function with force_raw=True
        content, prefix = await fetch_url_with_playwright("https://example.com", "TestUserAgent", force_raw=True)

        # Verify raw HTML is returned
        assert "Content type text/html cannot be simplified to markdown" in prefix
        assert "<html><body><p>Raw HTML</p></body></html>" in content

    @pytest.mark.asyncio
    async def test_http_error_response(self, mock_playwright):
        """Test handling HTTP error responses."""
        # Configure the mock response to have an error status
        mock_playwright["response"].status = 404

        # The function should raise an McpError
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright("https://example.com/not-found", "TestUserAgent")

        # Verify the error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "status code 404" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_no_response(self, mock_playwright):
        """Test handling no response from goto."""
        # Configure goto to return None (no response)
        mock_playwright["page"].goto.return_value = None

        # The function should raise an McpError
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "Failed to fetch" in str(excinfo.value)
        assert "no response received" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_playwright_error(self, mock_playwright):
        """Test handling Playwright errors."""
        # Configure goto to raise a PlaywrightError
        error = PlaywrightError("Connection refused")
        mock_playwright["page"].goto.side_effect = error

        # The function should raise an McpError
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "Failed to fetch" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_playwright):
        """Test handling timeout errors."""
        # Configure goto to raise a TimeoutError
        mock_playwright["page"].goto.side_effect = asyncio.TimeoutError()

        # The function should raise an McpError
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "Timeout when fetching" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_general_exception(self, mock_playwright):
        """Test handling general exceptions."""
        # Configure goto to raise a general exception
        mock_playwright["page"].goto.side_effect = Exception("Unexpected error")

        # The function should raise an McpError
        with pytest.raises(McpError) as excinfo:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "Error fetching" in str(excinfo.value)
        assert "Unexpected error" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_content_extraction_failure(self, mock_playwright):
        """Test when content extraction fails but HTML content is available."""
        # Configure the mock page content
        mock_playwright["page"].content.return_value = "<html><body><p>HTML content</p></body></html>"

        # Configure element selection to fail
        mock_playwright["page"].query_selector.side_effect = PlaywrightError("Selector error")

        # The function should fall back to the full HTML content
        content, prefix = await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the results - should have converted the full HTML to markdown
        assert prefix == ""
        assert "HTML content" in content
