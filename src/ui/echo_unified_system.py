#!/usr/bin/env python3
"""
ECHO Unified Radiology Study System
Complete platform matching the original ECHO interface design
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import time
import logging
import re
import uuid
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core system imports
from retrieval.rag_system import RadiologyRAGSystem
from study.board_study_system import BoardStudySystem
from study.performance_tracker import PerformanceTracker
from study.spaced_repetition import SpacedRepetitionSystem
from multimedia.video_manager import VideoManager
from multimedia.audio_narrator import AudioNarrator
from study.dictation_system import DictationCaseManager, DictationScorer, DictationCase, DictationAttempt
from multimedia.image_viewer import MedicalImageViewer
# Optional import - may not work on Streamlit Cloud
try:
    from multimedia.image_processor import RadiologyImageManager, RadiologyImage
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSOR_AVAILABLE = False
    RadiologyImageManager = None
    RadiologyImage = None
from study.flashcard_system import FlashcardManager, FlashCard, ReviewSession
from auth.user_system import StreamlitAuth, require_authentication, get_current_user, get_user_profile, update_user_study_progress

# CORE Exam Configuration
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

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="ECHO - Unified Radiology System",
    page_icon="🩻",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_echo_theme():
    """Load the ECHO theme CSS"""
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

    /* Comprehensive Button Color System */

    /* Primary Action Buttons - Green */
    button[kind="primary"], button[data-testid="baseButton-primary"] {
        background: linear-gradient(45deg, #10B981, #059669) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }

    /* Secondary Action Buttons - Blue */
    button[kind="secondary"], button[data-testid="baseButton-secondary"] {
        background: linear-gradient(45deg, #3B82F6, #2563EB) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }

    /* Navigation/Study Buttons - Cyan */
    .study-button button, button[data-button-type="study"] {
        background: linear-gradient(45deg, #06B6D4, #0891B2) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3) !important;
    }

    /* Warning/Alert Buttons - Orange */
    .warning-button button, button[data-button-type="warning"] {
        background: linear-gradient(45deg, #F59E0B, #D97706) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3) !important;
    }

    /* Info/Search Buttons - Purple */
    .info-button button, button[data-button-type="info"] {
        background: linear-gradient(45deg, #8B5CF6, #7C3AED) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3) !important;
    }

    /* Analytics/Stats Buttons - Indigo */
    .analytics-button button, button[data-button-type="analytics"] {
        background: linear-gradient(45deg, #6366F1, #4F46E5) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }

    /* Quick Action Dashboard Buttons - Column Based Colors */
    div[data-testid="column"]:nth-child(1) .stButton > button {
        background: linear-gradient(45deg, #10B981, #059669) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }

    div[data-testid="column"]:nth-child(2) .stButton > button {
        background: linear-gradient(45deg, #3B82F6, #2563EB) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }

    div[data-testid="column"]:nth-child(3) .stButton > button {
        background: linear-gradient(45deg, #F59E0B, #D97706) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3) !important;
    }

    /* Button hover effects */
    .stButton > button:hover, button:hover {
        transform: translateY(-1px) !important;
        filter: brightness(1.1) !important;
        transition: all 0.2s ease !important;
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
            radial-gradient(circle at 25% 25%, rgba(0, 191, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(51, 161, 255, 0.1) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--bg-card);
        border-right: 1px solid var(--border-color);
        box-shadow: var(--shadow-glow);
    }

    /* Cards and Containers */
    .metric-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
    }

    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 191, 255, 0.2);
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        min-height: 48px !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 191, 255, 0.3) !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--bg-card);
        border-radius: 12px;
        padding: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--text-muted);
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
        color: var(--text-primary);
    }

    /* Progress Bars */
    .stProgress > div > div {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
    }

    /* Text Inputs */
    .stTextInput > div > div > input {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 10px rgba(0, 191, 255, 0.3);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }

    .streamlit-expanderContent {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 8px 8px;
    }

    /* Video Container */
    .video-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
    }

    .video-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 191, 255, 0.2);
    }

    /* Chat Message Styling */
    .chat-message {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-glow);
    }

    /* Study Session Container */
    .study-session {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-glow);
    }

    /* Success/Error States */
    .stSuccess {
        background: var(--success);
        border-radius: 8px;
    }

    .stError {
        background: var(--danger);
        border-radius: 8px;
    }

    .stWarning {
        background: var(--warning);
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_systems():
    """Initialize all core systems"""
    try:
        systems = {
            'rag': RadiologyRAGSystem(),
            'board_study': BoardStudySystem(),
            'performance': PerformanceTracker(),
            'spaced_repetition': SpacedRepetitionSystem(),
            'video': VideoManager(),
            'audio': AudioNarrator(),
            'flashcards': FlashcardManager()
        }
        return systems
    except Exception as e:
        st.error(f"Error initializing systems: {e}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if 'systems' not in st.session_state:
        with st.spinner("Initializing ECHO systems..."):
            st.session_state.systems = initialize_systems()

    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = "dashboard"

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = False

    if 'current_question' not in st.session_state:
        st.session_state.current_question = None

    if 'study_progress' not in st.session_state:
        st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}

    if 'exam_date' not in st.session_state:
        st.session_state.exam_date = date.today() + timedelta(days=180)  # 6 months from now

    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

    # Initialize new streamlined modes
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = "study_hub"

    if 'study_submode' not in st.session_state:
        st.session_state.study_submode = "crack_core"

    if 'reference_submode' not in st.session_state:
        st.session_state.reference_submode = "search"

def filter_decks_by_category(all_decks, category_filter):
    """Filter flashcard decks based on radiology category"""
    if category_filter == "All Categories":
        return all_decks

    # Create keywords for each category
    category_keywords = {
        "Cardiothoracic": ["cardio", "thoracic", "chest", "heart", "lung", "pulmonary", "cardiac"],
        "Neuroradiology": ["neuro", "brain", "head", "spine", "neurological", "cranial"],
        "Musculoskeletal (MSK)": ["msk", "musculoskeletal", "bone", "joint", "orthopedic", "spine"],
        "Abdominal & Pelvic": ["abdominal", "abdomen", "pelvic", "pelvis", "gi", "gastrointestinal"],
        "Breast Imaging": ["breast", "mammography", "mammogram"],
        "Pediatric Radiology": ["pediatric", "paediatric", "child", "infant", "baby"],
        "Nuclear Medicine": ["nuclear", "pet", "spect", "scan", "isotope"],
        "Physics & Safety": ["physics", "safety", "radiation", "dose", "protocol"],
        "Interventional Radiology": ["interventional", "intervention", "procedure", "biopsy"],
        "Emergency Radiology": ["emergency", "trauma", "acute", "urgent"]
    }

    keywords = category_keywords.get(category_filter, [])
    filtered_decks = []

    for deck_name in all_decks:
        deck_lower = deck_name.lower()
        if any(keyword in deck_lower for keyword in keywords):
            filtered_decks.append(deck_name)

    return filtered_decks

def filter_videos_by_category(radiology_videos, category_filter):
    """Filter videos based on radiology category"""
    if category_filter == "All Categories":
        return radiology_videos

    # Map category filter to video section names
    category_to_section = {
        "Cardiothoracic": ["Chest", "Cardiac", "Thoracic"],
        "Neuroradiology": ["Neuro", "Brain", "Head", "Spine"],
        "Musculoskeletal (MSK)": ["MSK", "Bone", "Joint", "Orthopedic"],
        "Abdominal & Pelvic": ["Abdomen", "Pelvis", "GI", "Gastrointestinal"],
        "Breast Imaging": ["Breast", "Mammography"],
        "Pediatric Radiology": ["Pediatric", "Child"],
        "Nuclear Medicine": ["Nuclear", "PET", "SPECT"],
        "Physics & Safety": ["Physics", "Safety", "QA"],
        "Interventional Radiology": ["Interventional", "IR"],
        "Emergency Radiology": ["Emergency", "Trauma"]
    }

    target_sections = category_to_section.get(category_filter, [])
    filtered_videos = {}

    for section_name, video_data in radiology_videos.items():
        section_lower = section_name.lower()
        if any(target.lower() in section_lower for target in target_sections):
            filtered_videos[section_name] = video_data

    return filtered_videos

def render_sidebar():
    """Render the streamlined sidebar with two main modes"""
    with st.sidebar:
        st.markdown("### 🩻 ECHO Radiology")

        # Primary mode selection - simplified to two main uses
        st.markdown("#### Choose Your Mode")
        mode = st.radio(
            "Choose Your Mode",
            ["📚 Study Mode", "🔍 Reference Mode"],
            index=0,
            label_visibility="collapsed"
        )

        # Update current mode
        if mode == "📚 Study Mode":
            st.session_state.current_mode = "study_hub"
        elif mode == "🔍 Reference Mode":
            st.session_state.current_mode = "reference_hub"

        st.markdown("---")

        # Mode-specific quick actions
        if st.session_state.current_mode == "study_hub":
            st.markdown("#### 📚 Study Options")

            if st.button("🎯 Crack the Core", type="primary", use_container_width=True):
                st.session_state.study_submode = "crack_core"
                st.rerun()

            if st.button("🃏 Flashcards", type="secondary", use_container_width=True):
                st.session_state.study_submode = "flashcards"
                st.rerun()

            if st.button("📖 Lessons", type="secondary", use_container_width=True):
                st.session_state.study_submode = "lessons"
                st.rerun()

            if st.button("🎥 Video Teaching", type="secondary", use_container_width=True):
                st.session_state.study_submode = "videos"
                st.rerun()

        elif st.session_state.current_mode == "reference_hub":
            st.markdown("#### 🔍 Reference Tools")

            if st.button("🔍 Quick Search", type="primary", use_container_width=True):
                st.session_state.reference_submode = "search"
                st.rerun()

            if st.button("🎯 Differential Dx", type="secondary", use_container_width=True):
                st.session_state.reference_submode = "differential"
                st.rerun()

            if st.button("📄 AJR Articles", type="secondary", use_container_width=True):
                st.session_state.reference_submode = "articles"
                st.rerun()

            if st.button("📊 Imaging Guide", type="secondary", use_container_width=True):
                st.session_state.reference_submode = "imaging_guide"
                st.rerun()

        # Admin-only functions
        user_role = st.session_state.get('user_profile', {}).get('role', 'user')
        if user_role == 'admin':
            st.markdown("---")
            st.markdown("#### 🔧 Admin Functions")

            if st.button("📤 Upload Images", type="secondary", use_container_width=True):
                st.session_state.show_image_upload = True
                st.rerun()

            if st.button("🔄 Scan Directories", type="secondary", use_container_width=True):
                st.session_state.show_directory_scan = True
                st.rerun()

            if st.button("📚 Upload Documents", type="secondary", use_container_width=True):
                st.session_state.show_document_upload = True
                st.rerun()

        st.markdown("---")

        # System Status
        st.markdown("### System Status")
        if st.session_state.systems:
            st.success("✅ All systems operational")

            # Show quick stats
            try:
                videos = st.session_state.systems['video'].scan_local_videos()
                total_videos = sum(len(v) for v in videos.values())
                st.info(f"📹 {total_videos} videos available")

                if st.session_state.systems['performance']:
                    metrics = st.session_state.systems['performance'].get_current_metrics()
                    st.info(f"🎯 {metrics.total_questions_answered} questions answered")
            except:
                pass
        else:
            st.error("❌ System initialization failed")

        st.markdown("---")

        # User Profile Section
        from auth.user_system import auth
        auth.show_user_menu()

        st.markdown("---")

        # Audio Settings
        st.markdown("### Audio Settings")
        audio_enabled = st.checkbox("Enable Audio Narration", value=False)
        if audio_enabled:
            audio_speed = st.slider("Audio Speed", 0.5, 2.0, 1.0, 0.1)
            st.session_state.audio_enabled = True
            st.session_state.audio_speed = audio_speed
        else:
            st.session_state.audio_enabled = False

def create_search_interface():
    """Create the main search interface"""
    st.info("🔍 **Search & Chat Mode**: Ask ECHO any radiology question and get comprehensive answers from your knowledge base. Perfect for clarifying concepts, reviewing specific topics, or getting detailed explanations with source citations.")

    st.markdown("### What would you like to review today?")

    # Search input
    question = st.text_input(
        "Ask ECHO anything about radiology:",
        placeholder="e.g., What are the signs of pneumonia on chest CT?",
        key="main_search"
    )

    # Quick topic buttons - expanded
    st.markdown("#### Quick Topic Access")
    st.markdown("*💡 Click these buttons for focused review sessions on specific radiology subspecialties. Each topic provides comprehensive coverage of key findings, differential diagnoses, and board-relevant concepts.*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🫁 Chest Imaging", use_container_width=True):
            return "Review chest imaging findings and differential diagnoses"
        if st.button("🦴 MSK Imaging", use_container_width=True):
            return "Review musculoskeletal imaging and trauma"

    with col2:
        if st.button("🧠 Neuroradiology", use_container_width=True):
            return "Review neuroradiology findings and pathology"
        if st.button("🤱 Breast Imaging", use_container_width=True):
            return "Review breast imaging and BI-RADS classifications"

    with col3:
        if st.button("🏥 Abdominal Imaging", use_container_width=True):
            return "Review abdominal and pelvic imaging findings"
        if st.button("👶 Pediatric Radiology", use_container_width=True):
            return "Review pediatric imaging and common findings"

    with col4:
        if st.button("⚛️ Physics & Safety", use_container_width=True):
            return "Review radiology physics and safety concepts"
        if st.button("☢️ Nuclear Medicine", use_container_width=True):
            return "Review nuclear medicine and PET imaging"

    # Clinical scenarios
    st.markdown("#### Clinical Scenarios")
    st.markdown("*🎯 Practice with realistic clinical cases and structured learning approaches. These scenarios simulate real radiology workflows with case presentations, differentials, and board-style thinking.*")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚨 Emergency Radiology", use_container_width=True):
            return """
