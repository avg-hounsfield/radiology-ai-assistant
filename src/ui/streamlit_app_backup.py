import streamlit as st
import os
from pathlib import Path
import sys
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from retrieval.rag_system import RadiologyRAGSystem
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure all required files are created and dependencies are installed")
    st.stop()

# Page config
st.set_page_config(
    page_title="Radiology CORE Exam Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []

def main():
    st.title("🏥 Radiology CORE Exam AI Assistant")
    st.markdown("Your personalized study companion for diagnostic radiology")
    
    # Sidebar for document management
    with st.sidebar:
        st.header("📚 Document Management")
        
        # Document upload
        uploaded_files = st.file_uploader(
            "Upload your study materials",
            accept_multiple_files=True,
            type=['pdf', 'ppt', 'pptx'],
            help="Upload PDFs, PowerPoint presentations, and other study materials"
        )
        
        if uploaded_files and st.button("Process Documents"):
            with st.spinner("Processing documents..."):
                # Save uploaded files
                document_paths = []
                for file in uploaded_files:
                    file_path = f"./data/raw/{file.name}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                    document_paths.append(file_path)
                
                # Initialize RAG system if not exists
                if st.session_state.rag_system is None:
                    try:
                        st.session_state.rag_system = RadiologyRAGSystem()
                    except Exception as e:
                        st.error(f"Error initializing RAG system: {e}")
                        return
                
                # Process documents
                try:
                    st.session_state.rag_system.process_documents(document_paths)
                    st.session_state.processed_documents.extend(document_paths)
                    st.success(f"Processed {len(uploaded_files)} documents!")
                except Exception as e:
                    st.error(f"Error processing documents: {e}")
        
        # Show processed documents
        if st.session_state.processed_documents:
            st.subheader("📋 Processed Documents")
            for doc in st.session_state.processed_documents:
                st.write(f"• {os.path.basename(doc)}")
        
        # Study mode selector
        st.header("🎯 Study Mode")
        study_mode = st.selectbox(
            "Choose your study approach",
            ["Q&A Mode", "Topic Review", "Case Studies", "Mock Exam"]
        )
        
        # CORE exam areas
        st.header("📖 CORE Exam Areas")
        exam_areas = [
            "Physics", "Safety", "Informatics",
            "Chest", "Cardiac", "Gastrointestinal",
            "Genitourinary", "Ultrasound", "Mammography",
            "Musculoskeletal", "Neuroradiology",
            "Nuclear Medicine", "Pediatric", "Interventional"
        ]
        
        selected_areas = st.multiselect(
            "Focus on specific areas",
            exam_areas,
            help="Select areas you want to focus on"
        )
    
    # Main content area
    if st.session_state.rag_system is None:
        st.info("👆 Please upload and process your study materials to get started!")
        
        # Show sample queries
        st.subheader("🔍 Example Queries")
        example_queries = [
            "What are the key imaging findings in acute appendicitis?",
            "Explain the physics of CT contrast enhancement",
            "Compare MRI sequences for brain imaging",
            "What safety considerations apply to MRI screening?"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}"):
                st.info("Please process documents first to use this feature!")
    
    else:
        # Query interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("💬 Ask Your Question")
            question = st.text_area(
                "Enter your radiology question:",
                height=100,
                placeholder="e.g., What are the differential diagnoses for a solitary pulmonary nodule?"
            )
            
            col_ask, col_clear = st.columns([1, 1])
            with col_ask:
                ask_button = st.button("🔍 Ask Question", type="primary")
            with col_clear:
                if st.button("🗑️ Clear History"):
                    st.session_state.conversation_history = []
                    st.rerun()
        
        with col2:
            st.subheader("⚙️ Settings")
            num_sources = st.slider("Number of sources to retrieve", 1, 10, 5)
            show_sources = st.checkbox("Show source details", value=True)
            confidence_threshold = st.slider("Confidence threshold", 0.0, 1.0, 0.7)
        
        # Process query
        if ask_button and question:
            with st.spinner("Searching knowledge base..."):
                try:
                    response = st.session_state.rag_system.query(
                        question=question,
                        n_results=num_sources,
                        conversation_history=st.session_state.conversation_history
                    )
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        'question': question,
                        'answer': response['answer'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': response['sources']
                    })
                except Exception as e:
                    st.error(f"Error processing query: {e}")
        
        # Display conversation history
        if st.session_state.conversation_history:
            st.subheader("📝 Conversation History")
            
            for i, conv in enumerate(reversed(st.session_state.conversation_history)):
                with st.expander(f"Q{len(st.session_state.conversation_history)-i}: {conv['question'][:100]}...", expanded=(i==0)):
                    st.write("**Question:**", conv['question'])
                    st.write("**Answer:**", conv['answer'])
                    
                    if show_sources and conv.get('sources'):
                        st.write("**Sources:**")
                        for j, source in enumerate(conv['sources'][:3]):
                            st.write(f"{j+1}. {os.path.basename(source.get('source', 'Unknown'))}")
                            if source.get('page'):
                                st.write(f"   Page: {source['page']}")
                            if source.get('section'):
                                st.write(f"   Section: {source['section']}")
                    
                    st.write(f"*{conv['timestamp']}*")

if __name__ == "__main__":
    main()
