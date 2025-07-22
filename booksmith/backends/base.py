"""
Base classes and configuration for LLM backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration for LLM backends."""
    backend: str = "huggingface"  # "huggingface", "openai", "anthropic", "ollama", "mlx"
    model_name: str = "microsoft/DialoGPT-medium"  # Default small model for testing
    max_tokens: int = 1000
    temperature: float = 0.7
    device: str = "auto"  # "auto", "cpu", "cuda", "mps"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    # New: structured output settings
    use_json_mode: bool = True  # Enable JSON structured output when available
    enforce_schema: bool = True  # Enforce strict schema validation
    
class LLMBackend(ABC):
    """Abstract base class for LLM backends."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Union[str, Dict[str, Any]]:
        """Generate structured output with optional JSON schema.
        
        Args:
            prompt: The input prompt
            schema: Optional JSON schema to enforce structure
            **kwargs: Additional generation parameters
            
        Returns:
            Dict if structured output is supported and schema provided, otherwise str
        """
        # Default implementation falls back to regular generation
        return self.generate(prompt, **kwargs)
    
    def supports_structured_output(self) -> bool:
        """Check if backend supports structured JSON output."""
        return False
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available."""
        pass 