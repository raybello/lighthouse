"""Unit tests for ChatModelNode."""

import pytest
from unittest.mock import Mock
from lighthouse.nodes.execution.chat_model_node import ChatModelNode


@pytest.fixture
def chat_model_node():
    """Create a ChatModelNode instance."""
    return ChatModelNode(name="Test ChatModel")


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM API response."""
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm an AI assistant ready to help you."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 15,
            "total_tokens": 35
        }
    }
    return response


class TestChatModelNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, chat_model_node):
        """Test creating chat model node."""
        assert chat_model_node.name == "Test ChatModel"
        assert chat_model_node.id is not None

    def test_metadata(self, chat_model_node):
        """Test node metadata."""
        metadata = chat_model_node.metadata
        assert metadata.name == "ChatModel"
        assert len(metadata.fields) == 7  # model, base_url, temperature, max_tokens, timeout, system_prompt, query

    def test_default_state(self, chat_model_node):
        """Test default state values."""
        state = chat_model_node.state
        assert state["model"] == "gemma-3"
        assert state["base_url"] == "http://localhost:8080"
        assert state["temperature"] == 0.1
        assert state["max_tokens"] == 500
        assert state["timeout"] == 30
        assert "AI assistant" in state["system_prompt"]
        assert state["query"] == "Tell me about yourself"


class TestModelExecution:
    """Tests for model execution."""

    def test_successful_query(self, chat_model_node, mock_llm_response, mocker):
        """Test successful LLM query."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "model": "gemma-3",
            "base_url": "http://localhost:8080",
            "query": "What is Python?",
            "timeout": 10,
        })

        result = chat_model_node.execute({})

        assert result.success is True
        assert result.data["response"] == "Hello! I'm an AI assistant ready to help you."
        assert result.data["model"] == "gemma-3"
        assert result.data["usage"]["total_tokens"] == 35
        mock_post.assert_called_once()

    def test_query_with_system_prompt(self, chat_model_node, mock_llm_response, mocker):
        """Test query with custom system prompt."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "model": "gpt-4",
            "base_url": "http://localhost:8080",
            "system_prompt": "You are a Python expert.",
            "query": "Explain decorators",
        })

        result = chat_model_node.execute({})

        assert result.success is True
        # Verify system prompt was included in messages
        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a Python expert."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Explain decorators"

    def test_query_without_system_prompt(self, chat_model_node, mock_llm_response, mocker):
        """Test query without system prompt."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "system_prompt": "",
            "query": "Hello world",
        })

        result = chat_model_node.execute({})

        assert result.success is True
        # Verify only user message is sent
        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_custom_parameters(self, chat_model_node, mock_llm_response, mocker):
        """Test with custom temperature and max_tokens."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "temperature": 0.8,
            "max_tokens": 1000,
            "query": "Be creative",
        })

        result = chat_model_node.execute({})

        assert result.success is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.8
        assert call_kwargs["json"]["max_tokens"] == 1000

    def test_result_includes_all_fields(self, chat_model_node, mock_llm_response, mocker):
        """Test that result includes all expected fields."""
        mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({"query": "test"})
        result = chat_model_node.execute({})

        assert "response" in result.data
        assert "model" in result.data
        assert "usage" in result.data


class TestErrorHandling:
    """Tests for error handling."""

    def test_timeout_error(self, chat_model_node, mocker):
        """Test handling request timeout."""
        import requests
        mocker.patch('requests.post', side_effect=requests.Timeout("Request timed out"))

        chat_model_node.update_state({
            "query": "Long running query",
            "timeout": 1,
        })

        result = chat_model_node.execute({})

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_connection_error(self, chat_model_node, mocker):
        """Test handling connection error."""
        import requests
        mocker.patch('requests.post', side_effect=requests.ConnectionError("Failed to connect"))

        chat_model_node.update_state({"query": "test"})

        result = chat_model_node.execute({})

        assert result.success is False
        assert "connection error" in result.error.lower()

    def test_http_error(self, chat_model_node, mocker):
        """Test handling HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

        mocker.patch('requests.post', return_value=mock_response)

        chat_model_node.update_state({"query": "test"})

        result = chat_model_node.execute({})

        assert result.success is False
        assert "http error" in result.error.lower()

    def test_empty_query_error(self, chat_model_node):
        """Test error with empty query."""
        chat_model_node.update_state({"query": ""})

        result = chat_model_node.execute({})

        assert result.success is False
        assert "query" in result.error.lower()
        assert "empty" in result.error.lower()

    def test_empty_base_url_error(self, chat_model_node):
        """Test error with empty base URL."""
        chat_model_node.update_state({
            "base_url": "",
            "query": "test",
        })

        result = chat_model_node.execute({})

        assert result.success is False
        assert "base url" in result.error.lower()

    def test_unexpected_response_format(self, chat_model_node, mocker):
        """Test handling unexpected API response format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "format"}
        mock_response.raise_for_status.return_value = None

        mocker.patch('requests.post', return_value=mock_response)

        chat_model_node.update_state({"query": "test"})

        result = chat_model_node.execute({})

        assert result.success is False
        assert "response format" in result.error.lower()

    def test_invalid_numeric_parameters(self, chat_model_node):
        """Test error with invalid numeric parameters."""
        chat_model_node.update_state({
            "temperature": "not a number",
            "query": "test",
        })

        result = chat_model_node.execute({})

        assert result.success is False
        assert "parameter" in result.error.lower()


class TestAPIIntegration:
    """Tests for API integration details."""

    def test_correct_endpoint_format(self, chat_model_node, mock_llm_response, mocker):
        """Test that correct API endpoint is called."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "base_url": "http://localhost:8080",
            "query": "test",
        })

        chat_model_node.execute({})

        # Verify endpoint format
        call_args = mock_post.call_args[0]
        assert call_args[0] == "http://localhost:8080/v1/chat/completions"

    def test_endpoint_with_trailing_slash(self, chat_model_node, mock_llm_response, mocker):
        """Test that trailing slash in base URL is handled."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "base_url": "http://localhost:8080/",
            "query": "test",
        })

        chat_model_node.execute({})

        call_args = mock_post.call_args[0]
        assert call_args[0] == "http://localhost:8080/v1/chat/completions"

    def test_request_payload_structure(self, chat_model_node, mock_llm_response, mocker):
        """Test that request payload has correct structure."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "model": "custom-model",
            "temperature": 0.5,
            "max_tokens": 250,
            "query": "test query",
        })

        chat_model_node.execute({})

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "model" in payload
        assert payload["model"] == "custom-model"
        assert "messages" in payload
        assert "temperature" in payload
        assert payload["temperature"] == 0.5
        assert "max_tokens" in payload
        assert payload["max_tokens"] == 250

    def test_timeout_parameter_passed(self, chat_model_node, mock_llm_response, mocker):
        """Test that timeout is passed to request."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({
            "timeout": 60,
            "query": "test",
        })

        chat_model_node.execute({})

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 60.0


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, chat_model_node):
        """Test validation with valid configuration."""
        errors = chat_model_node.validate()
        assert errors == []

    def test_validate_empty_model(self, chat_model_node):
        """Test validation catches empty model."""
        chat_model_node.set_state_value("model", "")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("model" in err.lower() and "empty" in err.lower() for err in errors)

    def test_validate_empty_base_url(self, chat_model_node):
        """Test validation catches empty base URL."""
        chat_model_node.set_state_value("base_url", "")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("base url" in err.lower() for err in errors)

    def test_validate_invalid_url_protocol(self, chat_model_node):
        """Test validation catches invalid URL protocol."""
        chat_model_node.set_state_value("base_url", "ftp://example.com")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("http" in err.lower() for err in errors)

    def test_validate_temperature_too_low(self, chat_model_node):
        """Test validation catches temperature below 0."""
        chat_model_node.set_state_value("temperature", -0.5)

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("temperature" in err.lower() for err in errors)

    def test_validate_temperature_too_high(self, chat_model_node):
        """Test validation catches temperature above 2.0."""
        chat_model_node.set_state_value("temperature", 3.0)

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("temperature" in err.lower() for err in errors)

    def test_validate_invalid_temperature_type(self, chat_model_node):
        """Test validation catches non-numeric temperature."""
        chat_model_node.set_state_value("temperature", "hot")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("temperature" in err.lower() and "number" in err.lower() for err in errors)

    def test_validate_max_tokens_negative(self, chat_model_node):
        """Test validation catches negative max_tokens."""
        chat_model_node.set_state_value("max_tokens", -100)

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("max tokens" in err.lower() for err in errors)

    def test_validate_max_tokens_excessive(self, chat_model_node):
        """Test validation catches excessive max_tokens."""
        chat_model_node.set_state_value("max_tokens", 200000)

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("max tokens" in err.lower() for err in errors)

    def test_validate_invalid_max_tokens_type(self, chat_model_node):
        """Test validation catches non-numeric max_tokens."""
        chat_model_node.set_state_value("max_tokens", "many")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("max tokens" in err.lower() and "number" in err.lower() for err in errors)

    def test_validate_negative_timeout(self, chat_model_node):
        """Test validation catches negative timeout."""
        chat_model_node.set_state_value("timeout", -10)

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_empty_query(self, chat_model_node):
        """Test validation catches empty query."""
        chat_model_node.set_state_value("query", "")

        errors = chat_model_node.validate()

        assert len(errors) > 0
        assert any("query" in err.lower() for err in errors)


class TestStateManagement:
    """Tests for state management."""

    def test_state_persistence(self, chat_model_node):
        """Test that state persists across updates."""
        chat_model_node.update_state({
            "model": "gpt-4",
            "base_url": "https://api.openai.com",
            "temperature": 0.7,
        })

        state = chat_model_node.state

        assert state["model"] == "gpt-4"
        assert state["base_url"] == "https://api.openai.com"
        assert state["temperature"] == 0.7
        assert state["max_tokens"] == 500  # Default unchanged

    def test_parameter_type_conversion(self, chat_model_node, mock_llm_response, mocker):
        """Test that parameters are converted to correct types."""
        mock_post = mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.set_state_value("temperature", "0.5")
        chat_model_node.set_state_value("max_tokens", "750")
        chat_model_node.set_state_value("timeout", "45")
        chat_model_node.set_state_value("query", "test")

        result = chat_model_node.execute({})

        assert result.success is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.5
        assert call_kwargs["json"]["max_tokens"] == 750
        assert call_kwargs["timeout"] == 45.0


class TestExecutionResult:
    """Tests for execution result properties."""

    def test_result_has_duration(self, chat_model_node, mock_llm_response, mocker):
        """Test that result includes execution duration."""
        mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({"query": "test"})
        result = chat_model_node.execute({})

        assert result.duration_seconds >= 0

    def test_successful_result_structure(self, chat_model_node, mock_llm_response, mocker):
        """Test structure of successful result."""
        mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({"query": "test"})
        result = chat_model_node.execute({})

        assert result.success is True
        assert result.error is None
        assert isinstance(result.data, dict)
        assert "response" in result.data
        assert "model" in result.data
        assert "usage" in result.data

    def test_failed_result_structure(self, chat_model_node):
        """Test structure of failed result."""
        chat_model_node.update_state({"query": ""})
        result = chat_model_node.execute({})

        assert result.success is False
        assert result.error is not None
        assert isinstance(result.error, str)


class TestUsageStatistics:
    """Tests for usage statistics tracking."""

    def test_usage_stats_included(self, chat_model_node, mock_llm_response, mocker):
        """Test that usage statistics are captured."""
        mocker.patch('requests.post', return_value=mock_llm_response)

        chat_model_node.update_state({"query": "test"})
        result = chat_model_node.execute({})

        assert result.success is True
        usage = result.data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert usage["total_tokens"] == 35

    def test_missing_usage_stats(self, chat_model_node, mocker):
        """Test handling when usage stats are missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"role": "assistant", "content": "Response"}}
            ]
            # No usage field
        }
        mock_response.raise_for_status.return_value = None

        mocker.patch('requests.post', return_value=mock_response)

        chat_model_node.update_state({"query": "test"})
        result = chat_model_node.execute({})

        assert result.success is True
        assert result.data["usage"] == {}
