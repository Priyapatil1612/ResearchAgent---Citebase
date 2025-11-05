# Research Agent - AI-Powered Research Platform

A comprehensive research platform built with React and FastAPI that allows users to create research projects, perform AI-powered research, and manage knowledge through interactive notebooks.

## 🚀 Features

### Core Functionality
- **Project Management**: Create and manage research projects with topics and descriptions
- **AI Research**: Automated web research and content ingestion using your existing research agent
- **Interactive Q&A**: Chat interface for asking questions about researched topics
- **Notebook System**: Save and organize important Q&A pairs in personal notebooks
- **Real-time Updates**: Live research progress and status updates

### Technical Features
- **Modern UI**: Built with React 18, TypeScript, and Material-UI
- **RESTful API**: FastAPI backend with automatic documentation
- **Database Integration**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Responsive Design**: Mobile-friendly interface
- **Deployment Ready**: Configured for Vercel deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   Research Agent │
│                 │    │                 │    │                 │
│ • Project List  │◄──►│ • REST API      │◄──►│ • Web Search    │
│ • Chat Interface│    │ • Database      │    │ • Content Ingestion│
│ • Notebooks     │    │ • Authentication│    │ • Q&A Pipeline  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
Agents_Learning/
├── agent/                    # Existing research agent
│   ├── agent_react.py
│   └── __init__.py
├── backend/                  # FastAPI backend
│   ├── main.py              # Main API application
│   ├── database.py          # Database models and configuration
│   └── requirements.txt     # Backend dependencies
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Main application pages
│   │   ├── services/       # API service layer
│   │   ├── types/          # TypeScript type definitions
│   │   ├── App.tsx         # Main application component
│   │   └── index.tsx       # Application entry point
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies
│   └── tsconfig.json       # TypeScript configuration
├── config/                  # Configuration files
├── tools/                   # Research tools
├── pipelines/               # Data processing pipelines
├── vercel.json             # Vercel deployment configuration
└── README.md               # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+
- PostgreSQL (for production) or SQLite (for development)

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=sqlite:///./research_agent.db
   
   # OpenAI API (required for research agent)
   OPENAI_API_KEY=your_openai_api_key
   
   # Search API (choose one)
   SERPAPI_API_KEY=your_serpapi_key
   # OR use DuckDuckGo (no key required)
   SEARCH_PROVIDER=duckduckgo
   
   # Optional: Customize settings
   MAX_PAGES_TO_SCRAPE=8
   MAX_TOTAL_CHUNKS=200
   ```

3. **Run the backend**:
   ```bash
   cd backend
   python main.py
   ```
   
   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000/api
   ```

3. **Run the frontend**:
   ```bash
   npm start
   ```
   
   The application will be available at `http://localhost:3000`

## 🚀 Deployment on Vercel

### 1. Prepare for Deployment

1. **Update Vercel configuration**:
   Edit `vercel.json` and update the API URL:
   ```json
   {
     "env": {
       "REACT_APP_API_URL": "https://your-app-name.vercel.app/api"
     }
   }
   ```

2. **Set up environment variables in Vercel**:
   - Go to your Vercel project settings
   - Add the following environment variables:
     - `DATABASE_URL` (use a PostgreSQL database like Supabase or Neon)
     - `OPENAI_API_KEY`
     - `SERPAPI_API_KEY` (if using SerpAPI)
     - `REACT_APP_API_URL`

### 2. Deploy

1. **Connect your GitHub repository to Vercel**
2. **Deploy automatically** - Vercel will detect the configuration and deploy both frontend and backend

### 3. Database Setup (Production)

For production, use a PostgreSQL database:

1. **Create a PostgreSQL database** (Supabase, Neon, or Railway)
2. **Update DATABASE_URL** in Vercel environment variables
3. **Run database migrations** (the app will create tables automatically on first run)

## 📱 Usage Guide

### Creating a Research Project

1. **Navigate to the home page**
2. **Click "New Project"**
3. **Fill in project details**:
   - Project name
   - Research topic
   - Optional description
   - Optional namespace
4. **Click "Create Project"**

### Starting Research

1. **Select a project from the list**
2. **Click "Start Research"**
3. **Wait for the research to complete** (this may take a few minutes)
4. **Once completed, click "Ask Questions"**

### Using the Chat Interface

1. **Navigate to a completed project**
2. **Type your question in the chat input**
3. **Press Enter or click Send**
4. **View the AI-generated answer with sources**
5. **Save important Q&As to notebooks using the bookmark icon**

### Managing Notebooks

1. **Go to the Notebooks page**
2. **Create a new notebook**
3. **Add entries from chat conversations**
4. **Organize and review your saved knowledge**

## 🔧 Configuration

### Research Agent Settings

The research agent can be configured through environment variables:

```env
# Research settings
MAX_PAGES_TO_SCRAPE=8          # Maximum pages to scrape per research
MAX_TOTAL_CHUNKS=200           # Maximum chunks to process
CHUNK_SIZE_TOKENS=800          # Size of text chunks
CHUNK_OVERLAP_TOKENS=120       # Overlap between chunks
RETRIEVAL_TOP_K=6              # Number of relevant chunks for Q&A

# Search settings
SEARCH_PROVIDER=duckduckgo     # or serpapi
MAX_SEARCH_RESULTS=8

# LLM settings
LLM_PROVIDER=openai            # or gemini, groq
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### Frontend Configuration

Customize the frontend through environment variables:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
black .
flake8 .

# Frontend linting
cd frontend
npm run lint
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Review the API documentation at `/docs`
3. Check the browser console for frontend errors
4. Check the backend logs for API errors

## 🔮 Future Enhancements

- [ ] User authentication and multi-tenancy
- [ ] Real-time collaborative research
- [ ] Advanced notebook features (folders, tags, search)
- [ ] Export functionality (PDF, Markdown)
- [ ] Research analytics and insights
- [ ] Project templates
- [ ] API rate limiting and caching
- [ ] Mobile app (React Native)

## 🙏 Acknowledgments

- Built on top of the existing research agent infrastructure
- Uses OpenAI's GPT models for intelligent research
- Material-UI for beautiful, responsive components
- FastAPI for high-performance API development

