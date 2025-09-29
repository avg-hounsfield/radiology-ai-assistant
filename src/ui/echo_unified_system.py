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
from study.flashcard_system import FlashcardManager, FlashCard, ReviewSession

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
        height: 68px !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(0, 191, 255, 0.2) !important;
        transition: all 0.3s ease !important;
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

def render_sidebar():
    """Render the sidebar with navigation and controls"""
    with st.sidebar:
        st.markdown("### ECHO Navigation")

        # Mode selection
        mode = st.radio(
            "Select Mode:",
            ["🏠 Dashboard", "🔍 Search & Chat", "📚 Study Questions", "🃏 Flashcards", "🎥 Video Library", "📊 Analytics", "🩻 Practice Dictation"],
            index=0
        )

        # Update current mode
        if mode == "🏠 Dashboard":
            st.session_state.current_mode = "dashboard"
        elif mode == "🔍 Search & Chat":
            st.session_state.current_mode = "search"
        elif mode == "📚 Study Questions":
            st.session_state.current_mode = "study"
        elif mode == "🃏 Flashcards":
            st.session_state.current_mode = "flashcards"
        elif mode == "🎥 Video Library":
            st.session_state.current_mode = "videos"
        elif mode == "📊 Analytics":
            st.session_state.current_mode = "analytics"
        elif mode == "🩻 Practice Dictation":
            st.session_state.current_mode = "dictation"

        st.markdown("---")

        # Quick Actions
        st.markdown("### Quick Actions")

        if st.button("🚀 Start Study Session", type="primary", use_container_width=True):
            st.session_state.current_mode = "study"
            st.rerun()

        if st.button("📈 View Progress", type="secondary", use_container_width=True):
            st.session_state.current_mode = "analytics"
            st.rerun()

        if st.button("🎯 Random Question", type="secondary", use_container_width=True):
            st.session_state.quiz_mode = True
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
                                for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
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

    # Filters
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Filters")

        # Radiology section filter
        sections = list(radiology_videos.keys())
        selected_section = st.selectbox("Radiology Section", ["All"] + sections)

        # Search filter
        search_term = st.text_input("Search videos", placeholder="Enter keywords...")

        # Stats
        total_videos = sum(len(data['videos']) for data in radiology_videos.values())
        st.info(f"📹 {total_videos} videos available")

    with col2:
        st.markdown("### Available Videos")

        # Filter videos by section
        if selected_section == "All":
            sections_to_show = radiology_videos
        else:
            sections_to_show = {selected_section: radiology_videos[selected_section]}

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

    st.info("**Anki-Style Spaced Repetition Learning** - Review imported flashcards with intelligent scheduling for optimal retention")

    flashcard_manager = st.session_state.systems.get('flashcards')

    if not flashcard_manager:
        st.error("Flashcard system not available")
        return

    # Get deck statistics
    all_decks = flashcard_manager.get_all_decks()

    if not all_decks:
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

    # Deck selector with stats
    selected_deck = st.selectbox(
        "Choose a deck to study:",
        ["All Decks"] + all_decks,
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

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Main content based on mode
    if st.session_state.current_mode == "dashboard":
        render_dashboard()
    elif st.session_state.current_mode == "search":
        render_search_mode()
    elif st.session_state.current_mode == "study":
        render_study_mode()
    elif st.session_state.current_mode == "flashcards":
        render_flashcard_mode()
    elif st.session_state.current_mode == "videos":
        render_video_mode()
    elif st.session_state.current_mode == "analytics":
        render_analytics_mode()
    elif st.session_state.current_mode == "dictation":
        render_dictation_mode()

if __name__ == "__main__":
    main()