import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
import random # Added for placeholder data

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
    RAGSystemClass = RadiologyRAGSystem
    SYSTEM_STATUS = "original"
except ImportError as e:
    st.info("📋 Running in demo mode - RAG system not found. You can still explore the interface.")
    RAGSystemClass = DummyRAGSystem
    SYSTEM_STATUS = "demo"
# --------------------------------------------------------------------

# Configure page with ECHO branding
st.set_page_config(
    page_title="ECHO - Radiology CORE Ai", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ECHO Medical UI Theme (Clean Original CSS)
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
            radial-gradient(circle at 25% 25%, rgba(0, 191, 255, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(51, 161, 255, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }
    
    /* Main Content Area */
    .main .block-container {
        background: rgba(26, 31, 46, 0.3);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow-glow);
        padding: 2rem;
        margin-top: 1rem;
        margin-left: 21rem;
        width: calc(100vw - 23rem);
        max-width: calc(100vw - 23rem);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar - Always visible and fixed */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-card) 0%, rgba(26, 31, 46, 0.95) 100%);
        border-right: 1px solid var(--border-color);
        backdrop-filter: blur(10px);
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
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Buttons - Clean original styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
        color: var(--text-primary);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2);
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* ASK ECHO Button - Special fuschia styling */
    .main-search-container .stButton > button {
        background: var(--bg-primary) !important;
        color: #FF69B4 !important;
        border: 2px solid #FF69B4 !important;
        font-weight: 700 !important;
        height: 56px !important;
        box-shadow: 0 0 15px rgba(255, 105, 180, 0.3) !important;
    }
    
    .main-search-container .stButton > button:hover {
        background: #FF69B4 !important;
        color: white !important;
        box-shadow: 0 0 25px rgba(255, 105, 180, 0.6) !important;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 2px rgba(0, 191, 255, 0.1) !important;
    }
    
    /* Main search interface */
    .main-search-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .main-search-container:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 4px 20px rgba(0, 191, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* Cards and Containers */
    .element-container .stMarkdown,
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 4px 20px rgba(0, 191, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* Metric containers */
    .metric-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Progress cards */
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
    .css-15zrgzn {display: none;}
    .css-eczf16 {display: none;}
    .css-jn99sy {display: none;}
    </style>
    """, unsafe_allow_html=True)

# [Rest of the functions would be the same as your existing file...]

if __name__ == "__main__":
    load_echo_theme()
    st.write("Clean CSS version - test this to see if it works better")