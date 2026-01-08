"""Unit tests for HTTPRequestNode."""

import pytest
from unittest.mock import Mock, MagicMock
from lighthouse.nodes.execution.http_node import HTTPRequestNode, HTTPRequestType


@pytest.fixture
def http_node():
    """Create an HTTPRequestNode instance."""
    return HTTPRequestNode(name="Test HTTP")


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.headers = {"Content-Type": "application/json"}
    response.url = "https://api.example.com/test"
    response.json.return_value = {"message": "success"}
    response.text = '{"message": "success"}'
    return response


class TestHTTPNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, http_node):
        """Test creating HTTP node."""
        assert http_node.name == "Test HTTP"
        assert http_node.id is not None

    def test_metadata(self, http_node):
        """Test node metadata."""
        metadata = http_node.metadata
        assert metadata.name == "HTTPRequest"
        assert len(metadata.fields) == 4  # url, method, body, timeout

    def test_default_state(self, http_node):
        """Test default state values."""
        state = http_node.state
        assert "url" in state
        assert state["method"] == "GET"
        assert state["body"] == "{}"
        assert state["timeout"] == 30


class TestHTTPRequests:
    """Tests for HTTP request execution."""

    def test_get_request(self, http_node, mock_response, mocker):
        """Test GET request."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com/users",
            "method": "GET",
            "timeout": 10
        })

        result = http_node.execute({})

        assert result.success is True
        assert result.data["status_code"] == 200
        assert result.data["body"] == {"message": "success"}
        mock_request.assert_called_once()

    def test_post_request_with_body(self, http_node, mock_response, mocker):
        """Test POST request with JSON body."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com/users",
            "method": "POST",
            "body": '{"name": "John", "age": 30}',
            "timeout": 10
        })

        result = http_node.execute({})

        assert result.success is True
        # Verify JSON body was passed
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"name": "John", "age": 30}

    def test_put_request(self, http_node, mock_response, mocker):
        """Test PUT request."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com/users/1",
            "method": "PUT",
            "body": '{"name": "Updated"}',
        })

        result = http_node.execute({})

        assert result.success is True
        assert mock_request.call_args[1]["method"] == "PUT"

    def test_delete_request(self, http_node, mock_response, mocker):
        """Test DELETE request."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com/users/1",
            "method": "DELETE",
        })

        result = http_node.execute({})

        assert result.success is True
        assert mock_request.call_args[1]["method"] == "DELETE"


class TestResponseHandling:
    """Tests for response parsing."""

    def test_json_response(self, http_node, mocker):
        """Test handling JSON response."""
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.headers = {}
        response.url = "https://api.example.com"
        response.json.return_value = {"data": [1, 2, 3]}

        mocker.patch('requests.request', return_value=response)

        http_node.update_state({"url": "https://api.example.com"})
        result = http_node.execute({})

        assert result.data["body"] == {"data": [1, 2, 3]}

    def test_text_response(self, http_node, mocker):
        """Test handling non-JSON text response."""
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.headers = {}
        response.url = "https://api.example.com"
        response.json.side_effect = ValueError("Not JSON")
        response.text = "Plain text response"

        mocker.patch('requests.request', return_value=response)

        http_node.update_state({"url": "https://api.example.com"})
        result = http_node.execute({})

        assert result.data["body"] == "Plain text response"

    def test_response_includes_all_fields(self, http_node, mock_response, mocker):
        """Test that response includes all expected fields."""
        mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({"url": "https://api.example.com"})
        result = http_node.execute({})

        assert "status_code" in result.data
        assert "headers" in result.data
        assert "body" in result.data
        assert "url" in result.data
        assert "ok" in result.data


