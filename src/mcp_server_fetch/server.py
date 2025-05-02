"""
MCP Server for Playwright-based web fetching
Author: Wyatt Roersma <wyattroersma@gmail.com>
Licensed under MIT License
"""

import asyncio
import logging
import re
from typing import Annotated, Any, Dict, Literal, Optional, Tuple
from urllib.parse import urlparse, urlunparse

import markdownify
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    ErrorData,
)
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import ProxySettings, async_playwright
from protego import Protego
from pydantic import AnyUrl, BaseModel, Field

DEFAULT_USER_AGENT_AUTONOMOUS = (
    "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)"
)
DEFAULT_USER_AGENT_MANUAL = (
    "ModelContextProtocol/1.0 (User-Specified; +https://github.com/modelcontextprotocol/servers)"
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def html_to_markdown(html: str) -> str:
    """Convert HTML content to Markdown format.

    Args:
        html: Raw HTML content to process

    Returns:
        Simplified markdown version of the content
    """
    return markdownify.markdownify(html, heading_style=markdownify.ATX)


def get_robots_txt_url(url: str) -> str:
    """Get the robots.txt URL for a given website URL.

    Args:
        url: Website URL to get robots.txt for

    Returns:
        URL of the robots.txt file
    """
    # Parse the URL into components
    parsed = urlparse(url)

    # Reconstruct the base URL with just scheme, netloc, and /robots.txt path
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

    return robots_url


async def check_may_autonomously_fetch_url(url: str, user_agent: str, proxy_url: Optional[str] = None) -> None:
    """
    Check if the URL can be fetched by the user agent according to the robots.txt file.
    Raises a McpError if not.
    """
    from httpx import AsyncClient, HTTPError

    robot_txt_url = get_robots_txt_url(url)

    async with AsyncClient(proxies=proxy_url) as client:
        try:
            response = await client.get(robot_txt_url, follow_redirects=True, headers={"User-Agent": user_agent})
        except HTTPError:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Failed to fetch robots.txt {robot_txt_url} due to a connection issue",
                ),
            )
        if response.status_code in (401, 403):
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"When fetching robots.txt ({robot_txt_url}), received status {response.status_code} so assuming that autonomous fetching is not allowed, the user can try manually fetching by using the fetch prompt",
                ),
            )
        elif 400 <= response.status_code < 500:
            return
        robot_txt = response.text
    processed_robot_txt = "\n".join(line for line in robot_txt.splitlines() if not line.strip().startswith("#"))
    robot_parser = Protego.parse(processed_robot_txt)
    if not robot_parser.can_fetch(str(url), user_agent):
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"The site's robots.txt ({robot_txt_url}), specifies that autonomous fetching of this page is not allowed, "
                f"<useragent>{user_agent}</useragent>\n"
                f"<url>{url}</url>"
                f"<robots>\n{robot_txt}\n</robots>\n"
                f"The assistant must let the user know that it failed to view the page. The assistant may provide further guidance based on the above information.\n"
                f"The assistant can tell the user that they can try manually fetching the page by using the fetch prompt within their UI.",
            ),
        )


