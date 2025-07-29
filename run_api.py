#!/usr/bin/env python3
"""
Script to run the Booksmith API locally for development and testing.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn

    # Set environment variables if needed
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("The API will run but LLM generation will use placeholder text.")
        print("")

    print("🚀 Starting Booksmith API server...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    print("💡 Test with Postman or curl at: http://localhost:8000")
    print("")

    # Run the server
    uvicorn.run(
        "booksmith.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
