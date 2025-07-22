import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

from ..models.book import Book


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def create_book_epub(book: Book, output_dir: str = "generated_books") -> str:
    """
    Create a folder with the book name and generate an EPUB file with all chapters.
    
    Args:
        book: The Book object containing all book information
        output_dir: Base directory to create the book folder in
        
    Returns:
        Path to the created book folder
    """
    # Sanitize book title for folder name
    book_title = sanitize_filename(book.title) if book.title else "Untitled_Book"
    
    # Create the book folder
    book_folder = Path(output_dir) / book_title
    book_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate EPUB file
    epub_filename = sanitize_filename(book.title) if book.title else "untitled_book"
    epub_path = book_folder / f"{epub_filename}.epub"
    create_epub_file(book, epub_path)
    
    # Generate book info text file
    info_path = book_folder / "book_info.txt"
    create_book_info_text(book, info_path)
    
    return str(book_folder)


def create_epub_file(book: Book, output_path: Path) -> None:
    """Create an EPUB file with all chapters."""
    try:
        from ebooklib import epub
    except ImportError:
        raise ImportError("ebooklib is required for EPUB generation. Install it with: pip install ebooklib")
    
    # Create EPUB book
    epub_book = epub.EpubBook()
    
    # Set metadata
    epub_book.set_identifier(str(uuid.uuid4()))
    epub_book.set_title(book.title or "Untitled Book")
    epub_book.set_language(book.language)
    
    # Add author (you could extend the Book model to include author)
    epub_book.add_author("Booksmith AI")
    
    # Create single HTML file with all content
    all_content = f"""
    <html>
    <head>
        <title>{book.title or "Untitled Book"}</title>
        <style>
            body {{ font-family: serif; margin: 2em; line-height: 1.6; }}
            h1 {{ text-align: center; color: #2c3e50; margin: 2em 0; }}
            p {{ text-align: justify; margin: 1em 0; }}
            .chapter {{ page-break-before: always; }}
            .chapter:first-child {{ page-break-before: avoid; }}
        </style>
    </head>
    <body>
        <h1>{book.title or "Untitled Book"}</h1>
        
        {create_chapters_section(book.chapters)}
    </body>
    </html>
    """
    
    # Create single chapter file
    main_chapter = epub.EpubHtml(title='Book Content', file_name='content.xhtml', content=all_content)
    epub_book.add_item(main_chapter)
    chapters = [main_chapter]
    spine = ['nav', 'content']
    
    # Create table of contents
    epub_book.toc = [(epub.Section('Book Content'), chapters)]
    
    # Add default NCX and Nav files
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())
    
    # Define spine
    epub_book.spine = spine
    
    # Write EPUB file
    epub.write_epub(str(output_path), epub_book)


def create_characters_section(characters) -> str:
    """Create the characters section HTML."""
    if not characters:
        return ""
    
    char_content = '<h2>Characters</h2>'
    
    for character in characters:
        char_content += f"""
        <div class="character">
            <h3>{character.name}</h3>
            {f'<p><strong>Background:</strong> {character.background_story}</p>' if character.background_story else ''}
            {f'<p><strong>Appearance:</strong> {character.appearance}</p>' if character.appearance else ''}
            {f'<p><strong>Personality:</strong> {character.personality}</p>' if character.personality else ''}
            {f'<p><strong>Other Characteristics:</strong> {character.other_characteristics}</p>' if character.other_characteristics else ''}
        </div>
        """
    
    return char_content


def create_chapters_section(chapters) -> str:
    """Create the chapters section HTML."""
    if not chapters:
        return ""
    
    chapters_content = '<h2>Chapters</h2>'
    
    for chapter in chapters:
        if chapter.content.strip():
            chapters_content += f"""
            <div class="chapter">
                <h1>{chapter.chapter_number}: {chapter.title}</h1>
                {format_chapter_content(chapter.content)}
            </div>
            """
    
    return chapters_content


def format_chapter_content(content: str) -> str:
    """Format chapter content for EPUB HTML."""
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        if para.strip():
            # Clean up the paragraph and wrap in <p> tags
            clean_para = para.strip().replace('\n', ' ')
            formatted_paragraphs.append(f"<p>{clean_para}</p>")
    
    return '\n'.join(formatted_paragraphs)


def create_book_info_text(book: Book, output_path: Path) -> None:
    """Create a text file with book information, characters, and summary."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Book: {book.title or 'Untitled Book'}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Genre: {book.genre}\n")
        f.write(f"Target Audience: {book.target_audience}\n")
        f.write(f"Writing Style: {book.writing_style}\n")
        f.write(f"Language: {book.language}\n\n")
        
        if book.story_summary:
            f.write("STORY SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(book.story_summary + "\n\n")
        
        if book.characters:
            f.write("CHARACTERS\n")
            f.write("-" * 20 + "\n")
            for character in book.characters:
                f.write(f"Name: {character.name}\n")
                if character.background_story:
                    f.write(f"Background: {character.background_story}\n")
                if character.appearance:
                    f.write(f"Appearance: {character.appearance}\n")
                if character.personality:
                    f.write(f"Personality: {character.personality}\n")
                if character.other_characteristics:
                    f.write(f"Other: {character.other_characteristics}\n")
                f.write("\n")
        
        if book.chapters:
            f.write("CHAPTERS\n")
            f.write("-" * 20 + "\n")
            for chapter in book.chapters:
                f.write(f"Chapter {chapter.chapter_number}: {chapter.title}\n")
                if chapter.summary:
                    f.write(f"  Summary: {chapter.summary}\n")
                f.write("\n")


def create_simple_text_export(book: Book, output_dir: str = "generated_books") -> str:
    """
    Create a simple text export of the book as an alternative to EPUB.
    
    Args:
        book: The Book object containing all book information
        output_dir: Base directory to create the book folder in
        
    Returns:
        Path to the created book folder
    """
    # Sanitize book title for folder name
    book_title = sanitize_filename(book.title) if book.title else "Untitled_Book"
    
    # Create the book folder
    book_folder = Path(output_dir) / book_title
    book_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate complete book text file
    book_filename = sanitize_filename(book.title) if book.title else "untitled_book"
    book_path = book_folder / f"{book_filename}.txt"
    
    with open(book_path, 'w', encoding='utf-8') as f:
        f.write(f"{book.title or 'Untitled Book'}\n")
        f.write("=" * 50 + "\n\n")
        
        for chapter in book.chapters:
            if chapter.content.strip():
                f.write(f"Chapter {chapter.chapter_number}: {chapter.title}\n")
                f.write("-" * 40 + "\n\n")
                f.write(chapter.content + "\n\n")
    
    # Generate book info text file
    info_path = book_folder / "book_info.txt"
    create_book_info_text(book, info_path)
    
    return str(book_folder) 