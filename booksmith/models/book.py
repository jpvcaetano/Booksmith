from typing import List

from pydantic import BaseModel, Field

from .chapter import Chapter
from .character import Character


class Book(BaseModel):
    """A class to hold all the information about a book."""

    base_prompt: str
    language: str = "english"
    writing_style: str = "descriptive"
    genre: str = "fantasy"
    target_audience: str = "young adults"
    title: str = ""
    story_summary: str = ""
    characters: List[Character] = Field(default_factory=list)
    chapters: List[Chapter] = Field(default_factory=list)
