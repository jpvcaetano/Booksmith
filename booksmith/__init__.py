"""
Booksmith - AI-powered book generation library.

A structured, class-based approach to generating complete books using AI/LLM technology.
"""

# Generation components
# LLM backend
from .generation import (
    LLMConfig,
    OpenAIBackend,
    PromptTemplates,
    ResponseParser,
    WritingAgent,
)

# Core data models
from .models import Book, Chapter, Character

__version__ = "0.1.0"

__all__ = [
    # Core models
    "Book",
    "Chapter",
    "Character",
    # LLM backend
    "LLMConfig",
    "OpenAIBackend",
    # Generation
    "WritingAgent",
    "ResponseParser",
    "PromptTemplates",
]
