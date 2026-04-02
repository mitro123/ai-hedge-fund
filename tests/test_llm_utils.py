"""Unit testy pro src/utils/llm.py - LLM utility functions."""

import pytest

from src.exceptions import LLMResponseError
from src.utils.llm import create_default_response, extract_json_from_response


class TestExtractJsonFromResponse:
    def test_extract_valid_json(self):
        content = """Here is the analysis:
```json
{"signal": "bullish", "confidence": 85.0}
```
That's my analysis."""
        result = extract_json_from_response(content)
        assert result is not None
        assert result["signal"] == "bullish"
        assert result["confidence"] == 85.0

    def test_extract_complex_json(self):
        content = """```json
{
    "signal": "bearish",
    "confidence": 70.0,
    "reasoning": {
        "key_factors": ["declining revenue", "high debt"],
        "risk_level": "high"
    }
}
```"""
        result = extract_json_from_response(content)
        assert result is not None
        assert result["signal"] == "bearish"
        assert len(result["reasoning"]["key_factors"]) == 2

    def test_no_json_block_returns_none(self):
        content = "This is just plain text without any JSON."
        result = extract_json_from_response(content)
        assert result is None

    def test_invalid_json_raises(self):
        content = """```json
{invalid json here}
```"""
        with pytest.raises(LLMResponseError):
            extract_json_from_response(content)

    def test_empty_string(self):
        result = extract_json_from_response("")
        assert result is None

    def test_json_with_nested_code_blocks(self):
        content = """Some text
```json
{"key": "value", "number": 42}
```
More text"""
        result = extract_json_from_response(content)
        assert result == {"key": "value", "number": 42}


class TestCreateDefaultResponse:
    def test_creates_defaults_for_string_fields(self):
        from pydantic import BaseModel

        class TestModel(BaseModel):
            signal: str
            reasoning: str

        result = create_default_response(TestModel)
        assert isinstance(result, TestModel)
        assert isinstance(result.signal, str)
        assert isinstance(result.reasoning, str)

    def test_creates_defaults_for_numeric_fields(self):
        from pydantic import BaseModel

        class TestModel(BaseModel):
            confidence: float
            count: int

        result = create_default_response(TestModel)
        assert result.confidence == 0.0
        assert result.count == 0

    def test_creates_defaults_for_dict_fields(self):
        from typing import Dict

        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: Dict[str, str]

        result = create_default_response(TestModel)
        assert result.data == {}

    def test_creates_defaults_for_literal_fields(self):
        from typing import Literal

        from pydantic import BaseModel

        class TestModel(BaseModel):
            action: Literal["buy", "sell", "hold"]

        result = create_default_response(TestModel)
        assert result.action == "buy"  # First literal value
