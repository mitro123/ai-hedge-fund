# Type stubs for langchain_core.messages
from typing import Any, Optional

class HumanMessage:
    def __init__(self, content: str, name: Optional[str] = None) -> None: ...
    content: str
    name: Optional[str]
