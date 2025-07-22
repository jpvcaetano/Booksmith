from pydantic import BaseModel, Field
from typing import Dict

class Character(BaseModel):
    """A character in the book."""
    name: str = ""
    background_story: str = ""
    appearance: str = ""
    personality: str = ""
    role: str = "" 