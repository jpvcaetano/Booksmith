from typing import List

from pydantic import BaseModel


class Chapter(BaseModel):
    """A chapter in the book."""

    chapter_number: int = 0
    title: str = ""
    summary: str = ""
    key_characters: List[str] = []  # Main characters in this chapter
    plot_points: List[str] = []  # Important plot points/events
    content: str = ""
