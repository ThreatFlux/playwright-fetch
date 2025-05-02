"""
Separate handler functions for the MCP server
"""

from typing import Literal, cast

from mcp.shared.exceptions import McpError
from mcp.types import (
    INVALID_PARAMS,
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)

from .server import (
    DEFAULT_USER_AGENT_AUTONOMOUS,
    DEFAULT_USER_AGENT_MANUAL,
    Fetch,
    check_may_autonomously_fetch_url,
    fetch_url_with_playwright,
)

# Global configuration variables (will be set by serve)
user_agent_autonomous = DEFAULT_USER_AGENT_AUTONOMOUS
user_agent_manual = DEFAULT_USER_AGENT_MANUAL
ignore_robots_txt = False
proxy_url = None
headless = True
wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "networkidle"


async def list_tools() -> list[Tool]:
    """List available tools for the server."""
    return [
        Tool(
            name="playwright-fetch",
            description="""Fetches a URL from the internet using Playwright and optionally extracts its contents as markdown.
Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access. Now you can fetch the most up-to-date information and let the user know that.""",
            inputSchema=Fetch.model_json_schema(),
        ),
    ]


async def list_prompts() -> list[Prompt]:
    """List available prompts for the server."""
    return [
        Prompt(
            name="playwright-fetch",
            description="Fetch a URL using Playwright and extract its contents as markdown",
            arguments=[PromptArgument(name="url", description="URL to fetch", required=True)],
        ),
    ]


async def call_tool(name, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        args = Fetch(**arguments)
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

    url = str(args.url)
    if not url:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

    if not ignore_robots_txt:
        await check_may_autonomously_fetch_url(url, user_agent_autonomous, proxy_url)

    content, prefix = await fetch_url_with_playwright(
        url,
        user_agent_autonomous,
        force_raw=args.raw,
        proxy_url=proxy_url,
        headless=headless,
        wait_until=wait_until
        if args.wait_for_js
        else cast(Literal["commit", "domcontentloaded", "load", "networkidle"], "domcontentloaded"),
    )

    original_length = len(content)
    if args.start_index >= original_length:
        content = "<e>No more content available.</e>"
    else:
        truncated_content = content[args.start_index : args.start_index + args.max_length]
        if not truncated_content:
            content = "<e>No more content available.</e>"
        else:
            content = truncated_content
            actual_content_length = len(truncated_content)
            remaining_content = original_length - (args.start_index + actual_content_length)
            # Only add the prompt to continue fetching if there is still remaining content
            if actual_content_length == args.max_length and remaining_content > 0:
                next_start = args.start_index + actual_content_length
                content += f"\n\n<e>Content truncated. Call the playwright-fetch tool with a start_index of {next_start} to get more content.</e>"

    return [TextContent(type="text", text=f"{prefix}Contents of {url}:\n{content}")]


async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    """Handle prompt requests."""
    if not arguments or "url" not in arguments:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

    url = arguments["url"]

    try:
        current_wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = wait_until
        content, prefix = await fetch_url_with_playwright(
            url,
            user_agent_manual,
            proxy_url=proxy_url,
            headless=headless,
            wait_until=current_wait_until,
        )
    except McpError as e:
        return GetPromptResult(
            description=f"Failed to fetch {url}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=str(e)))],
        )

    return GetPromptResult(
        description=f"Contents of {url}",
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=prefix + content))],
    )
