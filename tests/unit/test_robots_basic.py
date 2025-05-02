"""Basic tests for robots.txt handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

from mcp_server_fetch.server import check_may_autonomously_fetch_url


# Create class for context manager
class MockAsyncContext:
    def __init__(self, mock_client):
        self.mock_client = mock_client

    async def __aenter__(self):
        return self.mock_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestRobotsBasic:
    """Basic tests for robots.txt functionality."""

    @pytest.mark.asyncio
    async def test_robots_allowed_basic(self):
        """Test robots.txt allows access."""
        # Create mock objects
        response = MagicMock()
        response.status_code = 200
        response.text = """
        User-agent: *
        Allow: /
        """

        client = MagicMock()
        client.get = AsyncMock(return_value=response)

        # Mock Protego can_fetch to return True
        protego_parser = MagicMock()
        protego_parser.can_fetch.return_value = True

        # Apply patches
        with (
            patch("httpx.AsyncClient", return_value=MockAsyncContext(client)),
            patch("protego.Protego.parse", return_value=protego_parser),
        ):
            # Should not raise an error
            await check_may_autonomously_fetch_url("https://example.com", "TestAgent")

            # Verify mocks were called
            client.get.assert_called_once()
            protego_parser.can_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_denied_basic(self):
        """Test robots.txt denies access."""
        # Create mock objects
        response = MagicMock()
        response.status_code = 200
        response.text = """
        User-agent: *
        Disallow: /
        """

        client = MagicMock()
        client.get = AsyncMock(return_value=response)

        # Mock Protego can_fetch to return False
        protego_parser = MagicMock()
        protego_parser.can_fetch.return_value = False

        # Apply patches
        with (
            patch("httpx.AsyncClient", return_value=MockAsyncContext(client)),
            patch("protego.Protego.parse", return_value=protego_parser),
        ):
            # Should raise an error
            with pytest.raises(McpError) as excinfo:
                await check_may_autonomously_fetch_url("https://example.com", "TestAgent")

            # Verify error and mocks
            assert "autonomous fetching of this page is not allowed" in str(excinfo.value)
            client.get.assert_called_once()
            protego_parser.can_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_404_basic(self):
        """Test robots.txt returns 404."""
        # Create mock objects
        response = MagicMock()
        response.status_code = 404

        client = MagicMock()
        client.get = AsyncMock(return_value=response)

        # Apply patches
        with patch("httpx.AsyncClient", return_value=MockAsyncContext(client)):
            # Should not raise an error for 404
            await check_may_autonomously_fetch_url("https://example.com", "TestAgent")

            # Verify mocks were called
            client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_403_basic(self):
        """Test robots.txt returns 403 Forbidden."""
        # Create mock objects
        response = MagicMock()
        response.status_code = 403

        client = MagicMock()
        client.get = AsyncMock(return_value=response)

        # Apply patches
        with patch("httpx.AsyncClient", return_value=MockAsyncContext(client)):
            # Should raise an error for 403
            with pytest.raises(McpError) as excinfo:
                await check_may_autonomously_fetch_url("https://example.com", "TestAgent")

            # Verify error and mocks
            assert "autonomous fetching is not allowed" in str(excinfo.value)
            client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_connection_error_basic(self):
        """Test connection error when fetching robots.txt."""
        from httpx import HTTPError

        # Create mock client that raises an error
        client = MagicMock()
        client.get = AsyncMock(side_effect=HTTPError("Connection error"))

        # Apply patches
        with patch("httpx.AsyncClient", return_value=MockAsyncContext(client)):
            # Should raise a McpError when HTTPError occurs
            with pytest.raises(McpError) as excinfo:
                await check_may_autonomously_fetch_url("https://example.com", "TestAgent")

            # Verify error and mocks
            assert "Failed to fetch robots.txt" in str(excinfo.value)
            client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_with_proxy_basic(self):
        """Test robots.txt check with proxy."""
        # Create mock objects
        response = MagicMock()
        response.status_code = 200
        response.text = """
        User-agent: *
        Allow: /
        """

        client = MagicMock()
        client.get = AsyncMock(return_value=response)

        # Track proxy usage
        proxy_used = False

        # Custom context manager factory to track proxy
        def mock_async_client(proxies=None):
            nonlocal proxy_used
            if proxies == "http://proxy.example.com":
                proxy_used = True
            return MockAsyncContext(client)

        # Mock Protego can_fetch to return True
        protego_parser = MagicMock()
        protego_parser.can_fetch.return_value = True

        # Apply patches
        with (
            patch("httpx.AsyncClient", side_effect=mock_async_client),
            patch("protego.Protego.parse", return_value=protego_parser),
        ):
            # Should not raise an error
            await check_may_autonomously_fetch_url("https://example.com", "TestAgent", "http://proxy.example.com")

            # Verify mocks were called and proxy was used
            client.get.assert_called_once()
            protego_parser.can_fetch.assert_called_once()
            assert proxy_used is True
