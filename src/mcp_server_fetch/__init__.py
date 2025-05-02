"""MCP server module for the Playwright fetch server."""

import argparse
import asyncio

from .server import serve

__version__ = "0.1.1"


def main():
    """MCP Playwright Fetch Server - Web content fetching with Playwright for MCP."""
    parser = argparse.ArgumentParser(description="give a model the ability to make web requests using Playwright")
    parser.add_argument("--user-agent", type=str, help="Custom User-Agent string")
    parser.add_argument("--ignore-robots-txt", action="store_true", help="Ignore robots.txt restrictions")
    parser.add_argument("--proxy-url", type=str, help="Proxy URL to use for requests")
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--wait-until",
        type=str,
        default="networkidle",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        help="When to consider navigation succeeded (default: networkidle)",
    )

    args = parser.parse_args()
    asyncio.run(serve(args.user_agent, args.ignore_robots_txt, args.proxy_url, args.headless, args.wait_until))


if __name__ == "__main__":
    main()
