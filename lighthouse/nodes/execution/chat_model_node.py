"""
ChatModel node for interfacing with chat/language models.

Pure business logic with NO UI dependencies.
"""

import time
from typing import Any, Dict

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import ExecutionResult, NodeMetadata, NodeType
from lighthouse.nodes.base.base_node import ExecutionNode


class ChatModelNode(ExecutionNode):
    """
    Node for interfacing with chat/language models via OpenAI-compatible APIs.

    Supports local LLMs (Ollama, LM Studio) and cloud providers.
    Configures and executes queries to language models with customizable parameters.

    State Fields:
        model: Model identifier (e.g., "gemma-3")
        base_url: API endpoint URL
        temperature: Model temperature (0.0 - 1.0)
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
        system_prompt: System prompt for model behavior
        query: User query to send to the model
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get chat model node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="ChatModel",
            description="Interfaces with chat/language models via OpenAI-compatible API",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="model",
                    label="Model",
                    field_type=FieldType.STRING,
                    default_value="gemma-3",
                    required=True,
                    description="Model identifier to use",
                ),
                FieldDefinition(
                    name="base_url",
                    label="Base URL",
                    field_type=FieldType.STRING,
                    default_value="http://localhost:8080",
                    required=True,
                    description="API endpoint base URL",
                ),
                FieldDefinition(
                    name="temperature",
                    label="Temperature",
                    field_type=FieldType.NUMBER,
                    default_value=0.1,
                    required=True,
                    description="Model temperature (0.0-1.0, lower = more deterministic)",
                ),
                FieldDefinition(
                    name="max_tokens",
                    label="Max Tokens",
                    field_type=FieldType.NUMBER,
                    default_value=500,
                    required=True,
                    description="Maximum number of tokens to generate",
                ),
                FieldDefinition(
                    name="timeout",
                    label="Timeout (seconds)",
                    field_type=FieldType.NUMBER,
                    default_value=30,
                    required=True,
                    description="Request timeout in seconds",
                ),
                FieldDefinition(
                    name="system_prompt",
                    label="System Prompt",
                    field_type=FieldType.STRING,  # Long text
                    default_value=(
                        "You are a highly capable AI assistant designed to help with \n"
                        "coding, technical problems, and general inquiries.\n"
                        "Your core strengths are problem-solving, clear explanations, \n"
                        "and writing high-quality code."
                    ),
                    required=False,
                    description="System prompt to guide model behavior",
                ),
                FieldDefinition(
                    name="query",
                    label="Query",
                    field_type=FieldType.STRING,
                    default_value="Tell me about yourself",
                    required=True,
                    description="User query to send to the model",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="AI",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the chat model query using OpenAI-compatible API.

        Args:
            context: Execution context (not used directly)

        Returns:
            ExecutionResult with model response, model info, and usage stats
        """
        import requests

        start_time = time.time()

        try:
            model = self.get_state_value("model", "gemma-3")
            base_url = self.get_state_value("base_url", "http://localhost:8080")
            temperature = self.get_state_value("temperature", 0.1)
            max_tokens = self.get_state_value("max_tokens", 500)
            timeout = self.get_state_value("timeout", 30)
            system_prompt = self.get_state_value("system_prompt", "")
            query = self.get_state_value("query", "")

            # Validate inputs
            if not query or not query.strip():
                return ExecutionResult.error_result(
                    error="Query cannot be empty",
                    duration=time.time() - start_time,
                )

            if not base_url or not base_url.strip():
                return ExecutionResult.error_result(
                    error="Base URL cannot be empty",
                    duration=time.time() - start_time,
                )

            # Build messages
            messages = []
            if system_prompt and system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": query})

            # Convert parameters to appropriate types
            try:
                temperature_val = float(temperature)
                max_tokens_val = int(max_tokens)
                timeout_val = float(timeout)
            except (ValueError, TypeError):
                return ExecutionResult.error_result(
                    error="Invalid numeric parameter values",
                    duration=time.time() - start_time,
                )

            # Make API call (OpenAI-compatible format)
            response = requests.post(
                f"{base_url.rstrip('/')}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature_val,
                    "max_tokens": max_tokens_val,
                },
                timeout=timeout_val,
            )

            response.raise_for_status()
            result = response.json()

            # Extract response text and usage
            response_text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            duration = time.time() - start_time

            return ExecutionResult.success_result(
                data={
                    "response": response_text,
                    "model": model,
                    "usage": usage,
                },
                duration=duration,
            )

        except requests.Timeout:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Model request timed out after {timeout}s",
                duration=duration,
            )

        except requests.ConnectionError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Connection error: {str(e)}",
                duration=duration,
            )

        except requests.HTTPError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"HTTP error: {str(e)}",
                duration=duration,
            )

        except KeyError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Unexpected response format: missing {e}",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Model request failed: {str(e)}",
                duration=duration,
            )

    def validate(self) -> list[str]:
        """
        Validate chat model configuration.

        Returns:
            List of validation errors
        """
        errors = super().validate()

        # Validate model
        model = self.get_state_value("model", "")
        if not model or not model.strip():
            errors.append("Model cannot be empty")

        # Validate base URL
        base_url = self.get_state_value("base_url", "")
        if not base_url or not base_url.strip():
            errors.append("Base URL cannot be empty")

        # Basic URL format check
        if base_url and not base_url.startswith(("http://", "https://")):
            errors.append("Base URL must start with http:// or https://")

        # Validate temperature
        temperature = self.get_state_value("temperature", 0.1)
        try:
            temp_val = float(temperature)
            if temp_val < 0.0 or temp_val > 2.0:
                errors.append("Temperature must be between 0.0 and 2.0")
        except (ValueError, TypeError):
            errors.append("Temperature must be a number")

        # Validate max_tokens
        max_tokens = self.get_state_value("max_tokens", 500)
        try:
            tokens_val = int(max_tokens)
            if tokens_val <= 0:
                errors.append("Max tokens must be greater than 0")
            if tokens_val > 100000:  # Reasonable upper limit
                errors.append("Max tokens cannot exceed 100000")
        except (ValueError, TypeError):
            errors.append("Max tokens must be a number")

        # Validate timeout
        timeout = self.get_state_value("timeout", 30)
        try:
            timeout_num = float(timeout)
            if timeout_num <= 0:
                errors.append("Timeout must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Timeout must be a number")

        # Validate query
        query = self.get_state_value("query", "")
        if not query or not query.strip():
            errors.append("Query cannot be empty")

        return errors
