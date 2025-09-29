# src/ui/radiology_streamlit_app.py
"""
RadReviews-inspired Streamlit interface for Radiology CORE Assistant
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

# Import from local directory
try:
    from medical_config import (
        MEDICAL_MODELS, CORE_EXAM_CONFIG, RADIOLOGY_KEYWORDS, 
        RESPONSE_TEMPLATES, UI_THEME_CONFIG
    )
except ImportError:
    # Create minimal config if file doesn't exist
    CORE_EXAM_CONFIG = {
        'exam_areas': {
            'physics': {'weight': 15, 'keywords': ['dose', 'radiation']},
            'chest': {'weight': 20, 'keywords': ['pneumonia', 'nodules']},
            'cardiac': {'weight': 10, 'keywords': ['heart', 'coronary']},
            'gastrointestinal': {'weight': 15, 'keywords': ['bowel', 'liver']},
            'neuroradiology': {'weight': 15, 'keywords': ['brain', 'stroke']},
            'musculoskeletal': {'weight': 10, 'keywords': ['bone', 'fracture']},
            'genitourinary': {'weight': 8, 'keywords': ['kidney', 'bladder']},
            'interventional': {'weight': 7, 'keywords': ['catheter', 'biopsy']}
        }
    }
    RADIOLOGY_KEYWORDS = {
        'imaging_modalities': ['ct', 'mri', 'xray', 'ultrasound'],
        'core_exam_buzzwords': ['differential diagnosis', 'radiation dose']
    }
    RESPONSE_TEMPLATES = {'case_study_analysis': 'Case Analysis Template'}
    UI_THEME_CONFIG = {'color_scheme': {'primary': '#1e40af', 'secondary': '#059669'}}
    MEDICAL_MODELS = {}

try:
    from retrieval.rag_system import RadiologyRAGSystem
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="RadCore AI - CORE Exam Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - RadReviews inspired design
def load_custom_css():
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #1e40af;
        --secondary-color: #059669;
        --accent-color: #dc2626;
        --background-color: #f8fafc;
        --surface-color: #ffffff;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, var(--primary-color) 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px rgba(30, 64, 175, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .metric-card {
        background: var(--surface-color);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .metric-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.025em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        line-height: 1;
    }
    
    /* Study area styling */
    .study-area {
        background: var(--surface-color);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .study-area-header {
        display: flex;
        justify-content: between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .study-area-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .progress-container {
        background: #f3f4f6;
        border-radius: 8px;
        height: 8px;
        overflow: hidden;
        margin-top: 1rem;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    .progress-excellent { background: var(--secondary-color); }
    .progress-good { background: #fbbf24; }
    .progress-needs-work { background: var(--accent-color); }
    
    /* Question styling */
    .question-container {
        background: var(--surface-color);
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #e5e7eb;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .question-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: var(--text-primary);
        margin-bottom: 1.5rem;
    }
    
    /* Response styling */
    .response-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--secondary-color);
    }
    
    .response-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .response-header::before {
        content: "🤖";
        margin-right: 0.5rem;
    }
    
    /* Source citation styling */
    .source-citation {
        background: #fffbeb;
        border: 1px solid #fbbf24;
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
        font-size: 0.875rem;
    }
    
    .source-citation::before {
        content: "📚 ";
    }
    
    /* Sidebar styling */
    .sidebar-section {
        background: var(--surface-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    
    .sidebar-section h3 {
        color: var(--primary-color);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
    }
    
    /* Button styling */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(30, 64, 175, 0.2);
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
    }
    
    /* Success button */
    .success-button {
        background: var(--secondary-color) !important;
    }
    
    .success-button:hover {
        background: #047857 !important;
    }
    
    /* Alert styling */
    .alert-info {
        background: #dbeafe;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: var(--primary-color);
    }
    
    .alert-success {
        background: #dcfce7;
        border: 1px solid var(--secondary-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: var(--secondary-color);
    }
    
    .alert-warning {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #d97706;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Unified search interface */
    .search-container {
        background: var(--surface-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(30, 64, 175, 0.08);
        border: 2px solid #e0e7ff;
        transition: all 0.3s ease;
    }
    
    .search-container:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 8px 32px rgba(30, 64, 175, 0.15);
    }
    
    .search-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .search-header h2 {
        color: var(--primary-color);
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .search-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
    }
    
    .search-input-row {
        display: flex;
        gap: 12px;
        align-items: stretch;
        margin-bottom: 1.5rem;
    }
    
    .search-input-container {
        flex: 1;
    }
    
    .search-input-container textarea {
        height: 56px !important;
        border-radius: 12px !important;
        border: 2px solid #e5e7eb !important;
        padding: 16px !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        resize: none !important;
        min-height: 56px !important;
        max-height: 56px !important;
        line-height: 1.4 !important;
    }
    
    .search-input-container textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1) !important;
    }
    
    .search-button-primary {
        height: 56px;
        min-width: 140px;
        background: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.2) !important;
    }
    
    .search-button-primary:hover {
        background: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(30, 64, 175, 0.3) !important;
    }
    
    .quick-actions {
        display: flex;
        gap: 8px;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .quick-action-btn {
        background: #f8fafc !important;
        border: 1px solid #e5e7eb !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }
    
    .quick-action-btn:hover {
        background: #e0e7ff !important;
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #1d4ed8;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'processed_documents' not in st.session_state:
        st.session_state.processed_documents = []
    if 'study_progress' not in st.session_state:
        st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
    if 'exam_date' not in st.session_state:
        st.session_state.exam_date = datetime.now().date() + timedelta(days=180)  # 6 months default
    if 'daily_goal' not in st.session_state:
        st.session_state.daily_goal = 5  # questions per day
    if 'questions_today' not in st.session_state:
        st.session_state.questions_today = 0

def create_header():
    st.markdown("""
    <div class="main-header">
        <h1>🏥 RadCore AI</h1>
        <p>Your Intelligent CORE Exam Study Companion</p>
    </div>
    """, unsafe_allow_html=True)

def create_study_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Documents Processed</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(len(st.session_state.processed_documents)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Questions Asked</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(len(st.session_state.conversation_history)), unsafe_allow_html=True)
    
    with col3:
        days_until_exam = (st.session_state.exam_date - datetime.now().date()).days
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Days Until CORE</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(max(0, days_until_exam)), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Today's Progress</div>
            <div class="metric-value">{}/{}</div>
        </div>
        """.format(st.session_state.questions_today, st.session_state.daily_goal), unsafe_allow_html=True)

