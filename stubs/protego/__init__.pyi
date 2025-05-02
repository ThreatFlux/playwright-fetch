"""Type stubs for protego."""

class Protego:
    @classmethod
    def parse(cls, robots_txt_content: str) -> "Protego": ...
    
    def can_fetch(self, url: str, user_agent: str) -> bool: ...