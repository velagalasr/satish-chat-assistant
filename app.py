"""
Main Streamlit Application
AI Chatbot with RAG capabilities
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import get_config, setup_logger
from src.agents import AgentManager
from src.rag import RAGManager
from src.ui import (
    render_sidebar,
    render_chat_message,
    render_file_uploader,
    render_chat_input,
    render_stats_panel,
    apply_custom_css
)

# Initialize logger
logger = setup_logger(
    name="chatbot_app",
    level="INFO",
    log_file="./logs/chatbot.log"
)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.messages = []
        logger.info("Session state initialized")


def initialize_components():
    """Initialize RAG and Agent components."""
    if 'rag_manager' not in st.session_state:
        with st.spinner("Initializing RAG system..."):
            try:
                st.session_state.rag_manager = RAGManager()
                logger.info("RAG Manager initialized")
            except Exception as e:
                logger.error(f"Error initializing RAG: {e}")
                st.error(f"Failed to initialize RAG system: {e}")
                st.session_state.rag_manager = None
    
    if 'agent_manager' not in st.session_state:
        with st.spinner("Loading agents..."):
            try:
                retriever = None
                if st.session_state.rag_manager and st.session_state.rag_manager.enabled:
                    retriever = st.session_state.rag_manager.get_retriever()
                
                st.session_state.agent_manager = AgentManager(rag_retriever=retriever)
                logger.info("Agent Manager initialized")
            except Exception as e:
                logger.error(f"Error initializing agents: {e}")
                st.error(f"Failed to initialize agents: {e}")
                st.stop()


def main():
    """Main application function."""
    # Load configuration
    config = get_config()
    ui_config = config.get_ui_config()
    
    # Page configuration
    st.set_page_config(
        page_title=ui_config.get('title', 'AI Chatbot'),
        page_icon=ui_config.get('page_icon', '🤖'),
        layout=ui_config.get('layout', 'wide'),
        initial_sidebar_state='collapsed'  # Hide sidebar by default
    )
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize components
    initialize_components()
    
    # Get managers from session state
    agent_manager = st.session_state.agent_manager
    rag_manager = st.session_state.rag_manager
    
    # Render sidebar (hidden by default, can be opened manually)
    # render_sidebar(agent_manager, rag_manager, ui_config)
    
    # Main chat interface - Clean minimal design
    st.title("💬 Satish's AI Assistant")
    st.caption("Ask me anything about Satish's experience, skills, and projects")
    
    # Hide file uploader and stats for clean interface
    # if ui_config.get('enable_file_upload', True) and rag_manager and rag_manager.enabled:
    #     render_file_uploader(rag_manager)
    # render_stats_panel(agent_manager, rag_manager)
    
    st.divider()
    
    # Display chat history
    for message in st.session_state.messages:
        render_chat_message(
            role=message['role'],
            content=message['content'],
            timestamp=message.get('timestamp')
        )
    
    # Check if there's an example prompt to process
    example_prompt = st.session_state.get('example_prompt', None)
    if example_prompt:
        # Clear the example prompt from session state
        st.session_state.example_prompt = None
        # Set it as the user input to be processed
        user_input = example_prompt
    else:
        # Chat input
        user_input = render_chat_input(agent_manager, ui_config)
    
    if user_input:
        # Add user message to history
        timestamp = datetime.now()
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        
        # Display user message
        render_chat_message('user', user_input, timestamp)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    response = agent_manager.chat(user_input)
                    timestamp = datetime.now()
                    
                    # Display response
                    st.markdown(response)
                    st.caption(f"_{timestamp.strftime('%H:%M:%S')}_")
                    
                    # Add to history
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': timestamp
                    })
                    
                    logger.info(f"User: {user_input[:50]}... | Response length: {len(response)}")
                
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Error generating response: {e}")
        
        # Rerun to update chat display
        st.rerun()
    
    # Hide footer for clean interface
    # st.divider()
    # col1, col2, col3 = st.columns([2, 1, 1])
    # with col1:
    #     current_agent = agent_manager.get_current_agent()
    #     st.caption(f"🤖 Active Agent: **{current_agent.name}**")
    # with col2:
    #     if rag_manager and rag_manager.enabled:
    #         st.caption(f"📚 RAG: **Enabled**")
    #     else:
    #         st.caption(f"📚 RAG: **Disabled**")
    # with col3:
    #     llm_config = config.get_llm_config()
    #     st.caption(f"🧠 Model: **{llm_config.get('model', 'N/A')}**")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An error occurred: {e}")
        st.stop()
