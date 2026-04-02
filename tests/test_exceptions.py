"""Unit testy pro src/exceptions.py - Custom exception hierarchy."""

import pytest

from src.exceptions import (
    AgentAnalysisError,
    AgentError,
    AgentNotFoundError,
    APIError,
    APIKeyError,
    APIRateLimitError,
    APIResponseError,
    ConfigurationError,
    DataFetchError,
    HedgeFundError,
    InsufficientDataError,
    InsufficientFundsError,
    InvalidPositionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
    ModelNotFoundError,
    PortfolioError,
    ValidationError,
    handle_exception,
    safe_execute,
)


class TestHedgeFundError:
    def test_basic_creation(self):
        err = HedgeFundError("Test error")
        assert str(err) == "Test error"
        assert err.message == "Test error"
        assert err.error_code == "HedgeFundError"
        assert err.details == {}
        assert err.original_exception is None

    def test_with_all_params(self):
        original = ValueError("original")
        err = HedgeFundError(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            original_exception=original,
        )
        assert err.error_code == "TEST_ERROR"
        assert err.details == {"key": "value"}
        assert err.original_exception is original

    def test_to_dict(self):
        err = HedgeFundError("Test", error_code="CODE", details={"k": "v"})
        d = err.to_dict()
        assert d["error_type"] == "HedgeFundError"
        assert d["error_code"] == "CODE"
        assert d["message"] == "Test"
        assert d["details"] == {"k": "v"}

    def test_inheritance(self):
        err = HedgeFundError("Test")
        assert isinstance(err, Exception)


class TestAPIErrors:
    def test_api_error_inherits(self):
        err = APIError("API failed")
        assert isinstance(err, HedgeFundError)

    def test_api_key_error(self):
        err = APIKeyError("OPENAI_API_KEY")
        assert err.api_key_name == "OPENAI_API_KEY"
        assert err.error_code == "API_KEY_MISSING"
        assert "OPENAI_API_KEY" in err.message

    def test_api_key_error_custom_message(self):
        err = APIKeyError("KEY", message="Custom message")
        assert err.message == "Custom message"

    def test_api_rate_limit_error(self):
        err = APIRateLimitError(retry_after=60)
        assert err.retry_after == 60
        assert err.error_code == "API_RATE_LIMIT"
        assert "60" in err.message

    def test_api_rate_limit_without_retry(self):
        err = APIRateLimitError()
        assert err.retry_after is None

    def test_api_response_error(self):
        err = APIResponseError(status_code=404, response_text="Not found", url="https://api.example.com")
        assert err.status_code == 404
        assert err.response_text == "Not found"
        assert err.url == "https://api.example.com"
        assert err.error_code == "API_RESPONSE_ERROR"
        assert "404" in err.message

    def test_api_response_error_truncates_text(self):
        long_text = "x" * 1000
        err = APIResponseError(status_code=500, response_text=long_text)
        assert len(err.details["response_text"]) == 500


class TestDataFetchError:
    def test_creation(self):
        err = DataFetchError(ticker="AAPL", data_type="price")
        assert err.ticker == "AAPL"
        assert err.data_type == "price"
        assert "AAPL" in err.message
        assert "price" in err.message

    def test_custom_message(self):
        err = DataFetchError(ticker="AAPL", data_type="price", message="Custom error")
        assert err.message == "Custom error"


