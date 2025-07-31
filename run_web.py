#!/usr/bin/env python3
"""
Launch script for Booksmith web application.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit web app."""
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "web/app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\nShutting down Booksmith web app...")
    except Exception as e:
        print(f"Error launching web app: {e}")

if __name__ == "__main__":
    main() 