from typing import Dict

from pydantic import BaseModel, Field


class Character(BaseModel):
    """A character in the book."""

    name: str = ""
    background_story: str = ""
    appearance: str = ""
    personality: str = ""
    role: str = ""
