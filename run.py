#!/usr/bin/env python3
"""
Entry point script for running the Playwright Fetch MCP Server in Docker.
"""

import os
import signal
import sys

# Ensure src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_server_fetch.__main__ import main

# Handle signals properly
def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    print("Received signal to terminate. Shutting down...", file=sys.stderr)
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Parse environment variables as configuration
    custom_user_agent = os.environ.get("PLAYWRIGHT_FETCH_USER_AGENT")
    ignore_robots_txt = os.environ.get("PLAYWRIGHT_FETCH_IGNORE_ROBOTS", "false").lower() == "true"
    proxy_url = os.environ.get("PLAYWRIGHT_FETCH_PROXY")
    headless = os.environ.get("PLAYWRIGHT_FETCH_HEADLESS", "true").lower() == "true"
    wait_until = os.environ.get("PLAYWRIGHT_FETCH_WAIT_UNTIL", "networkidle")
    
    # Override sys.argv with environment variables
    sys.argv = [sys.argv[0]]
    if custom_user_agent:
        sys.argv.extend(["--user-agent", custom_user_agent])
    if ignore_robots_txt:
        sys.argv.append("--ignore-robots-txt")
    if proxy_url:
        sys.argv.extend(["--proxy", proxy_url])
    if not headless:
        sys.argv.append("--no-headless")
    if wait_until:
        sys.argv.extend(["--wait-until", wait_until])
    
    # Run the main function
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)