EMERGENCY RADIOLOGY CLINICAL SCENARIO:

CASE PRESENTATION:
25-year-old male presents to ED following high-speed motor vehicle collision. Patient is conscious but complaining of severe chest pain and shortness of breath. Vital signs: BP 90/60, HR 120, O2 sat 88% on room air.

IMAGING APPROACH:
1. Primary Survey: FAST exam shows fluid in hepatorenal recess
2. CT Chest/Abdomen/Pelvis with IV contrast (trauma protocol)
3. Consider CT angiography if aortic injury suspected

KEY EMERGENCY FINDINGS TO IDENTIFY:
• Pneumothorax (tension vs simple)
• Hemothorax and pleural effusions
• Pulmonary contusions and lacerations
• Aortic injury (mediastinal hematoma, direct vessel injury)
• Solid organ injuries (liver, spleen, kidneys)
• Pelvic fractures with hemorrhage
• Traumatic brain injury

CRITICAL ACTIONS:
- Identify life-threatening injuries requiring immediate intervention
- Communicate findings urgently to trauma team
- Distinguish surgical from non-surgical management

BOARD FOCUS AREAS:
- Trauma imaging protocols and timing
- CT vs plain radiograph decision making
- Grading of solid organ injuries
- Signs of active extravasation
- When to call interventional radiology

Please ask follow-up questions about specific emergency scenarios, imaging protocols, or findings you'd like to review in detail.
"""

        if st.button("🔬 Interventional Radiology", use_container_width=True):
            return """
INTERVENTIONAL RADIOLOGY CLINICAL SCENARIO:

CASE PRESENTATION:
68-year-old male with pancreatic adenocarcinoma presents with progressive jaundice and elevated bilirubin (total 8.5 mg/dL). CT shows dilated intrahepatic ducts and common bile duct obstruction at the level of the pancreatic head.

CLINICAL DECISION MAKING:
Patient not a surgical candidate due to locally advanced disease. Needs palliative biliary drainage.

PROCEDURAL OPTIONS:
1. Percutaneous Transhepatic Cholangiography (PTC) with drainage
2. ERCP with stent placement (if anatomy allows)
3. EUS-guided biliary drainage

PRE-PROCEDURE PLANNING:
• Review cross-sectional imaging for anatomy
• Check coagulation studies (INR, platelets)
• Antibiotic prophylaxis
• Conscious sedation vs anesthesia

TECHNICAL CONSIDERATIONS:
- Access route: right vs left hepatic system
- Wire and catheter selection
- Internal vs external drainage
- Stent sizing and type

COMPLICATIONS TO MONITOR:
• Bleeding (hemobilia, intraperitoneal)
• Sepsis and cholangitis
• Bile leak
• Pneumothorax (right-sided access)

POST-PROCEDURE CARE:
- Monitor vital signs and lab values
- External drainage output and character
- Pain management
- Follow-up imaging if needed

BOARD REVIEW POINTS:
- Indications for different drainage approaches
- Anatomy of biliary system
- Complications and management
- When to choose internal vs external drainage

What specific interventional procedures or complications would you like to explore further?
"""

    with col2:
        if st.button("📊 Differential Diagnosis", use_container_width=True):
            return """
DIFFERENTIAL DIAGNOSIS CLINICAL SCENARIO:

CASE PRESENTATION:
45-year-old female presents with 6 months of progressive dyspnea and dry cough. No fever, weight loss, or chest pain. Non-smoker, works in office environment.

INITIAL CHEST X-RAY FINDINGS:
Bilateral lower lobe reticular opacities with honeycombing pattern

SYSTEMATIC APPROACH TO DIFFERENTIAL:

1. PATTERN RECOGNITION:
• Reticulonodular pattern
• Lower lobe predominance
• Honeycombing suggests end-stage fibrosis

2. CATEGORIZE BY ETIOLOGY:
A. IDIOPATHIC:
   - Usual Interstitial Pneumonia (UIP/IPF)
   - Non-specific Interstitial Pneumonia (NSIP)

B. CONNECTIVE TISSUE DISORDERS:
   - Rheumatoid arthritis
   - Scleroderma
   - Polymyositis/dermatomyositis

C. ENVIRONMENTAL/OCCUPATIONAL:
   - Asbestos exposure (asbestosis)
   - Silicosis
   - Chronic hypersensitivity pneumonitis

D. DRUG-INDUCED:
   - Methotrexate
   - Amiodarone
   - Bleomycin

3. NEXT IMAGING STEP:
High-resolution CT chest without contrast

4. HRCT PATTERN ANALYSIS:
• UIP pattern: Honeycombing, traction bronchiectasis, subpleural
• NSIP pattern: Ground glass, fine fibrosis, more symmetric
• Hypersensitivity pneumonitis: Upper lobe, mosaic pattern

5. CLINICAL CORRELATION:
- Detailed occupational/environmental history
- Autoimmune markers
- Pulmonary function tests
- Consider lung biopsy if diagnosis unclear

TEACHING POINTS:
- Pattern recognition drives differential diagnosis
- Location and distribution are key discriminators
- Clinical context narrows radiologic differential
- Multidisciplinary approach often needed

Which pattern or disease would you like to explore in more detail?
"""

        if st.button("📋 Case-Based Learning", use_container_width=True):
            return """
CASE-BASED LEARNING SCENARIO:

CASE 1: ACUTE ABDOMINAL PAIN

CLINICAL PRESENTATION:
32-year-old female presents to ED with sudden onset severe right lower quadrant pain, nausea, and fever (101.2°F). Pain started 8 hours ago and is worsening. Last menstrual period 2 weeks ago.

LABORATORY VALUES:
• WBC: 14,000 (left shift)
• Beta-hCG: Negative
• Urinalysis: Normal

YOUR DIAGNOSTIC APPROACH:
1. What is your next imaging study?
2. What are the top 3 differential diagnoses?
3. What specific findings would you look for?

IMAGING PERFORMED: CT Abdomen/Pelvis with IV contrast

KEY FINDINGS TO IDENTIFY:
• Appendiceal wall thickening (>6mm)
• Periappendiceal fat stranding
• Appendicolith
• Fluid collection (if perforated)
• Alternative diagnoses to exclude

CASE 2: PEDIATRIC RESPIRATORY DISTRESS

CLINICAL PRESENTATION:
2-year-old with 3 days of barking cough, stridor, and difficulty breathing. Parents report child was playing with small toys earlier.

DIFFERENTIAL CONSIDERATIONS:
• Viral croup
• Foreign body aspiration
• Bacterial tracheitis
• Epiglottitis

IMAGING STRATEGY:
- When to use chest X-ray vs CT
- Special considerations in pediatric imaging
- Radiation dose optimization

CASE 3: ELDERLY FALL

CLINICAL PRESENTATION:
78-year-old with fall from standing height, hip pain, unable to bear weight.

IMAGING APPROACH:
• Initial plain radiographs
• When to proceed to MRI or CT
• Occult fracture detection
• Complications to assess

LEARNING OBJECTIVES:
- Develop systematic approach to common presentations
- Practice pattern recognition
- Understand when to escalate imaging
- Consider patient-specific factors (age, pregnancy, radiation exposure)

Which case would you like to work through step by step?
"""

    with col3:
        if st.button("🎯 Board Review", use_container_width=True):
            return """
HIGH-YIELD BOARD REVIEW TOPICS:

CORE EXAM FOCUS AREAS (by percentage):

1. CARDIOTHORACIC (20%):
• Pneumonia patterns and complications
• Pulmonary nodule evaluation (Fleischner criteria)
• Congenital heart disease basics
• Pulmonary embolism protocols
• Interstitial lung disease patterns

2. NEURORADIOLOGY (15%):
• Acute stroke protocols and findings
• Traumatic brain injury grading
• Tumor classification and enhancement patterns
• Hydrocephalus types and causes
• Spine trauma and degenerative disease

3. ABDOMINAL & PELVIC (15%):
• Acute abdomen approach
• Bowel obstruction levels and causes
• Solid organ injury grading
• Adnexal mass characterization
• Hepatic lesion enhancement patterns

4. PHYSICS & SAFETY (15%):
• Radiation dose principles (ALARA)
• CT dose metrics (CTDIvol, DLP)
• MRI safety and contraindications
• Contrast reactions and management
• Pediatric dose optimization

5. MUSCULOSKELETAL (10%):
• Fracture pattern recognition
• Joint effusion vs synovitis
• Bone tumor matrix patterns
• Stress vs pathologic fractures
• Arthritis pattern recognition

6. BREAST IMAGING (8%):
• BI-RADS classification system
• Mammographic densities and implications
• MRI indications and protocols
• Breast cancer staging basics

7. PEDIATRIC (7%):
• Congenital anomalies
• Non-accidental trauma signs
• Developmental hip dysplasia
• Common pediatric masses

8. NUCLEAR MEDICINE (10%):
• Bone scan interpretation
• Thyroid imaging patterns
• Cardiac stress testing
• PET-CT oncologic applications

STUDY STRATEGIES:
- Focus on high-yield, high-frequency topics
- Practice systematic approach to each modality
- Review normal variants vs pathology
- Understand when to use each imaging modality
- Master emergency/urgent findings

BOARD EXAM TIPS:
- Read question carefully for clinical context
- Use process of elimination
- Look for classic patterns and buzzwords
- Consider patient age and demographics
- Don't overthink rare diagnoses

Which topic area would you like to review in detail?
"""

        if st.button("📚 Anatomy Review", use_container_width=True):
            return """
RADIOLOGIC ANATOMY REVIEW:

SYSTEMATIC ANATOMY APPROACH:

1. CHEST ANATOMY:
• Mediastinal compartments (anterior, middle, posterior)
• Pulmonary segments and bronchial anatomy
• Cardiac chambers and great vessels
• Normal measurement standards

KEY MEASUREMENTS:
- Cardiac silhouette: <50% on PA chest X-ray
- Aortic root: <3.7 cm (men), <3.4 cm (women)
- Main pulmonary artery: <2.9 cm

2. ABDOMINAL ANATOMY:
• Hepatic segments (Couinaud classification)
• Pancreatic ductal anatomy
• Biliary tree normal caliber
• Retroperitoneal spaces

NORMAL MEASUREMENTS:
- Common bile duct: <6 mm (<70 years), <8 mm (>70 years)
- Pancreatic duct: <3 mm
- Aorta: <3 cm diameter

3. NEUROANATOMY:
• Ventricular system and CSF spaces
• Circle of Willis anatomy
• Cranial nerve pathways
• Spinal cord segments and tracts

NORMAL VALUES:
- Lateral ventricles: <10 mm (frontal horns)
- Third ventricle: <5 mm
- Cisterna magna: <10 mm

4. MUSCULOSKELETAL ANATOMY:
• Joint spaces and alignment
• Bone landmarks and measurements
• Ligamentous anatomy
• Muscle compartments

NORMAL MEASUREMENTS:
- Joint spaces: >2 mm (knee, hip)
- Atlantodental interval: <3 mm (adults)
- Cervical lordosis: 20-40 degrees

5. DEVELOPMENTAL ANATOMY:
• Ossification centers and timing
• Growth plate appearance and closure
• Organ development patterns
• Age-related normal variants

COMMON ANATOMIC VARIANTS:
- Azygos lobe (chest)
- Hepatic vessel variants
- Renal collecting system duplications
- Accessory ossicles (foot)

PATHOLOGIC vs NORMAL VARIANTS:
Learn to distinguish between:
• Normal developmental variants
• Acquired changes with age
• Early pathologic changes
• Artifact vs anatomy

STUDY APPROACH:
1. Start with normal anatomy
2. Learn measurement standards
3. Recognize common variants
4. Understand age-related changes
5. Practice systematic review

