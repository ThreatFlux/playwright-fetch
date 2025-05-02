"""Tests for error handling in robots.txt functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

from mcp_server_fetch.server import check_may_autonomously_fetch_url


class MockAsyncContext:
    """Mock for an async context manager."""

    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
class TestRobotsTxtErrors:
    """Test the error handling in robots.txt functionality."""

    async def test_robots_txt_connection_error(self, monkeypatch):
        """Test handling of a connection error when fetching robots.txt."""
        # Import the necessary modules
        from httpx import AsyncClient, HTTPError

        # Create a mock client that raises an error
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=HTTPError("Connection error"))

        # Mock the AsyncClient context manager
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncContext(mock_client))

        # Call the function and expect a McpError
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "Failed to fetch robots.txt" in str(excinfo.value)
        assert "connection issue" in str(excinfo.value)

        # Verify the client was called with correct URL and headers
        mock_client.get.assert_called_once_with(
            "https://example.com/robots.txt",
            follow_redirects=True,
            headers={"User-Agent": "TestUserAgent"},
        )

    async def test_robots_txt_forbidden_response(self, monkeypatch):
        """Test handling of a 403 response for robots.txt."""
        # Create a mock response with 403 status code
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        # Create a mock client that returns the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Mock the AsyncClient context manager
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncContext(mock_client))

        # Call the function and expect a McpError
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "When fetching robots.txt" in str(excinfo.value)
        assert "received status 403" in str(excinfo.value)
        assert "autonomous fetching is not allowed" in str(excinfo.value)

    async def test_robots_txt_denied(self, monkeypatch):
        """Test handling when robots.txt explicitly denies access."""
        # Create a mock response with a robots.txt that denies access
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        User-agent: *
        Disallow: /
        """

        # Create a mock client that returns the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Create a mock Protego parser that denies access
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = False

        # Mock the AsyncClient context manager and Protego parser
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncContext(mock_client))
        monkeypatch.setattr("protego.Protego.parse", MagicMock(return_value=mock_parser))

        # Call the function and expect a McpError
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error message
        assert "The site's robots.txt" in str(excinfo.value)
        assert "autonomous fetching of this page is not allowed" in str(excinfo.value)

        # Verify Protego was called correctly
        mock_parser.can_fetch.assert_called_once_with("https://example.com", "TestUserAgent")

    async def test_robots_txt_allowed(self, monkeypatch):
        """Test successful case when robots.txt allows access."""
        # Create a mock response with a robots.txt that allows access
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        User-agent: *
        Allow: /
        """

        # Create a mock client that returns the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Create a mock Protego parser that allows access
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True

        # Mock the AsyncClient context manager and Protego parser
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncContext(mock_client))
        monkeypatch.setattr("protego.Protego.parse", MagicMock(return_value=mock_parser))

        # Call the function - should succeed without error
        await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify Protego was called correctly
        mock_parser.can_fetch.assert_called_once_with("https://example.com", "TestUserAgent")

    async def test_robots_txt_not_found(self, monkeypatch):
        """Test handling when robots.txt is not found (404)."""
        # Create a mock response with 404 status code
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Create a mock client that returns the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Mock the AsyncClient context manager
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncContext(mock_client))

        # Call the function - should succeed without error (404 is treated as permission)
        await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

    async def test_robots_txt_with_proxy(self, monkeypatch):
        """Test fetching robots.txt with a proxy."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        User-agent: *
        Allow: /
        """

        # Create a mock client that returns the response
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Keep track of the proxies passed to AsyncClient
        proxy_used = None

        def mock_async_client(proxies=None):
            nonlocal proxy_used
            proxy_used = proxies
            return MockAsyncContext(mock_client)

        # Create a mock Protego parser that allows access
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True

        # Mock the AsyncClient constructor and Protego parser
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)
        monkeypatch.setattr("protego.Protego.parse", MagicMock(return_value=mock_parser))

        # Call the function with a proxy
        proxy_url = "http://proxy.example.com"
        await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent", proxy_url)

        # Verify the proxy was passed to AsyncClient
        assert proxy_used == proxy_url
