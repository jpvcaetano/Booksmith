import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from booksmith.generation.openai import LLMConfig, OpenAIBackend


class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_create_default_config(self):
        """Test creating config with default values."""
        config = LLMConfig()

        assert config.model_name == "gpt-4.1"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.api_key is None
        assert config.api_base is None
        assert config.use_json_mode is True
        assert config.enforce_schema is True

    def test_create_custom_config(self):
        """Test creating config with custom values."""
        config = LLMConfig(
            model_name="gpt-3.5-turbo",
            max_tokens=2000,
            temperature=0.5,
            api_key="test-key",
            api_base="https://api.test.com",
            use_json_mode=False,
            enforce_schema=False,
        )

        assert config.model_name == "gpt-3.5-turbo"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
        assert config.api_key == "test-key"
        assert config.api_base == "https://api.test.com"
        assert config.use_json_mode is False
        assert config.enforce_schema is False


class TestOpenAIBackend:
    """Tests for OpenAIBackend class."""

    @patch("openai.OpenAI")
    def test_initialization_success(self, mock_openai_class, llm_config):
        """Test successful backend initialization."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        backend = OpenAIBackend(llm_config)

        assert backend.config == llm_config
        assert backend.client == mock_client
        mock_openai_class.assert_called_once_with(
            api_key=llm_config.api_key, base_url=llm_config.api_base
        )

    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        config = LLMConfig(api_key=None)

        with patch("openai.OpenAI"):
            backend = OpenAIBackend(config)
            assert backend.client is None

    @patch("openai.OpenAI")
    def test_initialization_import_error(self, mock_openai_class, llm_config):
        """Test initialization with import error."""
        mock_openai_class.side_effect = ImportError("OpenAI not installed")

        backend = OpenAIBackend(llm_config)
        assert backend.client is None

    def test_generate_success(self, mock_openai_backend):
        """Test successful text generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        result = mock_openai_backend.generate("Test prompt")

        assert result == "Generated response"
        mock_openai_backend.client.chat.completions.create.assert_called_once()

        # Check call arguments
        call_args = mock_openai_backend.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["messages"][0]["content"] == "Test prompt"
        assert call_args[1]["max_tokens"] == 1000
        assert call_args[1]["temperature"] == 0.7

    def test_generate_custom_params(self, mock_openai_backend):
        """Test generation with custom parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Custom response"
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        result = mock_openai_backend.generate(
            "Test prompt", max_tokens=500, temperature=0.9
        )

        assert result == "Custom response"

        # Check custom parameters were used
        call_args = mock_openai_backend.client.chat.completions.create.call_args
        assert call_args[1]["max_tokens"] == 500
        assert call_args[1]["temperature"] == 0.9

    def test_generate_no_client(self, llm_config):
        """Test generation when no client is available."""
        backend = OpenAIBackend(llm_config)
        backend.client = None

        with pytest.raises(RuntimeError, match="OpenAI client not available"):
            backend.generate("Test prompt")

    def test_generate_api_error(self, mock_openai_backend):
        """Test handling of API errors during generation."""
        mock_openai_backend.client.chat.completions.create.side_effect = Exception(
            "API Error"
        )

        result = mock_openai_backend.generate("Test prompt")

        assert result.startswith("Error: Failed to generate text")
        assert "API Error" in result

    def test_generate_structured_success(self, mock_openai_backend):
        """Test successful structured generation."""
        # Setup mock response with JSON
        json_response = {"name": "Test Character", "role": "Hero"}
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "role": {"type": "string"}},
        }

        result = mock_openai_backend.generate_structured("Test prompt", schema=schema)

        assert result == json_response

        # Check JSON mode was enabled
        call_args = mock_openai_backend.client.chat.completions.create.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}

    def test_generate_structured_no_schema(self, mock_openai_backend):
        """Test structured generation without schema falls back to regular generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Regular response"
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        result = mock_openai_backend.generate_structured("Test prompt")

        assert result == "Regular response"

        # Should not use JSON mode
        call_args = mock_openai_backend.client.chat.completions.create.call_args
        assert "response_format" not in call_args[1]

    def test_generate_structured_json_disabled(self, llm_config):
        """Test structured generation with JSON mode disabled."""
        config = LLMConfig(api_key="test", use_json_mode=False)

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client

            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Fallback response"
            mock_client.chat.completions.create.return_value = mock_response

            backend = OpenAIBackend(config)

            schema = {"type": "object", "properties": {}}
            result = backend.generate_structured("Test prompt", schema=schema)

            assert result == "Fallback response"

    def test_generate_structured_invalid_json(self, mock_openai_backend):
        """Test handling of invalid JSON in structured generation."""
        # Return invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        schema = {"type": "object", "properties": {}}

        # With schema enforcement enabled, should raise error
        with pytest.raises(ValueError, match="Generated invalid JSON"):
            mock_openai_backend.generate_structured("Test prompt", schema=schema)

    def test_generate_structured_invalid_json_no_enforcement(self, llm_config):
        """Test invalid JSON handling without schema enforcement."""
        config = LLMConfig(api_key="test", enforce_schema=False)

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client

            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Invalid JSON"
            mock_client.chat.completions.create.return_value = mock_response

            backend = OpenAIBackend(config)

            schema = {"type": "object", "properties": {}}
            result = backend.generate_structured("Test prompt", schema=schema)

            # Should return the invalid JSON as string
            assert result == "Invalid JSON"

    @patch("jsonschema.validate")
    def test_json_schema_validation(
        self, mock_jsonschema_validate, mock_openai_backend
    ):
        """Test JSON schema validation."""
        # Setup successful validation
        mock_jsonschema_validate.return_value = None

        json_response = {"name": "Test"}
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = mock_openai_backend.generate_structured("Test prompt", schema=schema)

        assert result == json_response
        mock_jsonschema_validate.assert_called_once_with(json_response, schema)

    @patch("jsonschema.validate")
    def test_json_schema_validation_error(
        self, mock_jsonschema_validate, mock_openai_backend
    ):
        """Test JSON schema validation error."""
        # Setup validation error
        mock_jsonschema_validate.side_effect = Exception("Schema validation failed")

        json_response = {"invalid": "data"}
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        mock_openai_backend.client.chat.completions.create.return_value = mock_response

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        with pytest.raises(ValueError, match="Response doesn't match schema"):
            mock_openai_backend.generate_structured("Test prompt", schema=schema)

    def test_supports_structured_output(self, mock_openai_backend):
        """Test that backend reports supporting structured output."""
        assert mock_openai_backend.supports_structured_output() is True

    def test_is_available_with_client(self, mock_openai_backend):
        """Test availability check with client."""
        assert mock_openai_backend.is_available() is True

    def test_is_available_without_client(self, llm_config):
        """Test availability check without client."""
        backend = OpenAIBackend(llm_config)
        backend.client = None

        assert backend.is_available() is False
