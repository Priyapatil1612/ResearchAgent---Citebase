#!/bin/bash

# Research Agent Development Startup Script

echo "🚀 Starting Research Agent Development Environment"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating a template..."
    cat > .env << EOF
# Database
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
EOF
    echo "📝 Please edit .env file with your API keys before running the application."
    echo "   At minimum, you need to set OPENAI_API_KEY"
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Create frontend .env file
if [ ! -f .env ]; then
    echo "📝 Creating frontend .env file..."
    echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
fi

cd ..

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "🔧 To start the application:"
echo "   1. Edit .env file with your API keys"
echo "   2. Run: python backend/main.py (in one terminal)"
echo "   3. Run: cd frontend && npm start (in another terminal)"
echo ""
echo "🌐 Application will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see README.md"

