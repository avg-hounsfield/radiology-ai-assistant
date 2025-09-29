import streamlit as st
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict
import pandas as pd
import random # Added for placeholder data
import atexit # For cleanup on app shutdown

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add src to path
# sys.path.append(str(Path(__file__).parent.parent)) # Uncomment if your structure requires this

# Inline configuration (no external imports needed)
CORE_EXAM_CONFIG = {
    'exam_areas': {
        'Physics & Safety': {'weight': 15, 'keywords': ['dose', 'radiation', 'kvp', 'technique']},
        'Cardiothoracic': {'weight': 20, 'keywords': ['pneumonia', 'nodules', 'consolidation', 'ground glass']},
        'Neuroradiology': {'weight': 15, 'keywords': ['brain', 'stroke', 'hemorrhage', 'midline shift']},
        'Musculoskeletal (MSK)': {'weight': 10, 'keywords': ['bone', 'fracture', 'marrow edema', 'joint effusion']},
        'Abdominal & Pelvic': {'weight': 15, 'keywords': ['bowel', 'liver', 'enhancement patterns', 'obstruction']},
        'Breast Imaging': {'weight': 8, 'keywords': ['birads', 'mass', 'calcifications']},
        'Pediatric Radiology': {'weight': 7, 'keywords': ['nicu', 'bowing fracture', 'intussusception']},
        'Nuclear Medicine': {'weight': 10, 'keywords': ['pet', 'spect', 'hida', 'v/q scan']}
    }
}

# --- This section can be replaced with your actual RAG system loading ---
# For demonstration purposes, we create a dummy class
class DummyRAGSystem:
    def get_answer(self, query):
        return f"This is a demo response for your query: '{query}'. The real RAG system would provide a detailed answer from its knowledge base."

try:
    # Add the src directory to Python path for imports
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Use your original working RAG system if available
    from retrieval.rag_system import RadiologyRAGSystem
    from study.performance_tracker import PerformanceTracker
    from study.r2_schedule_data import R2_STUDY_SCHEDULE, get_current_rotation, get_current_week
    RAGSystemClass = RadiologyRAGSystem
    SYSTEM_STATUS = "original"
except ImportError as e:
    st.info("📋 Running in demo mode - RAG system not found. You can still explore the interface.")
    RAGSystemClass = DummyRAGSystem
    PerformanceTracker = None
    SYSTEM_STATUS = "demo"
# --------------------------------------------------------------------