class TestLLMErrors:
    def test_llm_error_inherits(self):
        err = LLMError("LLM failed")
        assert isinstance(err, HedgeFundError)

    def test_model_not_found(self):
        err = ModelNotFoundError(model_name="gpt-5", provider="OpenAI")
        assert err.model_name == "gpt-5"
        assert err.provider == "OpenAI"
        assert err.error_code == "MODEL_NOT_FOUND"

    def test_llm_response_error(self):
        err = LLMResponseError(agent_name="warren_buffett", response_content="invalid json")
        assert err.agent_name == "warren_buffett"
        assert err.error_code == "LLM_RESPONSE_ERROR"

    def test_llm_response_error_truncates(self):
        long_content = "x" * 500
        err = LLMResponseError(agent_name="test", response_content=long_content)
        assert len(err.details["response_content"]) == 200

    def test_llm_timeout_error(self):
        err = LLMTimeoutError(agent_name="ben_graham", timeout_seconds=30)
        assert err.agent_name == "ben_graham"
        assert err.timeout_seconds == 30
        assert err.error_code == "LLM_TIMEOUT"


class TestAgentErrors:
    def test_agent_not_found(self):
        err = AgentNotFoundError(agent_name="nonexistent")
        assert err.agent_name == "nonexistent"
        assert err.error_code == "AGENT_NOT_FOUND"

    def test_agent_analysis_error(self):
        err = AgentAnalysisError(agent_name="warren_buffett", ticker="AAPL")
        assert err.agent_name == "warren_buffett"
        assert err.ticker == "AAPL"

    def test_insufficient_data_error(self):
        err = InsufficientDataError(ticker="AAPL", required_data="financial_metrics", agent_name="ben_graham")
        assert err.ticker == "AAPL"
        assert err.required_data == "financial_metrics"
        assert "ben_graham" in err.message

    def test_insufficient_data_without_agent(self):
        err = InsufficientDataError(ticker="AAPL", required_data="prices")
        assert err.agent_name is None
        assert "AAPL" in err.message


class TestPortfolioErrors:
    def test_insufficient_funds(self):
        err = InsufficientFundsError(required_amount=10000.0, available_amount=5000.0, ticker="AAPL")
        assert err.required_amount == 10000.0
        assert err.available_amount == 5000.0
        assert err.ticker == "AAPL"
        assert err.error_code == "INSUFFICIENT_FUNDS"

    def test_invalid_position(self):
        err = InvalidPositionError(ticker="AAPL")
        assert err.ticker == "AAPL"
        assert err.error_code == "INVALID_POSITION"

    def test_invalid_position_custom_message(self):
        err = InvalidPositionError(ticker="AAPL", message="No short position exists")
        assert err.message == "No short position exists"


class TestConfigurationErrors:
    def test_configuration_error(self):
        err = ConfigurationError(config_key="API_ENDPOINT")
        assert err.config_key == "API_ENDPOINT"
        assert err.error_code == "CONFIGURATION_ERROR"

    def test_validation_error(self):
        err = ValidationError(field_name="ticker", value="")
        assert err.field_name == "ticker"
        assert err.value == ""
        assert err.error_code == "VALIDATION_ERROR"


class TestHandleExceptionDecorator:
    def test_passes_through_on_success(self):
        @handle_exception
        def good_func():
            return 42

        assert good_func() == 42

    def test_passes_through_hedge_fund_error(self):
        @handle_exception
        def raise_custom():
            raise APIKeyError("TEST_KEY")

        with pytest.raises(APIKeyError):
            raise_custom()

    def test_wraps_generic_exception(self):
        @handle_exception
        def raise_generic():
            raise RuntimeError("something broke")

        with pytest.raises(HedgeFundError) as exc_info:
            raise_generic()
        assert exc_info.value.error_code == "UNEXPECTED_ERROR"
        assert exc_info.value.original_exception is not None


class TestSafeExecute:
    def test_returns_result_on_success(self):
        result = safe_execute(lambda: 42)
        assert result == 42

    def test_returns_default_on_error(self):
        result = safe_execute(lambda: 1 / 0, default_value="fallback")
        assert result == "fallback"

    def test_returns_none_default(self):
        result = safe_execute(lambda: 1 / 0)
        assert result is None

    def test_custom_error_message(self):
        # Should not raise, just log and return default
        result = safe_execute(lambda: 1 / 0, default_value=0, error_message="Division failed")
        assert result == 0
