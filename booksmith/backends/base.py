"""
Base classes and configuration for LLM backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
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
    
class LLMBackend(ABC):
    """Abstract base class for LLM backends."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available."""
        pass 