"""
OpenAI API backend implementation.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for OpenAI LLM backend."""

    model_name: str = "gpt-4.1"  # Default to a good OpenAI model
    max_tokens: int = 1000
    temperature: float = 0.7
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    # Structured output settings
    use_json_mode: bool = True  # Enable JSON structured output when available
    enforce_schema: bool = True  # Enforce strict schema validation


class OpenAIBackend:
    """OpenAI API backend with structured output support."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._setup_client()

    def _setup_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            if not self.config.api_key:
                logger.warning("No OpenAI API key provided")
                return

            self.client = OpenAI(
                api_key=self.config.api_key, base_url=self.config.api_base
            )

        except ImportError:
            logger.error(
                "OpenAI package not installed. Install with: poetry install -E api"
            )
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error: Failed to generate text - {str(e)}"

    def generate_structured(
        self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """Generate structured JSON output using OpenAI's JSON mode."""
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        if not schema or not self.config.use_json_mode:
            # Fall back to regular generation
            return self.generate(prompt, **kwargs)

        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON that matches this exact schema:
{json.dumps(schema, indent=2)}

Your response must be valid JSON only, no additional text or formatting."""

        try:
            # Use OpenAI's JSON mode for structured output
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": json_prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"},  # Enable JSON mode
            )

            response_text = response.choices[0].message.content.strip()

            # Parse and validate JSON
            try:
                parsed_json = json.loads(response_text)

                # Basic validation if schema enforcement is enabled
                if self.config.enforce_schema:
                    self._validate_json_schema(parsed_json, schema)

                return parsed_json

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in response: {e}")
                if self.config.enforce_schema:
                    raise ValueError(f"Generated invalid JSON: {e}")
                return response_text

        except Exception as e:
            logger.error(f"OpenAI structured generation failed: {e}")
            if self.config.enforce_schema:
                raise
            return f"Error: Failed to generate structured output - {str(e)}"

    def _validate_json_schema(
        self, data: Dict[str, Any], schema: Dict[str, Any]
    ) -> None:
        """Basic JSON schema validation."""
        try:
            import jsonschema

            jsonschema.validate(data, schema)
        except ImportError:
            logger.warning("jsonschema not installed, skipping validation")
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise ValueError(f"Response doesn't match schema: {e}")

    def supports_structured_output(self) -> bool:
        """Check if backend supports structured JSON output."""
        return True

    def is_available(self) -> bool:
        """Check if OpenAI client is ready."""
        return self.client is not None
