"""Integration tests for the Playwright Fetch MCP server."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_fetch.server import serve


class TestIntegration:
    """Integration tests for the server as a whole."""

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.check_may_autonomously_fetch_url", AsyncMock())
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    @patch("mcp.server.stdio_server")
    async def test_server_tool_call(self, mock_stdio_server, mock_fetch):
        """Test server handling a tool call request."""
        # Setup mock fetch function
        mock_fetch.return_value = ("Page content", "")

        # Setup mock streams for stdin/stdout
        read_stream = AsyncMock()
        write_stream = AsyncMock()

        # Setup mock context manager for stdio_server
        context_manager = MagicMock()
        context_manager.__aenter__.return_value = (read_stream, write_stream)
        context_manager.__aexit__.return_value = None
        mock_stdio_server.return_value = context_manager

        # Setup read_stream to return a tool call request followed by EOF
        tool_call_request = {
            "method": "tools/call",
            "params": {"name": "playwright-fetch", "arguments": {"url": "https://example.com", "max_length": 1000}},
        }

        # Queue the request and EOF
        request_line = json.dumps(tool_call_request) + "\n"
        read_queue = asyncio.Queue()
        await read_queue.put(request_line.encode())
        await read_queue.put(b"")  # EOF
        read_stream.readline.side_effect = lambda: read_queue.get()

        # Run the server
        await serve()

        # Verify the server responded
        write_stream.write.assert_called()

        # Get the response
        response = None
        for call in write_stream.write.call_args_list:
            response_data = call[0][0].decode()
            if "result" in response_data:
                response = json.loads(response_data)
                break

        assert response is not None
        assert "result" in response
        assert isinstance(response["result"], list)
        assert len(response["result"]) == 1
        assert response["result"][0]["type"] == "text"
        assert "Contents of https://example.com" in response["result"][0]["text"]
        assert "Page content" in response["result"][0]["text"]

    @pytest.mark.asyncio
    @patch("mcp_server_fetch.server.fetch_url_with_playwright")
    @patch("mcp.server.stdio_server")
    async def test_server_prompt_request(self, mock_stdio_server, mock_fetch):
        """Test server handling a get_prompt request."""
        # Setup mock fetch function
        mock_fetch.return_value = ("Page content", "")

        # Setup mock streams for stdin/stdout
        read_stream = AsyncMock()
        write_stream = AsyncMock()

        # Setup mock context manager for stdio_server
        context_manager = MagicMock()
        context_manager.__aenter__.return_value = (read_stream, write_stream)
        context_manager.__aexit__.return_value = None
        mock_stdio_server.return_value = context_manager

        # Setup read_stream to return a prompt request followed by EOF
        prompt_request = {
            "method": "prompts/get",
            "params": {"name": "playwright-fetch", "arguments": {"url": "https://example.com"}},
        }

        # Queue the request and EOF
        request_line = json.dumps(prompt_request) + "\n"
        read_queue = asyncio.Queue()
        await read_queue.put(request_line.encode())
        await read_queue.put(b"")  # EOF
        read_stream.readline.side_effect = lambda: read_queue.get()

        # Run the server
        await serve()

        # Verify the server responded
        write_stream.write.assert_called()

        # Get the response
        response = None
        for call in write_stream.write.call_args_list:
            response_data = call[0][0].decode()
            if "result" in response_data:
                response = json.loads(response_data)
                break

        assert response is not None
        assert "result" in response
        assert "description" in response["result"]
        assert "messages" in response["result"]
        assert len(response["result"]["messages"]) == 1
        assert response["result"]["messages"][0]["role"] == "user"
        assert "Page content" in response["result"]["messages"][0]["content"]["text"]
