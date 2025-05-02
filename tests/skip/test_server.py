"""Tests for the MCP server implementation."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData, GetPromptResult, PromptMessage, TextContent

from mcp_server_fetch.server import Fetch, serve


class TestFetchModel:
    """Tests for the Fetch model."""

    def test_valid_fetch_model(self):
        """Test creating a valid Fetch model."""
        fetch = Fetch(url="https://example.com", max_length=1000, start_index=0, raw=False, wait_for_js=True)

        assert str(fetch.url) == "https://example.com/"
        assert fetch.max_length == 1000
        assert fetch.start_index == 0
        assert fetch.raw is False
        assert fetch.wait_for_js is True

    def test_defaults(self):
        """Test default values of the Fetch model."""
        fetch = Fetch(url="https://example.com")

        assert fetch.max_length == 5000
        assert fetch.start_index == 0
        assert fetch.raw is False
        assert fetch.wait_for_js is True

    def test_invalid_url(self):
        """Test validation of invalid URLs."""
        with pytest.raises(ValueError):
            Fetch(url="not-a-url")

    def test_invalid_max_length(self):
        """Test validation of invalid max_length."""
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=0)

        with pytest.raises(ValueError):
            Fetch(url="https://example.com", max_length=2000000)

    def test_invalid_start_index(self):
        """Test validation of invalid start_index."""
        with pytest.raises(ValueError):
            Fetch(url="https://example.com", start_index=-1)


class TestServer:
    """Tests for the MCP server functionality."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test the list_tools handler."""
        # Create a mock server
        server_mock = MagicMock()
        list_tools_handler = None

        # Capture the list_tools handler
        @patch("mcp.server.Server", return_value=server_mock)
        async def setup_server(server_cls):
            nonlocal list_tools_handler
            # Instead of calling serve directly, patch it to capture the decorated function

            # Mock the decorated method to capture the handler
            def mock_decorator(*args, **kwargs):
                def decorator(func):
                    nonlocal list_tools_handler
                    list_tools_handler = func
                    return func

                return decorator

            # Replace the decorator with our mock
            server_mock.list_tools = mock_decorator

            # Call the serve function but don't await it
            with patch("asyncio.create_task"):
                await serve()

        # Run the setup coroutine
        asyncio.run(setup_server())
        assert list_tools_handler is not None

        # Call the handler
        tools = await list_tools_handler()

        # Verify the result
        assert len(tools) == 1
        assert tools[0].name == "playwright-fetch"
        assert "Fetches a URL" in tools[0].description

    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test the list_prompts handler."""
        # Create a mock server
        server_mock = MagicMock()
        list_prompts_handler = None

        # Capture the list_prompts handler
        @patch("mcp.server.Server", return_value=server_mock)
        async def setup_server(server_cls):
            nonlocal list_prompts_handler

            # Mock the decorated method to capture the handler
            def mock_decorator(*args, **kwargs):
                def decorator(func):
                    nonlocal list_prompts_handler
                    list_prompts_handler = func
                    return func

                return decorator

            # Replace the decorator with our mock
            server_mock.list_prompts = mock_decorator

            # Call the serve function but don't await it
            with patch("asyncio.create_task"):
                await serve()

        # Run the setup coroutine
        asyncio.run(setup_server())
        assert list_prompts_handler is not None

        # Call the handler
        prompts = await list_prompts_handler()

        # Verify the result
        assert len(prompts) == 1
        assert prompts[0].name == "playwright-fetch"
        assert "Fetch a URL" in prompts[0].description
        assert len(prompts[0].arguments) == 1
        assert prompts[0].arguments[0].name == "url"

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.check_may_autonomously_fetch_url", AsyncMock())
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    async def test_call_tool(self, mock_fetch):
        """Test the call_tool handler."""
        # Setup the mock fetch function
        mock_fetch.return_value = ("Markdown content", "")

        # Create a mock server
        server_mock = MagicMock()
        call_tool_handler = None

        # Capture the call_tool handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal call_tool_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the call_tool handler
            for call in server_mock.call_tool.call_args_list:
                call_tool_handler = call[0][0]

        setup_server()
        assert call_tool_handler is not None

        # Call the handler
        result = await call_tool_handler(
            "playwright-fetch",
            {"url": "https://example.com", "max_length": 1000, "start_index": 0, "raw": False, "wait_for_js": True},
        )

        # Verify the result
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
        assert "Contents of https://example.com" in result[0].text
        assert "Markdown content" in result[0].text

        # Verify fetch was called with correct parameters
        mock_fetch.assert_called_once()
        args, kwargs = mock_fetch.call_args
        assert args[0] == "https://example.com"
        assert "force_raw" in kwargs and kwargs["force_raw"] is False
        assert "wait_until" in kwargs and kwargs["wait_until"] == "networkidle"

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.check_may_autonomously_fetch_url", AsyncMock())
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    async def test_call_tool_content_truncation(self, mock_fetch):
        """Test content truncation in call_tool."""
        # Setup mock to return long content
        long_content = "A" * 6000
        mock_fetch.return_value = (long_content, "")

        # Create a mock server
        server_mock = MagicMock()
        call_tool_handler = None

        # Capture the call_tool handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal call_tool_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the call_tool handler
            for call in server_mock.call_tool.call_args_list:
                call_tool_handler = call[0][0]

        setup_server()

        # Call the handler with max_length=1000
        result = await call_tool_handler(
            "playwright-fetch",
            {"url": "https://example.com", "max_length": 1000, "start_index": 0},
        )

        # Verify the result is truncated
        assert "A" * 1000 in result[0].text
        assert "Content truncated" in result[0].text
        assert "start_index of 1000" in result[0].text

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.check_may_autonomously_fetch_url", AsyncMock())
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    async def test_call_tool_with_start_index(self, mock_fetch):
        """Test call_tool with a non-zero start_index."""
        # Setup mock to return content
        mock_fetch.return_value = ("ABCDEFGHIJ", "")

        # Create a mock server
        server_mock = MagicMock()
        call_tool_handler = None

        # Capture the call_tool handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal call_tool_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the call_tool handler
            for call in server_mock.call_tool.call_args_list:
                call_tool_handler = call[0][0]

        setup_server()

        # Call the handler with start_index=5
        result = await call_tool_handler("playwright-fetch", {"url": "https://example.com", "start_index": 5})

        # Verify only the content from the start_index is included
        assert "FGHIJ" in result[0].text
        assert "ABCDE" not in result[0].text

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    async def test_get_prompt(self, mock_fetch):
        """Test the get_prompt handler."""
        # Setup the mock fetch function
        mock_fetch.return_value = ("Markdown content", "")

        # Create a mock server
        server_mock = MagicMock()
        get_prompt_handler = None

        # Capture the get_prompt handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal get_prompt_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the get_prompt handler
            for call in server_mock.get_prompt.call_args_list:
                get_prompt_handler = call[0][0]

        setup_server()
        assert get_prompt_handler is not None

        # Call the handler
        result = await get_prompt_handler("playwright-fetch", {"url": "https://example.com"})

        # Verify the result
        assert isinstance(result, GetPromptResult)
        assert result.description == "Contents of https://example.com"
        assert len(result.messages) == 1
        assert result.messages[0].role == "user"
        assert result.messages[0].content.type == "text"
        assert "Markdown content" in result.messages[0].content.text

        # Verify fetch was called with the manual user agent
        mock_fetch.assert_called_once()
        args, kwargs = mock_fetch.call_args
        assert "TestUserAgent" in args[1] or "ModelContextProtocol" in args[1]

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    async def test_get_prompt_error(self, mock_fetch):
        """Test error handling in get_prompt."""
        # Setup the mock fetch function to raise an error
        error = McpError(ErrorData(code=INTERNAL_ERROR, message="Fetch error"))
        mock_fetch.side_effect = error

        # Create a mock server
        server_mock = MagicMock()
        get_prompt_handler = None

        # Capture the get_prompt handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal get_prompt_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the get_prompt handler
            for call in server_mock.get_prompt.call_args_list:
                get_prompt_handler = call[0][0]

        setup_server()

        # Call the handler
        result = await get_prompt_handler("playwright-fetch", {"url": "https://example.com"})

        # Verify the result includes the error message
        assert "Failed to fetch" in result.description
        assert len(result.messages) == 1
        assert result.messages[0].role == "user"
        assert "Fetch error" in result.messages[0].content.text

    @pytest.mark.asyncio
    async def test_get_prompt_missing_url(self):
        """Test get_prompt with missing URL parameter."""
        # Create a mock server
        server_mock = MagicMock()
        get_prompt_handler = None

        # Capture the get_prompt handler
        @patch("mcp.server.Server", return_value=server_mock)
        def setup_server(server_cls):
            nonlocal get_prompt_handler
            # Call serve but patch the server run to prevent it from actually running
            with patch.object(server_mock, "run", AsyncMock()):
                serve()
            # Extract the get_prompt handler
            for call in server_mock.get_prompt.call_args_list:
                get_prompt_handler = call[0][0]

        setup_server()

        # Call the handler with empty arguments
        with pytest.raises(McpError) as excinfo:
            await get_prompt_handler("playwright-fetch", {})

        # Verify an error is raised
        assert "URL is required" in str(excinfo.value)