async def fetch_url_with_playwright(
    url: str,
    user_agent: str,
    force_raw: bool = False,
    proxy_url: Optional[str] = None,
    headless: bool = True,
    wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "networkidle",
) -> Tuple[str, str]:
    """
    Fetch the URL using Playwright and return the content in a form ready for the LLM,
    as well as a prefix string with status information.
    """
    async with async_playwright() as p:
        browser_type = p.chromium
        browser_kwargs: Dict[str, Any] = {"headless": headless}

        if proxy_url:
            proxy_settings = ProxySettings(server=proxy_url)
            browser_kwargs["proxy"] = proxy_settings

        try:
            browser = await browser_type.launch(**browser_kwargs)
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()

            try:
                response = await page.goto(url, wait_until=wait_until, timeout=30000)
                if not response:
                    raise McpError(
                        ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - no response received"),
                    )

                if response.status >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Failed to fetch {url} - status code {response.status}",
                        ),
                    )

                # Wait for any client-side rendering to complete
                await page.wait_for_load_state("networkidle", timeout=5000)

                # Get content
                content_type = response.headers.get("content-type", "")
                is_page_html = "text/html" in content_type or not content_type

                if is_page_html and not force_raw:
                    # Get the rendered HTML content after JavaScript execution
                    html_content = await page.content()

                    # Extract the main content using a common article extraction selector pattern
                    try:
                        # Try to find main content area using common selectors
                        for selector in [
                            "main",
                            "article",
                            ".main-content",
                            "#main-content",
                            ".content",
                            "#content",
                            ".article",
                            ".post",
                            ".entry-content",
                        ]:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    main_content = await element.inner_html()
                                    break
                            except PlaywrightError:
                                continue
                        else:
                            # If no specific content area found, get the body
                            main_content = html_content

                        # Convert to markdown
                        markdown_content = html_to_markdown(main_content)

                        # Clean up markdown (remove excessive newlines, etc.)
                        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

                        return markdown_content, ""
                    except Exception as e:
                        logger.exception(f"Error extracting content: {e}")
                        return html_to_markdown(html_content), ""

                # For non-HTML or if raw content is requested
                page_content = await page.content()
                return (
                    page_content,
                    f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
                )

            finally:
                await context.close()
                await browser.close()

        except PlaywrightError as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))
        except asyncio.TimeoutError:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Timeout when fetching {url}"))
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error fetching {url}: {e!s}"))


class Fetch(BaseModel):
    """Parameters for fetching a URL."""

    url: Annotated[AnyUrl, Field(description="URL to fetch")]
    max_length: Annotated[
        int,
        Field(default=5000, description="Maximum number of characters to return.", gt=0, lt=1000000),
    ]
    start_index: Annotated[
        int,
        Field(
            default=0,
            description="On return output starting at this character index, useful if a previous fetch was truncated and more context is required.",
            ge=0,
        ),
    ]
    raw: Annotated[
        bool,
        Field(default=False, description="Get the actual HTML content of the requested page, without simplification."),
    ]
    wait_for_js: Annotated[
        bool,
        Field(default=True, description="Wait for JavaScript to execute (client-side rendering)."),
    ]


async def serve(
    custom_user_agent: Optional[str] = None,
    ignore_robots_txt: bool = False,
    proxy_url: Optional[str] = None,
    headless: bool = True,
    wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "networkidle",
) -> None:
    """Run the Playwright fetch MCP server.

    Args:
        custom_user_agent: Optional custom User-Agent string to use for requests
        ignore_robots_txt: Whether to ignore robots.txt restrictions
        proxy_url: Optional proxy URL to use for requests
        headless: Whether to run the browser in headless mode
        wait_until: When to consider navigation succeeded
    """
    # Import required modules
    import sys

    # Import the handlers
    from .handlers import (
        call_tool,
        get_prompt,
        list_prompts,
        list_tools,
    )

    handlers_module = sys.modules["mcp_server_fetch.handlers"]
    # Set configuration variables in the handlers module
    # Use type: ignore to handle dynamic attribute assignment through sys.modules
    handlers_module.user_agent_autonomous = custom_user_agent or DEFAULT_USER_AGENT_AUTONOMOUS  # type: ignore
    handlers_module.user_agent_manual = custom_user_agent or DEFAULT_USER_AGENT_MANUAL  # type: ignore
    handlers_module.ignore_robots_txt = ignore_robots_txt  # type: ignore
    handlers_module.proxy_url = proxy_url  # type: ignore
    handlers_module.headless = headless  # type: ignore
    handlers_module.wait_until = wait_until  # type: ignore

    # Create server instance
    server: Server = Server("mcp-playwright-fetch")

    # Register the handlers
    server.list_tools()(list_tools)
    server.list_prompts()(list_prompts)
    server.call_tool()(call_tool)
    server.get_prompt()(get_prompt)
    # Start the server
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
