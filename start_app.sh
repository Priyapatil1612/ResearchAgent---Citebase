#!/bin/bash

echo "🚀 Starting Research Agent with Virtual Environment"
echo "=================================================="

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source agents_tut/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run ./setup.sh first"
    exit 1
fi

# Check if frontend .env exists
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend .env file..."
    echo "REACT_APP_API_URL=http://localhost:8000/api" > frontend/.env
fi

echo "✅ Environment ready!"
echo ""
echo "🔧 Starting servers..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "🔧 Starting backend server..."
python backend/main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait
