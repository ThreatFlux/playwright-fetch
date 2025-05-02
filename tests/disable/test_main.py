"""Tests for the main function in the MCP server."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_fetch.__main__ import main
from mcp_server_fetch.server import serve


class TestMain:
    """Test the main entry point."""

    @pytest.mark.asyncio
    @patch("sys.argv", ["mcp_server_fetch"])
    @patch("mcp_server_fetch.server.serve", new_callable=AsyncMock)
    async def test_main_mocked(self, mock_serve):
        """Test that main calls serve with default parameters."""
        # Setup the mock
        mock_serve.return_value = None

        # Create a parser that doesn't exit
        with patch("argparse.ArgumentParser.exit") as mock_exit:
            mock_exit.side_effect = lambda *args, **kwargs: None

            # Run main with patched argv
            with patch.object(sys, "argv", ["mcp_server_fetch"]):
                main()

        # Verify serve was called
        assert mock_serve.called

    @pytest.mark.asyncio
    @patch("argparse.ArgumentParser.parse_args")
    @patch("mcp_server_fetch.server.serve", new_callable=AsyncMock)
    async def test_main_with_args_mocked(self, mock_serve, mock_parse_args):
        """Test that main passes CLI args to serve."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.user_agent = "CustomUserAgent"
        mock_args.ignore_robots_txt = True
        mock_args.proxy = "http://proxy.example.com:8080"
        mock_args.headless = False
        mock_args.wait_until = "load"
        mock_parse_args.return_value = mock_args
        mock_serve.return_value = None

        # Run main with patched argv and parser
        with patch("argparse.ArgumentParser.exit") as mock_exit:
            mock_exit.side_effect = lambda *args, **kwargs: None
            main()

        # Verify serve was called with parsed arguments
        assert mock_serve.called
        mock_serve.assert_called_once_with(
            custom_user_agent="CustomUserAgent",
            ignore_robots_txt=True,
            proxy_url="http://proxy.example.com:8080",
            headless=False,
            wait_until="load",
        )