Which anatomic region would you like to focus on for detailed review?
"""

    return question

def render_dashboard():
    """Render the main dashboard"""
    st.markdown("<p style='color: var(--text-muted);'>Welcome back, Dr. Matulich</p>", unsafe_allow_html=True)

    # Helper description for Dashboard
    st.info("📊 **Dashboard Overview**: Track your board preparation progress, daily goals, and quick access to all study modes. Use this as your daily starting point to see where you stand and plan your study session.")

    # Progress Overview
    st.subheader("Your Progress at a Glance")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.session_state.systems and st.session_state.systems['performance']:
            try:
                metrics = st.session_state.systems['performance'].get_current_metrics()
                total_questions = metrics.total_questions_answered
            except:
                total_questions = len(st.session_state.conversation_history)
        else:
            total_questions = len(st.session_state.conversation_history)

        st.markdown(f"""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Questions Answered</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{total_questions}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.session_state.systems:
            videos = st.session_state.systems['video'].scan_local_videos()
            total_videos = sum(len(v) for v in videos.values())
        else:
            total_videos = 0

        st.markdown(f"""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Videos Available</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{total_videos}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        days_until_exam = (st.session_state.exam_date - date.today()).days
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Days Until CORE</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{max(0, days_until_exam)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if st.session_state.systems and st.session_state.systems['performance']:
            try:
                current_streak = st.session_state.systems['performance'].performance_data.get('current_streak', 0)
            except:
                current_streak = 0
        else:
            current_streak = 0

        st.markdown(f"""
        <div class="metric-container">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Study Streak</div>
            <div style="font-size: 2rem; font-weight: 700; color: #00BFFF;">{current_streak} days</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Study Progress by Topic
    st.subheader("CORE Exam Areas Progress")

    # Create progress visualization
    topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
    progress_values = [st.session_state.study_progress.get(topic, 0) for topic in topics]

    # Progress bars
    for i, (topic, progress) in enumerate(zip(topics, progress_values)):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{topic}**")
            st.progress(progress / 100)
        with col2:
            st.write(f"{progress}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Enhanced Dashboard Features
    col1, col2 = st.columns(2)

    with col1:
        # Continue Where You Left Off
        with st.expander("Continue Where You Left Off", expanded=False):
            if st.session_state.conversation_history:
                recent_topics = [msg.get('topic', 'General') for msg in st.session_state.conversation_history[-5:]]
                unique_topics = list(set(recent_topics))

                st.write("Recent study topics:")
                for topic in unique_topics[:3]:
                    if st.button(f"Continue studying {topic}", key=f"continue_{topic}"):
                        st.session_state.current_mode = "study"
                        st.session_state.selected_topic = topic
                        st.rerun()
            else:
                st.write("Start studying to see your recent topics here!")

        # Quick Actions
        with st.expander("Quick Actions", expanded=True):
            st.markdown("*🚀 Jump quickly to different study modes with these color-coded action buttons*")

            # Color legend
            st.markdown("""
            <div style="font-size: 0.8em; margin-bottom: 10px; color: var(--text-muted);">
            🟢 Study & Practice | 🔵 Search & Knowledge | 🟣 Media & Videos | 🟠 Analytics | 🔴 Dictation
            </div>
            """, unsafe_allow_html=True)

            # Use custom HTML buttons with better color control and JavaScript functionality
            st.markdown("""
            <script>
            function navigateToMode(mode, quizMode = false) {
                // Update session state
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    key: 'navigation_action',
                    value: {mode: mode, quiz_mode: quizMode}
                }, '*');
            }
            </script>
            """, unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                # Study actions (Green)
                st.markdown("""
                <button onclick="navigateToMode('study', false)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #10B981, #059669);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    🚀 Start Study Session
                </button>
                """, unsafe_allow_html=True)

                st.markdown("""
                <button onclick="navigateToMode('study', true)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #06B6D4, #0891B2);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    🎯 Random Question
                </button>
                """, unsafe_allow_html=True)

            with col_b:
                # Search & Media actions (Blue/Purple)
                st.markdown("""
                <button onclick="navigateToMode('search', false)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #3B82F6, #2563EB);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    🔍 Search Knowledge
                </button>
                """, unsafe_allow_html=True)

                st.markdown("""
                <button onclick="navigateToMode('videos', false)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #8B5CF6, #7C3AED);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    🎥 Browse Videos
                </button>
                """, unsafe_allow_html=True)

            with col_c:
                # Analytics & Dictation (Orange/Red)
                st.markdown("""
                <button onclick="navigateToMode('analytics', false)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #F59E0B, #D97706);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    📊 View Analytics
                </button>
                """, unsafe_allow_html=True)

                st.markdown("""
                <button onclick="navigateToMode('dictation', false)"
                        style="width: 100%; padding: 12px; margin: 4px 0;
                               background: linear-gradient(45deg, #EF4444, #DC2626);
                               color: white; border: none; border-radius: 6px;
                               font-weight: 600; cursor: pointer;
                               transition: all 0.2s ease;">
                    🩻 Practice Dictation
                </button>
                """, unsafe_allow_html=True)

            # Handle navigation actions
            navigation_action = st.session_state.get('navigation_action')
            if navigation_action:
                st.session_state.current_mode = navigation_action['mode']
                st.session_state.quiz_mode = navigation_action['quiz_mode']
                st.session_state.navigation_action = None  # Clear the action
                st.rerun()


            # Debug info
            if st.checkbox("Show Debug Info", key="debug_dashboard"):
                st.write(f"Current Mode: {st.session_state.get('current_mode', 'None')}")
                st.write(f"Quiz Mode: {st.session_state.get('quiz_mode', False)}")
                st.write(f"Available Systems: {list(st.session_state.get('systems', {}).keys()) if st.session_state.get('systems') else 'None'}")
                st.write(f"Navigation Action: {navigation_action}")

    with col2:
        # Today's Goals
        with st.expander("Today's Study Goals", expanded=True):
            # Get current date
            today = date.today().strftime("%Y-%m-%d")

            # Get today's activity
            if st.session_state.systems and st.session_state.systems['performance']:
                daily_activity = st.session_state.systems['performance'].performance_data.get('daily_activity', {})
                today_data = daily_activity.get(today, {})
                questions_today = today_data.get('total_questions', 0)
                study_time = today_data.get('study_time_minutes', 0)
            else:
                questions_today = 0
                study_time = 0

            # Goals
            question_goal = 20
            time_goal = 60  # minutes

            st.write("📊 **Progress Today:**")

            # Questions progress
            question_progress = min(questions_today / question_goal, 1.0)
            st.write(f"Questions: {questions_today}/{question_goal}")
            st.progress(question_progress)

            # Study time progress
            time_progress = min(study_time / time_goal, 1.0)
            st.write(f"Study Time: {study_time}/{time_goal} minutes")
            st.progress(time_progress)

            if questions_today >= question_goal and study_time >= time_goal:
                st.success("🎉 Daily goals achieved!")
            elif questions_today >= question_goal:
                st.info("🎯 Question goal achieved! Keep studying!")
            elif study_time >= time_goal:
                st.info("⏰ Time goal achieved! Try more questions!")

        # Study Tips
        with st.expander("Study Tips", expanded=False):
            tips = [
                "🧠 Use spaced repetition for better retention",
                "🎧 Try audio mode for hands-free review",
                "📊 Focus on your weak areas",
                "🎥 Watch videos for visual learning",
                "⏰ Take breaks every 45-60 minutes",
                "📝 Review your mistakes regularly"
            ]

            import random
            daily_tip = random.choice(tips)
            st.info(daily_tip)

def render_search_mode():
    """Render search and chat interface"""
    question = create_search_interface()

    if question:
        # Start study session if not active
        if st.session_state.systems and st.session_state.systems['performance'] and not st.session_state.current_session_id:
            st.session_state.current_session_id = st.session_state.systems['performance'].start_study_session("search")

        # Process question
        if st.session_state.systems and st.session_state.systems['rag']:
            with st.spinner("ECHO is thinking..."):
                try:
                    response = st.session_state.systems['rag'].query(
                        question=question,
                        n_results=5,
                        conversation_history=st.session_state.conversation_history
                    )

                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        'question': question,
                        'answer': response,
                        'timestamp': datetime.now().isoformat(),
                        'topic': 'General'  # Could be enhanced with topic detection
                    })

                    # Display response
                    st.markdown('<div class="chat-message">', unsafe_allow_html=True)
                    st.markdown(f"**Question:** {question}")

                    # Format the response properly
                    if isinstance(response, dict):
                        # Extract the answer text
                        answer = response.get('answer', 'No answer provided')
                        st.markdown(f"**ECHO:** {answer}")

                        # Show sources if available
                        sources = response.get('sources', [])
                        if sources:
                            with st.expander("📚 Sources", expanded=False):
                                for i, source in enumerate(sources[:5], 1):  # Show top 5 sources
                                    if source.get('type') == 'flashcard':
                                        # Display flashcard source with link
                                        st.markdown(f"**{i}. 🃏 {source.get('title', 'Flashcard')}**")
                                        st.markdown(f"   Content: {source.get('content', '')}")

                                        # Tags display
                                        tags = source.get('tags', [])
                                        if tags:
                                            tags_str = ', '.join(tags[:3])  # Show first 3 tags
                                            st.markdown(f"   Tags: {tags_str}")

                                        # Button to jump to flashcard mode
                                        if st.button(f"🎯 Study this flashcard", key=f"flashcard_{i}", type="secondary"):
                                            st.session_state.current_mode = "flashcards"
                                            st.session_state.selected_flashcard = source.get('card_id')
                                            st.rerun()
                                    elif source.get('type') == 'image':
                                        # Display image source with thumbnail
                                        st.markdown(f"**{i}. 🖼️ {source.get('title', 'Medical Image')}**")

                                        # Display image thumbnail if file exists
                                        image_path = source.get('file_path', '')
                                        if image_path and os.path.exists(image_path):
                                            try:
                                                col1, col2 = st.columns([1, 3])
                                                with col1:
                                                    st.image(image_path, width=100)
                                                with col2:
                                                    st.markdown(f"   Modality: **{source.get('modality', 'Unknown')}**")
                                                    st.markdown(f"   Body Part: **{source.get('body_part', 'Unknown')}**")

                                                    # Tags display
                                                    tags = source.get('tags', [])
                                                    if tags:
                                                        tags_str = ', '.join(tags[:3])  # Show first 3 tags
                                                        st.markdown(f"   Tags: {tags_str}")
                                            except Exception as e:
                                                st.markdown(f"   Image: {os.path.basename(image_path)} (preview unavailable)")
                                                st.markdown(f"   Modality: **{source.get('modality', 'Unknown')}**")
                                                st.markdown(f"   Body Part: **{source.get('body_part', 'Unknown')}**")
                                        else:
                                            st.markdown(f"   Image: {source.get('file_path', 'Unknown')}")
                                            st.markdown(f"   Modality: **{source.get('modality', 'Unknown')}**")
                                    else:
                                        # Regular document source
                                        st.markdown(f"**{i}.** {source.get('filename', 'Unknown source')}")
                                        if source.get('section'):
                                            st.markdown(f"   Section: {source['section']}")
                                        if source.get('medical_relevance'):
                                            st.markdown(f"   Relevance: {source['medical_relevance']}/5")
                    else:
                        # Fallback for string responses
                        st.markdown(f"**ECHO:** {response}")

                    st.markdown('</div>', unsafe_allow_html=True)

                    # Audio playback option
                    if st.session_state.get('audio_enabled', False):
                        if st.button("🔊 Play Response", type="secondary"):
                            try:
                                # Extract text for audio
                                audio_text = response
                                if isinstance(response, dict):
                                    audio_text = response.get('answer', str(response))

                                audio_file = st.session_state.systems['audio'].generate_audio_file(
                                    audio_text, "response_audio.mp3"
                                )
                                if audio_file:
                                    st.audio(audio_file)
                            except Exception as e:
                                st.error(f"Audio generation failed: {e}")

                except Exception as e:
                    st.error(f"Error processing question: {e}")

    # Show conversation history
    if st.session_state.conversation_history:
        st.subheader("Recent Conversations")

        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(f"Q: {conv['question'][:50]}..."):
                st.write(f"**Question:** {conv['question']}")

                # Format answer properly
                answer = conv['answer']
                if isinstance(answer, dict):
                    answer = answer.get('answer', 'No answer provided')
                st.write(f"**Answer:** {answer}")

                st.write(f"**Time:** {conv['timestamp']}")

def render_study_mode():
    """Render study questions interface"""
    st.info("📚 **Study Questions Mode**: Practice CORE-style board questions with immediate feedback and explanations. Choose specific topics or let ECHO select questions based on your weak areas. Features spaced repetition for optimal retention.")

    st.subheader("Board Study Session")

    # Topic selection
    topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
    selected_topic = st.selectbox("Select Topic", topics)

    # Study mode options
    study_mode = st.selectbox(
        "Study Mode",
        ["Practice Questions", "Timed Session", "Weak Areas Focus", "Random Review"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Study Session", type="primary", use_container_width=True):
            if st.session_state.systems and st.session_state.systems['board_study']:
                try:
                    # Start performance tracking session
                    if st.session_state.systems['performance'] and not st.session_state.current_session_id:
                        st.session_state.current_session_id = st.session_state.systems['performance'].start_study_session("practice")

                    # Generate question
                    question_data = st.session_state.systems['board_study'].generate_board_question(selected_topic)
                    st.session_state.current_question = question_data
                    st.session_state.selected_topic = selected_topic
                    st.session_state.quiz_mode = True
                    st.success(f"Study session started for {selected_topic}!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error starting study session: {e}")
                    # Try to generate a simple question
                    try:
                        from study.board_study_system import BoardStudySystem
                        study_system = BoardStudySystem()
                        question_data = study_system.generate_board_question(selected_topic)
                        st.session_state.current_question = question_data
                        st.session_state.quiz_mode = True
                        st.rerun()
                    except Exception as e2:
                        st.error(f"Failed to generate question: {e2}")
            else:
                st.error("Study system not available")

    with col2:
        if st.button("Quick Random Question", type="secondary", use_container_width=True):
            try:
                # Pick random topic
                import random
                topics = list(CORE_EXAM_CONFIG['exam_areas'].keys())
                random_topic = random.choice(topics)

                # Generate question
                if st.session_state.systems and st.session_state.systems['board_study']:
                    question_data = st.session_state.systems['board_study'].generate_board_question(random_topic)
                    st.session_state.current_question = question_data
                    st.session_state.selected_topic = random_topic
                    st.session_state.quiz_mode = True
                    st.rerun()
                else:
                    st.error("Study system not available")
            except Exception as e:
                st.error(f"Error generating question: {e}")

    # Active study session
    if st.session_state.quiz_mode:
        render_quiz_interface()

def render_quiz_interface():
    """Render the quiz interface"""
    st.markdown('<div class="study-session">', unsafe_allow_html=True)

    # Generate question if needed
    if not st.session_state.current_question and st.session_state.systems:
        try:
            topic = st.session_state.get('selected_topic', 'Cardiothoracic')
            question_data = st.session_state.systems['board_study'].generate_board_question(topic)
            st.session_state.current_question = question_data
        except Exception as e:
            st.error(f"Error generating question: {e}")
            st.session_state.quiz_mode = False
            st.rerun()
            return

    if st.session_state.current_question:
        question = st.session_state.current_question

        # Display question
        st.markdown("### Question")
        st.write(question.get('question', 'Question not available'))

        # Audio for question
        if st.session_state.get('audio_enabled', False):
            if st.button("🔊 Play Question", type="secondary"):
                try:
                    audio_file = st.session_state.systems['audio'].generate_audio_file(
                        question.get('question', ''), "question_audio.mp3"
                    )
                    if audio_file:
                        st.audio(audio_file)
                except Exception as e:
                    st.error(f"Audio generation failed: {e}")

        # Options
        options = question.get('options', [])
        if options:
            st.markdown("### Answer Choices")
            answer_choice = st.radio("Select your answer:", options, key="quiz_answer")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Submit Answer", type="primary"):
                    st.session_state.answer_submitted = True
                    st.session_state.selected_answer = answer_choice
                    st.rerun()

            with col2:
                if st.button("Skip Question", type="secondary"):
                    st.session_state.current_question = None
                    st.rerun()

            with col3:
                if st.button("End Session", type="secondary"):
                    st.session_state.quiz_mode = False
                    st.session_state.current_question = None
                    if 'answer_submitted' in st.session_state:
                        del st.session_state.answer_submitted
                    st.success("Study session completed!")
                    st.rerun()

            # Show answer if submitted
            if st.session_state.get('answer_submitted', False):
                correct_answer = question.get('correct_answer', '')
                explanation = question.get('explanation', 'No explanation available.')
                selected_answer = st.session_state.get('selected_answer', '')

                is_correct = selected_answer == correct_answer

                if is_correct:
                    st.success(f"✅ Correct! The answer is: {correct_answer}")
                else:
                    st.error(f"❌ Incorrect. The correct answer is: {correct_answer}")
                    st.write(f"You selected: {selected_answer}")

                st.markdown("### Explanation")
                st.write(explanation)

                # Audio for explanation
                if st.session_state.get('audio_enabled', False):
                    if st.button("🔊 Play Explanation", type="secondary"):
                        try:
                            audio_file = st.session_state.systems['audio'].generate_audio_file(
                                explanation, "explanation_audio.mp3"
                            )
                            if audio_file:
                                st.audio(audio_file)
                        except Exception as e:
                            st.error(f"Audio generation failed: {e}")

                # Record performance
                if st.session_state.systems and st.session_state.systems['performance']:
                    try:
                        st.session_state.systems['performance'].record_question_result(
                            question.get('topic', 'General'),
                            is_correct,
                            question.get('difficulty', 'medium')
                        )
                    except Exception as e:
                        st.error(f"Error recording performance: {e}")

                # Next question
                if st.button("Next Question", type="primary"):
                    st.session_state.current_question = None
                    st.session_state.answer_submitted = False
                    if 'selected_answer' in st.session_state:
                        del st.session_state.selected_answer
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def clean_video_title(filename):
    """Clean up video filename to create a readable title (fallback for legacy videos)"""
    # Remove extension
    title = os.path.splitext(filename)[0]

    # Remove common prefixes and clean up
    title = re.sub(r'^[0-9]+[\-\._\s]*', '', title)  # Remove leading numbers
    title = re.sub(r'^boardsbuster[\-\._\s]*[0-9]*[\-\._\s]*', '', title, flags=re.IGNORECASE)  # Remove boardsbuster prefix
    title = re.sub(r'^boards?[\-\._\s]*buster[\-\._\s]*[0-9]*[\-\._\s]*', '', title, flags=re.IGNORECASE)  # Boards Buster variations
    title = re.sub(r'^lecture[\-\._\s]*[0-9]*[\-\._\s]*', '', title, flags=re.IGNORECASE)  # Lecture prefix
    title = re.sub(r'^video[\-\._\s]*[0-9]*[\-\._\s]*', '', title, flags=re.IGNORECASE)  # Video prefix
    title = re.sub(r'^[^a-zA-Z]*', '', title)  # Remove leading non-letters

    # Replace separators with spaces
    title = re.sub(r'[\-\._]+', ' ', title)

    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title)

    # Capitalize words properly
    title = title.strip().title()

    # Fix common medical terms that should stay uppercase
    medical_terms = {
        'Ct': 'CT', 'Mri': 'MRI', 'Xray': 'X-ray', 'Pet': 'PET', 'Spect': 'SPECT',
        'Us': 'US', 'Msk': 'MSK', 'Gi': 'GI', 'Gu': 'GU', 'Ob': 'OB', 'Gyn': 'GYN',
        'Birads': 'BI-RADS', 'Hida': 'HIDA', 'Vq': 'V/Q', 'Mr': 'MR', 'Dr': 'Dr.',
        'Md': 'MD', 'Facr': 'FACR'
    }

    for old, new in medical_terms.items():
        title = re.sub(r'\b' + old + r'\b', new, title)

    return title if title else filename

def categorize_videos_by_radiology_section(videos):
    """Categorize videos by radiology sections"""
    radiology_sections = {
        'Neuroradiology': {
            'keywords': ['neuro', 'brain', 'spine', 'head', 'neck', 'stroke', 'tumor', 'ct head', 'mri brain'],
            'videos': []
        },
        'Chest': {
            'keywords': ['chest', 'lung', 'thoracic', 'pneumonia', 'pulmonary', 'cardiac', 'heart'],
            'videos': []
        },
        'Abdomen': {
            'keywords': ['abdomen', 'liver', 'pancreas', 'bowel', 'gi', 'stomach', 'kidney', 'pelvis'],
            'videos': []
        },
        'Musculoskeletal': {
            'keywords': ['msk', 'bone', 'fracture', 'joint', 'arthritis', 'spine', 'shoulder', 'knee'],
            'videos': []
        },
        'Breast Imaging': {
            'keywords': ['breast', 'mammo', 'birads', 'mammography'],
            'videos': []
        },
        'Pediatrics': {
            'keywords': ['peds', 'pediatric', 'child', 'infant', 'neonatal', 'congenital'],
            'videos': []
        },
        'Nuclear Medicine': {
            'keywords': ['nuclear', 'pet', 'spect', 'bone scan', 'thyroid scan', 'cardiac nuclear'],
            'videos': []
        },
        'Physics': {
            'keywords': ['physics', 'safety', 'radiation', 'dose', 'technique', 'quality'],
            'videos': []
        },
        'Interventional': {
            'keywords': ['interventional', 'ir', 'angio', 'embolization', 'biopsy'],
            'videos': []
        },
        'Ultrasound': {
            'keywords': ['ultrasound', 'doppler', 'echo', 'ob', 'vascular'],
            'videos': []
        },
        'General': {
            'keywords': [],
            'videos': []
        }
    }

    # Categorize each video
    for category, video_list in videos.items():
        for video in video_list:
            filename_lower = video['filename'].lower()
            categorized = False

            for section, data in radiology_sections.items():
                if section == 'General':
                    continue

                for keyword in data['keywords']:
                    if keyword in filename_lower:
                        radiology_sections[section]['videos'].append(video)
                        categorized = True
                        break

                if categorized:
                    break

            # If not categorized, put in General
            if not categorized:
                radiology_sections['General']['videos'].append(video)

    # Remove empty sections
    return {section: data for section, data in radiology_sections.items() if data['videos']}

def render_video_mode():
    """Render video library interface"""
    st.info("🎥 **Video Library Mode**: Access your complete collection of radiology videos organized by subspecialty. Videos are automatically categorized (Neuro, Chest, Abdomen, etc.) and you can generate practice questions based on video content for enhanced learning.")

    st.subheader("Video Learning Center")

    # Get category filter from session state
    category_filter = st.session_state.get('selected_category', 'All Categories')

    if category_filter != "All Categories":
        st.info(f"📋 Filtering videos for: **{category_filter}**")

    if not st.session_state.systems:
        st.error("Video system not available")
        return

    # Scan for videos
    videos = st.session_state.systems['video'].scan_local_videos()

    if not any(videos.values()):
        st.warning("No videos found. Add videos to data/videos/ directories.")
        return

    # Categorize videos by radiology section
    radiology_videos = categorize_videos_by_radiology_section(videos)

    # Filter videos based on category selection
    if category_filter != "All Categories":
        filtered_videos = filter_videos_by_category(radiology_videos, category_filter)
    else:
        filtered_videos = radiology_videos

    # Filters
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Filters")

        # Radiology section filter - use filtered videos
        sections = list(filtered_videos.keys())
        selected_section = st.selectbox("Radiology Section", ["All"] + sections)

        # Search filter
        search_term = st.text_input("Search videos", placeholder="Enter keywords...")

        # Stats
        total_videos = sum(len(data['videos']) for data in filtered_videos.values())
        st.info(f"📹 {total_videos} videos available")

    with col2:
        st.markdown("### Available Videos")

        # Filter videos by section
        if selected_section == "All":
            sections_to_show = filtered_videos
        else:
            sections_to_show = {selected_section: filtered_videos[selected_section]}

        # Apply search filter
        if search_term:
            filtered_sections = {}
            for section, data in sections_to_show.items():
                filtered_videos = [
                    video for video in data['videos']
                    if search_term.lower() in video['filename'].lower() or
                       search_term.lower() in clean_video_title(video['filename']).lower()
                ]
                if filtered_videos:
                    filtered_sections[section] = {'videos': filtered_videos}
            sections_to_show = filtered_sections

        # Display videos by section
        if not sections_to_show:
            st.info("No videos found matching your criteria.")
            return

        for section, data in sections_to_show.items():
            video_list = data['videos']

            if not video_list:
                continue

            # Section header
            with st.expander(f"📂 {section} ({len(video_list)} videos)", expanded=True):

                # Show videos in a more organized way
                for i, video in enumerate(video_list[:20]):  # Limit to 20 per section
                    st.markdown('<div class="video-container">', unsafe_allow_html=True)

                    col_info, col_action = st.columns([4, 1])

                    with col_info:
                        # Enhanced video title display
                        title = video.get('title', clean_video_title(video['filename']))
                        st.markdown(f"**{title}**")

                        # Create metadata display
                        metadata_parts = []

                        # Speaker information
                        if video.get('speaker'):
                            metadata_parts.append(f"👨‍⚕️ **{video['speaker']}**")

                        # Series and video number
                        series_info = []
                        if video.get('series'):
                            series_info.append(video['series'])
                        if video.get('video_number'):
                            series_info.append(f"#{video['video_number']}")
                        if series_info:
                            metadata_parts.append(f"📺 {' - '.join(series_info)}")

                        # Duration
                        if video.get('duration_formatted'):
                            metadata_parts.append(f"⏱️ {video['duration_formatted']}")

                        # Difficulty and topics
                        if video.get('difficulty') and video['difficulty'] != 'intermediate':
                            difficulty_colors = {'Basic': '🟢', 'Intermediate': '🟡', 'Advanced': '🔴'}
                            color = difficulty_colors.get(video['difficulty'], '🟡')
                            metadata_parts.append(f"{color} {video['difficulty']}")

                        # Topics
                        if video.get('topics'):
                            topics_str = ", ".join(video['topics'][:3])  # Show first 3 topics
                            if len(video['topics']) > 3:
                                topics_str += f" +{len(video['topics']) - 3} more"
                            metadata_parts.append(f"🏷️ {topics_str}")

                        # Display metadata
                        if metadata_parts:
                            for part in metadata_parts:
                                st.caption(part)

                        # File details (smaller, less prominent)
                        size_mb = 0
                        if 'size_mb' in video:
                            size_mb = video['size_mb']
                        elif 'file_size' in video:
                            size_mb = video['file_size'] / (1024 * 1024)

                        file_details = f"📁 {video['filename']} • 💾 {size_mb:.1f} MB"
                        st.caption(file_details, help="Original filename and file size")

                    with col_action:
                        if st.button("▶️ View", key=f"view_{section}_{i}", type="secondary", use_container_width=True):
                            st.session_state.selected_video = video
                            st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

                if len(video_list) > 20:
                    st.info(f"Showing first 20 videos. Use search to find specific content.")

        # Quick section navigation
        st.markdown("### Quick Navigation")
        nav_cols = st.columns(len(sections))
        for i, section in enumerate(sections):
            with nav_cols[i]:
                count = len(radiology_videos[section]['videos'])
                if st.button(f"{section}\n({count})", key=f"nav_{section}", type="secondary", use_container_width=True):
                    # Update selectbox (this is a workaround for programmatic selectbox update)
                    st.session_state.selected_section = section
                    st.rerun()

    # Video details
    if hasattr(st.session_state, 'selected_video') and st.session_state.selected_video:
        video = st.session_state.selected_video

        st.markdown("---")
        st.subheader(f"Video: {video['filename']}")

        # Handle different path formats
        file_path = video.get('file_path', video.get('path', 'Unknown'))
        st.info(f"📁 Location: {file_path}")

        # Handle different size formats
        size_mb = 0
        if 'size_mb' in video:
            size_mb = video['size_mb']
        elif 'file_size' in video:
            size_mb = video['file_size'] / (1024 * 1024)

        st.write(f"📊 Size: {size_mb:.1f} MB")

        category = video.get('category', 'Unknown')
        st.write(f"📂 Category: {category}")

        if st.button("📁 Open Folder", type="secondary"):
            import subprocess
            try:
                folder_path = Path(file_path).parent
                subprocess.run(f'explorer "{folder_path}"', shell=True)
            except Exception as e:
                st.error(f"Could not open folder: {e}")

        # Generate related questions
        if st.button("Generate Practice Questions for This Topic", type="primary"):
            try:
                question = st.session_state.systems['board_study'].generate_board_question(video['category'])
                st.session_state.video_question = question
                st.rerun()
            except Exception as e:
                st.error(f"Error generating question: {e}")

        # Show video question
        if hasattr(st.session_state, 'video_question'):
            question = st.session_state.video_question

            st.markdown("### Related Practice Question")
            st.write(question.get('question', ''))

            options = question.get('options', [])
            if options:
                answer = st.radio("Your answer:", options, key="video_question_answer")

                if st.button("Check Answer", type="primary"):
                    correct = question.get('correct_answer', '')
                    if answer == correct:
                        st.success(f"✅ Correct! {question.get('explanation', '')}")
                    else:
                        st.error(f"❌ Incorrect. Correct answer: {correct}")
                        st.write(question.get('explanation', ''))

def render_analytics_mode():
    """Render analytics and progress tracking"""
    st.info("📊 **Analytics Mode**: Monitor your board preparation progress with detailed performance metrics. Track accuracy by topic, identify weak areas, view study streaks, and get data-driven insights to optimize your study strategy.")

    st.subheader("Study Analytics & Progress")

    if not st.session_state.systems or not st.session_state.systems['performance']:
        st.error("Analytics system not available")
        return

    try:
        # Get performance data
        perf_data = st.session_state.systems['performance'].performance_data

        # Overall metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_questions = perf_data.get('total_questions_answered', 0)
            correct_questions = perf_data.get('total_questions_correct', 0)

            if total_questions > 0:
                accuracy = (correct_questions / total_questions) * 100
            else:
                accuracy = 0

            # Accuracy gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=accuracy,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Accuracy"},
                delta={'reference': 70},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#00BFFF"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            current_streak = perf_data.get('current_streak', 0)
            longest_streak = perf_data.get('longest_streak', 0)

            st.metric("Current Streak", f"{current_streak} days")
            st.metric("Longest Streak", f"{longest_streak} days")
            st.metric("Total Questions", total_questions)

        with col3:
            total_time = perf_data.get('total_study_time_minutes', 0)
            hours = total_time // 60
            minutes = total_time % 60

            st.metric("Total Study Time", f"{hours}h {minutes}m")
            st.metric("Questions Correct", correct_questions)
            if total_questions > 0:
                st.metric("Accuracy Rate", f"{accuracy:.1f}%")

        # Topic performance
        st.subheader("Performance by Topic")

        topics_performance = perf_data.get('topics_performance', {})
        if topics_performance:
            topic_data = []
            for topic, data in topics_performance.items():
                questions_answered = data.get('questions_answered', 0)
                questions_correct = data.get('questions_correct', 0)
                accuracy = (questions_correct / max(questions_answered, 1)) * 100

                topic_data.append({
                    'Topic': topic,
                    'Questions': questions_answered,
                    'Accuracy': accuracy,
                    'Correct': questions_correct
                })

            if topic_data:
                df = pd.DataFrame(topic_data)

                # Bar chart
                fig = px.bar(df, x='Topic', y='Accuracy',
                           title="Accuracy by Topic",
                           color='Accuracy',
                           color_continuous_scale='blues')
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Data table
                st.dataframe(df, use_container_width=True)
        else:
            st.info("Complete some practice questions to see topic-specific analytics.")

        # Daily activity
        st.subheader("Daily Study Activity")

        daily_activity = perf_data.get('daily_activity', {})
        if daily_activity:
            activity_data = []
            for date_str, data in daily_activity.items():
                activity_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Questions': data.get('total_questions', 0),
                    'Study Time': data.get('study_time_minutes', 0),
                    'Topics': len(data.get('topics_studied', []))
                })

            if activity_data:
                df = pd.DataFrame(activity_data)
                df = df.sort_values('Date').tail(14)  # Last 14 days

                fig = px.line(df, x='Date', y='Questions',
                            title="Daily Question Practice",
                            markers=True)
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Start studying to see your daily activity here!")

    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def render_dictation_mode():
    """Render practice dictation mode"""
    st.info("🩻 **Practice Dictation Mode**: Master radiology reporting skills with realistic cases. View medical images, write findings and impressions, then get AI-powered scoring with detailed feedback. Perfect for developing professional dictation skills and board preparation.")

    st.markdown("## 🩻 Practice Dictation")
    st.markdown("Practice radiology reporting with real cases and AI-powered scoring")

    try:
        # Initialize dictation components
        if 'dictation_manager' not in st.session_state:
            st.session_state.dictation_manager = DictationCaseManager()
            st.session_state.dictation_scorer = DictationScorer()
            st.session_state.image_viewer = MedicalImageViewer()

        dictation_manager = st.session_state.dictation_manager
        dictation_scorer = st.session_state.dictation_scorer
        image_viewer = st.session_state.image_viewer

        # Create tabs for different dictation features
        tab1, tab2, tab3 = st.tabs(["📋 Practice Cases", "📊 My Performance", "➕ Add Case"])

        with tab1:
            render_dictation_practice(dictation_manager, dictation_scorer, image_viewer)

        with tab2:
            render_dictation_performance(dictation_manager)

        with tab3:
            render_add_dictation_case(dictation_manager)

    except Exception as e:
        st.error(f"Error loading dictation mode: {e}")
        logging.error(f"Dictation mode error: {e}")

