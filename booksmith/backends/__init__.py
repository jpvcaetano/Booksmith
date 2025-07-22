"""
Booksmith LLM backends.

This package contains different LLM backend implementations for local and cloud models.
"""

from .base import LLMConfig, LLMBackend
from .factory import create_llm_backend, RECOMMENDED_MODELS, MODEL_CATEGORIES
from .huggingface import HuggingFaceBackend
from .mlx import MLXBackend
from .openai import OpenAIBackend

__all__ = [
    "LLMConfig",
    "LLMBackend", 
    "create_llm_backend",
    "RECOMMENDED_MODELS",
    "MODEL_CATEGORIES",
    "HuggingFaceBackend",
    "MLXBackend", 
    "OpenAIBackend",
] 