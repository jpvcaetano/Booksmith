"""
Book generation system with structured LLM output support.
"""

from .agent import WritingAgent
from .parsers import ResponseParser, StructuredResponseParser
from .prompts import (
    generate_story_summary_prompt,
    generate_character_prompt,
    generate_chapter_plan_prompt,
    generate_chapter_content_prompt,
    generate_title_prompt,
    PromptTemplates
)
from .schemas import (
    CHARACTER_SCHEMA,
    CHAPTER_PLAN_SCHEMA,
    STORY_SUMMARY_SCHEMA,
    TITLE_SCHEMA,
    CHAPTER_CONTENT_SCHEMA,
    get_schema,
    get_schema_prompt_instruction
)
from .validation import (
    ValidationResult,
    PydanticValidator,
    StructuredOutputValidator
)

__all__ = [
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
    "StructuredOutputValidator"
] 