def render_dictation_practice(dictation_manager, dictation_scorer, image_viewer):
    """Render the main dictation practice interface"""

    # Case selection
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("### Select Practice Case")

    with col2:
        modality_filter = st.selectbox(
            "Filter by Modality:",
            ["All", "XR", "CT", "MR", "US", "NM"],
            key="dictation_modality_filter"
        )

    with col3:
        difficulty_filter = st.selectbox(
            "Difficulty:",
            ["All", "Basic", "Intermediate", "Advanced"],
            key="dictation_difficulty_filter"
        )

    # Get filtered cases
    cases = dictation_manager.get_cases_by_modality(None if modality_filter == "All" else modality_filter)
    if difficulty_filter != "All":
        cases = [case for case in cases if case.difficulty == difficulty_filter]

    if not cases:
        st.warning("No cases available with the selected filters.")
        return

    # Case selection
    case_titles = [f"{case.title} ({case.modality} - {case.difficulty})" for case in cases]
    selected_case_index = st.selectbox("Choose a case:", range(len(case_titles)), format_func=lambda x: case_titles[x])

    selected_case = cases[selected_case_index]

    # Display case details
    st.markdown("---")

    # Create layout: Image viewer on left, dictation on right
    col_image, col_dictation = st.columns([3, 2])

    with col_image:
        st.markdown("### 🖼️ Medical Images")

        # Case information
        with st.expander("📋 Case Information", expanded=True):
            st.markdown(f"**Title:** {selected_case.title}")
            st.markdown(f"**Modality:** {selected_case.modality}")
            st.markdown(f"**Body Part:** {selected_case.body_part}")
            st.markdown(f"**Clinical History:** {selected_case.clinical_history}")
            st.markdown(f"**Difficulty:** {selected_case.difficulty}")

        # Image viewer
        if selected_case.images:
            # Initialize image viewer if needed
            if 'current_dictation_case' not in st.session_state or st.session_state.current_dictation_case != selected_case.case_id:
                st.session_state.current_dictation_case = selected_case.case_id
                image_viewer.load_images(selected_case.images)

            # Image controls
            col_prev, col_info, col_next = st.columns([1, 2, 1])

            with col_prev:
                if st.button("⬅️ Previous", disabled=image_viewer.current_index <= 0):
                    image_viewer.previous_image()
                    st.rerun()

            with col_info:
                if image_viewer.get_image_count() > 0:
                    st.markdown(f"**Image {image_viewer.current_index + 1} of {image_viewer.get_image_count()}**")

            with col_next:
                if st.button("➡️ Next", disabled=image_viewer.current_index >= image_viewer.get_image_count() - 1):
                    image_viewer.next_image()
                    st.rerun()

            # Display current image
            if image_viewer.get_image_count() > 0:
                # Image adjustment controls
                with st.expander("🔧 Image Adjustments"):
                    col_bright, col_contrast = st.columns(2)
                    with col_bright:
                        brightness = st.slider("Brightness", 0.5, 2.0, 1.0, 0.1, key="brightness")
                    with col_contrast:
                        contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.1, key="contrast")

                # Get and display image
                image_b64 = image_viewer.get_image_base64(
                    max_width=600, max_height=500,
                    brightness=brightness, contrast=contrast
                )

                if image_b64:
                    st.markdown(
                        f'<img src="{image_b64}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Unable to display image. Please check the image file exists.")
            else:
                st.warning("No images available for this case.")
        else:
            st.info("This case has no associated images. Practice with the clinical history provided.")

    with col_dictation:
        st.markdown("### ✍️ Your Dictation")

        # Initialize session state for dictation
        if 'dictation_findings' not in st.session_state:
            st.session_state.dictation_findings = ""
        if 'dictation_impression' not in st.session_state:
            st.session_state.dictation_impression = ""
        if 'dictation_submitted' not in st.session_state:
            st.session_state.dictation_submitted = False
        if 'dictation_start_time' not in st.session_state:
            st.session_state.dictation_start_time = time.time()

        # Reset if new case
        if 'last_dictation_case' not in st.session_state or st.session_state.last_dictation_case != selected_case.case_id:
            st.session_state.dictation_findings = ""
            st.session_state.dictation_impression = ""
            st.session_state.dictation_submitted = False
            st.session_state.dictation_start_time = time.time()
            st.session_state.last_dictation_case = selected_case.case_id

        if not st.session_state.dictation_submitted:
            # Dictation input
            st.markdown("**FINDINGS:**")
            findings = st.text_area(
                "Describe the findings systematically:",
                value=st.session_state.dictation_findings,
                height=200,
                placeholder="Describe what you see in a systematic manner...",
                key="dictation_findings_input"
            )
            st.session_state.dictation_findings = findings

            st.markdown("**IMPRESSION:**")
            impression = st.text_area(
                "Provide your diagnostic impression:",
                value=st.session_state.dictation_impression,
                height=100,
                placeholder="Your diagnostic impression and recommendations...",
                key="dictation_impression_input"
            )
            st.session_state.dictation_impression = impression

            # Timer
            elapsed_time = int(time.time() - st.session_state.dictation_start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            st.markdown(f"**Time elapsed:** {minutes:02d}:{seconds:02d}")

            # Submit button
            col_submit, col_clear = st.columns(2)

            with col_submit:
                if st.button("📝 Submit Dictation", type="primary", use_container_width=True):
                    if findings.strip() and impression.strip():
                        # Score the dictation
                        findings_score, impression_score, feedback = dictation_scorer.score_dictation(
                            findings, impression,
                            selected_case.ground_truth_findings,
                            selected_case.ground_truth_impression
                        )

                        overall_score = (findings_score + impression_score) / 2

                        # Save attempt
                        attempt = DictationAttempt(
                            attempt_id=str(uuid.uuid4()),
                            case_id=selected_case.case_id,
                            user_findings=findings,
                            user_impression=impression,
                            timestamp=datetime.now().isoformat(),
                            findings_score=findings_score,
                            impression_score=impression_score,
                            overall_score=overall_score,
                            feedback=feedback,
                            time_taken_seconds=elapsed_time
                        )

                        dictation_manager.save_attempt(attempt)

                        # Store results in session state
                        st.session_state.dictation_results = {
                            'findings_score': findings_score,
                            'impression_score': impression_score,
                            'overall_score': overall_score,
                            'feedback': feedback,
                            'time_taken': elapsed_time,
                            'ground_truth_findings': selected_case.ground_truth_findings,
                            'ground_truth_impression': selected_case.ground_truth_impression
                        }

                        st.session_state.dictation_submitted = True
                        st.rerun()
                    else:
                        st.error("Please provide both findings and impression before submitting.")

            with col_clear:
                if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                    st.session_state.dictation_findings = ""
                    st.session_state.dictation_impression = ""
                    st.session_state.dictation_start_time = time.time()
                    st.rerun()

        else:
            # Show results
            st.markdown("### 📋 Your Results")

            results = st.session_state.dictation_results

            # Score display
            col_score1, col_score2, col_score3 = st.columns(3)

            with col_score1:
                st.metric("Findings Score", f"{results['findings_score']:.1%}")

            with col_score2:
                st.metric("Impression Score", f"{results['impression_score']:.1%}")

            with col_score3:
                overall_color = "green" if results['overall_score'] >= 0.8 else "orange" if results['overall_score'] >= 0.6 else "red"
                st.metric("Overall Score", f"{results['overall_score']:.1%}")

            # Time taken
            minutes, seconds = divmod(results['time_taken'], 60)
            st.markdown(f"**Time taken:** {minutes:02d}:{seconds:02d}")

            # Feedback
            st.markdown("### 📝 Detailed Feedback")

            for section, feedback_text in results['feedback'].items():
                if section == "findings":
                    st.markdown(f"**Findings:** {feedback_text}")
                elif section == "impression":
                    st.markdown(f"**Impression:** {feedback_text}")
                elif section == "overall":
                    st.markdown(f"**Overall:** {feedback_text}")

            # Show ground truth in expander
            with st.expander("📚 Ground Truth Comparison"):
                st.markdown("**Ground Truth Findings:**")
                st.text_area("", value=results['ground_truth_findings'], height=150, disabled=True, key="gt_findings")

                st.markdown("**Ground Truth Impression:**")
                st.text_area("", value=results['ground_truth_impression'], height=80, disabled=True, key="gt_impression")

            # Action buttons
            col_new, col_retry = st.columns(2)

            with col_new:
                if st.button("🆕 New Case", type="primary", use_container_width=True):
                    # Reset for new case
                    st.session_state.dictation_submitted = False
                    st.session_state.dictation_findings = ""
                    st.session_state.dictation_impression = ""
                    st.session_state.dictation_start_time = time.time()
                    if 'dictation_results' in st.session_state:
                        del st.session_state.dictation_results
                    st.rerun()

            with col_retry:
                if st.button("🔄 Retry Case", type="secondary", use_container_width=True):
                    # Reset for retry
                    st.session_state.dictation_submitted = False
                    st.session_state.dictation_findings = ""
                    st.session_state.dictation_impression = ""
                    st.session_state.dictation_start_time = time.time()
                    if 'dictation_results' in st.session_state:
                        del st.session_state.dictation_results
                    st.rerun()

def render_dictation_performance(dictation_manager):
    """Render dictation performance analytics"""
    st.markdown("### 📊 Your Dictation Performance")

    attempts = dictation_manager.get_user_attempts()

    if not attempts:
        st.info("No dictation attempts yet. Start practicing to see your progress here!")
        return

    # Performance statistics
    stats = dictation_manager.get_user_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Attempts", stats['total_attempts'])

    with col2:
        st.metric("Average Score", f"{stats['average_score']:.1%}")

    with col3:
        st.metric("Best Score", f"{stats['best_score']:.1%}")

    with col4:
        improvement_delta = f"{stats['improvement_trend']:.1%}" if stats['improvement_trend'] != 0 else None
        st.metric("Recent Average", f"{stats['recent_average']:.1%}", delta=improvement_delta)

    # Score trends
    if len(attempts) > 1:
        st.markdown("### 📈 Score Trends")

        df_attempts = pd.DataFrame([{
            'attempt': i+1,
            'overall_score': attempt.overall_score,
            'findings_score': attempt.findings_score,
            'impression_score': attempt.impression_score,
            'timestamp': attempt.timestamp
        } for i, attempt in enumerate(attempts)])

        fig = px.line(df_attempts, x='attempt', y=['overall_score', 'findings_score', 'impression_score'],
                     title="Score Progression Over Time",
                     labels={'value': 'Score', 'attempt': 'Attempt Number'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Recent attempts
    st.markdown("### 📋 Recent Attempts")

    recent_attempts = attempts[-10:]  # Last 10 attempts

    for i, attempt in enumerate(reversed(recent_attempts)):
        case = dictation_manager.get_case(attempt.case_id)
        case_title = case.title if case else "Unknown Case"

        with st.expander(f"Attempt {len(attempts) - i}: {case_title} - {attempt.overall_score:.1%}"):
            col_info, col_scores = st.columns([2, 1])

            with col_info:
                st.markdown(f"**Case:** {case_title}")
                st.markdown(f"**Date:** {attempt.timestamp[:19].replace('T', ' ')}")
                minutes, seconds = divmod(attempt.time_taken_seconds, 60)
                st.markdown(f"**Time:** {minutes:02d}:{seconds:02d}")

            with col_scores:
                st.markdown(f"**Overall:** {attempt.overall_score:.1%}")
                st.markdown(f"**Findings:** {attempt.findings_score:.1%}")
                st.markdown(f"**Impression:** {attempt.impression_score:.1%}")

def render_add_dictation_case(dictation_manager):
    """Render interface to add new dictation cases"""
    st.markdown("### ➕ Add New Dictation Case")
    st.markdown("Expand your practice library with custom cases")

    with st.form("add_dictation_case"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Case Title*", placeholder="e.g., Chest X-ray - Pneumonia")
            modality = st.selectbox("Modality*", ["XR", "CT", "MR", "US", "NM", "Other"])
            body_part = st.selectbox("Body Part*", ["Chest", "Abdomen", "Head", "Spine", "Extremities", "Pelvis", "Other"])

        with col2:
            difficulty = st.selectbox("Difficulty*", ["Basic", "Intermediate", "Advanced"])
            tags = st.text_input("Tags (comma-separated)", placeholder="pneumonia, consolidation, infection")

        clinical_history = st.text_area("Clinical History*", height=100,
                                      placeholder="Patient age, gender, presenting symptoms, and relevant history...")

        # Image upload
        st.markdown("**Images (optional)**")
        uploaded_files = st.file_uploader("Upload medical images",
                                        accept_multiple_files=True,
                                        type=['jpg', 'jpeg', 'png', 'dcm', 'dicom'])

        ground_truth_findings = st.text_area("Ground Truth Findings*", height=200,
                                           placeholder="Systematic description of findings...")

        ground_truth_impression = st.text_area("Ground Truth Impression*", height=100,
                                             placeholder="Diagnostic impression and recommendations...")

        submitted = st.form_submit_button("💾 Add Case", type="primary")

        if submitted:
            if title and modality and body_part and clinical_history and ground_truth_findings and ground_truth_impression:
                # Handle image files
                image_paths = []
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        # Save uploaded file
                        file_path = Path("data/dictation_images") / uploaded_file.name
                        file_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        image_paths.append(str(file_path))

                # Create new case
                new_case = DictationCase(
                    case_id=f"custom_{int(time.time())}",
                    title=title,
                    modality=modality,
                    body_part=body_part,
                    clinical_history=clinical_history,
                    images=image_paths,
                    ground_truth_findings=ground_truth_findings,
                    ground_truth_impression=ground_truth_impression,
                    difficulty=difficulty,
                    tags=tags.split(',') if tags else [],
                    created_date=datetime.now().isoformat()
                )

                dictation_manager.add_case(new_case)

                st.success(f"✅ Successfully added new case: {title}")
                st.balloons()

            else:
                st.error("Please fill in all required fields (marked with *)")

def render_flashcard_mode():
    """Render the flashcard study mode with Anki-style spaced repetition"""
    st.markdown("# 🃏 Flashcard Study Mode")

    # Get category filter from session state
    category_filter = st.session_state.get('selected_category', 'All Categories')

    if category_filter != "All Categories":
        st.info(f"📋 Filtering flashcards for: **{category_filter}**")

    st.info("**Anki-Style Spaced Repetition Learning** - Review imported flashcards with intelligent scheduling for optimal retention")

    flashcard_manager = st.session_state.systems.get('flashcards')

    if not flashcard_manager:
        st.error("Flashcard system not available")
        return

    # Get deck statistics
    all_decks = flashcard_manager.get_all_decks()

    # Filter decks based on category selection
    if category_filter != "All Categories":
        filtered_decks = filter_decks_by_category(all_decks, category_filter)
    else:
        filtered_decks = all_decks

    if not filtered_decks:
        if category_filter != "All Categories":
            st.warning(f"No flashcard decks found for {category_filter}. Try selecting 'All Categories' or import relevant decks.")
        else:
            st.warning("No flashcard decks found. Import Anki decks to get started!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-scan Downloads Folder", type="primary"):
                with st.spinner("Scanning for new Anki decks..."):
                    results = flashcard_manager.import_all_from_downloads()
                    if any(count > 0 for count in results.values()):
                        st.success("New decks imported!")
                        st.rerun()
                    else:
                        st.info("No new decks found")

        with col2:
            st.markdown("**Supported formats:** .apkg files from Anki")
        return

    # Deck selection
    st.markdown("## 📚 Select Deck")

    # Show deck stats
    deck_stats = {}
    for deck_name in all_decks:
        stats = flashcard_manager.get_deck_stats(deck_name)
        deck_stats[deck_name] = stats

    # Deck selector with stats - use filtered decks
    selected_deck = st.selectbox(
        "Choose a deck to study:",
        ["All Decks"] + filtered_decks,
        format_func=lambda x: f"{x} ({deck_stats.get(x, {}).get('total_cards', 0)} cards)" if x != "All Decks" else x
    )

    # Show selected deck statistics
    if selected_deck == "All Decks":
        stats = flashcard_manager.get_deck_stats()
    else:
        stats = flashcard_manager.get_deck_stats(selected_deck)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Cards", stats['total_cards'])

    with col2:
        st.metric("New Cards", stats['new_cards'])

    with col3:
        st.metric("Due for Review", stats['due_cards'])

    with col4:
        st.metric("Accuracy", f"{stats['accuracy']:.1f}%")

    # Study session controls
    st.markdown("## 🎯 Study Session")

    # Initialize session state for flashcard review
    if 'flashcard_session_active' not in st.session_state:
        st.session_state.flashcard_session_active = False
    if 'current_flashcard' not in st.session_state:
        st.session_state.current_flashcard = None
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'session_cards' not in st.session_state:
        st.session_state.session_cards = []
    if 'session_index' not in st.session_state:
        st.session_state.session_index = 0
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {'reviewed': 0, 'correct': 0}

    if not st.session_state.flashcard_session_active:
        # Start new session
        col_start, col_settings = st.columns([1, 1])

        with col_start:
            if st.button("🚀 Start Study Session", type="primary", use_container_width=True):
                # Get cards for review
                deck_filter = None if selected_deck == "All Decks" else selected_deck

                # Get due cards and new cards
                due_cards = flashcard_manager.get_due_cards(deck_filter)
                new_cards = flashcard_manager.get_new_cards(deck_filter, limit=10)

                # Combine and shuffle
                session_cards = due_cards + new_cards
                random.shuffle(session_cards)

                if session_cards:
                    st.session_state.session_cards = session_cards
                    st.session_state.session_index = 0
                    st.session_state.flashcard_session_active = True
                    st.session_state.current_flashcard = session_cards[0]
                    st.session_state.show_answer = False
                    st.session_state.session_stats = {'reviewed': 0, 'correct': 0}

                    # Start session in flashcard manager
                    session_id = flashcard_manager.start_review_session(deck_filter)
                    st.session_state.current_session_id = session_id

                    st.rerun()
                else:
                    st.info("No cards available for review right now. Great job staying on top of your studies!")

        with col_settings:
            st.markdown("**Study Tips:**")
            st.markdown("- Focus on understanding, not memorization")
            st.markdown("- Be honest with your self-assessment")
            st.markdown("- Review regularly for best results")

    else:
        # Active study session
        current_card = st.session_state.current_flashcard
        session_progress = f"{st.session_state.session_index + 1}/{len(st.session_state.session_cards)}"

        # Progress bar
        progress = (st.session_state.session_index + 1) / len(st.session_state.session_cards)
        st.progress(progress, text=f"Progress: {session_progress}")

        # Session stats
        col_stats1, col_stats2, col_end = st.columns([1, 1, 1])

        with col_stats1:
            st.metric("Reviewed", st.session_state.session_stats['reviewed'])

        with col_stats2:
            accuracy = (st.session_state.session_stats['correct'] / max(1, st.session_state.session_stats['reviewed'])) * 100
            st.metric("Session Accuracy", f"{accuracy:.1f}%")

        with col_end:
            if st.button("🏁 End Session", type="secondary"):
                # End session
                flashcard_manager.end_review_session(
                    st.session_state.current_session_id,
                    st.session_state.session_stats['reviewed'],
                    st.session_state.session_stats['correct']
                )

                st.session_state.flashcard_session_active = False
                st.success(f"Session completed! Reviewed {st.session_state.session_stats['reviewed']} cards with {accuracy:.1f}% accuracy.")
                st.rerun()

        st.markdown("---")

        # Card display
        if current_card:
            # Deck info
            st.markdown(f"**Deck:** {current_card.deck_name}")

            # Front of card
            st.markdown("### Question")

            # Handle HTML content and images
            front_content = current_card.front
            if current_card.images:
                for img_path in current_card.images:
                    if Path(img_path).exists():
                        try:
                            st.image(img_path, caption="Card Image", use_column_width=True)
                        except:
                            pass

            # Display front content
            if '<' in front_content and '>' in front_content:
                st.markdown(front_content, unsafe_allow_html=True)
            else:
                st.markdown(front_content)

            if not st.session_state.show_answer:
                # Show answer button
                col_show, col_audio = st.columns([2, 1])

                with col_show:
                    if st.button("🔍 Show Answer", type="primary", use_container_width=True):
                        st.session_state.show_answer = True
                        st.rerun()

                with col_audio:
                    audio_narrator = st.session_state.systems.get('audio')
                    if audio_narrator and st.button("🔊 Read Question", type="secondary"):
                        try:
                            audio_narrator.speak_text(front_content)
                            st.success("Playing audio...")
                        except:
                            st.warning("Audio not available")
            else:
                # Show answer
                st.markdown("### Answer")

                back_content = current_card.back
                if '<' in back_content and '>' in back_content:
                    st.markdown(back_content, unsafe_allow_html=True)
                else:
                    st.markdown(back_content)

                # Difficulty rating (Anki-style)
                st.markdown("### How did you do?")
                st.markdown("Rate your performance to optimize future reviews:")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("❌ Again\n(< 1 min)", type="secondary", use_container_width=True):
                        process_card_review(flashcard_manager, current_card, 1)

                with col2:
                    if st.button("🔴 Hard\n(< 6 min)", type="secondary", use_container_width=True):
                        process_card_review(flashcard_manager, current_card, 2)

                with col3:
                    if st.button("🟢 Good\n(< 10 min)", type="secondary", use_container_width=True):
                        process_card_review(flashcard_manager, current_card, 3)

                with col4:
                    if st.button("🔵 Easy\n(4 days)", type="primary", use_container_width=True):
                        process_card_review(flashcard_manager, current_card, 4)

def process_card_review(flashcard_manager, card, quality):
    """Process a card review and move to next card"""
    # Update spaced repetition data
    flashcard_manager.review_card(card.card_id, quality)

    # Update session stats
    st.session_state.session_stats['reviewed'] += 1
    if quality >= 3:  # Good or Easy
        st.session_state.session_stats['correct'] += 1

    # Move to next card
    st.session_state.session_index += 1

    if st.session_state.session_index >= len(st.session_state.session_cards):
        # Session complete
        accuracy = (st.session_state.session_stats['correct'] / st.session_state.session_stats['reviewed']) * 100
        flashcard_manager.end_review_session(
            st.session_state.current_session_id,
            st.session_state.session_stats['reviewed'],
            st.session_state.session_stats['correct']
        )

        st.session_state.flashcard_session_active = False
        st.success(f"🎉 Session completed! Reviewed {st.session_state.session_stats['reviewed']} cards with {accuracy:.1f}% accuracy.")
        st.balloons()
    else:
        # Next card
        st.session_state.current_flashcard = st.session_state.session_cards[st.session_state.session_index]
        st.session_state.show_answer = False

    st.rerun()

def main():
    """Main application function"""
    # Load theme
    load_echo_theme()

    # Check authentication first
    from auth.user_system import auth
    if not auth.check_authentication():
        auth.show_login_page()
        return

    # Add CSS to hide Streamlit UI elements after login
    st.markdown("""
    <style>
    /* Hide Streamlit header and menu after login */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Add smooth transition */
    .main .block-container {
        animation: fadeIn 0.5s ease-in;
    }

    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Main content based on streamlined modes
    if st.session_state.current_mode == "study_hub":
        render_study_hub()
    elif st.session_state.current_mode == "reference_hub":
        render_reference_hub()

    # Handle image management overlays
    if st.session_state.get('show_image_upload', False):
        render_image_upload_interface()

    if st.session_state.get('show_directory_scan', False):
        render_directory_scan_interface()

def render_study_hub():
    """Render the streamlined Study Hub with focused learning options"""
    st.title("📚 Study Mode")
    st.markdown("*Master radiology concepts through structured learning*")

    # Radiology Category Filter
    col1, col2 = st.columns([2, 3])
    with col1:
        category_filter = st.selectbox(
            "🎯 Filter by Radiology Area:",
            options=[
                "All Categories",
                "Cardiothoracic",
                "Neuroradiology",
                "Musculoskeletal (MSK)",
                "Abdominal & Pelvic",
                "Breast Imaging",
                "Pediatric Radiology",
                "Nuclear Medicine",
                "Physics & Safety",
                "Interventional Radiology",
                "Emergency Radiology"
            ],
            index=0,
            key="radiology_category_filter"
        )

    with col2:
        if category_filter != "All Categories":
            st.info(f"📋 Filtering content for: **{category_filter}**")
        else:
            st.info("📋 Showing all radiology content")

    # Store selected category in session state
    st.session_state.selected_category = category_filter

    # Get current submode
    submode = st.session_state.get('study_submode', 'crack_core')

    # Study mode tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Crack the Core", "🃏 Flashcards", "📖 Lessons", "🎥 Video Teaching"])

    with tab1:
        if submode == "crack_core" or st.session_state.get('show_crack_core', False):
            render_crack_the_core()
        else:
            st.info("**🎯 Crack the Core Method**: Master radiology through systematic pathology review")
            st.markdown("**Three-Step Approach for Each Pathology:**")
            st.markdown("1. **What is it?** - Definition and pathophysiology")
            st.markdown("2. **What is it associated with?** - Clinical presentations and risk factors")
            st.markdown("3. **What's the next step?** - Imaging recommendations and management")

            if st.button("🚀 Start Crack the Core", type="primary"):
                st.session_state.study_submode = "crack_core"
                st.session_state.show_crack_core = True
                st.rerun()

    with tab2:
        if submode == "flashcards":
            render_flashcard_mode()
        else:
            st.info("**🃏 Flashcard Learning**: Spaced repetition with your imported Anki decks")

            try:
                # Show flashcard stats
                flashcard_manager = st.session_state.systems.get('flashcards')
                if flashcard_manager:
                    total_cards = len(flashcard_manager.cards)
                    due_cards = len(flashcard_manager.get_due_cards())

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Cards", total_cards)
                    with col2:
                        st.metric("Due Today", due_cards)
                    with col3:
                        st.metric("Study Streak", "5 days")  # Placeholder

            except:
                pass

            if st.button("🚀 Start Flashcard Review", type="primary"):
                st.session_state.study_submode = "flashcards"
                st.rerun()

    with tab3:
        if submode == "lessons":
            render_lesson_reader()
        else:
            st.info("**📖 Lesson Reading**: Comprehensive radiology lessons with AI narration")
            st.markdown("Choose from core radiology topics with text-to-speech support")

            if st.button("🚀 Browse Lessons", type="primary"):
                st.session_state.study_submode = "lessons"
                st.rerun()

    with tab4:
        if submode == "videos":
            render_video_mode()
        else:
            st.info("**🎥 Video Teaching**: Educational videos with enhanced metadata")

            try:
                # Show video stats
                video_manager = st.session_state.systems.get('video')
                if video_manager:
                    videos = video_manager.scan_local_videos()
                    total_videos = sum(len(v) for v in videos.values())
                    st.metric("Available Videos", total_videos)
            except:
                pass

            if st.button("🚀 Browse Videos", type="primary"):
                st.session_state.study_submode = "videos"
                st.rerun()

def render_reference_hub():
    """Render the streamlined Reference Hub for workstation use"""
    st.title("🔍 Reference Mode")
    st.markdown("*Quick access to radiology reference tools*")

    # Get current submode
    submode = st.session_state.get('reference_submode', 'search')

    # Reference mode tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Quick Search", "🎯 Differential Dx", "📄 AJR Articles", "📊 Imaging Guide"])

    with tab1:
        if submode == "search":
            render_search_mode()
        else:
            st.info("**🔍 Quick Search**: AI-powered search with radiology focus")
            if st.button("🚀 Open Search", type="primary"):
                st.session_state.reference_submode = "search"
                st.rerun()

    with tab2:
        if submode == "differential":
            render_differential_diagnosis()
        else:
            st.info("**🎯 Differential Diagnosis**: Find differentials based on imaging findings")
            if st.button("🚀 Open Differential Tool", type="primary"):
                st.session_state.reference_submode = "differential"
                st.rerun()

    with tab3:
        if submode == "articles":
            render_ajr_articles()
        else:
            st.info("**📄 AJR Articles**: Search American Journal of Radiology publications")
            if st.button("🚀 Search AJR", type="primary"):
                st.session_state.reference_submode = "articles"
                st.rerun()

    with tab4:
        if submode == "imaging_guide":
            render_imaging_guide()
        else:
            st.info("**📊 Imaging Guide**: Best imaging modalities and protocols")
            if st.button("🚀 Open Imaging Guide", type="primary"):
                st.session_state.reference_submode = "imaging_guide"
                st.rerun()

def render_crack_the_core():
    """Render the Crack the Core learning method"""
    st.subheader("🎯 Crack the Core")
    st.markdown("*Master radiology through systematic pathology review*")

    # Get category filter from session state
    category_filter = st.session_state.get('selected_category', 'All Categories')

    # Core exam areas - filter based on category selection
    all_areas = list(CORE_EXAM_CONFIG['exam_areas'].keys())

    # Map category filter to area names
    category_mapping = {
        "All Categories": all_areas,
        "Cardiothoracic": ["Cardiothoracic"],
        "Neuroradiology": ["Neuroradiology"],
        "Musculoskeletal (MSK)": ["Musculoskeletal (MSK)"],
        "Abdominal & Pelvic": ["Abdominal & Pelvic"],
        "Breast Imaging": ["Breast Imaging"],
        "Pediatric Radiology": ["Pediatric Radiology"],
        "Nuclear Medicine": ["Nuclear Medicine"],
        "Physics & Safety": ["Physics & Safety"],
        "Interventional Radiology": ["Interventional Radiology"],
        "Emergency Radiology": ["Emergency Radiology"]
    }

    # Filter areas based on category selection
    filtered_areas = category_mapping.get(category_filter, all_areas)

    if category_filter != "All Categories":
        st.info(f"📋 Showing pathologies for: **{category_filter}**")

    selected_area = st.selectbox("Choose Radiology Area", filtered_areas)

    # Common pathologies for each area (simplified list)
    pathologies = {
        'Cardiothoracic': [
            'Pneumonia', 'Pulmonary Edema', 'Pneumothorax', 'Pleural Effusion',
            'Lung Cancer', 'COPD/Emphysema', 'Pulmonary Embolism'
        ],
        'Neuroradiology': [
            'Stroke (Acute)', 'Intracranial Hemorrhage', 'Brain Tumor', 'Multiple Sclerosis',
            'Hydrocephalus', 'Traumatic Brain Injury'
        ],
        'Abdominal & Pelvic': [
            'Appendicitis', 'Bowel Obstruction', 'Pancreatitis', 'Cholecystitis',
            'Liver Cirrhosis', 'Renal Stones', 'Ovarian Cyst'
        ],
        'Musculoskeletal (MSK)': [
            'Fractures', 'Arthritis', 'Osteomyelitis', 'Bone Tumors',
            'Soft Tissue Masses', 'Joint Effusion'
        ],
        'Breast Imaging': [
            'Breast Cancer', 'Fibroadenoma', 'Cysts', 'Calcifications',
            'Fat Necrosis', 'Invasive Ductal Carcinoma'
        ],
        'Physics & Safety': [
            'Radiation Dose', 'Contrast Reactions', 'MRI Safety',
            'CT Protocols', 'Radiation Protection'
        ],
        'Pediatric Radiology': [
            'Intussusception', 'Pyloric Stenosis', 'Non-accidental Trauma',
            'Congenital Heart Disease', 'Developmental Dysplasia'
        ],
        'Nuclear Medicine': [
            'Bone Scan', 'Thyroid Scan', 'PET/CT', 'HIDA Scan',
            'V/Q Scan', 'Renal Scan'
        ]
    }

    selected_pathology = st.selectbox("Select Pathology", pathologies.get(selected_area, []))

    if st.button("🎯 Study This Pathology", type="primary"):
        render_pathology_breakdown(selected_area, selected_pathology)

def render_pathology_breakdown(area, pathology):
    """Render the three-step pathology breakdown"""
    st.markdown("---")
    st.markdown(f"### 🎯 {pathology} ({area})")

    # Three-column layout for the three questions
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1️⃣ What is it?")
        with st.expander("Definition & Pathophysiology", expanded=True):
            if st.session_state.systems and st.session_state.systems['rag']:
                with st.spinner("Loading definition..."):
                    response = st.session_state.systems['rag'].query(
                        f"What is {pathology}? Provide definition and pathophysiology for radiology review.",
                        n_results=3
                    )
                    if isinstance(response, dict):
                        st.markdown(response.get('answer', 'Information not available'))
                    else:
                        st.markdown(response)

    with col2:
        st.markdown("#### 2️⃣ Associated with?")
        with st.expander("Clinical & Risk Factors", expanded=True):
            if st.session_state.systems and st.session_state.systems['rag']:
                with st.spinner("Loading associations..."):
                    response = st.session_state.systems['rag'].query(
                        f"What is {pathology} associated with? Clinical presentations, risk factors, and imaging findings.",
                        n_results=3
                    )
                    if isinstance(response, dict):
                        st.markdown(response.get('answer', 'Information not available'))
                    else:
                        st.markdown(response)

    with col3:
        st.markdown("#### 3️⃣ Next step?")
        with st.expander("Imaging & Management", expanded=True):
            if st.session_state.systems and st.session_state.systems['rag']:
                with st.spinner("Loading next steps..."):
                    response = st.session_state.systems['rag'].query(
                        f"What is the next step for {pathology}? Best imaging modalities and management approach.",
                        n_results=3
                    )
                    if isinstance(response, dict):
                        st.markdown(response.get('answer', 'Information not available'))
                    else:
                        st.markdown(response)

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📚 Find Related Flashcards", type="secondary"):
            st.session_state.study_submode = "flashcards"
            st.session_state.flashcard_search = pathology
            st.rerun()

    with col2:
        if st.button("🎥 Watch Videos", type="secondary"):
            st.session_state.study_submode = "videos"
            st.session_state.video_search = pathology
            st.rerun()

    with col3:
        if st.button("🔍 Deep Reference Search", type="secondary"):
            st.session_state.current_mode = "reference_hub"
            st.session_state.reference_submode = "search"
            st.session_state.reference_query = pathology
            st.rerun()

def render_lesson_reader():
    """Render lesson reading interface with AI narration"""
    st.subheader("📖 Radiology Lessons")

    # Get category filter from session state
    category_filter = st.session_state.get('selected_category', 'All Categories')

    if category_filter != "All Categories":
        st.info(f"📋 Filtering lessons for: **{category_filter}**")

    st.info("**Lesson Reading**: Comprehensive text lessons with optional AI narration")

    # Sample lessons with categories (in practice, these would be loaded from files)
    all_lessons = {
        "Chest X-Ray Interpretation": {"content": "A systematic approach to reading chest radiographs...", "category": "Cardiothoracic"},
        "CT Abdomen Protocols": {"content": "Understanding optimal CT protocols for abdominal imaging...", "category": "Abdominal & Pelvic"},
        "MRI Brain Basics": {"content": "Fundamentals of brain MRI interpretation...", "category": "Neuroradiology"},
        "Mammography Screening": {"content": "Approach to screening mammography interpretation...", "category": "Breast Imaging"},
        "MSK Trauma Imaging": {"content": "Systematic approach to musculoskeletal trauma...", "category": "Musculoskeletal (MSK)"},
        "Pediatric Chest Imaging": {"content": "Special considerations for pediatric chest imaging...", "category": "Pediatric Radiology"},
        "Nuclear Medicine Basics": {"content": "Introduction to nuclear medicine imaging...", "category": "Nuclear Medicine"}
    }

    # Filter lessons based on category selection
    if category_filter != "All Categories":
        filtered_lessons = {name: data for name, data in all_lessons.items()
                          if data["category"] == category_filter}
    else:
        filtered_lessons = all_lessons

    if not filtered_lessons:
        st.warning(f"No lessons available for {category_filter}. Try selecting 'All Categories'.")
        return

    selected_lesson = st.selectbox("Choose Lesson", list(filtered_lessons.keys()))

    if st.button("🎧 Start Audio Lesson", type="primary"):
        st.success(f"Starting audio narration for: {selected_lesson}")
        # Audio narration would be implemented here

    if st.button("📖 Read Text Lesson", type="secondary"):
        st.markdown(f"### {selected_lesson}")
        st.markdown(filtered_lessons[selected_lesson]["content"])

def render_differential_diagnosis():
    """Render differential diagnosis tool"""
    st.subheader("🎯 Differential Diagnosis Finder")
    st.info("**Find differentials based on imaging findings and clinical presentation**")

    # Input fields
    finding = st.text_input("Primary Imaging Finding", placeholder="e.g., pulmonary nodule, brain lesion")
    location = st.selectbox("Anatomic Location",
        ["Chest/Thorax", "Brain/Head", "Abdomen", "Pelvis", "MSK", "Breast"])

    patient_age = st.selectbox("Patient Age Group", ["Pediatric", "Young Adult", "Middle Age", "Elderly"])

    if st.button("🔍 Generate Differentials", type="primary") and finding:
        if st.session_state.systems and st.session_state.systems['rag']:
            with st.spinner("Generating differential diagnosis..."):
                query = f"Differential diagnosis for {finding} in {location} in {patient_age} patient. Include imaging features and next steps."
                response = st.session_state.systems['rag'].query(query, n_results=5)

                if isinstance(response, dict):
                    st.markdown("### 🎯 Differential Considerations")
                    st.markdown(response.get('answer', 'No differentials found'))

                    # Show sources including flashcards
                    sources = response.get('sources', [])
                    if sources:
                        with st.expander("📚 Reference Sources", expanded=False):
                            for i, source in enumerate(sources, 1):
                                if source.get('type') == 'flashcard':
                                    st.markdown(f"**{i}. 🃏 {source.get('title', 'Flashcard')}**")
                                    if st.button(f"Study Card", key=f"diff_card_{i}", type="secondary"):
                                        st.session_state.current_mode = "study_hub"
                                        st.session_state.study_submode = "flashcards"
                                        st.session_state.selected_flashcard = source.get('card_id')
                                        st.rerun()

def render_ajr_articles():
    """Render AJR article search"""
    st.subheader("📄 AJR Article Search")
    st.info("**Search American Journal of Radiology publications**")

    search_query = st.text_input("Search AJR Articles", placeholder="e.g., breast cancer screening")

    if st.button("🔍 Search AJR", type="primary") and search_query:
        st.info("🔍 Searching AJR database...")
        # In practice, this would integrate with AJR API or database
        st.markdown("### Sample Results:")
        st.markdown("- **Breast Cancer Screening Guidelines** - AJR 2023")
        st.markdown("- **AI in Mammography** - AJR 2022")
        st.markdown("- **BI-RADS Updates** - AJR 2021")

def render_imaging_guide():
    """Render imaging modality and protocol guide"""
    st.subheader("📊 Imaging Guide")
    st.info("**Best imaging modalities and protocols for clinical scenarios**")

    clinical_scenario = st.selectbox("Clinical Scenario", [
        "Acute Abdominal Pain",
        "Headache with Neurologic Signs",
        "Chest Pain",
        "Back Pain",
        "Suspected Cancer Screening",
        "Trauma Evaluation"
    ])

    if st.button("📊 Get Imaging Recommendations", type="primary"):
        if st.session_state.systems and st.session_state.systems['rag']:
            with st.spinner("Getting imaging recommendations..."):
                query = f"Best imaging modality and protocol for {clinical_scenario}. Include first-line, alternative options, and contraindications."
                response = st.session_state.systems['rag'].query(query, n_results=3)

                if isinstance(response, dict):
                    st.markdown("### 📊 Imaging Recommendations")
                    st.markdown(response.get('answer', 'No recommendations found'))

def render_image_upload_interface():
    """Render the image upload and tagging interface"""
    with st.container():
        st.markdown("## 🖼️ Image Upload & Tagging")

        # Close button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("✖️ Close", type="secondary"):
                st.session_state.show_image_upload = False
                st.rerun()

        with col1:
            st.markdown("Upload radiology images and add metadata tags for enhanced search")

        # File uploader
        uploaded_files = st.file_uploader(
            "Choose image files",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.markdown(f"### 📁 Processing {len(uploaded_files)} image(s)")

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Initialize image manager (if available)
                if not IMAGE_PROCESSOR_AVAILABLE:
                    st.error("🚫 Image processing not available on this deployment")
                    return
                image_manager = RadiologyImageManager()
                processed_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")

                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    try:
                        # Process the image
                        image = image_manager.process_image(temp_path)

                        # Display image preview and metadata form
                        col1, col2 = st.columns([2, 3])

                        with col1:
                            st.image(temp_path, caption=uploaded_file.name, width=200)

                        with col2:
                            st.markdown(f"**{uploaded_file.name}**")
                            st.markdown(f"Detected Modality: **{image.modality}**")
                            st.markdown(f"Detected Body Part: **{image.body_part}**")

                            # Allow user to modify tags
                            custom_tags = st.text_input(
                                "Custom Tags (comma-separated)",
                                value=", ".join(image.tags),
                                key=f"tags_{i}"
                            )

                            # Update tags if modified
                            if custom_tags:
                                new_tags = [tag.strip() for tag in custom_tags.split(",") if tag.strip()]
                                image.tags = new_tags

                            # Save to database
                            image_manager.add_to_database(image)
                            processed_count += 1

                        # Clean up temp file
                        os.unlink(temp_path)

                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_files))

                status_text.text(f"✅ Successfully processed {processed_count}/{len(uploaded_files)} images")
                st.success(f"🎉 Images added to database! You can now search for them using the RAG system.")

            except Exception as e:
                st.error(f"Error initializing image manager: {str(e)}")

def render_directory_scan_interface():
    """Render the directory scanning interface"""
    with st.container():
        st.markdown("## 🔄 Directory Scanner")

        # Close button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("✖️ Close", type="secondary", key="close_scan"):
                st.session_state.show_directory_scan = False
                st.rerun()

        with col1:
            st.markdown("Scan directories for radiology images and documents")

        # Directory input
        default_dir = r"X:\Subfolders\Rads HDD"
        scan_directory = st.text_input(
            "Directory to scan",
            value=default_dir,
            help="Enter the full path to scan for images, PDFs, and PowerPoint files"
        )

        # Scan options
        col1, col2, col3 = st.columns(3)
        with col1:
            scan_images = st.checkbox("📷 Scan Images", value=True)
        with col2:
            scan_pdfs = st.checkbox("📄 Scan PDFs", value=True)
        with col3:
            scan_ppts = st.checkbox("📊 Scan PowerPoints", value=True)

        # Start scanning button
        if st.button("🚀 Start Directory Scan", type="primary"):
            if not os.path.exists(scan_directory):
                st.error(f"Directory not found: {scan_directory}")
                return

            st.markdown("### 🔄 Scanning in progress...")

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.empty()

            try:
                # Initialize image manager (if available)
                if not IMAGE_PROCESSOR_AVAILABLE:
                    st.error("🚫 Image processing not available on this deployment")
                    return
                image_manager = RadiologyImageManager()

                # Get all files to process
                all_files = []
                if scan_images:
                    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff', '*.gif']
                    for ext in image_extensions:
                        all_files.extend(Path(scan_directory).rglob(ext))

                if scan_pdfs:
                    all_files.extend(Path(scan_directory).rglob('*.pdf'))

                if scan_ppts:
                    all_files.extend(Path(scan_directory).rglob('*.ppt*'))

                total_files = len(all_files)
                if total_files == 0:
                    st.warning("No files found to process")
                    return

                status_text.text(f"Found {total_files} files to process...")

                # Process files
                processed_count = 0
                error_count = 0
                results = []

                for i, file_path in enumerate(all_files):
                    status_text.text(f"Processing {file_path.name} ({i+1}/{total_files})")

                    try:
                        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
                            # Process image
                            image = image_manager.process_image(str(file_path))
                            image_manager.add_to_database(image)
                            results.append(f"✅ Image: {file_path.name} ({image.modality}, {image.body_part})")
                            processed_count += 1

                        elif file_path.suffix.lower() == '.pdf':
                            # Extract images from PDF
                            extracted_images = image_manager.extract_images_from_document(str(file_path))
                            for img in extracted_images:
                                image_manager.add_to_database(img)
                            results.append(f"📄 PDF: {file_path.name} - extracted {len(extracted_images)} images")
                            processed_count += len(extracted_images)

                        elif file_path.suffix.lower() in ['.ppt', '.pptx']:
                            # Extract images from PowerPoint
                            extracted_images = image_manager.extract_images_from_document(str(file_path))
                            for img in extracted_images:
                                image_manager.add_to_database(img)
                            results.append(f"📊 PPT: {file_path.name} - extracted {len(extracted_images)} images")
                            processed_count += len(extracted_images)

                    except Exception as e:
                        error_count += 1
                        results.append(f"❌ Error: {file_path.name} - {str(e)[:50]}...")

                    # Update progress
                    progress_bar.progress((i + 1) / total_files)

                # Show results
                status_text.text(f"✅ Scan complete! Processed {processed_count} images, {error_count} errors")

                with results_container.container():
                    st.markdown("### 📊 Scan Results")
                    st.markdown(f"**Summary:** {processed_count} images processed, {error_count} errors")

                    if results:
                        with st.expander("Detailed Results", expanded=False):
                            for result in results[-20:]:  # Show last 20 results
                                st.text(result)

                    st.success("🎉 Directory scan completed! Images have been added to the database.")

            except Exception as e:
                st.error(f"Error during directory scan: {str(e)}")

if __name__ == "__main__":
    main()