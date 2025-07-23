from unittest.mock import MagicMock, Mock

import pytest

from booksmith.generation.openai import LLMConfig
from booksmith.models import Book, Chapter, Character


@pytest.fixture
def sample_character():
    """A sample character for testing."""
    return Character(
        name="Test Hero",
        background_story="A brave adventurer from a small village.",
        appearance="Tall with dark hair and piercing blue eyes.",
        personality="Courageous, kind-hearted, and determined.",
        role="Protagonist",
    )


@pytest.fixture
def sample_characters():
    """A list of sample characters for testing."""
    return [
        Character(
            name="Alice Hero",
            background_story="A young mage discovering her powers.",
            appearance="Short with red hair and green eyes.",
            personality="Curious and brave.",
            role="Protagonist",
        ),
        Character(
            name="Bob Villain",
            background_story="A dark sorcerer seeking power.",
            appearance="Tall and menacing with a black cloak.",
            personality="Cunning and ruthless.",
            role="Antagonist",
        ),
    ]


@pytest.fixture
def sample_chapter():
    """A sample chapter for testing."""
    return Chapter(
        chapter_number=1,
        title="The Beginning",
        summary="Our hero starts their journey in a small village.",
        key_characters=["Alice Hero"],
        plot_points=["Hero discovers magical powers", "Meets mentor"],
        content="It was a dark and stormy night when Alice first discovered her magical abilities...",
    )


@pytest.fixture
def sample_chapters():
    """A list of sample chapters for testing."""
    return [
        Chapter(
            chapter_number=1,
            title="The Beginning",
            summary="The story starts",
            key_characters=["Alice Hero"],
            plot_points=["Discovery of powers"],
            content="Chapter 1 content here...",
        ),
        Chapter(
            chapter_number=2,
            title="The Journey",
            summary="The adventure continues",
            key_characters=["Alice Hero", "Bob Villain"],
            plot_points=["First encounter with villain"],
            content="Chapter 2 content here...",
        ),
    ]


@pytest.fixture
def sample_book(sample_characters, sample_chapters):
    """A complete sample book for testing."""
    return Book(
        base_prompt="A magical adventure story",
        language="english",
        writing_style="descriptive",
        genre="fantasy",
        target_audience="young adults",
        title="The Magic Within",
        story_summary="A young mage discovers her powers and faces an ancient evil threatening her world.",
        characters=sample_characters,
        chapters=sample_chapters,
    )


@pytest.fixture
def minimal_book():
    """A minimal book with just the required base_prompt."""
    return Book(base_prompt="A simple story")


@pytest.fixture
def llm_config():
    """Sample LLM configuration for testing."""
    return LLMConfig(
        model_name="gpt-4", max_tokens=1000, temperature=0.7, api_key="test-key"
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()

    # Mock chat completion response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Generated text response"

    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_openai_backend(mock_openai_client, llm_config):
    """Mock OpenAI backend for testing."""
    from booksmith.generation.openai import OpenAIBackend

    backend = OpenAIBackend(llm_config)
    backend.client = mock_openai_client

    return backend


# Sample LLM responses for parser testing
@pytest.fixture
def sample_story_summary_response():
    """Sample story summary response in JSON format."""
    return {
        "story_summary": "A young mage named Alice discovers her magical powers in a small village. She must learn to control her abilities while facing the dark sorcerer Bob who threatens to destroy everything she holds dear. Through courage and determination, she embarks on a quest to save her world."
    }


@pytest.fixture
def sample_characters_response():
    """Sample characters response in JSON format."""
    return {
        "characters": [
            {
                "name": "Alice Hero",
                "background_story": "A young mage discovering her powers.",
                "appearance": "Short with red hair and green eyes.",
                "personality": "Curious and brave.",
                "role": "Protagonist",
            },
            {
                "name": "Bob Villain",
                "background_story": "A dark sorcerer seeking power.",
                "appearance": "Tall and menacing with a black cloak.",
                "personality": "Cunning and ruthless.",
                "role": "Antagonist",
            },
        ]
    }


@pytest.fixture
def sample_chapter_plan_response():
    """Sample chapter plan response in JSON format."""
    return {
        "chapters": [
            {
                "chapter_number": 1,
                "title": "The Beginning",
                "summary": "Alice discovers her magical powers.",
                "key_characters": ["Alice Hero"],
                "plot_points": ["Discovery of powers", "Meets mentor"],
            },
            {
                "chapter_number": 2,
                "title": "The Challenge",
                "summary": "Alice faces her first real test.",
                "key_characters": ["Alice Hero", "Bob Villain"],
                "plot_points": ["First encounter", "Magical duel"],
            },
        ]
    }


@pytest.fixture
def sample_title_response():
    """Sample title response in JSON format."""
    return {
        "titles": [
            "The Magic Within",
            "Alice's Awakening",
            "The Mage's Journey",
            "Powers Unleashed",
            "The Crystal Quest",
        ],
        "recommended_title": "The Magic Within",
    }


@pytest.fixture
def sample_chapter_content_response():
    """Sample chapter content response in JSON format."""
    return {
        "content": "It was a dark and stormy night when Alice first discovered her magical abilities. The young girl had always felt different, but tonight something extraordinary happened. As lightning flashed across the sky, she felt a strange energy coursing through her veins. Little did she know that this moment would change her life forever.",
        "continuity_notes": "Sets up Alice's character and magical discovery.",
        "character_development": "Alice transforms from ordinary girl to aware mage.",
    }


# Text-based responses for fallback parser testing
@pytest.fixture
def sample_characters_text_response():
    """Sample characters response in text format for fallback parsing."""
    return """
**Character Name:** Alice Hero
**Background:** A young mage discovering her powers.
**Appearance:** Short with red hair and green eyes. 
**Personality:** Curious and brave.

**Character Name:** Bob Villain
**Background:** A dark sorcerer seeking power.
**Appearance:** Tall and menacing with a black cloak.
**Personality:** Cunning and ruthless.
"""


@pytest.fixture
def sample_chapter_plan_text_response():
    """Sample chapter plan response in text format for fallback parsing."""
    return """
**Chapter 1: The Beginning**
**Summary:** Alice discovers her magical powers in her small village.

**Chapter 2: The Challenge** 
**Summary:** Alice faces her first real test against dark forces.
"""
