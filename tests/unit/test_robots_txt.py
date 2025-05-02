"""Unit tests for robots.txt handling."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPError
from mcp.shared.exceptions import McpError

from mcp_server_fetch.server import check_may_autonomously_fetch_url, get_robots_txt_url


class TestRobotsTxtUrl:
    """Tests for robots.txt URL generation."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://example.com", "https://example.com/robots.txt"),
            ("https://example.com/path/to/page", "https://example.com/robots.txt"),
            ("https://example.com/path?query=value", "https://example.com/robots.txt"),
            ("https://example.com:8080/path", "https://example.com:8080/robots.txt"),
            ("http://localhost:3000", "http://localhost:3000/robots.txt"),
        ],
    )
    def test_get_robots_txt_url(self, url, expected):
        """Test generating robots.txt URLs for various input URLs."""
        result = get_robots_txt_url(url)
        assert result == expected


class TestRobotsCheck:
    """Tests for robots.txt checking functionality."""

    @pytest.mark.asyncio
    async def test_robots_allowed(self, monkeypatch):
        """Test when robots.txt allows access."""
        # Create mock response and client
        response_mock = MagicMock()
        response_mock.text = """
        User-agent: *
        Allow: /
        """
        response_mock.status_code = 200

        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Create async context manager for AsyncClient
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should complete without raising an exception
        await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", None)

    @pytest.mark.asyncio
    async def test_robots_404(self, monkeypatch):
        """Test when robots.txt returns a 404."""
        # Create mock response and client
        response_mock = MagicMock()
        response_mock.status_code = 404

        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Create async context manager for AsyncClient
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should complete without raising an exception (404 means no restrictions)
        await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", None)

    @pytest.mark.asyncio
    async def test_robots_denied(self, monkeypatch):
        """Test when robots.txt denies access."""
        # Create mock response and client
        response_mock = MagicMock()
        response_mock.text = """
        User-agent: *
        Disallow: /
        """
        response_mock.status_code = 200

        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Create async context manager for AsyncClient
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should raise an exception
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", None)
        assert "autonomous fetching of this page is not allowed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_robots_forbidden(self, monkeypatch):
        """Test when robots.txt returns a 403 Forbidden."""
        # Create mock response and client
        response_mock = MagicMock()
        response_mock.status_code = 403

        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Create async context manager for AsyncClient
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should raise an exception
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", None)
        assert "autonomous fetching is not allowed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_robots_connection_error(self, monkeypatch):
        """Test handling connection errors when fetching robots.txt."""
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(side_effect=HTTPError("Connection error"))

        # Create async context manager for AsyncClient
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should raise an exception
        with pytest.raises(McpError) as excinfo:
            await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", None)
        assert "Failed to fetch robots.txt" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_with_proxy(self, monkeypatch):
        """Test robots check with a proxy URL."""
        proxy_url = "http://proxy.example.com:8080"
        proxy_args = {}

        # Create mock response and client
        response_mock = MagicMock()
        response_mock.text = """
        User-agent: *
        Allow: /
        """
        response_mock.status_code = 200

        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Create async context manager for AsyncClient that captures proxy args
        @asynccontextmanager
        async def mock_async_client(*args, **kwargs):
            nonlocal proxy_args
            proxy_args = kwargs
            yield client_mock

        # Patch the AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        # Should complete without raising an exception
        await check_may_autonomously_fetch_url("https://example.com/page", "TestUserAgent", proxy_url)

        # Verify the client was created with the proxy
        assert proxy_args.get("proxies") == proxy_url
