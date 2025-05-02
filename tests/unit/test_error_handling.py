"""Tests for error handling across the application."""

import asyncio
import os
import sys
from typing import Literal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPError
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData
from playwright.async_api import Error as PlaywrightError

from mcp_server_fetch.server import (
    check_may_autonomously_fetch_url,
    fetch_url_with_playwright,
    serve,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tests.fixtures.browser_fixture import PlaywrightMockFactory

pytestmark = pytest.mark.asyncio


class TestFetchUrlErrorHandling:
    """Test error handling in fetch_url_with_playwright."""

    async def test_no_response_error(self, monkeypatch):
        """Test error when no response is received from goto."""
        # Setup mock
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]
        page_mock.goto.return_value = None

        # Patch async_playwright
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "no response received" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "no response received" in str(exc_info.value)

    async def test_http_error_response(self, monkeypatch):
        """Test error handling for HTTP error status codes."""
        # Setup mock with 500 status code
        mock_setup = PlaywrightMockFactory.setup_full_mock(status=500)

        # Patch async_playwright
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "status code 500" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "status code 500" in str(exc_info.value)

    async def test_playwright_error(self, monkeypatch):
        """Test error handling for Playwright errors."""
        # Setup mock with an error during launch
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        playwright_mock = mock_setup["playwright"]
        playwright_mock.chromium.launch = AsyncMock(side_effect=PlaywrightError("Browser launch failed"))

        # Patch async_playwright
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "Failed to fetch" in error_data.message
            assert "Browser launch failed" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "Failed to fetch" in str(exc_info.value)
            assert "Browser launch failed" in str(exc_info.value)

    async def test_timeout_error(self, monkeypatch):
        """Test error handling for timeout errors."""
        # Setup mock with a timeout during goto
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]
        page_mock.goto = AsyncMock(side_effect=asyncio.TimeoutError())

        # Patch async_playwright
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "Timeout when fetching" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "Timeout when fetching" in str(exc_info.value)

    async def test_general_exception(self, monkeypatch):
        """Test error handling for general exceptions."""
        # Setup mock with a general exception during goto
        mock_setup = PlaywrightMockFactory.setup_full_mock()
        page_mock = mock_setup["page"]
        page_mock.goto = AsyncMock(side_effect=Exception("Unexpected error"))

        # Patch async_playwright
        monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await fetch_url_with_playwright("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "Error fetching" in error_data.message
            assert "Unexpected error" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "Error fetching" in str(exc_info.value)
            assert "Unexpected error" in str(exc_info.value)


class TestRobotsTxtErrorHandling:
    """Test error handling in robots.txt checking."""

    async def test_connection_error(self, monkeypatch):
        """Test error handling for connection errors when fetching robots.txt."""
        # Mock the AsyncClient
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(side_effect=HTTPError("Connection error"))

        # Mock the context manager
        @pytest.fixture
        def mock_client():
            class MockAsyncClient:
                async def __aenter__(self):
                    return client_mock

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return MockAsyncClient()

        # Patch httpx.AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: mock_client())

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "Failed to fetch robots.txt" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "Failed to fetch robots.txt" in str(exc_info.value)

    async def test_forbidden_response(self, monkeypatch):
        """Test error handling for 403 responses when fetching robots.txt."""
        # Mock the response
        response_mock = MagicMock()
        response_mock.status_code = 403

        # Mock the AsyncClient
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Mock the context manager
        class MockAsyncClient:
            async def __aenter__(self):
                return client_mock

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Patch httpx.AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncClient())

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "autonomous fetching is not allowed" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "autonomous fetching is not allowed" in str(exc_info.value)

    async def test_robots_denied(self, monkeypatch):
        """Test error handling when robots.txt denies access."""
        # Mock the response
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.text = """
        User-agent: *
        Disallow: /
        """

        # Mock the AsyncClient
        client_mock = AsyncMock()
        client_mock.get = AsyncMock(return_value=response_mock)

        # Mock the context manager
        class MockAsyncClient:
            async def __aenter__(self):
                return client_mock

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Mock Protego.can_fetch to return False
        protego_mock = MagicMock()
        protego_mock.can_fetch.return_value = False
        monkeypatch.setattr("protego.Protego.parse", lambda _: protego_mock)

        # Patch httpx.AsyncClient
        monkeypatch.setattr("httpx.AsyncClient", lambda proxies=None: MockAsyncClient())

        # Test the function raises the correct error
        with pytest.raises(McpError) as exc_info:
            await check_may_autonomously_fetch_url("https://example.com", "TestUserAgent")

        # Verify the error - handle both error structures
        error_data = getattr(exc_info.value, "error_data", None)
        if error_data:
            assert error_data.code == "internal_error"
            assert "autonomous fetching of this page is not allowed" in error_data.message
        else:
            # For the newer McpError structure without error_data
            assert "autonomous fetching of this page is not allowed" in str(exc_info.value)


class TestServeFunctionErrorHandling:
    """Test error handling in the serve function."""

    async def test_server_run_error(self, monkeypatch):
        """Test error handling when server.run raises an exception."""
        # Mock Server class
        server_mock = MagicMock()
        server_mock.run = AsyncMock(side_effect=Exception("Server run failed"))
        server_mock.create_initialization_options.return_value = {}

        # Mock the decorators to do nothing
        server_mock.list_tools = lambda: lambda func: func
        server_mock.list_prompts = lambda: lambda func: func
        server_mock.call_tool = lambda: lambda func: func
        server_mock.get_prompt = lambda: lambda func: func

        monkeypatch.setattr("mcp.server.Server", lambda name: server_mock)

        # Mock stdio_server
        class MockStdioServer:
            async def __aenter__(self):
                return AsyncMock(), AsyncMock()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        monkeypatch.setattr("mcp.server.stdio.stdio_server", lambda: MockStdioServer())

        # Run serve and expect the exception to propagate
        with pytest.raises(Exception) as exc_info:
            await serve()

        # Verify the error
        assert "Server run failed" in str(exc_info.value)
