import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

# Inline configuration (no external imports needed)
CORE_EXAM_CONFIG = {
    'exam_areas': {
        'physics': {'weight': 15, 'keywords': ['dose', 'radiation', 'kvp', 'technique']},
        'chest': {'weight': 20, 'keywords': ['pneumonia', 'nodules', 'consolidation', 'ground glass']},
        'cardiac': {'weight': 10, 'keywords': ['heart', 'coronary', 'ejection fraction', 'perfusion']},
        'gastrointestinal': {'weight': 15, 'keywords': ['bowel', 'liver', 'enhancement patterns', 'obstruction']},
        'neuroradiology': {'weight': 15, 'keywords': ['brain', 'stroke', 'hemorrhage', 'midline shift']},
        'musculoskeletal': {'weight': 10, 'keywords': ['bone', 'fracture', 'marrow edema', 'joint effusion']},
        'genitourinary': {'weight': 8, 'keywords': ['kidney', 'bladder', 'hydronephrosis', 'calculi']},
        'interventional': {'weight': 7, 'keywords': ['catheter', 'biopsy', 'embolization', 'drainage']}
    }
}

try:
    # Use your original working RAG system
    from retrieval.rag_system import RadiologyRAGSystem
    RAGSystemClass = RadiologyRAGSystem
    st.success("✅ RAG System loaded successfully!")
    SYSTEM_STATUS = "original"
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.info("📋 Running in demo mode - you can still explore the interface")
    RAGSystemClass = None
    SYSTEM_STATUS = "demo"

# Configure page
st.set_page_config(
    page_title="RadCore AI - CORE Exam Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Medical theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
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
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background: #1e40af;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
    }
    
    .response-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #059669;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'study_progress' not in st.session_state:
    st.session_state.study_progress = {area: 0 for area in CORE_EXAM_CONFIG['exam_areas'].keys()}
if 'exam_date' not in st.session_state:
    st.session_state.exam_date = datetime.now().date() + timedelta(days=180)
if 'questions_today' not in st.session_state:
    st.session_state.questions_today = 0

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 RadCore AI</h1>
        <p>Your Intelligent CORE Exam Study Companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div><strong>Documents Processed</strong></div>
            <div style="font-size: 2rem; color: #1e40af; font-weight: bold;">{}</div>
        </div>
        """.format(len(st.session_state.processed_documents)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div><strong>Questions Asked</strong></div>
            <div style="font-size: 2rem; color: #1e40af; font-weight: bold;">{}</div>
        </div>
        """.format(len(st.session_state.conversation_history)), unsafe_allow_html=True)
    
    with col3:
        days_until_exam = (st.session_state.exam_date - datetime.now().date()).days
        st.markdown("""
        <div class="metric-card">
            <div><strong>Days Until CORE</strong></div>
            <div style="font-size: 2rem; color: #1e40af; font-weight: bold;">{}</div>
        </div>
        """.format(max(0, days_until_exam)), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div><strong>Today's Progress</strong></div>
            <div style="font-size: 2rem; color: #1e40af; font-weight: bold;">{}/5</div>
        </div>
        """.format(st.session_state.questions_today), unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📚 Document Management")
        
        uploaded_files = st.file_uploader(
            "Upload study materials",
            accept_multiple_files=True,
            type=['pdf', 'ppt', 'pptx'],
            help="Upload PDFs, PowerPoints, and other radiology materials"
        )
        
        if uploaded_files and st.button("🔄 Process Documents"):
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
                    st.success(f"✅ Processed {len(uploaded_files)} documents!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        if st.session_state.processed_documents:
            st.subheader("📋 Processed Documents")
            for doc in st.session_state.processed_documents:
                st.write(f"• {os.path.basename(doc)}")
        
        st.header("⚙️ Settings")
        st.session_state.exam_date = st.date_input(
            "CORE Exam Date",
            value=st.session_state.exam_date
        )
        
        st.header("🎯 CORE Areas")
        for area, config in CORE_EXAM_CONFIG['exam_areas'].items():
            progress = st.session_state.study_progress.get(area, 0)
            st.write(f"**{area.title()}** ({config['weight']}%)")
            st.progress(progress / 100)
    
    # Main content
    if st.session_state.rag_system is None:
        st.info("👆 Upload your study materials to get started!")
        
        st.subheader("🔍 Example Questions")
        examples = [
            "What are the key physics principles for CT imaging?",
            "Explain the differential diagnosis for pulmonary nodules",
            "What are the safety considerations for MRI?",
            "Describe the imaging protocol for acute stroke"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.info("Please process documents first!")
    
    else:
        st.subheader("💬 Ask Your Question")
        
        question = st.text_area(
            "Enter your radiology question:",
            height=100,
            placeholder="e.g., What are the imaging findings for acute appendicitis?"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ask_button = st.button("🔍 Get Answer", type="primary")
        with col2:
            if st.button("🗑️ Clear History"):
                st.session_state.conversation_history = []
                st.rerun()
        
        if ask_button and question:
            with st.spinner("🔍 Searching knowledge base..."):
                try:
                    response = st.session_state.rag_system.query(
                        question=question,
                        n_results=5,
                        conversation_history=st.session_state.conversation_history
                    )
                    
                    st.session_state.conversation_history.append({
                        'question': question,
                        'answer': response['answer'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': response.get('sources', [])
                    })
                    
                    st.session_state.questions_today += 1
                    
                    # Display response
                    st.markdown('<div class="response-container">', unsafe_allow_html=True)
                    st.markdown("**🤖 AI Response:**")
                    st.markdown(response.get('answer', 'No response generated'))
                    
                    if response.get('sources'):
                        st.markdown("---")
                        st.markdown("**📚 Sources:**")
                        for source in response['sources'][:3]:
                            source_name = os.path.basename(source.get('source', 'Unknown'))
                            st.markdown(f"• {source_name}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Show conversation history
        if st.session_state.conversation_history:
            st.subheader("📝 Recent Questions")
            
            for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
                with st.expander(f"Q: {conv['question'][:60]}...", expanded=(i == 0)):
                    st.write(f"**Question:** {conv['question']}")
                    st.write("**Answer:**")
                    st.write(conv['answer'])
                    
                    if conv.get('sources'):
                        st.write("**Sources:**")
                        for source in conv['sources'][:2]:
                            st.write(f"• {os.path.basename(source.get('source', 'Unknown'))}")
                    
                    timestamp = datetime.fromisoformat(conv['timestamp'])
                    st.write(f"*{timestamp.strftime('%Y-%m-%d %H:%M')}*")

if __name__ == "__main__":
    main()