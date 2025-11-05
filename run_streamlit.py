#!/usr/bin/env python3
"""
Startup script for the Streamlit Research Agent UI.
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit app."""
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Starting Research Agent Streamlit App...")
    print("📍 Make sure you have your .env file configured with API keys")
    print("🌐 The app will open in your browser at http://localhost:8501")
    print("=" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Research Agent...")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
