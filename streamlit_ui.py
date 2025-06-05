#!/usr/bin/env python3
"""
PROFESSIONAL STREAMLIT WEB INTERFACE
Beautiful, responsive UI for M1 Chatbot System
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import psutil
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="🤖 M1 AI Chatbot Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/ai-chatbot-pro-m1',
        'Report a bug': 'https://github.com/yourusername/ai-chatbot-pro-m1/issues',
        'About': "M1 AI Chatbot Hub - Professional AI Assistant System"
    }
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #4CAF50;
        --warning-color: #FF9800;
        --error-color: #f44336;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, var(--accent-color) 0%, #f5576c 100%);
        color: white;
        margin-right: auto;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .status-healthy {
        background: rgba(76, 175, 80, 0.1);
        border-left: 4px solid var(--success-color);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .status-warning {
        background: rgba(255, 152, 0, 0.1);
        border-left: 4px solid var(--warning-color);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid var(--primary-color);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 15px;
        border: 2px solid var(--primary-color);
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 1.5s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"

# Personality configurations
PERSONALITIES = {
    "technical_expert": {
        "name": "🛠️ Technical Expert",
        "icon": "🛠️", 
        "description": "Senior software engineer and system architect",
        "color": "#2196F3",
        "capabilities": ["Memory optimization", "Performance tuning", "Debugging", "API design"],
        "sample_questions": [
            "My React app is slow on mobile devices",
            "How do I optimize database queries?", 
            "My API has memory leaks, help me debug"
        ]
    },
    "creative_partner": {
        "name": "✍️ Creative Partner",
        "icon": "✍️",
        "description": "Award-winning creative writing mentor",
        "color": "#E91E63",
        "capabilities": ["Story development", "Character creation", "Plot structure", "Writing techniques"],
        "sample_questions": [
            "I want to write a mystery novel",
            "Help me develop compelling characters",
            "I'm stuck with writer's block"
        ]
    },
    "business_advisor": {
        "name": "💼 Business Advisor",
        "icon": "💼",
        "description": "Strategic business consultant",
        "color": "#FF9800",
        "capabilities": ["Pricing strategy", "Growth planning", "Market analysis", "SaaS metrics"],
        "sample_questions": [
            "What pricing strategy for my SaaS?",
            "How to scale my startup?",
            "Customer acquisition strategies"
        ]
    }
}

PROMPT_TECHNIQUES = {
    "standard": {"name": "Standard", "icon": "💬", "description": "Direct response"},
    "chain_of_thought": {"name": "Chain of Thought", "icon": "🧠", "description": "Step-by-step reasoning"},
    "few_shot": {"name": "Few-Shot", "icon": "📚", "description": "Example-based learning"},
    "step_by_step": {"name": "Step-by-Step", "icon": "📋", "description": "Structured guidance"},
    "socratic": {"name": "Socratic", "icon": "❓", "description": "Question-guided exploration"},
    "analogical": {"name": "Analogical", "icon": "🔄", "description": "Analogy-based explanation"}
}

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'messages': [],
        'current_session_id': None,
        'selected_personality': 'technical_expert',
        'selected_technique': 'standard',
        'api_status': 'unknown',
        'system_metrics': {},
        'conversation_count': 0,
        'total_response_time': 0.0,
        'personalities_data': {},
        'show_advanced_options': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def check_api_status():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_status = 'healthy'
            return True
    except:
        st.session_state.api_status = 'down'
        return False
    return False

def get_system_metrics():
    """Get system metrics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            st.session_state.system_metrics = response.json()
            return st.session_state.system_metrics
    except:
        pass
    return {}

