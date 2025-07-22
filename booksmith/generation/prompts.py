from typing import Any, Dict

from jinja2 import Template

from ..models import Book, Chapter, Character


class PromptTemplates:
    """Collection of prompt templates for book generation."""

    STORY_SUMMARY_TEMPLATE = Template(
        """
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
"""
    )

    CHARACTER_GENERATION_TEMPLATE = Template(
        """
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
"""
    )

    CHAPTER_PLAN_TEMPLATE = Template(
        """
You are a professional book planner. Create a detailed chapter outline for the following story.

**Story Summary:** {{ story_summary }}

**Characters:**
{% for character in characters %}
- **{{ character.name }}**: {{ character.personality }}
  - Background: {{ character.background_story }}
  - Appearance: {{ character.appearance }}
  {% if character.role %}- Role: {{ character.role }}{% endif %}
{% endfor %}

**Book Details:**
- Genre: {{ genre }}
- Target Audience: {{ target_audience }}
- Target Length: number of chapters should make sense for the story

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
"""
    )

    CHAPTER_CONTENT_TEMPLATE = Template(
        """
You are a professional {{ genre }} author. Write the full content for this chapter of the book.

**Story Context:**
{{ story_summary }}

**CURRENT CHAPTER FOCUS:**
- Chapter {{ chapter_number }}: {{ chapter_title }}
- Chapter Summary: {{ chapter_summary }}
- Position in Story: {% if chapter_number == 1 %}Opening chapter - establish setting, introduce main characters{% elif chapter_number == total_chapters %}Final chapter - resolution and conclusion{% elif chapter_number <= total_chapters // 3 %}Early story - character introduction and setup{% elif chapter_number <= (total_chapters * 2) // 3 %}Middle story - conflict development and complications{% else %}Late story - building toward climax and resolution{% endif %}

**STORY ARC CONTEXT:**
{% if chapter_number > 1 %}
**What happened in previous chapters:**
{% for ch in all_chapters %}
{% if ch.chapter_number < current_chapter_number %}
- Chapter {{ ch.chapter_number }}: {{ ch.summary }}
{% endif %}
{% endfor %}
{% endif %}

{% if chapter_number < total_chapters %}
**What needs to happen in upcoming chapters:**
{% for ch in all_chapters %}
{% if ch.chapter_number > current_chapter_number %}
- Chapter {{ ch.chapter_number }}: {{ ch.summary }}
{% endif %}
{% endfor %}

**IMPORTANT:** This chapter must set up events and character development that lead naturally into the next chapters while maintaining story continuity.
{% endif %}

**Characters in this chapter:**
{% for character in characters %}
- **{{ character.name }}**: {{ character.personality }}
  - Background: {{ character.background_story }}
  - Appearance: {{ character.appearance }}
  {% if character.role %}- Role: {{ character.role }}{% endif %}
{% endfor %}
                                        
{% if chapter_number > 1 %}
**Last 500 characters of the previous chapter:**
{{ previous_chapter_content }}
{% endif %}                            

**Writing Guidelines:**
- Genre: {{ genre }}
- Writing Style: {{ writing_style }}
- Target Audience: {{ target_audience }}
- Language: {{ language }}
- Use descriptive, engaging prose
- Include dialogue where appropriate
- Maintain consistency with the story summary and character personalities
- CRITICAL: Ensure this chapter flows naturally from previous chapters and sets up upcoming chapters
- Reference events from previous chapters when relevant
- Plant seeds for future chapter developments when appropriate
- Do not include the chapter name in the content
{% if chapter_number > 1 %}
- Make a smooth transition from the previous chapter
{% endif %}                                          

"""
    )

    TITLE_GENERATION_TEMPLATE = Template(
        """
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
"""
    )


def generate_story_summary_prompt(book: Book) -> str:
    """Generate prompt for story summary creation."""
    return PromptTemplates.STORY_SUMMARY_TEMPLATE.render(
        base_prompt=book.base_prompt,
        genre=book.genre,
        writing_style=book.writing_style,
        target_audience=book.target_audience,
        language=book.language,
    )


def generate_character_prompt(book: Book) -> str:
    """Generate prompt for character creation."""
    return PromptTemplates.CHARACTER_GENERATION_TEMPLATE.render(
        story_summary=book.story_summary,
        genre=book.genre,
        target_audience=book.target_audience,
        writing_style=book.writing_style,
    )


def generate_chapter_plan_prompt(book: Book) -> str:
    """Generate prompt for chapter planning."""
    return PromptTemplates.CHAPTER_PLAN_TEMPLATE.render(
        story_summary=book.story_summary,
        characters=book.characters,
        genre=book.genre,
        target_audience=book.target_audience,
    )


def generate_chapter_content_prompt(book: Book, chapter: Chapter) -> str:
    """Generate prompt for chapter content writing with full story context."""

    active_characters = [
        character
        for character in book.characters
        if character.name in chapter.key_characters
    ]
    print(f"Book: {book}")
    return PromptTemplates.CHAPTER_CONTENT_TEMPLATE.render(
        story_summary=book.story_summary,
        chapter_number=chapter.chapter_number,
        chapter_title=chapter.title,
        chapter_summary=chapter.summary,
        characters=active_characters,
        genre=book.genre,
        writing_style=book.writing_style,
        target_audience=book.target_audience,
        language=book.language,
        # Enhanced context for story consistency
        all_chapters=book.chapters,
        previous_chapter_content=book.chapters[chapter.chapter_number - 2].content[
            -500:
        ]
        if chapter.chapter_number > 1
        else "",
        current_chapter_number=chapter.chapter_number,
        total_chapters=len(book.chapters),
    )


def generate_title_prompt(book: Book) -> str:
    """Generate prompt for title creation."""
    return PromptTemplates.TITLE_GENERATION_TEMPLATE.render(
        story_summary=book.story_summary,
        genre=book.genre,
        target_audience=book.target_audience,
    )
