"""Tests for the main module of the package."""

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
class TestMainModule:
    """Tests for the __main__.py module."""

    async def test_main_module_calls_main(self, monkeypatch):
        """Test that __main__.py properly calls the main function."""
        # Mock the main function
        mock_main = MagicMock()
        monkeypatch.setattr("mcp_server_fetch.main", mock_main)

        # Make sure the module is fresh (not previously imported)
        if "mcp_server_fetch.__main__" in sys.modules:
            del sys.modules["mcp_server_fetch.__main__"]

        # Import the main module
        import mcp_server_fetch.__main__ as main_module

        # Save original __name__
        original_name = getattr(main_module, "__name__", None)

        try:
            # Set __name__ to "__main__" to trigger the if __name__ == "__main__" block
            main_module.__name__ = "__main__"

            # Re-execute the module code
            with open(main_module.__file__) as f:
                # This exec is necessary for testing module reloading and is safe in the context of testing
                exec(f.read(), main_module.__dict__)  # noqa: S102

            # Verify main was called
            mock_main.assert_called_once()
        finally:
            # Restore original name if we changed it
            if original_name:
                main_module.__name__ = original_name

    async def test_main_function_parses_args_and_calls_serve(self, monkeypatch):
        """Test that the main function parses arguments and calls serve correctly."""
        # Create a mock for the serve function
        mock_serve = AsyncMock()
        mock_asyncio_run = MagicMock()

        # Create a mock for argparse
        mock_args = MagicMock()
        mock_args.user_agent = "TestUserAgent"
        mock_args.ignore_robots_txt = True
        mock_args.proxy_url = "http://proxy.example.com"
        mock_args.headless = False
        mock_args.wait_until = "domcontentloaded"

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args

        # Apply mocks
        monkeypatch.setattr("mcp_server_fetch.server.serve", mock_serve)
        monkeypatch.setattr("argparse.ArgumentParser", lambda **kwargs: mock_parser)
        monkeypatch.setattr("asyncio.run", mock_asyncio_run)

        # Mock sys.argv
        original_argv = sys.argv
        sys.argv = [
            "mcp_server_fetch",
            "--user-agent",
            "TestUserAgent",
            "--ignore-robots-txt",
            "--proxy-url",
            "http://proxy.example.com",
            "--no-headless",
            "--wait-until",
            "domcontentloaded",
        ]

        try:
            # Import and reload the module to get fresh state
            import mcp_server_fetch

            importlib.reload(mcp_server_fetch)

            # Call the main function directly
            mcp_server_fetch.main()

            # Verify asyncio.run was called with the serve coroutine
            mock_asyncio_run.assert_called_once()
            # Instead of assigning to unused variable, just assert that args exist
            assert mock_asyncio_run.call_args and mock_asyncio_run.call_args[0]

            # Verify serve was called with correct arguments
            assert mock_serve.called
            mock_serve.assert_called_once_with(
                "TestUserAgent",
                True,
                "http://proxy.example.com",
                False,
                "domcontentloaded",
            )
        finally:
            # Restore original argv
            sys.argv = original_argv