def send_chat_message(message: str, personality: str, technique: str):
    """Send message to API"""
    try:
        payload = {
            "message": message,
            "personality": personality,
            "technique": technique,
            "session_id": st.session_state.current_session_id
        }
        
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.current_session_id = result["session_id"]
            return result
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def display_sidebar():
    """Display enhanced sidebar with system status and controls"""
    st.sidebar.markdown('<div class="sidebar-header">🤖 M1 AI Chatbot Hub</div>', unsafe_allow_html=True)
    
    # API Status
    st.sidebar.markdown("### 🔧 System Status")
    
    is_api_running = check_api_status()
    
    if is_api_running:
        st.sidebar.markdown('<div class="status-healthy">✅ API Server Online</div>', unsafe_allow_html=True)
        
        # Get and display metrics
        metrics = get_system_metrics()
        if metrics:
            cpu_usage = metrics.get('cpu_usage', 0)
            memory_usage = metrics.get('memory_usage', {})
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("CPU", f"{cpu_usage:.1f}%")
            with col2:
                st.metric("Memory", f"{memory_usage.get('percent', 0):.1f}%")
            
            st.sidebar.metric("Active Sessions", metrics.get('active_sessions', 0))
            st.sidebar.metric("Total Requests", metrics.get('total_requests', 0))
    else:
        st.sidebar.markdown('<div class="status-warning">⚠️ API Server Offline</div>', unsafe_allow_html=True)
        st.sidebar.error("Please start the API server:\n\n`python api_server.py`")
        return False
    
    # Personality Selection
    st.sidebar.markdown("### 🎭 Choose AI Personality")
    
    personality_options = [PERSONALITIES[key]["name"] for key in PERSONALITIES.keys()]
    selected_display_name = st.sidebar.selectbox(
        "AI Assistant:",
        personality_options,
        index=0,
        key="personality_selector"
    )
    
    # Map display name back to personality key
    for key, config in PERSONALITIES.items():
        if config["name"] == selected_display_name:
            st.session_state.selected_personality = key
            break
    
    # Show personality info
    personality_config = PERSONALITIES[st.session_state.selected_personality]
    
    with st.sidebar.expander("🎯 Personality Details", expanded=True):
        st.write(f"**{personality_config['description']}**")
        st.write("**Capabilities:**")
        for capability in personality_config['capabilities']:
            st.write(f"• {capability}")
    
    # Advanced Options
    st.sidebar.markdown("### 🔧 Advanced Options")
    st.session_state.show_advanced_options = st.sidebar.toggle("Show Advanced Settings")
    
    if st.session_state.show_advanced_options:
        technique_options = [PROMPT_TECHNIQUES[key]["name"] for key in PROMPT_TECHNIQUES.keys()]
        selected_technique_name = st.sidebar.selectbox(
            "Prompt Technique:",
            technique_options,
            index=0,
            key="technique_selector"
        )
        
        # Map technique name back to key
        for key, config in PROMPT_TECHNIQUES.items():
            if config["name"] == selected_technique_name:
                st.session_state.selected_technique = key
                break
        
        # Show technique info
        technique_config = PROMPT_TECHNIQUES[st.session_state.selected_technique]
        st.sidebar.info(f"**{technique_config['name']}**: {technique_config['description']}")
    
    # Quick Actions
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.session_state.conversation_count = 0
            st.session_state.total_response_time = 0.0
            st.rerun()
    
    with col2:
        if st.button("📊 Refresh Metrics", use_container_width=True):
            get_system_metrics()
            st.rerun()
    
    # Session Stats
    if st.session_state.messages:
        st.sidebar.markdown("### 📈 Session Stats")
        st.sidebar.metric("Messages", len(st.session_state.messages))
        if st.session_state.conversation_count > 0:
            avg_time = st.session_state.total_response_time / st.session_state.conversation_count
            st.sidebar.metric("Avg Response Time", f"{avg_time:.3f}s")
    
    return True

def display_main_interface():
    """Display main chat interface"""
    # Header
    st.markdown('<h1 class="main-header">🤖 M1 AI Chatbot Hub</h1>', unsafe_allow_html=True)
    
    # Current personality indicator
    personality_config = PERSONALITIES[st.session_state.selected_personality]
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"### Currently chatting with: {personality_config['name']}")
    with col2:
        if st.session_state.show_advanced_options:
            technique_config = PROMPT_TECHNIQUES[st.session_state.selected_technique]
            st.markdown(f"**Technique:** {technique_config['icon']} {technique_config['name']}")
    with col3:
        if st.session_state.current_session_id:
            st.success("🔗 Connected")
        else:
            st.info("💭 New Session")
    
    # Chat Interface
    st.markdown("### 💬 Conversation")
    
    # Display messages
    chat_container = st.container()
    with chat_container:
        if st.session_state.messages:
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>👤 You:</strong><br>{message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>{personality_config['icon']} {personality_config['name']}:</strong><br>{message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show metadata for advanced users
                    if st.session_state.show_advanced_options and "metadata" in message:
                        with st.expander(f"📊 Response #{i//2 + 1} Details"):
                            metadata = message["metadata"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Processing Time", f"{metadata.get('processing_time', 0):.3f}s")
                            with col2:
                                st.metric("Technique", metadata.get('technique', 'standard'))
                            with col3:
                                st.metric("Personality", metadata.get('personality', 'unknown'))
        else:
            # Welcome message and quick starts
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 15px; color: white; margin: 2rem 0;">
                <h3>👋 Welcome to M1 AI Chatbot Hub!</h3>
                <p>I'm your <strong>{personality_config['name']}</strong> - {personality_config['description']}</p>
                <p>Ask me anything about {', '.join(personality_config['capabilities'][:2])} and more!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick start buttons
            st.markdown("### 🚀 Quick Start - Try These Questions:")
            
            cols = st.columns(len(personality_config['sample_questions']))
            for i, question in enumerate(personality_config['sample_questions']):
                with cols[i]:
                    if st.button(f"💡 {question[:30]}...", key=f"quick_{i}", use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": question
                        })
                        st.rerun()
    
    # Message Input
    st.markdown("### ✍️ Send Message")
    
    # Create form for message input
    with st.form("message_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_area(
                "Your message:",
                placeholder=f"Ask {personality_config['name']} anything about {', '.join(personality_config['capabilities'][:2])}...",
                height=100,
                key="message_input"
            )
        
        with col2:
            st.write("")  # Spacing
            submitted = st.form_submit_button("📤 Send", type="primary", use_container_width=True)
    
    # Process message
    if submitted and user_message.strip():
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Show loading indicator
        with st.spinner(f"🤖 {personality_config['name']} is thinking..."):
            # Send to API
            result = send_chat_message(
                user_message, 
                st.session_state.selected_personality,
                st.session_state.selected_technique
            )
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "metadata": {
                        "processing_time": result.get("processing_time", 0),
                        "technique": result.get("technique", "standard"),
                        "personality": result.get("personality", "unknown")
                    }
                })
                
                # Update stats
                st.session_state.conversation_count += 1
                st.session_state.total_response_time += result.get("processing_time", 0)
                
                st.success("✅ Response generated!")
        
        st.rerun()

