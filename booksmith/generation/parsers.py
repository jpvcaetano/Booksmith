import re
import json
import logging
from typing import List, Dict, Any, Optional, Union
from ..models import Book, Character, Chapter
from .validation import StructuredOutputValidator, ValidationResult

logger = logging.getLogger(__name__)

class ResponseParser:
    """Parses LLM responses into structured data."""
    
    @staticmethod
    def parse_story_summary(response: str) -> str:
        """Extract story summary from LLM response."""
        # Look for content after "Story Summary:" or similar headers
        patterns = [
            r"(?:\*\*)?Story Summary(?:\*\*)?:?\s*(.*?)(?:\n\n|\Z)",
            r"Summary:?\s*(.*?)(?:\n\n|\Z)",
            r"^(.*?)(?:\n\n|\Z)"  # Fallback: take first paragraph
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.strip(), re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:  # Ensure it's substantial
                    return summary
        
        # Fallback: clean and return the whole response
        return response.strip()
    
    @staticmethod
    def parse_characters(response: str) -> List[Character]:
        """Extract character list from LLM response."""
        characters = []
        
        # Pattern to match character blocks
        character_pattern = r"\*\*Character Name:\*\*\s*([^\n]+)\s*\*\*Background:\*\*\s*([^\n*]+)\s*\*\*Appearance:\*\*\s*([^\n*]+)\s*\*\*Personality:\*\*\s*([^\n*]+)"
        
        matches = re.finditer(character_pattern, response, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            try:
                name = match.group(1).strip()
                background = match.group(2).strip()
                appearance = match.group(3).strip()
                personality = match.group(4).strip()
                
                character = Character(
                    name=name,
                    background_story=background,
                    appearance=appearance,
                    personality=personality
                )
                characters.append(character)
                
            except Exception as e:
                logger.warning(f"Failed to parse character: {e}")
                continue
        
        # Fallback: try simpler parsing
        if not characters:
            characters = ResponseParser._parse_characters_fallback(response)
        
        return characters
    
    @staticmethod
    def _parse_characters_fallback(response: str) -> List[Character]:
        """Fallback character parsing for less structured responses."""
        characters = []
        
        # Split by lines and look for name patterns
        lines = response.split('\n')
        current_character = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for character names (often in bold or with special formatting)
            if ('**' in line and ':' not in line) or line.isupper() or line.startswith('Character'):
                if current_character.get('name'):
                    # Save previous character
                    try:
                        char = Character(
                            name=current_character.get('name', 'Unknown'),
                            background_story=current_character.get('background', 'No background provided'),
                            appearance=current_character.get('appearance', 'No description provided'),
                            personality=current_character.get('personality', 'No personality described')
                        )
                        characters.append(char)
                    except:
                        pass
                
                # Start new character
                current_character = {'name': line.replace('*', '').replace('Character:', '').strip()}
            
            elif current_character.get('name'):
                # Accumulate description for current character
                desc = current_character.get('description', '')
                current_character['description'] = desc + ' ' + line
        
        # Handle last character
        if current_character.get('name'):
            try:
                desc = current_character.get('description', 'No description provided')
                char = Character(
                    name=current_character['name'],
                    background_story=desc[:100] + '...' if len(desc) > 100 else desc,
                    appearance='No description provided',
                    personality=desc[:100] + '...' if len(desc) > 100 else desc
                )
                characters.append(char)
            except:
                pass
        
        return characters[:5]  # Limit to 5 characters
    
    @staticmethod
    def parse_chapter_plan(response: str) -> List[Chapter]:
        """Extract chapter plan from LLM response."""
        chapters = []
        
        # Pattern for structured chapter format
        chapter_pattern = r"\*\*Chapter\s+(\d+):\s*([^\n*]+)\*\*\s*\*\*Summary:\*\*\s*([^\n*]+)"
        
        matches = re.finditer(chapter_pattern, response, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            try:
                chapter_num = int(match.group(1))
                title = match.group(2).strip()
                summary = match.group(3).strip()
                
                chapter = Chapter(
                    chapter_number=chapter_num,
                    title=title,
                    summary=summary,
                    content=""  # Content will be generated later
                )
                chapters.append(chapter)
                
            except Exception as e:
                logger.warning(f"Failed to parse chapter: {e}")
                continue
        
        # Fallback: try simpler parsing
        if not chapters:
            chapters = ResponseParser._parse_chapters_fallback(response)
        
        return chapters
    
    @staticmethod
    def _parse_chapters_fallback(response: str) -> List[Chapter]:
        """Fallback chapter parsing for less structured responses."""
        chapters = []
        lines = response.split('\n')
        
        chapter_num = 1
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for chapter titles
            if ('chapter' in line.lower() and ':' in line) or line.startswith('#'):
                title = line.replace('#', '').replace('Chapter', '').replace(':', '').strip()
                if title and len(title) > 3:
                    chapter = Chapter(
                        chapter_number=chapter_num,
                        title=title,
                        summary=f"Chapter {chapter_num} content",
                        content=""
                    )
                    chapters.append(chapter)
                    chapter_num += 1
        
        return chapters[:12]  # Limit to 12 chapters
    
    @staticmethod
    def parse_chapter_content(response: str) -> str:
        """Extract chapter content from LLM response."""
        # Look for content after headers
        patterns = [
            r"(?:\*\*)?Chapter Content(?:\*\*)?:?\s*(.*)",
            r"Content:?\s*(.*)",
            r"^(.*)"  # Fallback: entire response
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.strip(), re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if len(content) > 100:  # Ensure substantial content
                    return content
        
        return response.strip()
    
    @staticmethod
    def parse_title(response: str) -> str:
        """Extract book title from LLM response."""
        # Look for recommended title or first title in list
        patterns = [
            r"(?:\*\*)?Recommended Title(?:\*\*)?:?\s*([^\n]+)",
            r"(?:\*\*)?Best Title(?:\*\*)?:?\s*([^\n]+)",
            r"\d+\.\s*([^\n]+)",  # First numbered item
            r"Title:?\s*([^\n]+)",
            r"^([^\n]+)"  # First line
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.strip(), re.IGNORECASE)
            if match:
                title = match.group(1).strip().replace('"', '').replace("'", "")
                if len(title) > 3 and len(title) < 100:
                    return title
        
        return "Untitled Book" 

class StructuredResponseParser:
    """Parser for structured JSON responses with validation and fallback to regex parsing."""
    
    @staticmethod
    def parse_story_summary(response: Union[str, Dict[str, Any]]) -> str:
        """Extract story summary from JSON or text response."""
        # Try structured validation first
        validation_result = StructuredOutputValidator.validate_and_parse(response, "story_summary")
        
        if validation_result.success:
            if validation_result.corrected:
                logger.info("Story summary was auto-corrected during validation")
            return validation_result.data
        else:
            logger.warning(f"Structured validation failed: {validation_result.errors}")
            # Fallback to regex parsing
            return ResponseParser.parse_story_summary(str(response))
    
    @staticmethod
    def parse_characters(response: Union[str, Dict[str, Any]]) -> List[Character]:
        """Extract character list from JSON or text response."""
        # Try structured validation first
        validation_result = StructuredOutputValidator.validate_and_parse(response, "character")
        
        if validation_result.success:
            if validation_result.corrected:
                logger.info("Characters were auto-corrected during validation")
            if validation_result.errors:
                logger.warning(f"Some characters had validation issues: {validation_result.errors}")
            return validation_result.data
        else:
            logger.warning(f"Structured validation failed: {validation_result.errors}")
            # Fallback to regex parsing
            return ResponseParser.parse_characters(str(response))
    
    @staticmethod
    def parse_chapter_plan(response: Union[str, Dict[str, Any]]) -> List[Chapter]:
        """Extract chapter plan from JSON or text response."""
        # Try structured validation first
        validation_result = StructuredOutputValidator.validate_and_parse(response, "chapter_plan")
        
        if validation_result.success:
            if validation_result.corrected:
                logger.info("Chapter plan was auto-corrected during validation")
            if validation_result.errors:
                logger.warning(f"Some chapters had validation issues: {validation_result.errors}")
            return validation_result.data
        else:
            logger.warning(f"Structured validation failed: {validation_result.errors}")
            # Fallback to regex parsing
            return ResponseParser.parse_chapter_plan(str(response))
    
    @staticmethod
    def parse_chapter_content(response: Union[str, Dict[str, Any]]) -> str:
        """Extract chapter content from JSON or text response."""
        # Try structured validation first
        validation_result = StructuredOutputValidator.validate_and_parse(response, "chapter_content")
        
        if validation_result.success:
            if validation_result.corrected:
                logger.info("Chapter content was auto-corrected during validation")
            return validation_result.data
        else:
            logger.warning(f"Structured validation failed: {validation_result.errors}")
            # Fallback to regex parsing
            return ResponseParser.parse_chapter_content(str(response))
    
    @staticmethod
    def parse_title(response: Union[str, Dict[str, Any]]) -> str:
        """Extract book title from JSON or text response."""
        # Try structured validation first
        validation_result = StructuredOutputValidator.validate_and_parse(response, "title")
        
        if validation_result.success:
            if validation_result.corrected:
                logger.info("Title was auto-corrected during validation")
            return validation_result.data
        else:
            logger.warning(f"Structured validation failed: {validation_result.errors}")
            # Fallback to regex parsing
            return ResponseParser.parse_title(str(response)) 