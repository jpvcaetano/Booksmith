"""
Validation utilities for structured LLM outputs using Pydantic models.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError

from ..models import Character, Chapter, Book

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class ValidationResult:
    """Result of validation with optional corrections."""
    
    def __init__(self, success: bool, data: Any = None, errors: List[str] = None, corrected: bool = False):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.corrected = corrected

class PydanticValidator:
    """Validator that uses Pydantic models for structured data validation."""
    
    @staticmethod
    def validate_characters(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> ValidationResult:
        """Validate character data against Character model."""
        try:
            # Handle both single character and character list formats
            if isinstance(data, dict):
                if "characters" in data:
                    char_list = data["characters"]
                else:
                    # Assume it's a single character
                    char_list = [data]
            else:
                char_list = data
            
            validated_characters = []
            errors = []
            corrected = False
            
            for i, char_data in enumerate(char_list):
                try:
                    # Try direct validation first
                    character = Character.model_validate(char_data)
                    validated_characters.append(character)
                    
                except ValidationError as e:
                    # Try auto-correction
                    corrected_data = PydanticValidator._auto_correct_character(char_data)
                    try:
                        character = Character.model_validate(corrected_data)
                        validated_characters.append(character)
                        corrected = True
                        logger.info(f"Auto-corrected character {i}: {corrected_data.get('name', 'Unknown')}")
                    except ValidationError as e2:
                        errors.append(f"Character {i}: {str(e2)}")
                        logger.error(f"Failed to validate character {i}: {e2}")
            
            if errors and not validated_characters:
                return ValidationResult(success=False, errors=errors)
            
            return ValidationResult(
                success=True, 
                data=validated_characters, 
                errors=errors if errors else None,
                corrected=corrected
            )
            
        except Exception as e:
            return ValidationResult(success=False, errors=[f"Validation failed: {str(e)}"])
    
    @staticmethod
    def validate_chapters(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> ValidationResult:
        """Validate chapter data against Chapter model."""
        try:
            # Handle both single chapter and chapter list formats
            if isinstance(data, dict):
                if "chapters" in data:
                    chapter_list = data["chapters"]
                else:
                    chapter_list = [data]
            else:
                chapter_list = data
            
            validated_chapters = []
            errors = []
            corrected = False
            
            for i, chapter_data in enumerate(chapter_list):
                try:
                    chapter = Chapter.model_validate(chapter_data)
                    validated_chapters.append(chapter)
                    
                except ValidationError as e:
                    # Try auto-correction
                    corrected_data = PydanticValidator._auto_correct_chapter(chapter_data, i + 1)
                    try:
                        chapter = Chapter.model_validate(corrected_data)
                        validated_chapters.append(chapter)
                        corrected = True
                        logger.info(f"Auto-corrected chapter {i + 1}: {corrected_data.get('title', 'Untitled')}")
                    except ValidationError as e2:
                        errors.append(f"Chapter {i + 1}: {str(e2)}")
                        logger.error(f"Failed to validate chapter {i + 1}: {e2}")
            
            if errors and not validated_chapters:
                return ValidationResult(success=False, errors=errors)
            
            return ValidationResult(
                success=True, 
                data=validated_chapters, 
                errors=errors if errors else None,
                corrected=corrected
            )
            
        except Exception as e:
            return ValidationResult(success=False, errors=[f"Validation failed: {str(e)}"])
    
    @staticmethod
    def _auto_correct_character(char_data: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-correct common character data issues."""
        corrected = char_data.copy()
        
        # Ensure all required fields exist with defaults
        field_defaults = {
            "name": "Unknown Character",
            "background_story": "No background provided",
            "appearance": "No description provided", 
            "personality": "No personality described",
            "role": ""
        }
        
        for field, default in field_defaults.items():
            if field not in corrected or not corrected[field] or corrected[field].strip() == "":
                corrected[field] = default
        
        # Handle common field name variations
        field_mappings = {
            "background": "background_story",
            "backstory": "background_story",
            "description": "appearance",
            "physical_description": "appearance",
            "traits": "personality",
            "character_traits": "personality",
            "story_role": "role",
            "character_role": "role",
            "other_characteristics": "role"  # For backward compatibility
        }
        
        for old_field, new_field in field_mappings.items():
            if old_field in corrected and new_field not in corrected:
                corrected[new_field] = corrected[old_field]
                del corrected[old_field]
        
        return corrected
    
    @staticmethod
    def _auto_correct_chapter(chapter_data: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        """Auto-correct common chapter data issues."""
        corrected = chapter_data.copy()
        
        # Ensure required fields
        if "chapter_number" not in corrected:
            corrected["chapter_number"] = chapter_num
        
        if "title" not in corrected or not corrected["title"]:
            corrected["title"] = f"Chapter {chapter_num}"
        
        if "summary" not in corrected or not corrected["summary"]:
            corrected["summary"] = f"Chapter {chapter_num} content"
        
        if "content" not in corrected:
            corrected["content"] = ""
        
        # Ensure new fields exist with defaults
        if "key_characters" not in corrected:
            corrected["key_characters"] = []
        
        if "plot_points" not in corrected:
            corrected["plot_points"] = []
        
        # Handle field mappings
        field_mappings = {
            "description": "summary",
            "chapter_summary": "summary",
            "number": "chapter_number",
            "chapter_title": "title",
            "characters": "key_characters",
            "main_characters": "key_characters",
            "plot": "plot_points",
            "events": "plot_points",
            "key_events": "plot_points"
        }
        
        for old_field, new_field in field_mappings.items():
            if old_field in corrected and new_field not in corrected:
                corrected[new_field] = corrected[old_field]
                del corrected[old_field]
        
        return corrected

class StructuredOutputValidator:
    """High-level validator that combines JSON schema and Pydantic validation."""
    
    @staticmethod
    def validate_and_parse(response: Union[str, Dict[str, Any]], expected_type: str) -> ValidationResult:
        """Validate and parse response based on expected type."""
        
        # First, ensure we have a dict
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as e:
                return ValidationResult(success=False, errors=[f"Invalid JSON: {str(e)}"])
        
        # Validate based on type
        if expected_type == "character":
            return PydanticValidator.validate_characters(response)
        elif expected_type == "chapter_plan":
            return PydanticValidator.validate_chapters(response)
        elif expected_type == "story_summary":
            if isinstance(response, dict) and "story_summary" in response:
                summary = response["story_summary"]
                if isinstance(summary, str) and len(summary.strip()) > 10:
                    return ValidationResult(success=True, data=summary.strip())
                else:
                    return ValidationResult(success=False, errors=["Story summary too short or invalid"])
            else:
                return ValidationResult(success=False, errors=["Missing 'story_summary' field"])
        elif expected_type == "title":
            if isinstance(response, dict):
                if "recommended_title" in response:
                    title = response["recommended_title"]
                elif "titles" in response and response["titles"]:
                    title = response["titles"][0]
                else:
                    return ValidationResult(success=False, errors=["No title found in response"])
                
                if isinstance(title, str) and len(title.strip()) > 3:
                    return ValidationResult(success=True, data=title.strip())
                else:
                    return ValidationResult(success=False, errors=["Title too short or invalid"])
            else:
                return ValidationResult(success=False, errors=["Invalid title response format"])
        elif expected_type == "chapter_content":
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                if isinstance(content, str) and len(content.strip()) > 50:
                    return ValidationResult(success=True, data=content.strip())
                else:
                    return ValidationResult(success=False, errors=["Chapter content too short"])
            else:
                return ValidationResult(success=False, errors=["Missing 'content' field"])
        else:
            return ValidationResult(success=False, errors=[f"Unknown validation type: {expected_type}"]) 