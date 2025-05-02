"""Tests for the individual server handler functions."""

import asyncio
from typing import Any, Dict, List, Literal, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server import Server
from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    ErrorData,
    GetPromptResult,
    PromptMessage,
    TextContent,
)

from mcp_server_fetch.handlers import call_tool, get_prompt, list_prompts, list_tools
from mcp_server_fetch.server import Fetch


class AsyncContextManagerMock:
    """Mock for async context manager pattern."""

    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
class TestServerHandlers:
    """Tests for the individual server handler functions."""

    # Set up shared test variables
    user_agent_autonomous = "TestUserAgent-Autonomous"
    user_agent_manual = "TestUserAgent-Manual"
    proxy_url = "http://test.proxy"
    headless = False
    wait_until = "domcontentloaded"
    ignore_robots_txt = True

    async def setup_test_environment(self, monkeypatch):
        """Set up common test environment."""
        # Create a fake server for handler binding
        mock_server = MagicMock(spec=Server)

        # Mock fetch_url_with_playwright in both server and handlers modules
        mock_fetch = AsyncMock(return_value=("Sample content", ""))
        monkeypatch.setattr("mcp_server_fetch.server.fetch_url_with_playwright", mock_fetch)
        monkeypatch.setattr("mcp_server_fetch.handlers.fetch_url_with_playwright", mock_fetch)

        # Mock check_may_autonomously_fetch_url
        mock_check_robots = AsyncMock()
        monkeypatch.setattr("mcp_server_fetch.server.check_may_autonomously_fetch_url", mock_check_robots)
        monkeypatch.setattr("mcp_server_fetch.handlers.check_may_autonomously_fetch_url", mock_check_robots)

        return mock_server, mock_fetch, mock_check_robots

    async def test_call_tool_basic(self, monkeypatch):
        """Test the call_tool function with basic arguments."""
        # Set up test environment
        mock_server, mock_fetch, mock_check_robots = await self.setup_test_environment(monkeypatch)

        # Set the config values directly in the handlers module
        monkeypatch.setattr("mcp_server_fetch.handlers.ignore_robots_txt", True)

        # Set up test parameters
        args = {"url": "https://example.com"}

        # Call the function directly
        result = await call_tool("playwright-fetch", args)

        # Verify results
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
        assert "Contents of https://example.com" in result[0].text
        assert "Sample content" in result[0].text

        # Verify correct function calls
        mock_check_robots.assert_not_called()  # With ignore_robots_txt=True
        mock_fetch.assert_called_once()

    async def test_call_tool_with_robots_check(self, monkeypatch):
        """Test the call_tool function with robots.txt checking."""
        # Set up test environment
        mock_server, mock_fetch, mock_check_robots = await self.setup_test_environment(monkeypatch)

        # Setup configuration
        monkeypatch.setattr("mcp_server_fetch.handlers.DEFAULT_USER_AGENT_AUTONOMOUS", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.user_agent_autonomous", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.ignore_robots_txt", False)
        monkeypatch.setattr("mcp_server_fetch.handlers.proxy_url", self.proxy_url)

        # Set up test parameters
        args = {"url": "https://example.com"}

        # Call the function directly - we don't need to store the result since we're only verifying the calls
        await call_tool("playwright-fetch", args)

        # Verify robots.txt was checked - allow any URL as the slash could be added by normalization
        mock_check_robots.assert_called_once()
        call_args = mock_check_robots.call_args[0]
        assert call_args[0].startswith("https://example.com")
        assert call_args[1] == self.user_agent_autonomous
        assert call_args[2] == self.proxy_url

    async def test_call_tool_raw_content(self, monkeypatch):
        """Test the call_tool function with raw content."""
        # Set up test environment
        mock_server, mock_fetch, mock_check_robots = await self.setup_test_environment(monkeypatch)

        # Setup configuration
        monkeypatch.setattr("mcp_server_fetch.handlers.DEFAULT_USER_AGENT_AUTONOMOUS", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.user_agent_autonomous", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.ignore_robots_txt", self.ignore_robots_txt)
        monkeypatch.setattr("mcp_server_fetch.handlers.proxy_url", self.proxy_url)
        monkeypatch.setattr("mcp_server_fetch.handlers.headless", self.headless)
        monkeypatch.setattr("mcp_server_fetch.handlers.wait_until", self.wait_until)

        # Set up test parameters
        args = {"url": "https://example.com", "raw": True}

        # Call the function directly - we don't need to store the result since we're only verifying the calls
        await call_tool("playwright-fetch", args)

        # Verify fetch was called with raw=True
        # Check that the call happened and inspect args
        assert mock_fetch.called
        call_args, call_kwargs = mock_fetch.call_args
        assert call_args[0].startswith("https://example.com")
        assert call_args[1] == self.user_agent_autonomous
        assert call_kwargs["force_raw"] is True
        assert call_kwargs["proxy_url"] == self.proxy_url
        assert call_kwargs["headless"] == self.headless
        assert call_kwargs["wait_until"] == self.wait_until

    async def test_call_tool_wait_for_js_false(self, monkeypatch):
        """Test the call_tool function with wait_for_js=False."""
        # Set up test environment
        mock_server, mock_fetch, mock_check_robots = await self.setup_test_environment(monkeypatch)

        # Setup configuration
        monkeypatch.setattr("mcp_server_fetch.handlers.DEFAULT_USER_AGENT_AUTONOMOUS", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.user_agent_autonomous", self.user_agent_autonomous)
        monkeypatch.setattr("mcp_server_fetch.handlers.ignore_robots_txt", self.ignore_robots_txt)
        monkeypatch.setattr("mcp_server_fetch.handlers.proxy_url", self.proxy_url)
        monkeypatch.setattr("mcp_server_fetch.handlers.headless", self.headless)
        monkeypatch.setattr("mcp_server_fetch.handlers.wait_until", self.wait_until)

        # Set up test parameters
        args = {"url": "https://example.com", "wait_for_js": False}

        # Call the function directly - we don't need to store the result since we're only verifying the calls
        await call_tool("playwright-fetch", args)

        # Verify fetch used domcontentloaded instead of the configured wait_until
        assert mock_fetch.called
        call_args, call_kwargs = mock_fetch.call_args
        assert call_args[0].startswith("https://example.com")
        assert call_args[1] == self.user_agent_autonomous
        assert call_kwargs["force_raw"] is False
        assert call_kwargs["proxy_url"] == self.proxy_url
        assert call_kwargs["headless"] == self.headless
        assert call_kwargs["wait_until"] == "domcontentloaded"

    async def test_call_tool_content_truncation(self, monkeypatch):
        """Test content truncation in call_tool."""
        # Set up test environment
        mock_server, mock_fetch, mock_check_robots = await self.setup_test_environment(monkeypatch)

        # Setup configuration
        monkeypatch.setattr("mcp_server_fetch.handlers.ignore_robots_txt", self.ignore_robots_txt)

        # Create long content
        long_content = "A" * 10000
        mock_fetch.return_value = (long_content, "")

        # Test with max_length
        args = {"url": "https://example.com", "max_length": 1000}

        # Call the function directly
        result = await call_tool("playwright-fetch", args)

        # Verify truncation
        assert "Content truncated" in result[0].text
        assert "start_index of 1000" in result[0].text

        # Test with start_index
        args = {"url": "https://example.com", "max_length": 1000, "start_index": 5000}

        # Call the function directly
        result = await call_tool("playwright-fetch", args)

        # Verify truncation and content from the correct position
        assert result[0].text.count("A") <= 1000
        assert "start_index of 6000" in result[0].text

        # Test with start_index beyond content length
        args = {"url": "https://example.com", "start_index": 15000}

        # Call the function directly
        result = await call_tool("playwright-fetch", args)

        # Verify no more content message
        assert "No more content available" in result[0].text

    async def test_call_tool_invalid_args(self, monkeypatch):
        """Test call_tool with invalid arguments."""
        # Set up test environment
        _, _, _ = await self.setup_test_environment(monkeypatch)

        # Test invalid URL - since the handlers are now throwing McpError we need to catch that
        args = {"url": "not-a-url"}
        with pytest.raises(McpError) as excinfo:
            await call_tool("playwright-fetch", args)
        assert "Input should be a valid URL" in str(excinfo.value)

        # Test empty URL - this will also raise McpError
        args = {"url": ""}
        with pytest.raises(McpError) as excinfo:
            await call_tool("playwright-fetch", args)
        # Either the error will mention URL validation or "URL is required"
        assert any(phrase in str(excinfo.value) for phrase in ["URL is required", "Input should be a valid URL"])

    async def test_get_prompt_handler(self, monkeypatch):
        """Test the get_prompt handler."""
        # Set up test environment
        _, mock_fetch, _ = await self.setup_test_environment(monkeypatch)

        # Setup configuration
        monkeypatch.setattr("mcp_server_fetch.handlers.DEFAULT_USER_AGENT_MANUAL", self.user_agent_manual)
        monkeypatch.setattr("mcp_server_fetch.handlers.user_agent_manual", self.user_agent_manual)
        monkeypatch.setattr("mcp_server_fetch.handlers.proxy_url", self.proxy_url)
        monkeypatch.setattr("mcp_server_fetch.handlers.headless", self.headless)
        monkeypatch.setattr("mcp_server_fetch.handlers.wait_until", self.wait_until)

        # Set up test parameters
        args = {"url": "https://example.com"}

        # Call the function directly
        result = await get_prompt("playwright-fetch", args)

        # Verify results
        assert isinstance(result, GetPromptResult)
        assert result.description == "Contents of https://example.com"
        assert len(result.messages) == 1
        assert result.messages[0].role == "user"
        assert "Sample content" in result.messages[0].content.text

        # Verify fetch was called with correct parameters
        mock_fetch.assert_called_once_with(
            "https://example.com",
            self.user_agent_manual,
            proxy_url=self.proxy_url,
            headless=self.headless,
            wait_until=self.wait_until,
        )

    async def test_get_prompt_missing_url(self, monkeypatch):
        """Test get_prompt with missing URL."""
        # Set up test environment
        _, _, _ = await self.setup_test_environment(monkeypatch)

        # Test with empty arguments
        with pytest.raises(McpError) as excinfo:
            await get_prompt("playwright-fetch", {})

        assert "URL is required" in str(excinfo.value)

        # Test with None arguments
        with pytest.raises(McpError) as excinfo:
            await get_prompt("playwright-fetch", None)

        assert "URL is required" in str(excinfo.value)

    async def test_get_prompt_fetch_error(self, monkeypatch):
        """Test get_prompt when fetch fails."""
        # Set up test environment
        _, mock_fetch, _ = await self.setup_test_environment(monkeypatch)

        # Make fetch raise an error
        error_message = "Failed to fetch: Connection error"
        mock_fetch.side_effect = McpError(
            ErrorData(code=INTERNAL_ERROR, message=error_message),
        )

        # Set up test parameters
        args = {"url": "https://example.com"}

        # Call the function directly
        result = await get_prompt("playwright-fetch", args)

        # Verify error is reported in the result
        assert result.description == "Failed to fetch https://example.com"
        assert error_message in result.messages[0].content.text

    async def test_list_tools_handler(self, monkeypatch):
        """Test the list_tools handler."""
        # Set up test environment
        _, _, _ = await self.setup_test_environment(monkeypatch)

        # Call the function directly
        result = await list_tools()

        # Verify results
        assert isinstance(result, list)
        assert len(result) == 1
        tool = result[0]
        assert tool.name == "playwright-fetch"
        assert "Fetches a URL" in tool.description

        # Check schema properties
        schema = tool.inputSchema
        assert "url" in schema["required"]
        assert "url" in schema["properties"]
        assert "max_length" in schema["properties"]
        assert "start_index" in schema["properties"]
        assert "raw" in schema["properties"]
        assert "wait_for_js" in schema["properties"]

    async def test_list_prompts_handler(self, monkeypatch):
        """Test the list_prompts handler."""
        # Set up test environment
        _, _, _ = await self.setup_test_environment(monkeypatch)

        # Call the function directly
        result = await list_prompts()

        # Verify results
        assert isinstance(result, list)
        assert len(result) == 1
        prompt = result[0]
        assert prompt.name == "playwright-fetch"
        assert "Fetch a URL" in prompt.description
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "url"
        assert prompt.arguments[0].required is True

    async def test_fetch_model_validation(self):
        """Test the Fetch model validation."""
        # Valid URL
        fetch = Fetch(url="https://example.com")
        assert str(fetch.url).startswith("https://example.com")

        # Default values
        assert fetch.max_length == 5000
        assert fetch.start_index == 0
        assert fetch.raw is False
        assert fetch.wait_for_js is True

        # Test with custom values
        fetch = Fetch(
            url="https://example.com",
            max_length=2000,
            start_index=100,
            raw=True,
            wait_for_js=False,
        )
        assert fetch.max_length == 2000
        assert fetch.start_index == 100
        assert fetch.raw is True
        assert fetch.wait_for_js is False

        # Test invalid URL
        with pytest.raises(ValueError):
            Fetch(url="not-a-url")

        # Test invalid max_length
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=0)

        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=2000000)

        # Test invalid start_index
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", start_index=-1)