class TestErrorHandling:
    """Tests for error conditions."""

    def test_timeout_error(self, http_node, mocker):
        """Test handling request timeout."""
        import requests
        mocker.patch('requests.request', side_effect=requests.Timeout("Request timed out"))

        http_node.update_state({
            "url": "https://slow-api.example.com",
            "timeout": 1
        })

        result = http_node.execute({})

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_connection_error(self, http_node, mocker):
        """Test handling connection error."""
        import requests
        mocker.patch('requests.request', side_effect=requests.ConnectionError("Failed to connect"))

        http_node.update_state({"url": "https://invalid.example.com"})

        result = http_node.execute({})

        assert result.success is False
        assert "connection error" in result.error.lower()

    def test_empty_url_error(self, http_node):
        """Test error with empty URL."""
        http_node.update_state({"url": ""})

        result = http_node.execute({})

        assert result.success is False
        assert "url is required" in result.error.lower()

    def test_invalid_json_body(self, http_node, mock_response, mocker):
        """Test with invalid JSON body."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com",
            "method": "POST",
            "body": "{invalid json",
        })

        result = http_node.execute({})

        # Should still make request but with None body
        assert result.success is True
        assert mock_request.call_args[1]["json"] is None


class TestBodyParsing:
    """Tests for request body parsing."""

    def test_empty_body_for_get(self, http_node, mock_response, mocker):
        """Test that GET requests don't send body."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com",
            "method": "GET",
            "body": '{"ignored": "value"}',
        })

        result = http_node.execute({})

        assert result.success is True
        assert mock_request.call_args[1]["json"] is None

    def test_body_for_post(self, http_node, mock_response, mocker):
        """Test that POST requests send JSON body."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com",
            "method": "POST",
            "body": '{"key": "value"}',
        })

        result = http_node.execute({})

        assert mock_request.call_args[1]["json"] == {"key": "value"}

    def test_empty_body_string(self, http_node, mock_response, mocker):
        """Test with empty body string."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com",
            "method": "POST",
            "body": "",
        })

        result = http_node.execute({})

        assert mock_request.call_args[1]["json"] is None


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, http_node):
        """Test validation with valid configuration."""
        errors = http_node.validate()
        assert errors == []

    def test_validate_empty_url(self, http_node):
        """Test validation catches empty URL."""
        http_node.set_state_value("url", "")

        errors = http_node.validate()

        assert len(errors) > 0
        assert any("url" in err.lower() and "empty" in err.lower() for err in errors)

    def test_validate_invalid_url_protocol(self, http_node):
        """Test validation catches invalid URL protocol."""
        http_node.set_state_value("url", "ftp://example.com")

        errors = http_node.validate()

        assert len(errors) > 0
        assert any("http" in err.lower() for err in errors)

    def test_validate_negative_timeout(self, http_node):
        """Test validation catches negative timeout."""
        http_node.set_state_value("timeout", -5)

        errors = http_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_invalid_json_body(self, http_node):
        """Test validation catches invalid JSON."""
        http_node.set_state_value("body", "{invalid json")

        errors = http_node.validate()

        assert len(errors) > 0
        assert any("json" in err.lower() for err in errors)

    def test_validate_valid_json_body(self, http_node):
        """Test that valid JSON passes validation."""
        http_node.set_state_value("body", '{"valid": "json", "number": 123}')

        errors = http_node.validate()

        # Should have no JSON-related errors
        assert not any("json" in err.lower() for err in errors)


class TestHTTPMethods:
    """Tests for different HTTP methods."""

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
    def test_all_http_methods(self, http_node, mock_response, mocker, method):
        """Test all HTTP methods are supported."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.update_state({
            "url": "https://api.example.com",
            "method": method,
        })

        result = http_node.execute({})

        assert result.success is True
        assert mock_request.call_args[1]["method"] == method


class TestStateManagement:
    """Tests for state management."""

    def test_custom_timeout(self, http_node, mock_response, mocker):
        """Test custom timeout value."""
        mock_request = mocker.patch('requests.request', return_value=mock_response)

        http_node.set_state_value("timeout", 60)
        http_node.set_state_value("url", "https://api.example.com")

        result = http_node.execute({})

        assert mock_request.call_args[1]["timeout"] == 60.0

    def test_state_persistence(self, http_node):
        """Test that state persists across updates."""
        http_node.update_state({
            "url": "https://custom.api.com",
            "method": "POST"
        })

        state = http_node.state

        assert state["url"] == "https://custom.api.com"
        assert state["method"] == "POST"
        assert state["timeout"] == 30  # Default unchanged


class TestResponseStatusCodes:
    """Tests for different response status codes."""

    @pytest.mark.parametrize("status_code,is_ok", [
        (200, True),
        (201, True),
        (400, False),
        (404, False),
        (500, False),
    ])
    def test_various_status_codes(self, http_node, mocker, status_code, is_ok):
        """Test handling various HTTP status codes."""
        response = Mock()
        response.status_code = status_code
        response.ok = is_ok
        response.headers = {}
        response.url = "https://api.example.com"
        response.json.return_value = {}

        mocker.patch('requests.request', return_value=response)

        http_node.update_state({"url": "https://api.example.com"})
        result = http_node.execute({})

        assert result.success is True  # Request completed
        assert result.data["status_code"] == status_code
        assert result.data["ok"] == is_ok
