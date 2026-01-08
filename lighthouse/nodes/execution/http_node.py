"""
HTTP Request node for making HTTP/REST API calls.

Pure business logic with NO UI dependencies.
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import time

from lighthouse.nodes.base.base_node import ExecutionNode
from lighthouse.domain.models.node import NodeMetadata, NodeType, ExecutionResult
from lighthouse.domain.models.field_types import FieldDefinition, FieldType


class HTTPRequestType(Enum):
    """Supported HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class HTTPRequestNode(ExecutionNode):
    """
    Node for making HTTP/REST API requests.

    Supports various HTTP methods with configurable URL, body, and timeout.
    Returns response status, headers, and body.

    State Fields:
        url: Target URL for the HTTP request
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        body: Request body content (JSON string)
        timeout: Request timeout in seconds
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get HTTP request node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="HTTPRequest",
            description="Makes HTTP/REST API requests with configurable method, URL, and body",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="url",
                    label="URL",
                    field_type=FieldType.STRING,
                    default_value="https://api.example.com/endpoint",
                    required=True,
                    description="Target URL for the HTTP request",
                ),
                FieldDefinition(
                    name="method",
                    label="Method",
                    field_type=FieldType.ENUM,
                    default_value=HTTPRequestType.GET.value,
                    required=True,
                    enum_options=[m.value for m in HTTPRequestType],
                    description="HTTP request method",
                ),
                FieldDefinition(
                    name="body",
                    label="Request Body",
                    field_type=FieldType.STRING,  # JSON string
                    default_value="{}",
                    required=False,
                    description="Request body (JSON format)",
                ),
                FieldDefinition(
                    name="timeout",
                    label="Timeout (seconds)",
                    field_type=FieldType.NUMBER,
                    default_value=30,
                    required=True,
                    description="Request timeout in seconds",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="API",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the HTTP request.

        Args:
            context: Execution context (not used directly)

        Returns:
            ExecutionResult with response data (status, headers, body)
        """
        import requests

        start_time = time.time()

        try:
            url = self.get_state_value("url", "")
            method = self.get_state_value("method", "GET")
            body = self.get_state_value("body", "{}")
            timeout = self.get_state_value("timeout", 30)

            # Validate inputs
            if not url:
                return ExecutionResult.error_result(
                    error="URL is required",
                    duration=time.time() - start_time,
                )

            # Parse body as JSON for methods that support it
            json_body = self._parse_body(body, method)

            # Make the request
            response = requests.request(
                method=method.upper(),
                url=url,
                json=json_body if json_body is not None else None,
                timeout=float(timeout),
            )

            # Parse response
            response_body = self._parse_response(response)

            duration = time.time() - start_time

            return ExecutionResult.success_result(
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                    "url": response.url,
                    "ok": response.ok,
                },
                duration=duration,
            )

        except requests.Timeout:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Request timed out after {timeout}s",
                duration=duration,
            )

        except requests.ConnectionError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Connection error: {str(e)}",
                duration=duration,
            )

        except requests.RequestException as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Request failed: {str(e)}",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Unexpected error: {str(e)}",
                duration=duration,
            )

    def _parse_body(self, body: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Parse request body as JSON if applicable.

        Args:
            body: Request body string
            method: HTTP method

        Returns:
            Parsed JSON dict or None if not applicable/invalid
        """
        # Only parse body for methods that support it
        if method.upper() not in ["POST", "PUT", "PATCH"]:
            return None

        if not body or body.strip() in ["", "{}", "null"]:
            return None

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            # Return None if JSON is invalid - caller will handle error
            return None

    def _parse_response(self, response) -> Any:
        """
        Parse HTTP response body.

        Attempts to parse as JSON, falls back to text if not JSON.

        Args:
            response: requests.Response object

        Returns:
            Parsed response body (dict if JSON, str otherwise)
        """
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return response.text

    def validate(self) -> list[str]:
        """
        Validate HTTP request configuration.

        Returns:
            List of validation errors
        """
        errors = super().validate()  # Base validation

        # Additional validation
        url = self.get_state_value("url", "")
        if not url or not url.strip():
            errors.append("URL cannot be empty")

        # Validate URL format (basic check)
        if url and not url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")

        # Validate timeout
        timeout = self.get_state_value("timeout", 30)
        try:
            timeout_num = float(timeout)
            if timeout_num <= 0:
                errors.append("Timeout must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Timeout must be a number")

        # Validate JSON body format
        body = self.get_state_value("body", "{}")
        if body and body.strip() not in ["", "{}", "null"]:
            try:
                json.loads(body)
            except json.JSONDecodeError:
                errors.append("Request body must be valid JSON")

        return errors
