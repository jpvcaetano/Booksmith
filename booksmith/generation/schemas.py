"""
JSON schemas for structured LLM output generation.
Based on the existing Pydantic models but optimized for LLM generation.
"""

from typing import Dict, Any

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
                        "description": "The character's full name"
                    },
                    "background_story": {
                        "type": "string",
                        "description": "Character's backstory in 2-3 sentences"
                    },
                    "appearance": {
                        "type": "string", 
                        "description": "Physical description in 2-3 sentences"
                    },
                    "personality": {
                        "type": "string",
                        "description": "Personality traits and characteristics in 2-3 sentences"
                    },
                    "other_characteristics": {
                        "type": "string",
                        "description": "Additional relevant character details"
                    }
                },
                "required": ["name", "background_story", "appearance", "personality"],
                "additionalProperties": False
            },
            "minItems": 2,
            "maxItems": 6
        }
    },
    "required": ["characters"],
    "additionalProperties": False
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
                        "description": "Sequential chapter number"
                    },
                    "title": {
                        "type": "string",
                        "description": "Engaging chapter title"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Chapter summary in 3-4 sentences describing key events"
                    }
                },
                "required": ["chapter_number", "title", "summary"],
                "additionalProperties": False
            },
            "minItems": 3,
            "maxItems": 15
        }
    },
    "required": ["chapters"],
    "additionalProperties": False
}

# Schema for story summary generation
STORY_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "story_summary": {
            "type": "string",
            "description": "Comprehensive story summary (300-500 words) including main plot, conflict, and resolution",
            "minLength": 200,
            "maxLength": 1000
        }
    },
    "required": ["story_summary"],
    "additionalProperties": False
}

# Schema for title generation
TITLE_SCHEMA = {
    "type": "object",
    "properties": {
        "titles": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 5,
                "maxLength": 100
            },
            "minItems": 3,
            "maxItems": 5,
            "description": "List of 3-5 creative book title suggestions"
        },
        "recommended_title": {
            "type": "string",
            "description": "The best title from the list",
            "minLength": 5,
            "maxLength": 100
        }
    },
    "required": ["titles", "recommended_title"],
    "additionalProperties": False
}

# Schema for chapter content generation
CHAPTER_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "Complete chapter content (1000-3000 words)",
            "minLength": 500,
            "maxLength": 5000
        }
    },
    "required": ["content"],
    "additionalProperties": False
}

# Schema registry for easy access
SCHEMAS = {
    "character": CHARACTER_SCHEMA,
    "chapter_plan": CHAPTER_PLAN_SCHEMA,
    "story_summary": STORY_SUMMARY_SCHEMA,
    "title": TITLE_SCHEMA, 
    "chapter_content": CHAPTER_CONTENT_SCHEMA
}

def get_schema(schema_name: str) -> Dict[str, Any]:
    """Get a schema by name."""
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}. Available: {list(SCHEMAS.keys())}")
    return SCHEMAS[schema_name]

def get_schema_prompt_instruction(schema_name: str) -> str:
    """Get instruction text to append to prompts for JSON output."""
    return f"""

IMPORTANT: Respond with valid JSON that matches this exact schema:
{get_schema(schema_name)}

Your response must be valid JSON only, no additional text or formatting.""" 