from typing import Any, Dict, List, Literal, Optional

from mcp.types import GetPromptResult, TextContent, Tool

# Global configuration variables
user_agent_autonomous: str
user_agent_manual: str
ignore_robots_txt: bool
proxy_url: Optional[str]
headless: bool
wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"]

# Handler functions
async def list_tools() -> List[Tool]: ...
async def list_prompts() -> List[Any]: ...
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]: ...
async def get_prompt(name: str, arguments: Optional[Dict[str, Any]]) -> GetPromptResult: ...
