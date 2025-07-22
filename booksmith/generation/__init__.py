"""
Booksmith text generation logic.

This package contains the core generation components including prompts, parsers, and the main WritingAgent.
"""

from .agent import WritingAgent
from .prompts import (
    PromptTemplates,
    generate_story_summary_prompt,
    generate_character_prompt,
    generate_chapter_plan_prompt,
    generate_chapter_content_prompt,
    generate_title_prompt
)
from .parsers import ResponseParser

__all__ = [
    "WritingAgent",
    "PromptTemplates",
    "generate_story_summary_prompt",
    "generate_character_prompt", 
    "generate_chapter_plan_prompt",
    "generate_chapter_content_prompt",
    "generate_title_prompt",
    "ResponseParser",
] 