# Configure page with ECHO branding
st.set_page_config(
    page_title="ECHO - Radiology CORE Ai", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ECHO Medical UI Theme (Your provided CSS)
def load_echo_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables - ECHO Theme */
    :root {
        --bg-primary: #0B121A;
        --bg-secondary: #111111;
        --bg-card: #1a1f2e;
        --bg-hover: #252a3a;
        --accent-cyan: #00BFFF;
        --accent-blue: #33A1FF;
        --text-primary: #FFFFFF;
        --text-secondary: #EAEAEA;
        --text-muted: #9CA3AF;
        --border-color: #2d3748;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --shadow-glow: 0 0 20px rgba(0, 191, 255, 0.1);
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-secondary);
    }
    
    /* Background Pattern */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 25% 25%, rgba(0, 191, 255, 0.05) 0%, transparent S50%),
            radial-gradient(circle at 75% 75%, rgba(51, 161, 255, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }
    
    /* Main Content Area */
    .main .block-container {
        padding: 2rem 3rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    h2 {
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-card) 0%, rgba(26, 31, 46, 0.95) 100%);
        border-right: 1px solid var(--border-color);
        backdrop-filter: blur(10px);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
        color: var(--text-primary);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 20px rgba(0, 191, 255, 0.3) !important;
        background-color: rgba(26, 31, 46, 0.95) !important;
        transform: translateY(-2px) !important;
    }
    
    .stTextArea > div > div > textarea:hover {
        border-color: rgba(0, 191, 255, 0.5) !important;
        box-shadow: 0 4px 15px rgba(0, 191, 255, 0.1) !important;
    }
    
    /* Remove main-search-container styling - no longer needed */
    
    /* Fuscia ASK ECHO Button - more specific targeting */
    .echo-ask-button .stButton > button,
    .echo-ask-button button[data-testid="baseButton-secondary"] {
        background: var(--bg-primary) !important;
        color: #FF69B4 !important;
        border: 2px solid #FF69B4 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        height: 56px !important;
        box-shadow: 0 0 15px rgba(255, 105, 180, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .echo-ask-button .stButton > button:hover,
    .echo-ask-button button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #FF69B4, #FF1493) !important;
        color: white !important;
        box-shadow: 0 0 25px rgba(255, 105, 180, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    /* ASK ECHO Button in div.stVerticalBlock - same styling as sidebar buttons, 68px height */
    div.stVerticalBlock .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        height: 68px !important;
        min-height: 68px !important;
        max-height: 68px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div.stVerticalBlock .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3) !important;
    }
    
    /* Removed old hover targeting - handled by div.stVerticalBlock above */
    
    /* Additional override for ASK ECHO button - target by key */
    div[data-testid*="ask_main"] button,
    button[data-baseweb*="ask_main"],
    .stButton:has(button[key="ask_main"]) button {
        background: #0B121A !important;
        background-color: #0B121A !important;
        background-image: none !important;
        color: #FF69B4 !important;
        border: 2px solid #FF69B4 !important;
    }
    
    /* All buttons in div.st-emotion-cache-yty0fn.etg4nir4 - uniform styling */
    div.st-emotion-cache-yty0fn.etg4nir4 .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        height: 68px !important;
        min-height: 68px !important;
        max-height: 68px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div.st-emotion-cache-yty0fn.etg4nir4 .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3) !important;
    }
    
    /* All buttons in div.stHorizontalBlock.st-emotion-cache-1permvm.e52wr8w2 - EXACTLY THE SAME */
    div.stHorizontalBlock.st-emotion-cache-1permvm.e52wr8w2 .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        height: 68px !important;
        min-height: 68px !important;
        max-height: 68px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0.75rem 1.5rem !important;
        margin: 0 !important;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2) !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
        line-height: normal !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        box-sizing: border-box !important;
    }
    
    div.stHorizontalBlock.st-emotion-cache-1permvm.e52wr8w2 .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3) !important;
    }
    
    div.stHorizontalBlock.st-emotion-cache-1permvm.e52wr8w2 .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Specific targeting for the shorter buttons */
    button:contains("Random Question"),
    button:contains("Physics Focus"),
    .quick-study-buttons div[data-testid="column"]:first-child button,
    .quick-study-buttons div[data-testid="column"]:nth-child(2) button {
        height: 52px !important;
        min-height: 52px !important;
        max-height: 52px !important;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--text-primary) !important;
        border: none !important;
    }
    
    .quick-study-buttons .stButton > button:hover,
    .quick-study-buttons button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        background-color: var(--accent-blue) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3) !important;
    }
    
    /* Bright blue metric containers */
    .metric-container {
        background: var(--bg-card) !important;
        border: 2px solid #00BFFF !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 10px rgba(0, 191, 255, 0.2) !important;
    }
    
    .metric-container:hover {
        box-shadow: 0 0 20px rgba(0, 191, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Unified Search Interface */
    .unified-search-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 191, 255, 0.05);
    }
    
    .unified-search-container:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 6px 30px rgba(0, 191, 255, 0.1);
    }
    
    .search-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .search-header h2 {
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border: none;
        padding: 0;
        margin-top: 0;
    }
    
    .search-header p {
        color: var(--text-muted);
        font-size: 1rem;
        margin: 0;
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
        min-height: 56px !important;
        max-height: 56px !important;
        resize: none !important;
        line-height: 1.4 !important;
        font-size: 1rem !important;
    }
    
    .search-button-container {
        display: flex;
        align-items: stretch;
    }
    
    .search-button-container button {
        height: 56px !important;
        min-width: 140px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .quick-actions {
        display: flex;
        gap: 8px;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .quick-action-btn {
        background: var(--bg-hover) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }
    
    .quick-action-btn:hover {
        background: var(--accent-cyan) !important;
        border-color: var(--accent-cyan) !important;
        color: var(--text-primary) !important;
    }
    
    /* Custom Card Containers */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .metric-card:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 4px 20px rgba(0, 191, 255, 0.1);
        transform: translateY(-4px);
    }

    .metric-card-icon {
        font-size: 2rem;
        line-height: 1;
        margin-bottom: 1rem;
    }
    .metric-card h3 {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    .metric-card p {
        color: var(--text-muted);
        flex-grow: 1;
        margin-bottom: 1rem;
    }
    .metric-card a {
        color: var(--accent-cyan);
        font-weight: 600;
        text-decoration: none;
    }
    
    .progress-card, .streak-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    
    .progress-card h4, .streak-card h4 {
        margin-top: 0;
        color: var(--text-primary);
    }

    .weak-area-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }
    .weak-area-item:last-child {
        border-bottom: none;
    }
    .weak-area-item .tag {
        background-color: var(--danger);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .streak-meter {
        text-align: center;
    }

    .streak-meter .days {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--accent-cyan);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Make sidebar completely non-collapsible */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 21rem !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        height: 100vh !important;
        z-index: 999 !important;
        transform: translateX(0px) !important;
    }
    
    /* Hide ALL collapse controls and arrows */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapse"],
    button[aria-label*="collapse"],
    button[aria-label*="Close"],
    .css-1544g2n [data-testid="stSidebarNav"] button {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Ensure sidebar content is visible */
    [data-testid="stSidebar"] > div {
        display: block !important;
        visibility: visible !important;
        width: 100% !important;
        padding: 1rem !important;
    }
    
    /* Adjust main content to account for fixed sidebar */
    .main .block-container {
        margin-left: 21rem !important;
        padding-left: 1rem !important;
        padding-right: 2rem !important;
        max-width: calc(100vw - 22rem) !important;
        width: calc(100vw - 22rem) !important;
    }
    
    /* Force all main content containers to respect sidebar */
    .stApp > div:not([data-testid="stSidebar"]) {
        margin-left: 21rem !important;
        width: calc(100vw - 21rem) !important;
    }
    
    /* Target the main content area more specifically */
    div[data-testid="main-content-area"],
    section[data-testid="main-content"] {
        margin-left: 21rem !important;
        width: calc(100vw - 21rem) !important;
    }
    
    /* Clean up - removed main-search-container references */
    
    /* Ensure sidebar inputs work */
    [data-testid="stSidebar"] .stTextArea,
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stDateInput,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stSelectbox {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Ensure only our main search interface is visible */
    .main-search-container {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Medical term highlight styling */
    .medical-term {
        background-color: #FFA500 !important;
        color: #000000 !important;
        font-weight: bold !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .medical-term:hover {
        background-color: #FF8C00 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(255, 165, 0, 0.3) !important;
    }
    
    /* Definition tooltip styling */
    .definition-tooltip {
        position: fixed;
        background: var(--bg-card);
        border: 2px solid #FFA500;
        border-radius: 8px;
        padding: 12px;
        max-width: 400px;
        z-index: 9999;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.4;
    }
    
    .definition-header {
        font-weight: bold;
        color: #FFA500;
        margin-bottom: 6px;
        border-bottom: 1px solid #FFA500;
        padding-bottom: 4px;
    }
    
    .definition-close {
        position: absolute;
        top: 4px;
        right: 8px;
        cursor: pointer;
        color: #FFA500;
        font-weight: bold;
    }
    </style>
    
    <script>
    function showDefinition(term, definition) {
        // Remove any existing tooltips
        const existingTooltip = document.querySelector('.definition-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }
        
        // Create new tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'definition-tooltip';
        tooltip.innerHTML = `
            <div class="definition-close" onclick="this.parentElement.remove()">×</div>
            <div class="definition-header">${term}</div>
            <div>${definition}</div>
        `;
        
        // Position tooltip near cursor (simplified positioning)
        tooltip.style.top = '50%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translate(-50%, -50%)';
        
        document.body.appendChild(tooltip);
        
        // Auto-close after 10 seconds
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, 10000);
    }
    
    // Close tooltip when clicking outside
    document.addEventListener('click', function(event) {
        const tooltip = document.querySelector('.definition-tooltip');
        if (tooltip && !tooltip.contains(event.target) && !event.target.classList.contains('medical-term')) {
            tooltip.remove();
        }
    });
    </script>
    """, unsafe_allow_html=True)

# --- Helper Functions for UI Components ---

def render_sidebar():
    """Renders the main navigation sidebar."""
    with st.sidebar:
        st.markdown("<h1 style='font-size: 2rem; text-align: center; margin-bottom: 1rem;'>ECHO</h1>", unsafe_allow_html=True)
        
        # User Profile
        st.markdown("""
        <div style="background: var(--bg-hover); padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 1.5rem;">
            <p style="margin: 0; font-weight: 600; color: var(--text-primary);">Dr. Matulich</p>
            <p style="margin: 0; font-size: 0.9rem; color: var(--text-muted);">Overall Mastery: 78%</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Study Tools")
        if st.button("Start New Quiz", use_container_width=True):
            # Always start a new quiz when button is clicked
            st.session_state.quiz_mode = True
            st.session_state.quiz_questions = []
            st.session_state.quiz_current_q = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_topic = None
            st.rerun()
        if st.button("Flashcard Decks", use_container_width=True):
            st.session_state.current_mode = "flashcards"
            st.rerun()
        if st.button("Case of the Day", use_container_width=True):
            # Generate a case-based question
            if st.session_state.rag_system:
                try:
                    case_question = "Generate a clinical case presentation with imaging findings for radiology board exam practice"
                    st.session_state.case_question = case_question
                    st.rerun()
                except:
                    st.info("Case generation requires RAG system. Upload documents first!")
            else:
                st.info("Upload radiology materials first to generate cases!")
        
        # Add Random Questions and Physics Focus buttons here
        random_question = st.button("Random Question", key="sidebar_random_q", help="Generate a random CORE exam question", use_container_width=True)
        physics_focus = st.button("Physics Focus", key="sidebar_physics_q", help="Quick physics question", use_container_width=True)
        
        if random_question:
            # Try to use the real question generator
            try:
                if st.session_state.rag_system and hasattr(st.session_state.rag_system, '_init_question_generator'):
                    question_generator = st.session_state.rag_system._init_question_generator()
                    if question_generator and hasattr(question_generator, 'generate_random_question'):
                        return question_generator.generate_random_question()
            except:
                pass
            # Fallback
            import random
            topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
            random_topic = random.choice(topics)
            return f"Generate a CORE exam style question about {random_topic}"
        
        if physics_focus:
            # Try to use the real question generator
            try:
                if st.session_state.rag_system and hasattr(st.session_state.rag_system, '_init_question_generator'):
                    question_generator = st.session_state.rag_system._init_question_generator()
                    if question_generator and hasattr(question_generator, 'generate_physics_question'):
                        return question_generator.generate_physics_question()
            except:
                pass
            # Fallback
            return "What are the key physics principles for CT imaging?"
        
        st.subheader("Core Topics")
        
        # Ensure study_progress is a dictionary (fix if corrupted)
        if 'study_progress' not in st.session_state or not isinstance(st.session_state.study_progress, dict):
            st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
        
        # Double check that all required keys exist
        for topic in CORE_EXAM_CONFIG['exam_areas'].keys():
            if topic not in st.session_state.study_progress:
                st.session_state.study_progress[topic] = 0
        
        for topic in CORE_EXAM_CONFIG['exam_areas'].keys():
            with st.expander(topic):
                weight = CORE_EXAM_CONFIG['exam_areas'][topic]['weight']
                keywords = CORE_EXAM_CONFIG['exam_areas'][topic]['keywords']
                progress = st.session_state.study_progress.get(topic, 0)
                st.write(f"**Weight:** {weight}% of CORE exam")
                st.write(f"**Progress:** {progress}%")
                st.progress(progress / 100)
                st.write(f"**Key areas:** {', '.join(keywords[:3])}...")

        if st.button("📚 R2 Study Schedule", use_container_width=True):
            st.session_state.current_mode = "r2_schedule"
            st.rerun()
        if st.button("Dashboard", use_container_width=True):
            st.session_state.current_mode = "dashboard"
            st.rerun()
        if st.button("History & Review", use_container_width=True):
            st.session_state.current_mode = "history"
            st.rerun()
        
    # Return None by default if no button was clicked
    return None

def metric_card(icon, title, text, link_text="#"):
    """Generates HTML for a dashboard card."""
    return f"""
    <div class="metric-card">
        <div>
            <div class="metric-card-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{text}</p>
        </div>
        <a href="{link_text}" target="_self">Start Now →</a>
    </div>
    """


def render_progress_overview():
    """Renders the personalized focus and study streak sections with real performance data."""
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Get real performance metrics if available
        if st.session_state.performance_tracker:
            try:
                metrics = st.session_state.performance_tracker.get_current_metrics()
                weak_areas = metrics.weak_areas
                
                # Generate ECHO Analysis with real data
                if weak_areas:
                    st.markdown("""
                    <div class="progress-card">
                        <h4>ECHO Analysis</h4>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Based on your recent performance, focus here for the biggest gains:</p>
                    """, unsafe_allow_html=True)
                    
                    for area in weak_areas[:3]:  # Top 3 weak areas
                        accuracy = area['accuracy']
                        color = "var(--danger)" if accuracy < 50 else "var(--warning)" if accuracy < 70 else "var(--success)"
                        st.markdown(f"""
                        <div class="weak-area-item">
                            <span>{area['topic']}</span>
                            <span class="tag" style="background-color: {color};">{accuracy:.0f}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="progress-card">
                        <h4>ECHO Analysis</h4>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Based on your recent performance, focus here for the biggest gains:</p>
                        <div class="weak-area-item">
                            <span style="color: var(--text-muted); font-style: italic;">Start answering questions to see personalized recommendations</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                # Fallback to placeholder on error
                st.markdown("""
                <div class="progress-card">
                    <h4>ECHO Analysis</h4>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Performance tracking initializing...</p>
                    <div class="weak-area-item">
                        <span style="color: var(--text-muted); font-style: italic;">Start studying to see personalized insights</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Fallback for demo mode
            st.markdown("""
            <div class="progress-card">
                <h4>ECHO Analysis</h4>
                <p style="color: var(--text-muted); font-size: 0.9rem;">Performance tracking not available in demo mode</p>
                <div class="weak-area-item">
                    <span style="color: var(--text-muted); font-style: italic;">Upload documents to enable full tracking</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        # Get real streak data if available
        if st.session_state.performance_tracker:
            try:
                streak_info = st.session_state.performance_tracker.get_study_streak_info()
                current_streak = streak_info['current_streak']
                streak_status = streak_info['streak_status']
                
                st.markdown(f"""
                <div class="streak-card">
                    <h4>Your Study Streak</h4>
                    <div class="streak-meter">
                        <div class="days">{current_streak} Days</div>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">{streak_status}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                # Fallback on error
                st.markdown("""
                <div class="streak-card">
                    <h4>Your Study Streak</h4>
                    <div class="streak-meter">
                        <div class="days">0 Days</div>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Start your learning journey today!</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Demo mode fallback
            st.markdown("""
            <div class="streak-card">
                <h4>Your Study Streak</h4>
                <div class="streak-meter">
                    <div class="days">Demo</div>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Upload documents to track progress</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

def highlight_medical_terms(text):
    """Return plain text without any highlighting or HTML - feature disabled"""
    # Simply return the original text without any processing
    # This removes all HTML spans and highlighting
    return text

def render_continue_section():
    """Renders the 'Continue where you left off' list."""
    st.write("**Reading: Abdominal CT Protocols**")
    st.write("A comprehensive guide to abdominal CT protocols.")
    st.progress(80)
    
    st.write("**Quiz: Breast Imaging Fundamentals**") 
    st.write("7/20 questions complete.")
    st.progress(35)

def render_flashcards_mode():
    """Renders the flashcards study mode."""
    st.title("📚 Flashcard Decks")
    
    # Back button
    if st.button("← Back to Main", key="back_from_flashcards"):
        st.session_state.current_mode = "main"
        st.rerun()
    
    # Flashcard topics
    topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Decks")
        for topic in topics[:4]:
            weight = CORE_EXAM_CONFIG['exam_areas'][topic]['weight']
            if st.button(f"{topic} ({weight}% of CORE)", key=f"flashcard_{topic}", use_container_width=True):
                st.session_state.flashcard_topic = topic
                st.session_state.flashcard_mode = True
                st.rerun()
    
    with col2:
        st.subheader("More Decks")
        for topic in topics[4:]:
            weight = CORE_EXAM_CONFIG['exam_areas'][topic]['weight']
            if st.button(f"{topic} ({weight}% of CORE)", key=f"flashcard_{topic}", use_container_width=True):
                st.session_state.flashcard_topic = topic
                st.session_state.flashcard_mode = True
                st.rerun()
    
    st.markdown("---")
    st.info("💡 Tip: Flashcards are generated from your uploaded documents. Upload more materials for better coverage!")

def render_history_mode():
    """Renders the history and review mode."""
    st.title("📖 History & Review")
    
    # Back button
    if st.button("← Back to Main", key="back_from_history"):
        st.session_state.current_mode = "main"
        st.rerun()
    
    # Show conversation history in detail
    if st.session_state.conversation_history:
        # Header with clear all button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"Your Question History ({len(st.session_state.conversation_history)} questions)")
        with col2:
            if st.button("🗑️ Clear All", key="clear_all_history", help="Clear entire conversation history"):
                st.session_state.conversation_history = []
                # Save the cleared state
                if st.session_state.session_manager:
                    st.session_state.session_manager.save_conversation_history([])
                st.success("Conversation history cleared!")
                st.rerun()
        
        # Reverse chronological order
        for i, conv in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(f"Q{len(st.session_state.conversation_history)-i}: {conv['question'][:80]}...", expanded=(i == 0)):
                st.write(f"**Question:** {conv['question']}")
                st.write("**Answer:**")
                # Display answer as plain text without any HTML processing
                st.write(conv['answer'])
                
                if conv.get('sources'):
                    st.write("**Sources:**")
                    for source in conv['sources']:
                        st.write(f"• {os.path.basename(source.get('source', 'Unknown'))}")
                
                timestamp = datetime.fromisoformat(conv['timestamp'])
                st.write(f"*Asked on {timestamp.strftime('%Y-%m-%d at %H:%M')}*")
                
                # Add review buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Ask Similar", key=f"similar_{i}"):
                        similar_question = f"Can you provide more details about: {conv['question']}"
                        st.session_state.review_question = similar_question
                        st.session_state.current_mode = "main"
                        st.rerun()
                with col2:
                    if st.button("Mark for Review", key=f"review_{i}"):
                        if 'marked_for_review' not in st.session_state:
                            st.session_state.marked_for_review = []
                        st.session_state.marked_for_review.append(conv)
                        st.success("Marked for review!")
                with col3:
                    if st.button("Generate Quiz", key=f"quiz_{i}"):
                        # Generate quiz question based on this topic
                        quiz_prompt = f"Generate quiz questions about: {conv['question']}"
                        st.session_state.review_question = quiz_prompt
                        st.session_state.current_mode = "main"
                        st.rerun()
                with col4:
                    if st.button("❌", key=f"delete_{i}", help="Delete this question"):
                        # Find the actual index in the original list (since we're showing reversed)
                        actual_index = len(st.session_state.conversation_history) - 1 - i
                        # Remove the conversation from the list
                        del st.session_state.conversation_history[actual_index]
                        # Save the updated conversation history
                        if st.session_state.session_manager:
                            st.session_state.session_manager.save_conversation_history(st.session_state.conversation_history)
                        st.success("Question deleted!")
                        st.rerun()
    else:
        st.info("No question history yet. Start asking questions to build your study history!")

def render_dashboard_mode():
    """Renders the detailed dashboard mode.""" 
    st.title("📊 Study Dashboard")
    
    # Back button
    if st.button("← Back to Main", key="back_from_dashboard"):
        st.session_state.current_mode = "main"
        st.rerun()
    
    # Detailed metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Study Statistics")
        
        # Performance metrics
        if st.session_state.performance_tracker:
            try:
                metrics = st.session_state.performance_tracker.get_current_metrics()
                
                st.metric("Total Questions", metrics.total_questions_answered)
                st.metric("Overall Accuracy", f"{metrics.overall_accuracy:.1f}%")
                st.metric("Study Hours", f"{metrics.total_study_time_hours:.1f}")
                st.metric("Current Streak", f"{metrics.current_streak} days")
                
                # Weak areas
                if hasattr(metrics, 'weak_areas') and metrics.weak_areas:
                    st.subheader("🎯 Areas for Improvement")
                    for area in metrics.weak_areas[:5]:
                        st.write(f"• {area['topic']}: {area['accuracy']:.0f}% accuracy")
                        
            except Exception as e:
                st.warning(f"Performance tracking not available: {e}")
        else:
            st.info("Performance tracking will be available after uploading documents and answering questions.")
    
    with col2:
        st.subheader("📚 Topic Progress")
        
        # Topic breakdown
        for topic, config in CORE_EXAM_CONFIG['exam_areas'].items():
            progress = st.session_state.study_progress.get(topic, 0)
            weight = config['weight']
            
            st.write(f"**{topic}** ({weight}% of CORE)")
            st.progress(progress / 100)
            st.write(f"Progress: {progress}%")
    
    # Document stats
    st.subheader("📄 Knowledge Base")
    doc_count = len(st.session_state.processed_documents)
    st.metric("Processed Documents", doc_count)
    
    if st.session_state.rag_system and hasattr(st.session_state.rag_system, 'embedding_system'):
        try:
            stats = st.session_state.rag_system.embedding_system.get_collection_stats()
            st.write(f"• Text chunks: {stats.get('text_chunks', 0)}")
            st.write(f"• Total knowledge chunks: {stats.get('total_chunks', 0)}")
        except:
            pass

def render_r2_schedule_mode():
    """Renders the R2 study schedule with interactive lessons and progress tracking."""
    st.title("📚 R2 Radiology Study Schedule")
    
    # Back button
    if st.button("← Back to Main", key="back_from_r2_schedule"):
        st.session_state.current_mode = "main"
        st.rerun()
    
    # Initialize R2 progress tracking if not exists
    if 'r2_lesson_progress' not in st.session_state:
        st.session_state.r2_lesson_progress = {}
    if 'r2_quiz_scores' not in st.session_state:
        st.session_state.r2_quiz_scores = {}
    
    try:
        # Get current rotation
        current_rotation = get_current_rotation()
        current_week = get_current_week(current_rotation["id"])
        
        # Header with current rotation info
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {current_rotation['color']}20, {current_rotation['color']}10); 
                    border-left: 4px solid {current_rotation['color']}; 
                    padding: 1rem; margin: 1rem 0; border-radius: 8px;">
            <h2 style="color: {current_rotation['color']}; margin: 0;">
                {current_rotation['icon']} Current Rotation: {current_rotation['name']}
            </h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">
                Week {current_week} of 4 • {current_rotation['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Rotation Timeline
        st.subheader("📅 Rotation Timeline")
        
        cols = st.columns(5)
        for i, rotation in enumerate(R2_STUDY_SCHEDULE["rotations"][:5]):
            with cols[i]:
                is_current = rotation["id"] == current_rotation["id"]
                bg_color = rotation["color"] if is_current else "#f0f0f0"
                text_color = "white" if is_current else "#666"
                
                st.markdown(f"""
                <div style="background: {bg_color}; color: {text_color}; padding: 0.5rem; 
                           text-align: center; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="font-size: 1.2em;">{rotation['icon']}</div>
                    <div style="font-size: 0.8em; font-weight: bold;">{rotation['abbreviation']}</div>
                    <div style="font-size: 0.7em;">{rotation['start_date'].strftime('%m/%d')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        cols2 = st.columns(5)
        for i, rotation in enumerate(R2_STUDY_SCHEDULE["rotations"][5:]):
            with cols2[i]:
                is_current = rotation["id"] == current_rotation["id"]
                bg_color = rotation["color"] if is_current else "#f0f0f0"
                text_color = "white" if is_current else "#666"
                
                st.markdown(f"""
                <div style="background: {bg_color}; color: {text_color}; padding: 0.5rem; 
                           text-align: center; border-radius: 8px;">
                    <div style="font-size: 1.2em;">{rotation['icon']}</div>
                    <div style="font-size: 0.8em; font-weight: bold;">{rotation['abbreviation']}</div>
                    <div style="font-size: 0.7em;">{rotation['start_date'].strftime('%m/%d')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Current Week's Study Plan
        st.subheader(f"📖 Week {current_week} Study Plan")
        
        # Check if current rotation has detailed schedule
        if current_rotation["id"] == "ir" and "weekly_schedule" in current_rotation:
            render_weekly_schedule(current_rotation, current_week)
        else:
            # Default view for rotations without detailed schedule yet
            st.info(f"""
            📅 **{current_rotation['name']} - Week {current_week}**
            
            Detailed interactive lessons for this rotation are coming soon! 
            
            For now, focus on:
            • {current_rotation['description']}
            • Review relevant textbook chapters
            • Practice questions in this specialty area
            • Correlate with daily cases
            """)
        
        # Progress Overview
        render_r2_progress_overview()
        
    except Exception as e:
        st.error(f"Error loading R2 schedule: {e}")
        st.info("Please check that the R2 schedule data is properly configured.")

def render_weekly_schedule(rotation, current_week):
    """Render the weekly schedule for a rotation with interactive lessons."""
    weekly_schedule = rotation.get("weekly_schedule", {})
    
    for day, day_info in weekly_schedule.items():
        with st.expander(f"📅 {day} - {day_info['title']} ({day_info['duration']})"):
            topics = day_info.get("topics", [])
            
            for topic in topics:
                if topic["week"] == current_week:
                    st.markdown(f"### {topic['title']}")
                    
                    # Lessons checklist
                    st.markdown("**📚 Lessons:**")
                    lessons_completed = 0
                    total_lessons = len(topic["lessons"])
                    
                    for i, lesson in enumerate(topic["lessons"]):
                        lesson_key = f"{rotation['id']}_{day}_{current_week}_{i}"
                        completed = st.session_state.r2_lesson_progress.get(lesson_key, False)
                        
                        col1, col2 = st.columns([0.1, 0.9])
                        with col1:
                            new_completed = st.checkbox("", value=completed, key=f"lesson_{lesson_key}")
                            if new_completed != completed:
                                st.session_state.r2_lesson_progress[lesson_key] = new_completed
                                if st.session_state.session_manager:
                                    # Save progress to persistence
                                    st.session_state.session_manager.save_user_settings({
                                        'r2_lesson_progress': st.session_state.r2_lesson_progress
                                    })
                        with col2:
                            st.write(lesson)
                        
                        if new_completed:
                            lessons_completed += 1
                    
                    # Progress bar for lessons
                    if total_lessons > 0:
                        progress = lessons_completed / total_lessons
                        st.progress(progress)
                        st.caption(f"Completed: {lessons_completed}/{total_lessons} lessons")
                    
                    # Quiz Questions
                    questions = topic.get("questions", [])
                    if questions:
                        st.markdown("---")
                        st.markdown("**🧠 Practice Questions:**")
                        
                        for q_idx, question in enumerate(questions):
                            question_key = f"{rotation['id']}_{day}_{current_week}_q_{q_idx}"
                            
                            with st.container():
                                st.markdown(f"**Question {q_idx + 1}:** {question['question']}")
                                
                                # Multiple choice options
                                selected = st.radio(
                                    "Select your answer:",
                                    question["options"],
                                    key=f"quiz_{question_key}",
                                    index=None
                                )
                                
                                if selected:
                                    if selected == question["correct"]:
                                        st.success(f"✅ Correct! {question['explanation']}")
                                        # Track correct answer
                                        st.session_state.r2_quiz_scores[question_key] = True
                                    else:
                                        st.error(f"❌ Incorrect. The correct answer is: **{question['correct']}**")
                                        st.info(f"💡 {question['explanation']}")
                                        st.session_state.r2_quiz_scores[question_key] = False

def render_r2_progress_overview():
    """Render overall R2 progress overview."""
    st.subheader("📊 Overall Progress")
    
    # Calculate progress statistics
    total_lessons = len(st.session_state.r2_lesson_progress)
    completed_lessons = sum(st.session_state.r2_lesson_progress.values())
    
    total_questions = len(st.session_state.r2_quiz_scores)
    correct_questions = sum(st.session_state.r2_quiz_scores.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Lessons Completed", f"{completed_lessons}/{total_lessons}")
    
    with col2:
        if total_lessons > 0:
            lesson_pct = (completed_lessons / total_lessons) * 100
            st.metric("Lesson Progress", f"{lesson_pct:.1f}%")
        else:
            st.metric("Lesson Progress", "0%")
    
    with col3:
        st.metric("Questions Answered", f"{total_questions}")
    
    with col4:
        if total_questions > 0:
            accuracy = (correct_questions / total_questions) * 100
            st.metric("Quiz Accuracy", f"{accuracy:.1f}%")
        else:
            st.metric("Quiz Accuracy", "N/A")
    
    # Rotation progress
    if total_lessons > 0 or total_questions > 0:
        st.markdown("### 📈 Study Activity")
        
        # Simple progress visualization
        rotations = R2_STUDY_SCHEDULE["rotations"]
        for rotation in rotations:
            rotation_lessons = {k: v for k, v in st.session_state.r2_lesson_progress.items() if k.startswith(rotation["id"])}
            if rotation_lessons:
                completed = sum(rotation_lessons.values())
                total = len(rotation_lessons)
                progress = completed / total if total > 0 else 0
                
                st.markdown(f"**{rotation['icon']} {rotation['name']}**")
                st.progress(progress)
                st.caption(f"{completed}/{total} lessons completed")

def create_simple_search_interface():
    """Creates a simple search interface below the title."""
    # Create the search input row with styling - inline button (no wrapper div)
    col1, col2 = st.columns([4, 1])
    
    with col1:
        question = st.text_area(
            "",
            height=68,
            placeholder="e.g., Show me classic signs of interstitial lung disease, or What are the imaging findings for acute appendicitis?",
            help="Ask specific questions about radiology concepts, imaging findings, or CORE exam topics",
            key="main_search_input",
            label_visibility="collapsed"
        )
    
    with col2:
        ask_button = st.button("ASK ECHO", key="ask_main", help="Search your knowledge base", use_container_width=True)
    
    if ask_button and question.strip():
        return question.strip()
    
    return None

def render_quiz_interface():
    """Renders the quiz interface when in quiz mode."""
    st.markdown("""
    <div style="background: var(--bg-card); border: 2px solid var(--accent-cyan); border-radius: 16px; padding: 2rem; margin: 2rem 0;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: var(--accent-cyan); margin: 0;">CORE Exam Quiz</h2>
            <p style="color: var(--text-muted); margin: 0.5rem 0;">Test your radiology knowledge</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quiz setup if no questions generated yet
    if not st.session_state.quiz_questions:
        st.subheader("Quiz Setup")
        
        col1, col2 = st.columns(2)
        with col1:
            quiz_topic = st.selectbox(
                "Select Topic",
                ["All Topics", "Physics & Safety", "Cardiothoracic", "Neuroradiology", 
                 "Musculoskeletal (MSK)", "Abdominal & Pelvic", "Breast Imaging", 
                 "Pediatric Radiology", "Nuclear Medicine"],
                key="quiz_topic_select"
            )
        
        with col2:
            quiz_length = st.selectbox(
                "Number of Questions",
                [5, 10, 15, 20],
                index=1,
                key="quiz_length_select"
            )
        
        if st.button("Generate Quiz Questions", key="generate_quiz"):
            with st.spinner("Generating quiz questions..."):
                # Generate questions using the RAG system or fallback
                generated_questions = generate_quiz_questions(quiz_topic, quiz_length)
                st.session_state.quiz_questions = generated_questions
                st.session_state.quiz_topic = quiz_topic
                st.session_state.quiz_current_q = 0
                st.session_state.quiz_score = 0
                st.rerun()
        
        if st.button("Exit Quiz", key="exit_quiz_setup"):
            st.session_state.quiz_mode = False
            st.rerun()
    
    else:
        # Display current question
        current_q = st.session_state.quiz_current_q
        total_q = len(st.session_state.quiz_questions)
        
        if current_q < total_q:
            question_data = st.session_state.quiz_questions[current_q]
            
            # Progress indicator
            progress = (current_q + 1) / total_q
            st.progress(progress)
            st.write(f"**Question {current_q + 1} of {total_q}** | Score: {st.session_state.quiz_score}/{current_q if current_q > 0 else 0}")
            
            # Question content
            st.markdown(f"""
            <div style="background: var(--bg-hover); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <h4 style="color: var(--text-primary); margin-top: 0;">{question_data['question']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Answer options
            if 'options' in question_data:
                selected_answer = st.radio(
                    "Select your answer:",
                    question_data['options'],
                    key=f"quiz_answer_{current_q}"
                )
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("Submit Answer", key=f"submit_{current_q}"):
                        # Check if correct
                        correct_answer = question_data.get('correct_answer', question_data['options'][0])
                        is_correct = selected_answer == correct_answer
                        
                        if is_correct:
                            st.session_state.quiz_score += 1
                            st.success("Correct!")
                        else:
                            st.error(f"Incorrect. The correct answer is: {correct_answer}")
                        
                        # Show explanation if available
                        if 'explanation' in question_data:
                            st.write(f"**Explanation:** {question_data['explanation']}")
                        
                        # Track performance
                        if st.session_state.performance_tracker:
                            topics = [st.session_state.quiz_topic] if st.session_state.quiz_topic != "All Topics" else ["General Radiology"]
                            session_id = st.session_state.performance_tracker.start_study_session("quiz")
                            st.session_state.performance_tracker.end_study_session(
                                session_id=session_id,
                                questions_answered=1,
                                questions_correct=1 if is_correct else 0,
                                topics_studied=topics
                            )
                        
                        # Move to next question
                        st.session_state.quiz_current_q += 1
                        st.rerun()
                
                with col2:
                    if st.button("Skip Question", key=f"skip_{current_q}"):
                        st.session_state.quiz_current_q += 1
                        st.rerun()
                
                with col3:
                    if st.button("Exit Quiz", key=f"exit_{current_q}"):
                        st.session_state.quiz_mode = False
                        st.rerun()
            else:
                st.write("Question format error. Please regenerate quiz.")
        
        else:
            # Quiz completed
            final_score = st.session_state.quiz_score
            total_questions = len(st.session_state.quiz_questions)
            percentage = (final_score / total_questions) * 100 if total_questions > 0 else 0
            
            st.markdown(f"""
            <div style="background: var(--bg-card); border: 2px solid var(--success); border-radius: 16px; padding: 2rem; text-align: center;">
                <h2 style="color: var(--success); margin-bottom: 1rem;">Quiz Complete!</h2>
                <div style="font-size: 3rem; font-weight: 700; color: var(--accent-cyan); margin: 1rem 0;">
                    {final_score}/{total_questions}
                </div>
                <div style="font-size: 1.5rem; color: var(--text-primary); margin-bottom: 1rem;">
                    {percentage:.1f}%
                </div>
                <p style="color: var(--text-muted);">
                    {"Excellent work!" if percentage >= 80 else "Good job!" if percentage >= 60 else "Keep studying!"}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Take Another Quiz", key="retake_quiz"):
                    st.session_state.quiz_questions = []
                    st.session_state.quiz_current_q = 0
                    st.session_state.quiz_score = 0
                    st.rerun()
            
            with col2:
                if st.button("Back to Dashboard", key="back_dashboard"):
                    st.session_state.quiz_mode = False
                    st.rerun()

def generate_quiz_questions(topic, num_questions):
    """Generate quiz questions for the specified topic using AI."""
    
    # Try to use the real question generator
    try:
        if st.session_state.rag_system and hasattr(st.session_state.rag_system, '_init_question_generator'):
            question_generator = st.session_state.rag_system._init_question_generator()
            
            if question_generator and hasattr(question_generator, 'generate_quiz_questions'):
                # Get some context from the knowledge base if available
                context_chunks = None
                if st.session_state.rag_system.embedding_system:
                    # Get relevant context for the topic
                    search_query = f"radiology {topic.lower()} imaging findings diagnosis"
                    try:
                        search_results = st.session_state.rag_system.embedding_system.search_similar_texts(search_query, 3)
                        if search_results.get('documents') and search_results['documents'][0]:
                            context_chunks = [
                                {'text': doc, 'metadata': meta} 
                                for doc, meta in zip(
                                    search_results['documents'][0], 
                                    search_results.get('metadatas', [[{}]])[0]
                                )
                            ]
                    except:
                        pass  # Continue without context if search fails
                
                # Generate questions with context
                generated_questions = question_generator.generate_quiz_questions(
                    topic=topic, 
                    num_questions=num_questions,
                    context_chunks=context_chunks
                )
                
                if generated_questions:
                    return generated_questions
    except Exception as e:
        st.warning(f"AI question generation unavailable: {e}")
    
    # Fallback to sample questions
    sample_questions = [
        {
            "question": "What is the most common cause of acute stroke in adults?",
            "options": ["Hemorrhage", "Thrombosis", "Embolism", "Vasculitis"],
            "correct_answer": "Thrombosis",
            "explanation": "Thrombotic stroke accounts for approximately 60-70% of all strokes in adults."
        },
        {
            "question": "Which imaging finding is pathognomonic for pneumonia?",
            "options": ["Ground glass opacities", "Consolidation", "Pleural effusion", "Lymphadenopathy"],
            "correct_answer": "Consolidation",
            "explanation": "Consolidation represents alveolar filling and is the classic finding in bacterial pneumonia."
        },
        {
            "question": "What is the radiation dose limit for the lens of the eye per year?",
            "options": ["15 mSv", "20 mSv", "50 mSv", "150 mSv"],
            "correct_answer": "20 mSv",
            "explanation": "The annual dose limit for the lens of the eye is 20 mSv (150 mSv for the lens was the old limit)."
        },
        {
            "question": "Which MRI sequence is best for detecting acute hemorrhage?",
            "options": ["T1-weighted", "T2-weighted", "FLAIR", "Gradient Echo (GRE)"],
            "correct_answer": "Gradient Echo (GRE)",
            "explanation": "GRE sequences are highly sensitive to blood products due to susceptibility artifacts."
        },
        {
            "question": "What is the typical appearance of a breast fibroadenoma on ultrasound?",
            "options": ["Hypoechoic with irregular margins", "Hyperechoic with shadowing", "Hypoechoic with smooth margins", "Cystic with debris"],
            "correct_answer": "Hypoechoic with smooth margins",
            "explanation": "Fibroadenomas typically appear as well-circumscribed hypoechoic masses on ultrasound."
        }
    ]
    
    # Return a subset based on requested number
    import random
    if num_questions <= len(sample_questions):
        return random.sample(sample_questions, num_questions)
    else:
        # Repeat questions if more requested than available
        questions = sample_questions * (num_questions // len(sample_questions) + 1)
        return questions[:num_questions]

# --- Main App Logic ---

# Apply the custom theme
load_echo_theme()

# Initialize session persistence
try:
    from persistence.session_manager import SessionManager
    
    # Initialize session manager
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    # Auto-save function for cleanup
    def save_session_on_exit():
        """Save session data when app is closing"""
        if hasattr(st.session_state, 'session_manager'):
            session_data = {
                'conversation_history': getattr(st.session_state, 'conversation_history', []),
                'quiz_score': getattr(st.session_state, 'quiz_score', 0),
                'quiz_questions': getattr(st.session_state, 'quiz_questions', []),
                'questions_today': getattr(st.session_state, 'questions_today', 0),
                'current_mode': getattr(st.session_state, 'current_mode', 'main'),
                'demo_mode': getattr(st.session_state, 'demo_mode', True),
                'r2_lesson_progress': getattr(st.session_state, 'r2_lesson_progress', {}),
                'r2_quiz_scores': getattr(st.session_state, 'r2_quiz_scores', {})
            }
            
            # Add performance data if available
            if hasattr(st.session_state, 'performance_tracker') and st.session_state.performance_tracker:
                try:
                    metrics = st.session_state.performance_tracker.get_current_metrics()
                    session_data['performance_data'] = {
                        'total_questions': metrics.total_questions_answered,
                        'correct_answers': metrics.correct_answers,
                        'accuracy': metrics.overall_accuracy,
                        'weak_areas': [{'topic': area['topic'], 'accuracy': area['accuracy']} for area in metrics.weak_areas]
                    }
                except:
                    pass
            
            st.session_state.session_manager.save_all_session_data(session_data)
    
    # Register cleanup function
    atexit.register(save_session_on_exit)
    
except ImportError:
    st.warning("Session persistence not available - data will not be saved between sessions")
    st.session_state.session_manager = None

# Helper function to load/save processed documents
def load_processed_documents():
    """Load processed documents list from persistent storage"""
    try:
        import json
        doc_list_path = "./data/processed_documents.json"
        if os.path.exists(doc_list_path):
            with open(doc_list_path, 'r') as f:
                docs = json.load(f)
                # Filter to only existing files
                return [doc for doc in docs if os.path.exists(doc)]
        return []
    except Exception as e:
        st.warning(f"Could not load document list: {e}")
        return []

def save_processed_documents(doc_list):
    """Save processed documents list to persistent storage"""
    try:
        import json
        os.makedirs("./data", exist_ok=True)
        doc_list_path = "./data/processed_documents.json"
        with open(doc_list_path, 'w') as f:
            json.dump(doc_list, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save document list: {e}")

# Initialize session state at the top level
if 'rag_system' not in st.session_state:
    if RAGSystemClass:
        st.session_state.rag_system = RAGSystemClass()
    else:
        st.session_state.rag_system = None
if 'performance_tracker' not in st.session_state:
    if PerformanceTracker:
        st.session_state.performance_tracker = PerformanceTracker()
    else:
        st.session_state.performance_tracker = None
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
# Load persistent session data on startup
if 'session_data_loaded' not in st.session_state:
    if st.session_state.session_manager:
        try:
            # Load all session data
            saved_data = st.session_state.session_manager.load_all_session_data()
            
            # Initialize conversation history
            st.session_state.conversation_history = saved_data.get('conversation_history', [])
            
            # Initialize quiz and study progress
            st.session_state.quiz_score = saved_data.get('quiz_score', 0)
            st.session_state.quiz_questions = saved_data.get('quiz_questions', [])
            st.session_state.questions_today = saved_data.get('questions_today', 0)
            
            # Initialize study progress - ensure it's always a dictionary
            default_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
            loaded_progress = saved_data.get('study_progress', default_progress)
            
            # Fix if loaded progress is not a dictionary or is empty
            if not isinstance(loaded_progress, dict) or not loaded_progress:
                st.session_state.study_progress = default_progress
            else:
                # Merge with default to ensure all areas are present
                st.session_state.study_progress = default_progress.copy()
                st.session_state.study_progress.update(loaded_progress)
            
            # Initialize user settings
            st.session_state.current_mode = saved_data.get('current_mode', 'main')
            st.session_state.demo_mode = saved_data.get('demo_mode', True)
            
            # Initialize R2 study schedule progress
            st.session_state.r2_lesson_progress = saved_data.get('r2_lesson_progress', {})
            st.session_state.r2_quiz_scores = saved_data.get('r2_quiz_scores', {})
            
            # Load performance data if available
            if 'performance_data' in saved_data and st.session_state.performance_tracker:
                try:
                    # TODO: Restore performance tracker state from saved data
                    pass
                except:
                    pass
                    
            st.session_state.session_data_loaded = True
            
        except Exception as e:
            # Fall back to defaults if loading fails
            st.session_state.conversation_history = []
            st.session_state.quiz_score = 0
            st.session_state.quiz_questions = []
            st.session_state.questions_today = 0
            st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
            st.session_state.current_mode = 'main'
            st.session_state.demo_mode = True
            st.session_state.r2_lesson_progress = {}
            st.session_state.r2_quiz_scores = {}
            st.session_state.session_data_loaded = True
            print(f"Session loading error (using defaults): {e}")
    else:
        # No session manager - use defaults
        st.session_state.conversation_history = []
        st.session_state.quiz_score = 0
        st.session_state.quiz_questions = []
        st.session_state.questions_today = 0
        st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
        st.session_state.current_mode = 'main'
        st.session_state.demo_mode = True
        st.session_state.r2_lesson_progress = {}
        st.session_state.r2_quiz_scores = {}
        st.session_state.session_data_loaded = True

# Ensure these are set if not already loaded
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'processed_documents' not in st.session_state:
    # Load from persistent storage
    st.session_state.processed_documents = load_processed_documents()
if 'study_progress' not in st.session_state:
    st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
if 'exam_date' not in st.session_state:
    st.session_state.exam_date = datetime.now().date() + timedelta(days=180)
if 'questions_today' not in st.session_state:
    st.session_state.questions_today = 0
if "daily_goal" not in st.session_state:
    st.session_state.daily_goal = 10
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = False
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []
if 'quiz_current_q' not in st.session_state:
    st.session_state.quiz_current_q = 0
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'quiz_topic' not in st.session_state:
    st.session_state.quiz_topic = None
if 'r2_lesson_progress' not in st.session_state:
    st.session_state.r2_lesson_progress = {}
if 'r2_quiz_scores' not in st.session_state:
    st.session_state.r2_quiz_scores = {}
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "main"
if 'case_question' not in st.session_state:
    st.session_state.case_question = None

# Top level content moved to main() function

def main():
# ECHO Header removed per user request
    
    # Render the sidebar and capture any question it might return
    sidebar_question = render_sidebar()

    # Main page content
    st.markdown("<p style='color: var(--text-muted);'>Welcome back, Dr. Matulich</p>", unsafe_allow_html=True)
    st.title("What would you like to review today?")

    # Search interface moved here - right below the title
    question = create_simple_search_interface()
    
    # Override question if sidebar button clicked
    if sidebar_question:
        question = sidebar_question

    # Quiz Mode Interface
    if st.session_state.quiz_mode:
        render_quiz_interface()
        return  # Exit early to show only quiz content
    
    # Handle special case question
    if st.session_state.case_question:
        question = st.session_state.case_question
        st.session_state.case_question = None  # Clear it
    
    # Handle review questions from history
    if hasattr(st.session_state, 'review_question') and st.session_state.review_question:
        question = st.session_state.review_question
        st.session_state.review_question = None  # Clear it
    
    # Handle different modes
    if st.session_state.current_mode == "flashcards":
        render_flashcards_mode()
        return
    elif st.session_state.current_mode == "history":
        render_history_mode()
        return
    elif st.session_state.current_mode == "dashboard":
        render_dashboard_mode()
        return
    elif st.session_state.current_mode == "r2_schedule":
        render_r2_schedule_mode()
        return
    
    # Personalized Progress Section
    st.subheader("Your Progress at a Glance")
    render_progress_overview()

    # Add spacing before Continue section
    st.markdown("<br>", unsafe_allow_html=True)

    # Continue Where You Left Off Section - moved to expander
    with st.expander("Continue Where You Left Off", expanded=False):
        render_continue_section()
    
    # Styled metrics with bright blue containers - using real performance data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Documents Processed</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{}</div>
        </div>
        """.format(len(st.session_state.processed_documents)), unsafe_allow_html=True)
    
    with col2:
        # Show total questions answered from performance tracker if available
        total_questions = 0
        if st.session_state.performance_tracker:
            try:
                metrics = st.session_state.performance_tracker.get_current_metrics()
                total_questions = metrics.total_questions_answered
            except:
                total_questions = len(st.session_state.conversation_history)
        else:
            total_questions = len(st.session_state.conversation_history)
            
        st.markdown("""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Questions Answered</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{}</div>
        </div>
        """.format(total_questions), unsafe_allow_html=True)
    
    with col3:
        days_until_exam = (st.session_state.exam_date - datetime.now().date()).days
        st.markdown("""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Days Until CORE</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{}</div>
        </div>
        """.format(max(0, days_until_exam)), unsafe_allow_html=True)
    
    with col4:
        # Show study time instead of daily progress
        total_hours = 0
        if st.session_state.performance_tracker:
            try:
                metrics = st.session_state.performance_tracker.get_current_metrics()
                total_hours = metrics.total_study_time_hours
            except:
                pass
                
        st.markdown("""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Study Hours</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{:.1f}</div>
        </div>
        """.format(total_hours), unsafe_allow_html=True)
    
    # Additional sidebar items in main function to add to what render_sidebar creates
    with st.sidebar:
        # Add Study Settings as accordion
        with st.expander("Study Settings"):
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
        
        # Document Management as accordion - moved to bottom
        with st.expander("Document Management"):
            uploaded_files = st.file_uploader(
                "Upload study materials",
                accept_multiple_files=True,
                type=['pdf', 'ppt', 'pptx'],
                help="Upload PDFs, PowerPoints, and other radiology materials"
            )
            
            if uploaded_files and st.button("Process Documents", key="process_docs"):
                with st.spinner("Processing documents..."):
                    document_paths = []
                    for file in uploaded_files:
                        file_path = f"./data/raw/{file.name}"
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, "wb") as f:
                            f.write(file.read())
                        document_paths.append(file_path)
                    
                    if st.session_state.rag_system is None and RAGSystemClass is not None:
                        st.session_state.rag_system = RAGSystemClass()
                    
                    try:
                        st.session_state.rag_system.process_documents(document_paths)
                        st.session_state.processed_documents.extend(document_paths)
                        # Save to persistent storage
                        save_processed_documents(st.session_state.processed_documents)
                        st.success(f"Processed {len(uploaded_files)} documents!")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            if st.session_state.processed_documents:
                st.write("**Processed Documents:**")
                for doc in st.session_state.processed_documents:
                    st.write(f"• {os.path.basename(doc)}")
        
        # Session Management Controls
        st.markdown("---")
        st.subheader("💾 Session Management")
        
        # Show persistence status
        if st.session_state.session_manager:
            try:
                summary = st.session_state.session_manager.get_data_summary()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Saved Conversations", summary['conversations_count'])
                with col2:
                    total_size = sum([summary.get(f'{name}_size_kb', 0) for name in ['conversations', 'performance', 'quiz', 'settings']])
                    st.metric("Data Size", f"{total_size:.1f} KB")
            except:
                st.info("Session persistence active - data saves automatically")
        else:
            st.warning("⚠️ Session persistence disabled - data will not be saved between sessions")
        
        # Manual save and load buttons
        if st.session_state.session_manager:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Now", key="save_session", use_container_width=True):
                    session_data = {
                        'conversation_history': st.session_state.conversation_history,
                        'quiz_score': getattr(st.session_state, 'quiz_score', 0),
                        'quiz_questions': getattr(st.session_state, 'quiz_questions', []),
                        'questions_today': getattr(st.session_state, 'questions_today', 0),
                        'study_progress': getattr(st.session_state, 'study_progress', {}),
                        'current_mode': getattr(st.session_state, 'current_mode', 'main')
                    }
                    
                    if st.session_state.session_manager.save_all_session_data(session_data):
                        st.success("✅ Session data saved!")
                    else:
                        st.error("❌ Failed to save session data")
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("📂 Load Saved", key="load_session", use_container_width=True):
                    try:
                        saved_data = st.session_state.session_manager.load_all_session_data()
                        st.session_state.conversation_history = saved_data.get('conversation_history', [])
                        st.session_state.quiz_score = saved_data.get('quiz_score', 0)
                        st.session_state.questions_today = saved_data.get('questions_today', 0)
                        st.session_state.study_progress = saved_data.get('study_progress', {})
                        st.success("✅ Session data loaded!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to load session data: {str(e)}")
            
            with col3:
                if st.button("🗑️ Clear All Data", key="clear_all_data", use_container_width=True):
                    if st.session_state.session_manager.clear_all_data():
                        st.session_state.conversation_history = []
                        st.session_state.quiz_score = 0
                        st.session_state.questions_today = 0
                        st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
                        st.success("✅ All data cleared!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear data")
        
        # Clear History (legacy button - now clears current session only)
        st.markdown("---")
        if st.button("Clear Current Session", key="clear_history_main", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.questions_today = 0
            st.rerun()
        
        # Add Clear Documents button (optional - for complete reset)
        if st.button("Clear Documents", key="clear_docs", use_container_width=True, help="Remove all processed documents from memory"):
            if st.session_state.processed_documents:
                st.session_state.processed_documents = []
                save_processed_documents([])  # Clear persistent storage too
                st.success("All document references cleared!")
                st.rerun()
    
    # Handle search response - question is already captured above
    if question:
        # Start a study session if not already active
        if st.session_state.performance_tracker and st.session_state.current_session_id is None:
            st.session_state.current_session_id = st.session_state.performance_tracker.start_study_session("search")
            
        if st.session_state.rag_system:
            with st.spinner("ECHO is thinking..."):
                try:
                    response = st.session_state.rag_system.query(
                        question=question,
                        n_results=5,
                        conversation_history=st.session_state.conversation_history
                    )
                    
                    # Determine if this was answered correctly (simplified - assume all are correct for search)
                    questions_answered = 1
                    questions_correct = 1 if response.get('success', True) else 0
                    
                    # Extract topics from the question for performance tracking
                    topics_studied = []
                    question_lower = question.lower()
                    for area_name, area_info in CORE_EXAM_CONFIG['exam_areas'].items():
                        for keyword in area_info['keywords']:
                            if keyword.lower() in question_lower:
                                topics_studied.append(area_name)
                                break
                    
                    # If no specific topics found, categorize as "General Radiology"
                    if not topics_studied:
                        topics_studied = ["General Radiology"]
                    
                    # Track the performance if tracker is available
                    if st.session_state.performance_tracker and st.session_state.current_session_id:
                        st.session_state.performance_tracker.end_study_session(
                            session_id=st.session_state.current_session_id,
                            questions_answered=questions_answered,
                            questions_correct=questions_correct,
                            topics_studied=topics_studied
                        )
                        # Reset session ID for next question
                        st.session_state.current_session_id = None
                    
                    st.session_state.conversation_history.append({
                        'question': question,
                        'answer': response['answer'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': response.get('sources', [])
                    })
                    
                    # Auto-save conversation history after each question
                    if st.session_state.session_manager:
                        try:
                            st.session_state.session_manager.save_conversation_history(
                                st.session_state.conversation_history
                            )
                        except:
                            pass  # Fail silently if save fails
                    
                    st.session_state.questions_today += 1
                    
                    # Display response with ECHO styling
                    st.markdown('<div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">', unsafe_allow_html=True)
                    st.markdown("**ECHO Response:**")
                    
                    # Display response as plain text
                    st.write(response.get('answer', 'No response generated'))
                    
                    if response.get('sources'):
                        st.markdown("---")
                        st.markdown("**Sources:**")
                        for source in response['sources'][:3]:
                            source_name = os.path.basename(source.get('source', 'Unknown'))
                            st.markdown(f"• {source_name}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please upload study materials first to get AI-powered answers from your documents.")
    
    # Show welcome message or example questions if no documents loaded
    if st.session_state.rag_system is None and not question:
        with st.expander("Example Questions", expanded=False):
            examples = [
                "What are the key physics principles for CT imaging?",
                "Explain the differential diagnosis for pulmonary nodules", 
                "What are the safety considerations for MRI?",
                "Describe the imaging protocol for acute stroke"
            ]
            
            for example in examples:
                st.markdown(f"• {example}")
    
    # Show conversation history
    if st.session_state.conversation_history:
        st.subheader("Recent Questions")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
            with st.expander(f"Q: {conv['question'][:60]}...", expanded=(i == 0)):
                st.write(f"**Question:** {conv['question']}")
                st.write("**Answer:**")
                # Display answer as plain text without any HTML processing
                st.write(conv['answer'])
                
                if conv.get('sources'):
                    st.write("**Sources:**")
                    for source in conv['sources'][:2]:
                        st.write(f"• {os.path.basename(source.get('source', 'Unknown'))}")
                
                timestamp = datetime.fromisoformat(conv['timestamp'])
                st.write(f"*{timestamp.strftime('%Y-%m-%d %H:%M')}*")

if __name__ == "__main__":
    main()