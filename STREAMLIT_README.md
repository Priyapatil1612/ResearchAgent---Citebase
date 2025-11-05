# Research Agent Streamlit UI

A modern web interface for your Research Agent that allows you to research topics and ask follow-up questions with persistent topic history.

## Features

### 🔍 Research New Topics
- Enter any topic to research
- Automatic web search and content indexing
- Custom namespace support
- Force re-ingest option for updated information

### ❓ Ask Follow-up Questions
- Ask questions about previously researched topics
- Adjustable retrieval parameters
- Rich answer display with citations
- Question history tracking

### 📚 Topic History Management
- **Persistent Storage**: All researched topics are saved and accessible across sessions
- **Sidebar Navigation**: Quick access to all previous research
- **Topic Metadata**: View indexed pages, chunks, and sources for each topic
- **Question History**: Track all questions and answers for each topic

### 🎨 Modern UI
- Clean, responsive design
- Color-coded sections
- Interactive elements
- Real-time feedback

## Quick Start

### 1. Install Dependencies
```bash
# Make sure you're in the project directory
cd /Users/priyapatil/Desktop/GITchakaam/Agents_Learning

# Install Streamlit (if not already installed)
pip install streamlit>=1.28.0

# Or install all requirements
pip install -r requirements.txt
```

### 2. Configure Environment
Make sure your `.env` file is set up with the required API keys:
```bash
# Required for OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Optional for search (if using SerpAPI)
SERPAPI_API_KEY=your_serpapi_key_here

# Optional settings
LOG_LEVEL=INFO
MAX_PAGES_TO_SCRAPE=8
RETRIEVAL_TOP_K=6
```

### 3. Run the App
```bash
# Option 1: Use the startup script
python run_streamlit.py

# Option 2: Run directly
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Guide

### Researching a New Topic

1. **Navigate to Research Tab**: Click on the "🔍 Research" tab
2. **Enter Topic**: Type your research topic (e.g., "artificial intelligence trends 2024")
3. **Optional Namespace**: Leave empty for auto-generation or specify a custom namespace
4. **Start Research**: Click "🚀 Start Research"
5. **Wait for Completion**: The agent will search the web, fetch pages, and index content
6. **View Results**: See indexed pages, chunks, and sources

### Asking Questions

1. **Select a Topic**: Choose from the sidebar or complete research first
2. **Navigate to Questions Tab**: Click on the "❓ Ask Questions" tab
3. **Enter Question**: Type your question about the researched topic
4. **Adjust Parameters**: Use the slider to control retrieval depth
5. **Get Answer**: Click "🤔 Ask Question" for AI-generated answers with citations

### Managing Topic History

- **View All Topics**: All researched topics appear in the left sidebar
- **Switch Topics**: Click any topic in the sidebar to switch to it
- **View Metadata**: Each topic shows creation date, indexed pages, and chunks
- **Question History**: Expand any question in the history to see previous Q&As
- **Clear History**: Use the "🗑️ Clear All Topics" button to reset

## File Structure

```
├── streamlit_app.py          # Main Streamlit application
├── run_streamlit.py         # Startup script
├── topics_history.json      # Persistent topic storage (auto-created)
├── .env                     # Environment configuration
└── requirements.txt         # Python dependencies
```

## Configuration Options

The app respects all settings from your `config/settings.py`:

- **Search Provider**: DuckDuckGo (free) or SerpAPI (paid)
- **Max Pages**: Control how many pages to scrape per topic
- **Chunk Size**: Adjust text chunking for better retrieval
- **Top-K Retrieval**: Number of relevant chunks to retrieve
- **Rate Limiting**: Control API call frequency

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your `.env` file has the correct API keys
2. **Import Errors**: Make sure you're running from the project root directory
3. **Port Already in Use**: Change the port in `run_streamlit.py` if needed
4. **Memory Issues**: Reduce `MAX_PAGES_TO_SCRAPE` for large topics

### Debug Mode

For debugging, you can run with debug logging:
```bash
LOG_LEVEL=DEBUG streamlit run streamlit_app.py
```

### Reset Everything

To start fresh:
1. Delete `topics_history.json`
2. Clear your browser cache
3. Restart the Streamlit app

## Advanced Features

### Custom Namespaces
Use custom namespaces to organize related research:
- "ai-trends-2024" for AI trends
- "ml-frameworks" for machine learning frameworks
- "blockchain-news" for blockchain updates

### Batch Research
Research multiple related topics and ask cross-topic questions by switching between namespaces.

### Export Data
Topic history is stored in `topics_history.json` and can be exported or backed up.

## Development

### Adding New Features
1. Modify `streamlit_app.py` for UI changes
2. Update `TopicManager` class for data management
3. Test with different topics and questions

### Customization
- Modify CSS in the `st.markdown()` sections
- Add new tabs or sections
- Integrate additional tools from the `tools/` directory

## Support

For issues or questions:
1. Check the console output for error messages
2. Verify your `.env` configuration
3. Ensure all dependencies are installed
4. Check the debug logs for detailed error information
