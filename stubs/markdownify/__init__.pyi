"""Type stubs for markdownify."""
from typing import Optional

# Define constants
ATX: str

def markdownify(
    html: str,
    heading_style: Optional[str] = None,
    strip: Optional[list[str]] = None,
    convert: Optional[list[str]] = None,
    escape_asterisks: bool = False,
    escape_underscores: bool = False
) -> str: ...