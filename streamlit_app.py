#!/usr/bin/env python3
"""
Streamlit UI for Research Agent
Provides a web interface for researching topics and asking follow-up questions.
"""

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import sys
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.agent_react import ResearchAgent
from config.settings import SETTINGS
from utils.common import slugify


# Page configuration
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .topic-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .research-result {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .question-result {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0d5aa7;
    }
</style>
""", unsafe_allow_html=True)


class TopicManager:
    """Manages topic history and persistence."""
    
    def __init__(self):
        self.topics_file = "topics_history.json"
        self.topics = self.load_topics()
    
    def load_topics(self) -> Dict:
        """Load topics from file."""
        if os.path.exists(self.topics_file):
            try:
                with open(self.topics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading topics: {e}")
                return {}
        return {}
    
    def save_topics(self):
        """Save topics to file."""
        try:
            with open(self.topics_file, 'w') as f:
                json.dump(self.topics, f, indent=2)
        except Exception as e:
            st.error(f"Error saving topics: {e}")
    
    def add_topic(self, topic: str, namespace: str, research_result: Dict):
        """Add a new topic to history."""
        self.topics[namespace] = {
            "topic": topic,
            "namespace": namespace,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "research_summary": {
                "indexed_pages": research_result.get("ingest_summary", {}).get("indexed_pages", 0),
                "indexed_chunks": research_result.get("ingest_summary", {}).get("indexed_chunks", 0),
                "sources": research_result.get("ingest_summary", {}).get("sources", [])
            },
            "questions": []
        }
        self.save_topics()
    
    def add_question(self, namespace: str, question: str, answer: str, citations: List):
        """Add a question and answer to a topic."""
        if namespace in self.topics:
            self.topics[namespace]["questions"].append({
                "question": question,
                "answer": answer,
                "citations": citations,
                "timestamp": datetime.now().isoformat()
            })
            self.topics[namespace]["last_accessed"] = datetime.now().isoformat()
            self.save_topics()
    
    def get_topic(self, namespace: str) -> Optional[Dict]:
        """Get topic by namespace."""
        return self.topics.get(namespace)
    
    def get_all_topics(self) -> Dict:
        """Get all topics sorted by last accessed."""
        return dict(sorted(
            self.topics.items(),
            key=lambda x: x[1]["last_accessed"],
            reverse=True
        ))


def initialize_session_state():
    """Initialize session state variables."""
    if 'agent' not in st.session_state:
        st.session_state.agent = ResearchAgent()
    
    if 'topic_manager' not in st.session_state:
        st.session_state.topic_manager = TopicManager()
    
    if 'current_namespace' not in st.session_state:
        st.session_state.current_namespace = None
    
    if 'research_completed' not in st.session_state:
        st.session_state.research_completed = False
    
    if 'research_result' not in st.session_state:
        st.session_state.research_result = None


def render_sidebar():
    """Render the sidebar with topic history."""
    st.sidebar.markdown('<div class="sidebar-header">📚 Research History</div>', unsafe_allow_html=True)
    
    topic_manager = st.session_state.topic_manager
    all_topics = topic_manager.get_all_topics()
    
    if not all_topics:
        st.sidebar.info("No research topics yet. Start by researching a new topic!")
        return None
    
    # Display topics
    for namespace, topic_data in all_topics.items():
        with st.sidebar.container():
            st.markdown(f"""
            <div class="topic-card">
                <strong>{topic_data['topic']}</strong><br>
                <small>Created: {topic_data['created_at'][:10]}</small><br>
                <small>Pages: {topic_data['research_summary']['indexed_pages']} | 
                Chunks: {topic_data['research_summary']['indexed_chunks']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select {topic_data['topic']}", key=f"select_{namespace}"):
                st.session_state.current_namespace = namespace
                st.session_state.research_completed = True
                st.session_state.research_result = topic_data
                st.rerun()
    
    # Clear all topics button
    if st.sidebar.button("🗑️ Clear All Topics", type="secondary"):
        if st.sidebar.button("Confirm Clear", type="secondary"):
            topic_manager.topics = {}
            topic_manager.save_topics()
            st.session_state.current_namespace = None
            st.session_state.research_completed = False
            st.session_state.research_result = None
            st.rerun()


def render_research_tab():
    """Render the research tab."""
    st.markdown("## 🔍 Research New Topic")
    
    with st.form("research_form"):
        topic = st.text_input(
            "Enter a topic to research:",
            placeholder="e.g., artificial intelligence trends 2024",
            help="Enter a topic you want to research. The agent will search the web and index relevant information."
        )
        
        namespace = st.text_input(
            "Namespace (optional):",
            placeholder="Leave empty for auto-generated",
            help="A unique identifier for this research. If empty, it will be auto-generated from the topic."
        )
        
        force_ingest = st.checkbox(
            "Force re-ingest",
            help="Re-ingest even if this topic was previously researched"
        )
        
        submitted = st.form_submit_button("🚀 Start Research", type="primary")
        
        if submitted and topic:
            with st.spinner("Researching topic... This may take a few minutes."):
                try:
                    # Generate namespace if not provided
                    if not namespace:
                        namespace = slugify(topic)
                    
                    # Perform research
                    result = st.session_state.agent.research(
                        topic=topic,
                        namespace=namespace,
                        force=force_ingest
                    )
                    
                    # Store result in session state
                    st.session_state.research_result = result
                    st.session_state.current_namespace = namespace
                    st.session_state.research_completed = True
                    
                    # Add to topic manager
                    if result.get("did_ingest", False):
                        st.session_state.topic_manager.add_topic(topic, namespace, result)
                    
                    st.success("Research completed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during research: {str(e)}")
                    st.error(f"Traceback: {traceback.format_exc()}")


def render_questions_tab():
    """Render the questions tab."""
    if not st.session_state.research_completed:
        st.warning("Please complete research first before asking questions.")
        return
    
    st.markdown("## ❓ Ask Questions")
    
    # Display current topic info
    if st.session_state.research_result:
        topic_data = st.session_state.research_result
        if isinstance(topic_data, dict) and 'ingest_summary' in topic_data:
            summary = topic_data['ingest_summary']
            st.info(f"""
            **Current Topic:** {st.session_state.current_namespace}
            - **Indexed Pages:** {summary.get('indexed_pages', 0)}
            - **Indexed Chunks:** {summary.get('indexed_chunks', 0)}
            - **Sources:** {len(summary.get('sources', []))}
            """)
    
    # Question input
    with st.form("question_form"):
        question = st.text_area(
            "Ask a question about the researched topic:",
            placeholder="e.g., What are the key trends in AI?",
            height=100,
            help="Ask specific questions about the topic you researched."
        )
        
        top_k = st.slider(
            "Number of relevant chunks to retrieve:",
            min_value=1,
            max_value=20,
            value=6,
            help="More chunks may provide more comprehensive answers but could be slower."
        )
        
        submitted = st.form_submit_button("🤔 Ask Question", type="primary")
        
        if submitted and question:
            with st.spinner("Thinking about your question..."):
                try:
                    # Get answer
                    result = st.session_state.agent.ask(
                        question=question,
                        namespace=st.session_state.current_namespace,
                        top_k=top_k
                    )
                    
                    # Display answer
                    st.markdown("### 💡 Answer")
                    st.markdown(f"""
                    <div class="question-result">
                        {result['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display citations
                    if result.get('citations'):
                        st.markdown("### 📚 Sources")
                        for i, citation in enumerate(result['citations'], 1):
                            st.markdown(f"""
                            **{i}. {citation['title']}**
                            - URL: {citation['url']}
                            """)
                    
                    # Store in topic manager
                    st.session_state.topic_manager.add_question(
                        st.session_state.current_namespace,
                        question,
                        result['content'],
                        result.get('citations', [])
                    )
                    
                except Exception as e:
                    st.error(f"Error getting answer: {str(e)}")
                    st.error(f"Traceback: {traceback.format_exc()}")


def render_question_history():
    """Render the question history for the current topic."""
    if not st.session_state.current_namespace:
        return
    
    topic_data = st.session_state.topic_manager.get_topic(st.session_state.current_namespace)
    if not topic_data or not topic_data.get('questions'):
        return
    
    st.markdown("### 📝 Question History")
    
    for i, qa in enumerate(reversed(topic_data['questions']), 1):
        with st.expander(f"Q{i}: {qa['question'][:50]}..."):
            st.markdown("**Question:**")
            st.write(qa['question'])
            st.markdown("**Answer:**")
            st.write(qa['answer'])
            
            if qa.get('citations'):
                st.markdown("**Sources:**")
                for j, citation in enumerate(qa['citations'], 1):
                    st.write(f"{j}. [{citation['title']}]({citation['url']})")


def main():
    """Main application."""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🔍 Research Agent</div>', unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if st.session_state.current_namespace:
        # Show current topic info
        topic_data = st.session_state.topic_manager.get_topic(st.session_state.current_namespace)
        if topic_data:
            st.success(f"Currently viewing: **{topic_data['topic']}**")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🔍 Research", "❓ Ask Questions"])
    
    with tab1:
        render_research_tab()
    
    with tab2:
        render_questions_tab()
        render_question_history()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        Research Agent - Powered by AI | Built with Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
