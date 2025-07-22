"""
Book generation system with structured LLM output support.
"""

from .agent import WritingAgent
from .openai import LLMConfig, OpenAIBackend
from .parsers import ResponseParser, StructuredResponseParser
from .prompts import (
    PromptTemplates,
    generate_chapter_content_prompt,
    generate_chapter_plan_prompt,
    generate_character_prompt,
    generate_story_summary_prompt,
    generate_title_prompt,
)
from .schemas import (
    CHAPTER_CONTENT_SCHEMA,
    CHAPTER_PLAN_SCHEMA,
    CHARACTER_SCHEMA,
    STORY_SUMMARY_SCHEMA,
    TITLE_SCHEMA,
    get_schema,
    get_schema_prompt_instruction,
)
from .validation import PydanticValidator, StructuredOutputValidator, ValidationResult

__all__ = [
    # Backend
    "LLMConfig",
    "OpenAIBackend",
    # Core components
    "WritingAgent",
    # Parsers
    "ResponseParser",
    "StructuredResponseParser",
    # Prompt generation
    "generate_story_summary_prompt",
    "generate_character_prompt",
    "generate_chapter_plan_prompt",
    "generate_chapter_content_prompt",
    "generate_title_prompt",
    "PromptTemplates",
    # Schemas for structured output
    "CHARACTER_SCHEMA",
    "CHAPTER_PLAN_SCHEMA",
    "STORY_SUMMARY_SCHEMA",
    "TITLE_SCHEMA",
    "CHAPTER_CONTENT_SCHEMA",
    "get_schema",
    "get_schema_prompt_instruction",
    # Validation utilities
    "ValidationResult",
    "PydanticValidator",
    "StructuredOutputValidator",
]
