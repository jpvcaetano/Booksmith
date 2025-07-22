from jinja2 import Template
from typing import Dict, Any
from ..models import Book, Character, Chapter

class PromptTemplates:
    """Collection of prompt templates for book generation."""
    
    STORY_SUMMARY_TEMPLATE = Template("""
You are a professional book editor and story developer. Create a detailed story summary based on the following prompt.

**Original Prompt:** {{ base_prompt }}

**Book Details:**
- Genre: {{ genre }}
- Writing Style: {{ writing_style }}
- Target Audience: {{ target_audience }}
- Language: {{ language }}

**Instructions:**
1. Expand the original prompt into a comprehensive story summary (300-500 words)
2. Include the main plot, central conflict, and resolution approach
3. Ensure the story fits the specified genre and target audience
4. Write in {{ language }}

**Story Summary:**
""")

    CHARACTER_GENERATION_TEMPLATE = Template("""
You are a character development expert. Based on the story summary below, create detailed character profiles.

**Story Summary:** {{ story_summary }}

**Book Details:**
- Genre: {{ genre }}
- Target Audience: {{ target_audience }}
- Writing Style: {{ writing_style }}

**Instructions:**
Create 3-5 main characters for this story. For each character, provide:
1. Name
2. Background story (2-3 sentences)
3. Physical appearance (2-3 sentences)
4. Personality traits (2-3 sentences)
5. Role in the story

Format each character as:
**Character Name:** [Name]
**Background:** [Background story]
**Appearance:** [Physical description]
**Personality:** [Personality traits]
**Role:** [Their role in the story]

---

**Characters:**
""")

    CHAPTER_PLAN_TEMPLATE = Template("""
You are a professional book planner. Create a detailed chapter outline for the following story.

**Story Summary:** {{ story_summary }}

**Characters:**
{% for character in characters %}
- {{ character.name }}: {{ character.personality }}
{% endfor %}

**Book Details:**
- Genre: {{ genre }}
- Target Audience: {{ target_audience }}
- Target Length: 8-12 chapters

**Instructions:**
Create a chapter-by-chapter outline. For each chapter, provide:
1. Chapter number and title
2. Chapter summary (3-4 sentences describing what happens)
3. Key characters involved
4. Important plot points

Format as:
**Chapter X: [Title]**
**Summary:** [What happens in this chapter]
**Characters:** [Main characters in this chapter]
**Plot Points:** [Key events]

**Chapter Outline:**
""")

    CHAPTER_CONTENT_TEMPLATE = Template("""
You are a professional {{ genre }} author. Write the full content for this chapter of the book.

**Story Context:**
{{ story_summary }}

**Chapter Details:**
- Chapter {{ chapter_number }}: {{ chapter_title }}
- Chapter Summary: {{ chapter_summary }}

**Characters in this chapter:**
{% for character in characters %}
- {{ character.name }}: {{ character.personality }}
{% endfor %}

**Writing Guidelines:**
- Genre: {{ genre }}
- Writing Style: {{ writing_style }}
- Target Audience: {{ target_audience }}
- Language: {{ language }}
- Length: 1500-2500 words
- Use descriptive, engaging prose
- Include dialogue where appropriate
- Maintain consistency with the story summary and character personalities

**Chapter Content:**
""")

    TITLE_GENERATION_TEMPLATE = Template("""
You are a book marketing expert. Create an engaging title for this book.

**Story Summary:** {{ story_summary }}

**Book Details:**
- Genre: {{ genre }}
- Target Audience: {{ target_audience }}

**Instructions:**
Generate 5 potential book titles that are:
1. Engaging and memorable
2. Appropriate for the {{ genre }} genre
3. Appealing to {{ target_audience }}
4. Reflective of the story content

**Titles:**
1. 
2. 
3. 
4. 
5. 

**Recommended Title:** [Pick the best one and explain why]
""")

def generate_story_summary_prompt(book: Book) -> str:
    """Generate prompt for story summary creation."""
    return PromptTemplates.STORY_SUMMARY_TEMPLATE.render(
        base_prompt=book.base_prompt,
        genre=book.genre,
        writing_style=book.writing_style,
        target_audience=book.target_audience,
        language=book.language
    )

def generate_character_prompt(book: Book) -> str:
    """Generate prompt for character creation."""
    return PromptTemplates.CHARACTER_GENERATION_TEMPLATE.render(
        story_summary=book.story_summary,
        genre=book.genre,
        target_audience=book.target_audience,
        writing_style=book.writing_style
    )

def generate_chapter_plan_prompt(book: Book) -> str:
    """Generate prompt for chapter planning."""
    return PromptTemplates.CHAPTER_PLAN_TEMPLATE.render(
        story_summary=book.story_summary,
        characters=book.characters,
        genre=book.genre,
        target_audience=book.target_audience
    )

def generate_chapter_content_prompt(book: Book, chapter: Chapter) -> str:
    """Generate prompt for chapter content writing."""
    return PromptTemplates.CHAPTER_CONTENT_TEMPLATE.render(
        story_summary=book.story_summary,
        chapter_number=chapter.chapter_number,
        chapter_title=chapter.title,
        chapter_summary=chapter.summary,
        characters=book.characters,
        genre=book.genre,
        writing_style=book.writing_style,
        target_audience=book.target_audience,
        language=book.language
    )

def generate_title_prompt(book: Book) -> str:
    """Generate prompt for title creation."""
    return PromptTemplates.TITLE_GENERATION_TEMPLATE.render(
        story_summary=book.story_summary,
        genre=book.genre,
        target_audience=book.target_audience
    ) 