def display_analytics_page():
    """Display analytics dashboard"""
    st.markdown('<h1 class="main-header">📊 Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.info("🔍 Start a conversation to see analytics!")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card"><h3>Total Messages</h3><h2>{}</h2></div>'.format(len(st.session_state.messages)), unsafe_allow_html=True)
    
    with col2:
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.markdown('<div class="metric-card"><h3>Your Messages</h3><h2>{}</h2></div>'.format(user_messages), unsafe_allow_html=True)
    
    with col3:
        if st.session_state.conversation_count > 0:
            avg_time = st.session_state.total_response_time / st.session_state.conversation_count
            st.markdown('<div class="metric-card"><h3>Avg Response</h3><h2>{:.3f}s</h2></div>'.format(avg_time), unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><h3>Avg Response</h3><h2>0.000s</h2></div>', unsafe_allow_html=True)
    
    with col4:
        personality_name = PERSONALITIES[st.session_state.selected_personality]["name"]
        st.markdown('<div class="metric-card"><h3>Current AI</h3><h2>{}</h2></div>'.format(personality_name.split()[0]), unsafe_allow_html=True)
    
    # Conversation timeline
    if len(st.session_state.messages) > 4:
        st.markdown("### 📈 Conversation Timeline")
        
        # Create timeline data
        timeline_data = []
        for i, msg in enumerate(st.session_state.messages):
            timeline_data.append({
                "Message": i + 1,
                "Role": msg["role"].title(),
                "Length": len(msg["content"]),
                "Type": msg["role"]
            })
        
        df = pd.DataFrame(timeline_data)
        
        # Message length chart
        fig = px.line(
            df, x="Message", y="Length", color="Role",
            title="Message Length Over Time",
            color_discrete_map={"User": "#667eea", "Assistant": "#f093fb"}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Response time analysis (if available)
        response_times = []
        for msg in st.session_state.messages:
            if msg["role"] == "assistant" and "metadata" in msg:
                response_times.append(msg["metadata"].get("processing_time", 0))
        
        if response_times and len(response_times) > 1:
            fig2 = px.bar(
                x=list(range(1, len(response_times) + 1)),
                y=response_times,
                title="Response Time by Message",
                labels={"x": "Response Number", "y": "Processing Time (seconds)"}
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig2, use_container_width=True)

def main():
    """Main application"""
    initialize_session_state()
    
    # Check API status first
    if not display_sidebar():
        st.error("🚨 Cannot connect to API server. Please start it first:")
        st.code("python api_server.py", language="bash")
        return
    
    # Navigation
    page = st.sidebar.radio(
        "Navigate:",
        ["💬 Chat", "📊 Analytics", "🔧 Settings"],
        key="navigation"
    )
    
    if page == "💬 Chat":
        display_main_interface()
    elif page == "📊 Analytics":
        display_analytics_page()
    elif page == "🔧 Settings":
        st.markdown('<h1 class="main-header">🔧 Settings</h1>', unsafe_allow_html=True)
        
        st.markdown("### 🎛️ System Configuration")
        
        with st.expander("🔧 API Configuration", expanded=True):
            st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
            st.info("API server must be running on localhost:8000")
        
        with st.expander("🎨 UI Preferences"):
            st.selectbox("Theme", ["Professional Dark", "Light Mode (Coming Soon)"], disabled=True)
            st.slider("Animation Speed", 0.5, 2.0, 1.0, disabled=True)
        
        with st.expander("📊 Data Export"):
            if st.session_state.messages:
                export_data = {
                    "conversation": st.session_state.messages,
                    "stats": {
                        "total_messages": len(st.session_state.messages),
                        "conversation_count": st.session_state.conversation_count,
                        "total_response_time": st.session_state.total_response_time
                    },
                    "export_time": datetime.now().isoformat()
                }
                
                st.download_button(
                    "📥 Download Conversation",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"chatbot_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No conversation to export yet.")

if __name__ == "__main__":
    main()