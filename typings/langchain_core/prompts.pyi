# Type stubs for langchain_core.prompts
from typing import Any, List, Tuple

class ChatPromptTemplate:
    @classmethod
    def from_messages(cls, messages: List[Tuple[str, str]]) -> "ChatPromptTemplate": ...
    def invoke(self, input_dict: dict) -> Any: ...
