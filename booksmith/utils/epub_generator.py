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
    """Create an EPUB file with separate chapters and linear reading flow."""
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
    
    # Set reading direction and page progression
    epub_book.set_direction('default')
    
    # Add author (you could extend the Book model to include author)
    epub_book.add_author("Booksmith AI")
    
    # Create title page
    title_content = f"""
    <html>
    <head>
        <title>{book.title or "Untitled Book"}</title>
        <style>
            body {{ font-family: serif; margin: 2em; line-height: 1.6; text-align: center; }}
            h1 {{ color: #2c3e50; margin: 3em 0; font-size: 2.5em; }}
            .info {{ margin: 2em 0; font-size: 1.1em; color: #666; }}
        </style>
    </head>
    <body>
        <h1>{book.title or "Untitled Book"}</h1>
        <div class="info">
            <p>Genre: {book.genre}</p>
            <p>Target Audience: {book.target_audience}</p>
            <p>Writing Style: {book.writing_style}</p>
        </div>
    </body>
    </html>
    """
    
    # Create title page chapter
    title_chapter = epub.EpubHtml(title='Title Page', file_name='title.xhtml', content=title_content)
    epub_book.add_item(title_chapter)
    
    # Create chapters list for linear reading
    epub_chapters = []
    toc_entries = [title_chapter]
    
    # Filter and sort chapters with content
    content_chapters = [ch for ch in book.chapters if ch.content.strip()]
    content_chapters.sort(key=lambda x: x.chapter_number)
    
    # Create individual chapters with navigation links
    for i, chapter in enumerate(content_chapters):
        # Determine previous and next chapters for navigation
        prev_chapter = content_chapters[i-1] if i > 0 else None
        next_chapter = content_chapters[i+1] if i < len(content_chapters) - 1 else None
        
        # Build navigation links
        nav_links = ""
        if prev_chapter:
            nav_links += f'<link rel="prev" href="chapter_{prev_chapter.chapter_number:03d}.xhtml" />'
        if next_chapter:
            nav_links += f'<link rel="next" href="chapter_{next_chapter.chapter_number:03d}.xhtml" />'
        
        chapter_content = f"""
        <html>
        <head>
            <title>Chapter {chapter.chapter_number}: {chapter.title}</title>
            {nav_links}
            <style>
                body {{ font-family: serif; margin: 2em; line-height: 1.6; }}
                h1 {{ text-align: center; color: #2c3e50; margin: 2em 0; }}
                p {{ text-align: justify; margin: 1em 0; }}
            </style>
        </head>
        <body>
            <h1>Chapter {chapter.chapter_number}: {chapter.title}</h1>
            {format_chapter_content(chapter.content)}
        </body>
        </html>
        """
        
        # Create EPUB chapter
        chapter_filename = f"chapter_{chapter.chapter_number:03d}.xhtml"
        epub_chapter = epub.EpubHtml(
            title=f"Chapter {chapter.chapter_number}: {chapter.title}",
            file_name=chapter_filename,
            content=chapter_content
        )
        
        epub_book.add_item(epub_chapter)
        epub_chapters.append(epub_chapter)
        toc_entries.append(epub_chapter)
    
    # Create table of contents (less intrusive)
    epub_book.toc = toc_entries
    
    # Add navigation files
    nav_chapter = epub.EpubNav()
    epub_book.add_item(nav_chapter)
    
    ncx_chapter = epub.EpubNcx()
    epub_book.add_item(ncx_chapter)
    
    # Define spine with linear reading order
    # Title page first, then all chapters in linear sequence
    spine_items = [
        title_chapter,  # Title page
        nav_chapter,    # Navigation (accessible but not interrupting flow)
    ]
    
    # Add all content chapters to spine with linear="yes" for sequential reading
    spine_items.extend(epub_chapters)
    
    epub_book.spine = spine_items
    
    # Write EPUB file
    epub.write_epub(str(output_path), epub_book)








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
                if character.role:
                    f.write(f"Role: {character.role}\n")
                f.write("\n")
        
        if book.chapters:
            f.write("CHAPTERS\n")
            f.write("-" * 20 + "\n")
            for chapter in book.chapters:
                f.write(f"Chapter {chapter.chapter_number}: {chapter.title}\n")
                if chapter.summary:
                    f.write(f"  Summary: {chapter.summary}\n")
                if chapter.key_characters:
                    f.write(f"  Key Characters: {', '.join(chapter.key_characters)}\n")
                if chapter.plot_points:
                    f.write(f"  Plot Points: {'; '.join(chapter.plot_points)}\n")
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