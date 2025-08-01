"""
Booksmith - AI-Powered Book Generation Platform
Main Streamlit Application Entry Point
"""

import os
import sys
import logging
from pathlib import Path

from booksmith.models.book import Book

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Firebase modules
from web.firebase import FirebaseAuth, FirebaseUserManager
from booksmith.generation.agent import WritingAgent, PartialGenerationFailure
from booksmith.api.state import BookStateManager

# Page configuration
st.set_page_config(
    page_title="Booksmith",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto"
)

# Simple, clean design with no custom CSS

def init_firebase():
    """Initialize Firebase services."""
    try:
        # Initialize Firebase User Manager (Admin SDK)
        if 'firebase_user_manager' not in st.session_state:
            st.session_state.firebase_user_manager = FirebaseUserManager()
            if not st.session_state.firebase_user_manager.initialize():
                st.error("❌ Failed to initialize Firebase Admin SDK")
                return False
        
        # Initialize Firebase Auth (Client SDK)
        if 'firebase_auth' not in st.session_state:
            project_id = os.environ.get("FIREBASE_PROJECT_ID")
            st.session_state.firebase_auth = FirebaseAuth(project_id)
            if not st.session_state.firebase_auth.is_available():
                st.warning("⚠️ Firebase Authentication not fully configured")
        
        return True
    except Exception as e:
        st.error(f"❌ Firebase initialization error: {str(e)}")
        return False

def check_authentication():
    """Check if user is authenticated."""
    return (
        'user_token' in st.session_state and 
        'user_data' in st.session_state and 
        st.session_state.user_token and 
        st.session_state.user_data
    )

def logout():
    """Log out the current user."""
    # Clear authentication data
    for key in ['user_token', 'user_data', 'user_books']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("👋 Successfully logged out!")
    st.rerun()

