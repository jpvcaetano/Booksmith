"""
Booksmith - AI-powered book generation library.

A structured, class-based approach to generating complete books using AI/LLM technology.
"""

# Core data models
from .models import Book, Chapter, Character

# LLM backends
from .backends import (
    LLMConfig, 
    LLMBackend,
    create_llm_backend,
    RECOMMENDED_MODELS,
    MODEL_CATEGORIES,
    HuggingFaceBackend,
    MLXBackend,
    OpenAIBackend,
)

# Generation components
from .generation import (
    WritingAgent,
    ResponseParser,
    PromptTemplates,
)

__version__ = "0.1.0"

__all__ = [
    # Core models
    "Book",
    "Chapter", 
    "Character",
    
    # LLM backends
    "LLMConfig",
    "LLMBackend",
    "create_llm_backend",
    "RECOMMENDED_MODELS",
    "MODEL_CATEGORIES",
    "HuggingFaceBackend",
    "MLXBackend", 
    "OpenAIBackend",
    
    # Generation
    "WritingAgent",
    "ResponseParser",
    "PromptTemplates",
] 