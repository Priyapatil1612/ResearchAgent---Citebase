#!/usr/bin/env python3
"""
Simple script to run the Research Agent locally
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return the process"""
    return subprocess.Popen(
        command,
        cwd=cwd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except:
        print("❌ Node.js not found. Please install Node.js 18+")
        return False
    
    return True

def setup_environment():
    """Set up environment files if they don't exist"""
    print("🔧 Setting up environment...")
    
    # Backend .env
    if not os.path.exists(".env"):
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""# Database
DATABASE_URL=sqlite:///./research_agent.db

# OpenAI API (required for research agent)
OPENAI_API_KEY=your_openai_api_key_here

# Search API (choose one)
# SERPAPI_API_KEY=your_serpapi_key_here
SEARCH_PROVIDER=duckduckgo

# Optional: Customize settings
MAX_PAGES_TO_SCRAPE=8
MAX_TOTAL_CHUNKS=200
LOG_LEVEL=INFO
""")
        print("⚠️  Please edit .env file with your OpenAI API key!")
        return False
    
    # Frontend .env
    frontend_env = Path("frontend/.env")
    if not frontend_env.exists():
        print("📝 Creating frontend .env file...")
        frontend_env.write_text("REACT_APP_API_URL=http://localhost:8000/api")
    
    return True

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("📦 Installing dependencies...")
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to install Python dependencies: {result.stderr}")
        return False
    
    # Install Node.js dependencies
    print("Installing Node.js dependencies...")
    result = subprocess.run(["npm", "install"], cwd="frontend", capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to install Node.js dependencies: {result.stderr}")
        return False
    
    print("✅ Dependencies installed successfully!")
    return True

def main():
    """Main function to run the application"""
    print("🚀 Research Agent Local Development Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install the required dependencies and try again.")
        return
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Please configure your environment and try again.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return
    
    print("\n🎉 Setup complete! Starting the application...")
    print("\n📋 Instructions:")
    print("1. The backend will start on http://localhost:8000")
    print("2. The frontend will start on http://localhost:3000")
    print("3. API documentation will be available at http://localhost:8000/docs")
    print("4. Press Ctrl+C to stop both servers")
    print("\n" + "=" * 50)
    
    # Start backend
    print("🔧 Starting backend server...")
    backend_process = run_command(f"{sys.executable} backend/main.py")
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    print("🎨 Starting frontend server...")
    frontend_process = run_command("npm start", cwd="frontend")
    
    # Function to handle cleanup
    def cleanup(signum, frame):
        print("\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend server stopped unexpectedly")
                break
                
            if frontend_process.poll() is not None:
                print("❌ Frontend server stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    main()
