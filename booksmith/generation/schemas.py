"""
JSON schemas for structured LLM output generation.
Based on the existing Pydantic models but optimized for LLM generation.
"""

from typing import Any, Dict

# Schema for character generation
CHARACTER_SCHEMA = {
    "type": "object",
    "properties": {
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The character's full name",
                    },
                    "background_story": {
                        "type": "string",
                        "description": "Character's backstory in 2-3 sentences",
                    },
                    "appearance": {
                        "type": "string",
                        "description": "Physical description in 2-3 sentences",
                    },
                    "personality": {
                        "type": "string",
                        "description": "Personality traits and characteristics in 2-3 sentences",
                    },
                    "role": {
                        "type": "string",
                        "description": "The character's role in the story",
                    },
                },
                "required": ["name", "background_story", "appearance", "personality"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["characters"],
    "additionalProperties": False,
}

# Schema for chapter plan generation
CHAPTER_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chapter_number": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Sequential chapter number",
                    },
                    "title": {
                        "type": "string",
                        "description": "Engaging chapter title",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Chapter summary in 3-4 sentences describing key events",
                    },
                    "key_characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of main characters involved in this chapter",
                    },
                    "plot_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of important plot points and key events in this chapter",
                    },
                },
                "required": [
                    "chapter_number",
                    "title",
                    "summary",
                    "key_characters",
                    "plot_points",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["chapters"],
    "additionalProperties": False,
}

# Schema for story summary generation
STORY_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "story_summary": {
            "type": "string",
            "description": "Comprehensive story summary (300-500 words) including main plot, conflict, and resolution",
        }
    },
    "required": ["story_summary"],
    "additionalProperties": False,
}

# Schema for title generation
TITLE_SCHEMA = {
    "type": "object",
    "properties": {
        "titles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of 3-5 creative book title suggestions",
        },
        "recommended_title": {
            "type": "string",
            "description": "The best title from the list",
        },
    },
    "required": ["titles", "recommended_title"],
    "additionalProperties": False,
}

# Schema for chapter content generation
CHAPTER_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "Complete chapter content (1000-10000 words) that maintains story continuity",
        },
        "continuity_notes": {
            "type": "string",
            "description": "Optional notes about how this chapter connects to previous/future chapters",
        },
        "character_development": {
            "type": "string",
            "description": "Optional notes about character development in this chapter",
        },
    },
    "required": ["content"],
    "additionalProperties": False,
}

# Schema registry for easy access
SCHEMAS = {
    "character": CHARACTER_SCHEMA,
    "chapter_plan": CHAPTER_PLAN_SCHEMA,
    "story_summary": STORY_SUMMARY_SCHEMA,
    "title": TITLE_SCHEMA,
    "chapter_content": CHAPTER_CONTENT_SCHEMA,
}


def get_schema(schema_name: str) -> Dict[str, Any]:
    """Get a schema by name."""
    if schema_name not in SCHEMAS:
        raise ValueError(
            f"Unknown schema: {schema_name}. Available: {list(SCHEMAS.keys())}"
        )
    return SCHEMAS[schema_name]


def get_schema_prompt_instruction(schema_name: str) -> str:
    """Get instruction text to append to prompts for JSON output."""
    return f"""

IMPORTANT: Respond with valid JSON that matches this exact schema:
{get_schema(schema_name)}

Your response must be valid JSON only, no additional text or formatting."""