def show_auth_page():
    """Display authentication page with login and register tabs."""
    st.title("📚 Booksmith")
    st.markdown("**AI-Powered Book Generation Platform**")
    st.markdown("---")
    
    # Check Firebase availability
    if not st.session_state.firebase_auth.is_available():
        st.error("🔥 Firebase Authentication is not properly configured. Please check your environment variables.")
        return
    
    # Create tabs for login and register
    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])
    
    with login_tab:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔒 Password", type="password", placeholder="Your password")
            
            if st.form_submit_button("🚪 Login", use_container_width=True):
                if email and password:
                    with st.spinner("🔐 Logging in..."):
                        result = st.session_state.firebase_auth.login(email, password)
                        
                    if result['success']:
                        st.session_state.user_token = result['token']
                        st.session_state.user_data = result['user']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error("⚠️ Please fill in all fields")
    
    with register_tab:
        with st.form("register_form"):
            st.subheader("Create Account")
            reg_email = st.text_input("📧 Email", placeholder="your.email@example.com", key="reg_email")
            reg_password = st.text_input("🔒 Password", type="password", placeholder="Choose a strong password", key="reg_password")
            reg_password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat your password", key="reg_password_confirm")
            display_name = st.text_input("👤 Display Name (Optional)", placeholder="Your name", key="reg_display_name")
            
            if st.form_submit_button("📝 Create Account", use_container_width=True):
                if reg_email and reg_password:
                    if reg_password != reg_password_confirm:
                        st.error("❌ Passwords do not match")
                    elif len(reg_password) < 6:
                        st.error("❌ Password must be at least 6 characters long")
                    else:
                        with st.spinner("📝 Creating account..."):
                            result = st.session_state.firebase_auth.register(
                                reg_email, 
                                reg_password, 
                                display_name or None
                            )
                        
                        if result['success']:
                            st.session_state.user_token = result['token']
                            st.session_state.user_data = result['user']
                            st.success("✅ Account created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Registration failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error("⚠️ Please fill in all required fields")

def show_dashboard():
    """Display the main dashboard for authenticated users."""
    # Check if we're viewing a specific book
    if 'viewing_book_id' in st.session_state:
        show_book_viewer()
        return
    
    user_data = st.session_state.user_data
    
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {user_data.get('display_name', user_data.get('email', 'User'))}!")
        st.markdown(f"**Email:** {user_data.get('email')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        # Load user books for stats
        if 'user_books' not in st.session_state:
            with st.spinner("📚 Loading your books..."):
                try:
                    state_manager = BookStateManager()
                    user_books = state_manager.list_user_books(user_data['uid'])
                    st.session_state.user_books = user_books
                except Exception as e:
                    st.error(f"Error loading books: {str(e)}")
                    st.session_state.user_books = {}
        
        book_count = len(st.session_state.user_books)
        st.metric("📚 Total Books", book_count)
    
    # Main dashboard content
    st.title("📚 Your Book Library")
    
    # Create two main sections
    col1, col2 = st.columns([1, 1])
    
    with col1:
        show_create_book_section()
    
    with col2:
        show_books_section()

def show_create_book_section():
    """Display the create new book section."""
    st.markdown("### ✍️ Create New Book")
    
    with st.expander("📝 Book Details", expanded=True):
        with st.form("create_book_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                genre = st.selectbox(
                    "Genre",
                    ["fantasy", "science fiction", "mystery", "romance", "thriller", "horror", "adventure", "literary fiction", "historical fiction"],
                    index=0
                )
                
                target_audience = st.selectbox(
                    "Target Audience",
                    ["young adults", "adults", "children", "teens", "all ages"],
                    index=0
                )
                
                language = st.selectbox(
                    "Language",
                    ["english", "spanish", "french", "german", "portuguese (Portugal)"],
                    index=0
                )
            
            with col2:
                writing_style = st.selectbox(
                    "Writing Style",
                    ["descriptive", "narrative", "dialogue-heavy", "action-packed", "literary", "minimalist"],
                    index=0
                )
            
            base_prompt = st.text_area(
                "Book Concept/Outline",
                placeholder="Describe your book idea, main plot, setting, or any specific elements you want included...",
                height=150,
                help="Be as detailed as possible. This will guide the AI in creating your book."
            )
            
            if st.form_submit_button("🎨 Generate Book", use_container_width=True):
                if base_prompt.strip():
                    generate_book(base_prompt, genre, target_audience, language, writing_style)
                else:
                    st.error("⚠️ Please provide a book concept or outline")

def generate_book(base_prompt, genre, target_audience, language, writing_style):
    """Generate a new book using the WritingAgent with retry support."""
    try:
        # Import and create book model
        from booksmith.models.book import Book
        
        # Create book object
        book = Book(
            base_prompt=base_prompt,
            genre=genre,
            target_audience=target_audience,
            language=language,
            writing_style=writing_style
        )
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        progress_log = st.empty()
        
        # Progress callback for real-time updates
        progress_messages = []
        
        def progress_callback(message: str):
            progress_messages.append(message)
            # Show the latest message in status
            status_text.text(message)
            # Show a log of recent messages
            if len(progress_messages) > 10:
                progress_messages.pop(0)
            with progress_log.container():
                for msg in progress_messages[-5:]:  # Show last 5 messages
                    st.text(msg)
        
        # Initialize writing agent
        with st.spinner("🤖 Initializing AI Writing Agent..."):
            agent = WritingAgent(progress_callback=progress_callback)
            
            # Check if agent is available
            if not agent.llm_backend or not agent.llm_backend.is_available():
                st.error("❌ AI Writing Agent not available. Please check your OpenAI API configuration.")
                return
                
        try:
            # Generate full book using the agent's robust method
            agent.write_full_book(book)
            
            # Update progress for saving
            progress_bar.progress(90)
            progress_callback("💾 Saving your book...")
            
            # Save book
            state_manager = BookStateManager()
            book_id, saved_book = state_manager.create_book(
                st.session_state.user_data['uid'],
                **book.model_dump()
            )
            
            progress_bar.progress(100)
            progress_callback("✅ Book generation completed!")
            
            # Show success message
            st.success(f"🎉 Successfully generated '{book.title or 'Untitled Book'}'!")
            
            # Display book stats
            completed_chapters = [ch for ch in book.chapters if ch.content]
            total_words = sum(len(ch.content.split()) for ch in completed_chapters)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📖 Chapters", f"{len(completed_chapters)}/{len(book.chapters) if book.chapters else 0}")
            with col2:
                st.metric("👥 Characters", len(book.characters) if book.characters else 0)
            with col3:
                st.metric("📝 Words", f"{total_words:,}")
            
            # Store book info for potential regeneration
            st.session_state.last_generated_book = {
                'book': book,
                'book_id': book_id,
                'agent': agent
            }
            
        except PartialGenerationFailure as e:
            # Handle partial failures gracefully
            progress_bar.progress(100)
            
            st.warning(f"⚠️ Book generation completed with some issues: {str(e)}")
            
            # Still save what we have
            state_manager = BookStateManager()
            book_id, saved_book = state_manager.create_book(
                st.session_state.user_data['uid'],
                **book.model_dump()
            )
            
            # Show partial stats
            completed_chapters = [ch for ch in book.chapters if ch.content]
            total_words = sum(len(ch.content.split()) for ch in completed_chapters)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📖 Chapters", f"{len(completed_chapters)}/{len(book.chapters) if book.chapters else 0}")
            with col2:
                st.metric("👥 Characters", len(book.characters) if book.characters else 0)
            with col3:
                st.metric("📝 Words", f"{total_words:,}")
            
            # Store for regeneration
            st.session_state.last_generated_book = {
                'book': book,
                'book_id': book_id,
                'agent': agent,
                'failed_steps': e.failed_steps
            }
            
            # Show retry options
            st.markdown("---")
            st.markdown("### 🔄 Retry Options")
            
            if st.button("🔄 Retry Failed Steps", type="primary"):
                retry_failed_steps(book, agent, e.failed_steps)
        
        # Refresh books list
        if 'user_books' in st.session_state:
            del st.session_state.user_books
        st.rerun()
        
    except Exception as e:
        logger.error(f"Book generation error: {e}")
        st.error(f"❌ Book generation failed: {str(e)}")
        
        # Show retry option for complete failure
        if st.button("🔄 Try Again"):
            st.rerun()


def retry_failed_steps(book: Book, agent: WritingAgent, failed_steps: list):
    """Retry failed generation steps."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        total_steps = len(failed_steps)
        for i, step in enumerate(failed_steps):
            progress = int((i / total_steps) * 100)
            progress_bar.progress(progress)
            status_text.text(f"🔄 Retrying: {step}")
            
            if step == "Story Summary":
                agent.generate_story_summary(book)
            elif step == "Title":
                agent.generate_title(book)
            elif step == "Characters":
                agent.generate_characters(book)
            elif step == "Chapter Plan":
                agent.generate_chapter_plan(book)
            elif step.startswith("Chapters:"):
                # Extract chapter numbers from the step
                chapter_nums_str = step.split(":")[1].strip()
                chapter_nums = [int(x.strip()) for x in chapter_nums_str.split(",")]
                for chapter_num in chapter_nums:
                    agent.regenerate_chapter(book, chapter_num)
        
        progress_bar.progress(100)
        status_text.text("✅ Retry completed!")
        st.success("🎉 Successfully retried failed steps!")
        
        # Update the saved book
        if 'last_generated_book' in st.session_state:
            book_id = st.session_state.last_generated_book['book_id']
            state_manager = BookStateManager()
            # Update the book in storage
            # Note: We'd need to add an update method to BookStateManager
            
    except Exception as e:
        st.error(f"❌ Retry failed: {str(e)}")
        logger.error(f"Retry error: {e}")

def show_books_section():
    """Display the user's books section."""
    st.markdown("### 📚 Your Books")
    
    if 'user_books' not in st.session_state:
        st.info("📚 Loading your books...")
        return
    
    user_books = st.session_state.user_books
    
    if not user_books:
        st.info("📖 No books yet. Create your first book using the form on the left!")
        return
    
    # Display books
    for book_id, book in user_books.items():
        with st.expander(f"📚 {book.title or 'Untitled Book'}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Genre:** {book.genre.title()}")
                st.write(f"**Target Audience:** {book.target_audience.title()}")
                st.write(f"**Language:** {book.language.title()}")
                st.write(f"**Chapters:** {len(book.chapters)}")
                
                if book.story_summary:
                    st.write("**Summary:**")
                    st.write(book.story_summary[:200] + "..." if len(book.story_summary) > 200 else book.story_summary)
                
                if book.characters:
                    st.write(f"**Characters:** {', '.join([char.name for char in book.characters[:3]])}")
                    if len(book.characters) > 3:
                        st.write(f"... and {len(book.characters) - 3} more")
            
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{book_id}"):
                    delete_book(book_id)
                
                if st.button(f"👁️ View", key=f"view_{book_id}"):
                    st.session_state.viewing_book_id = book_id
                    st.rerun()

def show_book_viewer():
    """Display the book viewer interface."""
    if 'viewing_book_id' not in st.session_state:
        return
    
    book_id = st.session_state.viewing_book_id
    user_books = st.session_state.get('user_books', {})
    
    if book_id not in user_books:
        st.error("Book not found!")
        del st.session_state.viewing_book_id
        st.rerun()
        return
    
    book = user_books[book_id]
    
    # Header with back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Library"):
            del st.session_state.viewing_book_id
            st.rerun()
    
    with col2:
        st.title(f"📖 {book.title or 'Untitled Book'}")
    
    # Book metadata
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Genre:** {book.genre.title()}")
        st.write(f"**Language:** {book.language.title()}")
    with col2:
        st.write(f"**Target Audience:** {book.target_audience.title()}")
        st.write(f"**Writing Style:** {book.writing_style.title()}")
    with col3:
        st.write(f"**Chapters:** {len(book.chapters)}")
        if book.characters:
            st.write(f"**Characters:** {len(book.characters)}")
    
    # Story Summary
    if book.story_summary:
        st.markdown("### 📝 Story Summary")
        st.write(book.story_summary)
        st.markdown("---")
    
    # Characters
    if book.characters:
        st.markdown("### 👥 Characters")
        for i, character in enumerate(book.characters):
            with st.expander(f"{character.name}", expanded=i==0):
                st.write(f"**Background Story:** {character.background_story}")
                st.write(f"**Appearance:** {character.appearance}")
                st.write(f"**Personality:** {character.personality}")
                st.write(f"**Role:** {character.role}")
        st.markdown("---")
    
    # Chapters
    if book.chapters:
        st.markdown("### 📚 Chapters")
        
        # Chapter navigation
        chapter_titles = [f"Chapter {ch.chapter_number}: {ch.title}" for ch in book.chapters]
        selected_chapter = st.selectbox(
            "Select Chapter to Read:",
            options=range(len(book.chapters)),
            format_func=lambda x: chapter_titles[x],
            key="chapter_selector"
        )
        
        # Display selected chapter
        chapter = book.chapters[selected_chapter]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {chapter_titles[selected_chapter]}")

        
        if chapter.content:
            # Format the content nicely
            content_paragraphs = chapter.content.split('\n\n')
            for paragraph in content_paragraphs:
                if paragraph.strip():
                    st.write(paragraph.strip())
                    st.write("")  # Add spacing between paragraphs
        else:
            st.warning("Chapter content not available.")
            
            # Show regenerate button for missing content
            if st.button(f"🔄 Generate Chapter Content", key=f"gen_ch_{chapter.chapter_number}"):
                regenerate_single_chapter(book_id, chapter.chapter_number)


def regenerate_single_chapter(book_id: str, chapter_number: int):
    """Regenerate a single chapter."""
    try:
        # Get the book from session
        user_books = st.session_state.get('user_books', {})
        if book_id not in user_books:
            st.error("Book not found!")
            return
        
        book = user_books[book_id]
        
        # Create a progress callback
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(message: str):
            status_text.text(message)
        
        # Initialize agent for regeneration
        with st.spinner("🤖 Initializing AI Writing Agent..."):
            agent = WritingAgent(progress_callback=progress_callback)
            
            if not agent.llm_backend or not agent.llm_backend.is_available():
                st.error("❌ AI Writing Agent not available. Please check your OpenAI API configuration.")
                return
        
        progress_bar.progress(50)
        
        # Regenerate the chapter
        agent.regenerate_chapter(book, chapter_number)
        
        progress_bar.progress(90)
        status_text.text("💾 Saving changes...")
        
        # Update the book in storage
        state_manager = BookStateManager()
        state_manager.update_book(st.session_state.user_data['uid'], book_id, book)
        
        progress_bar.progress(100)
        status_text.text("✅ Chapter regenerated!")
        
        st.success(f"🎉 Chapter {chapter_number} regenerated successfully!")
        
        # Refresh the page to show new content
        if 'user_books' in st.session_state:
            del st.session_state.user_books
        st.rerun()
        
    except Exception as e:
        logger.error(f"Chapter regeneration error: {e}")
        st.error(f"❌ Chapter regeneration failed: {str(e)}")

def delete_book(book_id):
    """Delete a book."""
    try:
        state_manager = BookStateManager()
        success = state_manager.delete_book(st.session_state.user_data['uid'], book_id)
        
        if success:
            st.success("📚 Book deleted successfully!")
            # Refresh books list
            if 'user_books' in st.session_state:
                del st.session_state.user_books
            st.rerun()
        else:
            st.error("❌ Failed to delete book")
    except Exception as e:
        st.error(f"❌ Error deleting book: {str(e)}")

def main():
    """Main application entry point."""
    # Initialize Firebase
    if not init_firebase():
        st.stop()
    
    # Check authentication and route to appropriate page
    if check_authentication():
        show_dashboard()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()
