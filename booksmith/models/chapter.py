from pydantic import BaseModel

class Chapter(BaseModel):
    """A chapter in the book."""
    chapter_number: int = 0
    title: str = ""
    summary: str = ""
    content: str = "" 