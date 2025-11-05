#!/bin/bash

echo "🚀 Research Agent Setup Script"
echo "=============================="

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source agents_tut/bin/activate

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
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
    echo "⚠️  Please edit .env file with your OpenAI API key!"
fi

# Create frontend .env file
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend .env file..."
    echo "REACT_APP_API_URL=http://localhost:8000/api" > frontend/.env
fi

echo "✅ Environment files created!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: source agents_tut/bin/activate && python run_local.py"
echo "   OR"
echo "3. Run backend: source agents_tut/bin/activate && python backend/main.py"
echo "4. Run frontend: cd frontend && npm start"
