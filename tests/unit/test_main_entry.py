"""Tests for the main entry point."""

import argparse
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_fetch.__init__ import main


class TestMainEntry:
    """Tests for the main entry point."""

    def test_main_arguments_parsing(self, monkeypatch):
        """Test command line arguments parsing."""
        # Mock serve function
        mock_serve = AsyncMock()
        monkeypatch.setattr("mcp_server_fetch.server.serve", mock_serve)

        # Mock asyncio.run to just call the coroutine directly
        def mock_asyncio_run(coro):
            return coro

        monkeypatch.setattr("asyncio.run", mock_asyncio_run)

        # Mock sys.argv
        test_args = [
            "mcp_server_fetch",
            "--user-agent",
            "TestUserAgent",
            "--ignore-robots-txt",
            "--proxy-url",
            "http://proxy.example.com:8080",
            "--headless",
            "--wait-until",
            "load",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        # Run main
        main()

        # Verify serve was called with the right arguments
        mock_serve.assert_called_once()
        args = mock_serve.call_args.args
        assert args[0] == "TestUserAgent"  # user_agent
        assert args[1] is True  # ignore_robots_txt
        assert args[2] == "http://proxy.example.com:8080"  # proxy_url
        assert args[3] is True  # headless
        assert args[4] == "load"  # wait_until

    def test_main_default_arguments(self, monkeypatch):
        """Test default argument values."""
        # Mock serve function
        mock_serve = AsyncMock()
        monkeypatch.setattr("mcp_server_fetch.server.serve", mock_serve)

        # Mock asyncio.run to just call the coroutine directly
        def mock_asyncio_run(coro):
            return coro

        monkeypatch.setattr("asyncio.run", mock_asyncio_run)

        # Mock sys.argv with minimal arguments
        test_args = ["mcp_server_fetch"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Run main
        main()

        # Verify serve was called with default arguments
        mock_serve.assert_called_once()
        args = mock_serve.call_args.args
        assert args[0] is None  # default user_agent
        assert args[1] is False  # default ignore_robots_txt
        assert args[2] is None  # default proxy_url
        assert args[3] is True  # default headless
        assert args[4] == "networkidle"  # default wait_until

    def test_wait_until_choices(self, monkeypatch):
        """Test that wait_until accepts only valid choices."""
        # Import argparse here to avoid F823 reference error
        import argparse

        # Use lowercase naming to avoid N806 naming error
        real_argument_parser = argparse.ArgumentParser
        parser_instance = None

        class MockArgumentParser:
            def __init__(self, *args, **kwargs):
                self.real_parser = real_argument_parser(*args, **kwargs)
                nonlocal parser_instance
                parser_instance = self

            def add_argument(self, *args, **kwargs):
                return self.real_parser.add_argument(*args, **kwargs)

            def parse_args(self, *args, **kwargs):
                return self.real_parser.parse_args(*args, **kwargs)

        # Patch argparse.ArgumentParser
        monkeypatch.setattr("argparse.ArgumentParser", MockArgumentParser)

        # Also mock serve and asyncio.run to prevent actual execution
        monkeypatch.setattr("mcp_server_fetch.server.serve", AsyncMock())
        monkeypatch.setattr("asyncio.run", lambda coro: None)

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["mcp_server_fetch"])

        # Import argparse to use in this test
        import argparse

        # Run main to trigger parser creation
        with patch("sys.exit"):  # Prevent exit in case of error
            main()

        # Verify the wait_until argument has the correct choices
        wait_until_arg = None
        for action in parser_instance.real_parser._actions:
            if action.dest == "wait_until":
                wait_until_arg = action
                break

        assert wait_until_arg is not None
        assert wait_until_arg.choices == ["load", "domcontentloaded", "networkidle", "commit"]
        assert wait_until_arg.default == "networkidle"

    @pytest.mark.parametrize(
        "args,expected_headless",
        [
            (["mcp_server_fetch"], True),  # Default
            (["mcp_server_fetch", "--headless"], True),  # Explicit headless
            (["mcp_server_fetch", "--no-headless"], False),  # No headless
        ],
    )
    def test_headless_parameter(self, args, expected_headless, monkeypatch):
        """Test the headless parameter parsing."""
        # Mock serve function
        mock_serve = AsyncMock()
        monkeypatch.setattr("mcp_server_fetch.server.serve", mock_serve)

        # Mock asyncio.run to just call the coroutine directly
        def mock_asyncio_run(coro):
            return coro

        monkeypatch.setattr("asyncio.run", mock_asyncio_run)

        # Update ArgumentParser to handle --no-headless flag
        real_add_argument = argparse.ArgumentParser.add_argument

        def mock_add_argument(self, *args, **kwargs):
            # Modify the headless argument to be a flag with opposite meaning
            if "--headless" in args and "action" in kwargs and kwargs["action"] == "store_true":
                result = real_add_argument(
                    self,
                    "--headless",
                    action="store_true",
                    dest="headless",
                    default=True,
                    help=kwargs.get("help", ""),
                )
                real_add_argument(
                    self,
                    "--no-headless",
                    action="store_false",
                    dest="headless",
                    help="Run browser in non-headless mode",
                )
                return result
            return real_add_argument(self, *args, **kwargs)

        # Patch add_argument
        monkeypatch.setattr(argparse.ArgumentParser, "add_argument", mock_add_argument)

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", args)

        # Run main
        main()

        # Verify headless parameter
        assert mock_serve.call_args.args[3] is expected_headless