def create_progress_visualization():
    # Create progress chart for CORE areas
    areas = list(CORE_EXAM_CONFIG['exam_areas'].keys())
    progress = [st.session_state.study_progress.get(area, 0) for area in areas]
    weights = [CORE_EXAM_CONFIG['exam_areas'][area]['weight'] for area in areas]
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Area': [area.replace('_', ' ').title() for area in areas],
        'Progress': progress,
        'Weight': weights,
        'Status': ['Excellent' if p >= 80 else 'Good' if p >= 60 else 'Needs Work' for p in progress]
    })
    
    # Create horizontal bar chart
    fig = px.bar(
        df, 
        x='Progress', 
        y='Area',
        color='Status',
        color_discrete_map={
            'Excellent': '#059669',
            'Good': '#fbbf24', 
            'Needs Work': '#dc2626'
        },
        title="CORE Exam Area Progress",
        labels={'Progress': 'Mastery Level (%)', 'Area': 'Study Areas'}
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, system-ui", size=12)
    )
    
    return fig

def create_sidebar():
    with st.sidebar:
        # Document Management Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 📚 Document Management")
        
        uploaded_files = st.file_uploader(
            "Upload study materials",
            accept_multiple_files=True,
            type=['pdf', 'ppt', 'pptx'],
            help="Upload PDFs, PowerPoints, and other radiology materials"
        )
        
        if uploaded_files and st.button("🔄 Process Documents", key="process_docs"):
            with st.spinner("Processing documents..."):
                document_paths = []
                for file in uploaded_files:
                    file_path = f"./data/raw/{file.name}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                    document_paths.append(file_path)
                
                if st.session_state.rag_system is None:
                    st.session_state.rag_system = RadiologyRAGSystem()
                
                try:
                    st.session_state.rag_system.process_documents(document_paths)
                    st.session_state.processed_documents.extend(document_paths)
                    st.success(f"✅ Processed {len(uploaded_files)} documents!")
                except Exception as e:
                    st.error(f"❌ Error processing documents: {e}")
        
        if st.session_state.processed_documents:
            st.markdown("**📋 Processed Documents:**")
            for doc in st.session_state.processed_documents[-3:]:  # Show last 3
                st.write(f"• {os.path.basename(doc)}")
            if len(st.session_state.processed_documents) > 3:
                st.write(f"... and {len(st.session_state.processed_documents) - 3} more")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Study Settings Section  
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Study Settings")
        
        st.session_state.exam_date = st.date_input(
            "CORE Exam Date",
            value=st.session_state.exam_date,
            min_value=datetime.now().date()
        )
        
        st.session_state.daily_goal = st.slider(
            "Daily Question Goal",
            min_value=1,
            max_value=20,
            value=st.session_state.daily_goal
        )
        
        study_mode = st.selectbox(
            "Study Mode",
            ["Comprehensive Review", "Weak Areas Focus", "Physics Deep Dive", "Case Studies", "Mock Exam"]
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Topic Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 Focus Areas")
        
        selected_areas = []
        for area, config in CORE_EXAM_CONFIG['exam_areas'].items():
            area_name = area.replace('_', ' ').title()
            if st.checkbox(f"{area_name} ({config['weight']}%)", key=f"focus_{area}"):
                selected_areas.append(area)
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_unified_search_interface():
    # Add some top spacing to make search more prominent
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="search-container">
        <div class="search-header">
            <h2>🔍 Ask Your Radiology Question</h2>
            <p>Get instant answers from your study materials and radiology knowledge base</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create the unified search input row
    col1, col2 = st.columns([4, 1])
    
    with col1:
        question = st.text_area(
            "",
            height=56,
            placeholder="e.g., What are the imaging findings and differential diagnosis for a solitary pulmonary nodule on chest CT?",
            help="Ask specific questions about radiology concepts, imaging findings, or CORE exam topics",
            key="unified_search_input",
            label_visibility="collapsed"
        )
    
    with col2:
        # Use container to align button properly
        st.container()
        ask_button = st.button("🔍 Get Answer", key="ask_main", help="Search your knowledge base", use_container_width=True)
    
    # Quick action buttons below the search
    st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🎲 Random Question", key="random_q", help="Generate a random CORE exam question", use_container_width=True):
            import random
            topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
            random_topic = random.choice(topics)
            return f"Generate a CORE exam style question about {random_topic.replace('_', ' ')}"
    
    with col2:
        if st.button("⚡ Physics Focus", key="physics_q", help="Quick physics question", use_container_width=True):
            return "What are the key physics principles for CT imaging?"
    
    with col3:
        if st.button("🫁 Chest Imaging", key="chest_q", help="Chest radiology question", use_container_width=True):
            return "Explain the differential diagnosis for pulmonary nodules"
    
    with col4:
        if st.button("📝 Clear History", key="clear_hist", help="Clear conversation history", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.questions_today = 0
            st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if ask_button and question.strip():
        return question.strip()
    
    return None

def display_response(response_data, question):
    st.markdown('<div class="response-container">', unsafe_allow_html=True)
    st.markdown('<div class="response-header">AI Response</div>', unsafe_allow_html=True)
    
    # Display the answer
    st.markdown(response_data.get('answer', 'No response generated'))
    
    # Display sources if available
    if response_data.get('sources'):
        st.markdown("---")
        st.markdown("**📚 Sources:**")
        for i, source in enumerate(response_data['sources'][:3]):
            source_name = os.path.basename(source.get('source', 'Unknown'))
            st.markdown(f"• {source_name}")
            if source.get('page'):
                st.markdown(f"  *Page {source['page']}*")
            if source.get('slide'):
                st.markdown(f"  *Slide {source['slide']}*")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_conversation_history():
    if not st.session_state.conversation_history:
        return
    
    st.markdown("## 📝 Recent Questions")
    
    # Show last 5 conversations
    recent_conversations = st.session_state.conversation_history[-5:]
    
    for i, conv in enumerate(reversed(recent_conversations)):
        with st.expander(f"Q: {conv['question'][:80]}...", expanded=(i == 0)):
            st.markdown(f"**Question:** {conv['question']}")
            st.markdown("**Answer:**")
            st.markdown(conv['answer'])
            
            if conv.get('sources'):
                st.markdown("**Sources:**")
                for source in conv['sources'][:2]:
                    source_name = os.path.basename(source.get('source', 'Unknown'))
                    st.markdown(f"• {source_name}")
            
            timestamp = datetime.fromisoformat(conv['timestamp'])
            st.markdown(f"*Asked: {timestamp.strftime('%Y-%m-%d %H:%M')}*")

def main():
    load_custom_css()
    init_session_state()
    
    # Header
    create_header()
    
    # Metrics
    create_study_metrics()
    
    # Sidebar
    create_sidebar()
    
    # Main content area
    if st.session_state.rag_system is None:
        # Welcome message with less visual weight
        st.markdown("""
        <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
            <strong>👋 Welcome to RadCore AI!</strong><br>
            Upload your radiology study materials using the sidebar to get started.
        </div>
        """, unsafe_allow_html=True)
        
        # Show the unified search interface even when no documents are loaded
        question = create_unified_search_interface()
        
        if question:
            st.markdown("""
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                📚 <strong>Please upload study materials first</strong><br>
                Use the sidebar to upload PDFs or PowerPoints to get AI-powered answers from your documents.
            </div>
            """, unsafe_allow_html=True)
        
        # Compact example section
        with st.expander("💡 Example Questions", expanded=False):
            examples = [
                "What are the ACR appropriateness criteria for chest pain?",
                "Explain the physics of CT contrast enhancement", 
                "What are the BI-RADS categories and their meanings?",
                "Describe the imaging findings in acute appendicitis"
            ]
            
            for example in examples:
                st.markdown(f"• {example}")
        
        # Progress visualization in expander
        with st.expander("📊 Study Progress Tracker", expanded=False):
            fig = create_progress_visualization()
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        # Main interaction area - unified search interface
        question = create_unified_search_interface()
        
        if question:
            with st.spinner("🔍 Searching knowledge base..."):
                try:
                    response = st.session_state.rag_system.query(
                        question=question,
                        n_results=5,
                        conversation_history=st.session_state.conversation_history
                    )
                    
                    # Update session state
                    st.session_state.conversation_history.append({
                        'question': question,
                        'answer': response['answer'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': response.get('sources', [])
                    })
                    
                    st.session_state.questions_today += 1
                    
                    # Display response
                    display_response(response, question)
                    
                    # Update progress (simple heuristic)
                    for area in CORE_EXAM_CONFIG['exam_areas']:
                        area_keywords = CORE_EXAM_CONFIG['exam_areas'][area].get('keywords', [])
                        if any(keyword in question.lower() for keyword in area_keywords):
                            st.session_state.study_progress[area] = min(100, 
                                st.session_state.study_progress[area] + 2)
                    
                except Exception as e:
                    st.error(f"❌ Error processing question: {e}")
        
        # Show conversation history
        display_conversation_history()
        
        # Progress visualization
        with st.expander("📊 Study Progress Analytics", expanded=False):
            fig = create_progress_visualization()
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()