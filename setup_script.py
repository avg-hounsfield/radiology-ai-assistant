#!/usr/bin/env python3
"""
Automated setup script for Radiology CORE Assistant
This script creates all necessary Python files and configuration
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with the given content"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Write content to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created: {filepath}")

def setup_project():
    """Create all project files"""
    
    # 1. PDF Processor
    pdf_processor_content = '''import pymupdf
from typing import List, Dict
import re

class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.overlap = 200
    
    def extract_text_and_metadata(self, pdf_path: str) -> Dict:
        doc = pymupdf.open(pdf_path)
        content = {
            'text': '',
            'metadata': {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'pages': doc.page_count,
                'source': pdf_path
            },
            'pages': []
        }
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            
            # Extract images from page
            images = []
            for img_index, img in enumerate(page.get_images()):
                xref = img[0]
                pix = pymupdf.Pixmap(doc, xref)
                img_data = pix.tobytes("png")
                images.append({
                    'page': page_num,
                    'index': img_index,
                    'data': img_data
                })
            
            content['pages'].append({
                'page_num': page_num,
                'text': text,
                'images': images
            })
            content['text'] += text + '\\n'
        
        return content
    
    def semantic_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        # Medical-specific chunking logic
        sections = self._identify_medical_sections(text)
        chunks = []
        
        for section in sections:
            if len(section['text']) > self.chunk_size:
                # Split large sections while preserving context
                sub_chunks = self._split_with_overlap(section['text'])
                for i, chunk_text in enumerate(sub_chunks):
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            **metadata,
                            'section': section['title'],
                            'chunk_id': f"{section['title']}_{i}",
                            'chunk_type': 'text'
                        }
                    })
            else:
                chunks.append({
                    'text': section['text'],
                    'metadata': {
                        **metadata,
                        'section': section['title'],
                        'chunk_type': 'text'
                    }
                })
        
        return chunks
    
    def _identify_medical_sections(self, text: str) -> List[Dict]:
        # Identify medical sections: Anatomy, Pathology, Imaging, etc.
        section_patterns = [
            r'(?i)(anatomy|pathology|clinical features|imaging findings|differential diagnosis|treatment)',
            r'(?i)(case \\d+|patient \\d+)',
            r'(?i)(introduction|conclusion|discussion|references)'
        ]
        
        sections = []
        current_section = {'title': 'General', 'text': ''}
        
        lines = text.split('\\n')
        for line in lines:
            is_header = False
            for pattern in section_patterns:
                if re.search(pattern, line.strip()):
                    if current_section['text'].strip():
                        sections.append(current_section)
                    current_section = {'title': line.strip(), 'text': ''}
                    is_header = True
                    break
            
            if not is_header:
                current_section['text'] += line + '\\n'
        
        if current_section['text'].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_with_overlap(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(' '.join(chunk_words))
            
            if i + self.chunk_size >= len(words):
                break
        
        return chunks
'''
    
    # 2. PPT Processor
    ppt_processor_content = '''from pptx import Presentation
from typing import List, Dict
import base64

class PPTProcessor:
    def extract_content(self, ppt_path: str) -> Dict:
        prs = Presentation(ppt_path)
        content = {
            'slides': [],
            'metadata': {
                'title': prs.core_properties.title or '',
                'author': prs.core_properties.author or '',
                'slide_count': len(prs.slides),
                'source': ppt_path
            }
        }
        
        for slide_num, slide in enumerate(prs.slides):
            slide_content = {
                'slide_number': slide_num + 1,
                'title': '',
                'text': '',
                'images': [],
                'notes': ''
            }
            
            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    if shape.text.strip():
                        if not slide_content['title'] and len(shape.text.strip().split('\\n')[0]) < 100:
                            slide_content['title'] = shape.text.strip().split('\\n')[0]
                        slide_content['text'] += shape.text + '\\n'
                
                # Extract images
                if shape.shape_type == 13:  # Picture
                    try:
                        image_data = shape.image.blob
                        slide_content['images'].append({
                            'data': base64.b64encode(image_data).decode(),
                            'format': shape.image.ext
                        })
                    except:
                        pass
            
            # Extract speaker notes
            if slide.has_notes_slide:
                slide_content['notes'] = slide.notes_slide.notes_text_frame.text
            
            content['slides'].append(slide_content)
        
        return content
    
    def create_chunks(self, ppt_content: Dict) -> List[Dict]:
        chunks = []
        
        for slide in ppt_content['slides']:
            # Create text chunk for each slide
            text_content = f"Slide {slide['slide_number']}: {slide['title']}\\n{slide['text']}"
            if slide['notes']:
                text_content += f"\\nNotes: {slide['notes']}"
            
            chunks.append({
                'text': text_content,
                'metadata': {
                    **ppt_content['metadata'],
                    'slide_number': slide['slide_number'],
                    'slide_title': slide['title'],
                    'chunk_type': 'slide',
                    'has_images': len(slide['images']) > 0
                }
            })
            
            # Create separate chunks for images with descriptions
            for img_idx, image in enumerate(slide['images']):
                chunks.append({
                    'text': f"Image from slide {slide['slide_number']}: {slide['title']}",
                    'image_data': image['data'],
                    'metadata': {
                        **ppt_content['metadata'],
                        'slide_number': slide['slide_number'],
                        'image_index': img_idx,
                        'chunk_type': 'image'
                    }
                })
        
        return chunks
'''

    # 3. Embedding Generator
    embedding_generator_content = '''from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict
import uuid

class EmbeddingSystem:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Use medical-specific embeddings if available
        # Consider: "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./data/embeddings",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections
        self.text_collection = self.chroma_client.get_or_create_collection(
            name="radiology_texts",
            metadata={"description": "Radiology text content"}
        )
        
        self.image_collection = self.chroma_client.get_or_create_collection(
            name="radiology_images",
            metadata={"description": "Radiology images and descriptions"}
        )
    
    def add_text_chunks(self, chunks: List[Dict]):
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            if chunk['metadata']['chunk_type'] == 'text' or chunk['metadata']['chunk_type'] == 'slide':
                texts.append(chunk['text'])
                metadatas.append(chunk['metadata'])
                ids.append(str(uuid.uuid4()))
        
        if texts:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Add to ChromaDB
            self.text_collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    def search_similar_texts(self, query: str, n_results: int = 5) -> Dict:
        query_embedding = self.embedding_model.encode([query])
        
        results = self.text_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        return results
    
    def add_medical_keywords_boost(self, chunks: List[Dict]) -> List[Dict]:
        """Boost chunks containing important medical terms"""
        medical_keywords = [
            'pathology', 'diagnosis', 'imaging', 'radiograph', 'ct scan', 'mri',
            'ultrasound', 'contrast', 'lesion', 'mass', 'nodule', 'tumor',
            'anatomy', 'physiology', 'syndrome', 'disease', 'treatment'
        ]
        
        for chunk in chunks:
            boost_score = 0
            text_lower = chunk['text'].lower()
            
            for keyword in medical_keywords:
                if keyword in text_lower:
                    boost_score += text_lower.count(keyword)
            
            chunk['metadata']['medical_relevance_score'] = boost_score
        
        return chunks
'''

    # 4. Local LLM Manager
    llm_manager_content = '''import ollama
from typing import List, Dict, Optional
import json

class LocalLLMManager:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = ollama.Client()
        
        # Download model if not exists
        try:
            self.client.show(model_name)
        except:
            print(f"Downloading {model_name}...")
            self.client.pull(model_name)
    
    def generate_response(self, query: str, context_chunks: List[Dict], 
                         conversation_history: List[Dict] = None) -> Dict:
        
        # Prepare context
        context = self._format_context(context_chunks)
        
        # Create medical-focused prompt
        system_prompt = """You are a specialized AI assistant helping medical professionals study diagnostic radiology for the CORE exam. 

Key guidelines:
- Provide accurate, evidence-based medical information
- Always cite your sources from the provided context
- If you're uncertain, say so explicitly
- Focus on educational value for radiology training
- Use appropriate medical terminology
- Structure answers clearly with key points
- When discussing imaging findings, be specific about modalities and techniques

Always end your response with source citations in the format: [Source: filename, page/slide number]"""

        user_prompt = f"""Based on the following context from radiology materials:

{context}

Question: {query}

Please provide a comprehensive answer suitable for CORE exam preparation."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Lower for medical accuracy
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            )
            
            return {
                "answer": response['message']['content'],
                "sources": self._extract_sources(context_chunks),
                "model_used": self.model_name,
                "success": True
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "model_used": self.model_name,
                "success": False
            }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            source_info = f"Source {i}: {metadata.get('source', 'Unknown')}"
            
            if 'page' in metadata:
                source_info += f", Page {metadata['page']}"
            elif 'slide_number' in metadata:
                source_info += f", Slide {metadata['slide_number']}"
            
            context_parts.append(f"{source_info}\\n{chunk['text']}\\n---")
        
        return "\\n".join(context_parts)
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        sources = []
        for chunk in chunks:
            metadata = chunk['metadata']
            sources.append({
                'source': metadata.get('source', 'Unknown'),
                'page': metadata.get('page'),
                'slide': metadata.get('slide_number'),
                'section': metadata.get('section'),
                'relevance_score': metadata.get('medical_relevance_score', 0)
            })
        return sources
'''

    # 5. RAG System
    rag_system_content = '''from typing import List, Dict, Optional
import logging
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embeddings.embedding_generator import EmbeddingSystem
from llm.local_llm import LocalLLMManager

class RadiologyRAGSystem:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", 
                 llm_model: str = "llama3.1:8b"):
        self.embedding_system = EmbeddingSystem(embedding_model)
        self.llm_manager = LocalLLMManager(llm_model)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def process_documents(self, document_paths: List[str]):
        """Process and index all documents"""
        from document_processor.pdf_processor import PDFProcessor
        from document_processor.ppt_processor import PPTProcessor
        
        pdf_processor = PDFProcessor()
        ppt_processor = PPTProcessor()
        
        all_chunks = []
        
        for doc_path in document_paths:
            self.logger.info(f"Processing: {doc_path}")
            
            try:
                if doc_path.lower().endswith('.pdf'):
                    content = pdf_processor.extract_text_and_metadata(doc_path)
                    chunks = pdf_processor.semantic_chunking(content['text'], content['metadata'])
                elif doc_path.lower().endswith(('.ppt', '.pptx')):
                    content = ppt_processor.extract_content(doc_path)
                    chunks = ppt_processor.create_chunks(content)
                else:
                    self.logger.warning(f"Unsupported file type: {doc_path}")
                    continue
                
                all_chunks.extend(chunks)
            except Exception as e:
                self.logger.error(f"Error processing {doc_path}: {str(e)}")
        
        # Add medical keyword boosting
        all_chunks = self.embedding_system.add_medical_keywords_boost(all_chunks)
        
        # Add to vector store
        self.embedding_system.add_text_chunks(all_chunks)
        
        self.logger.info(f"Processed {len(all_chunks)} chunks from {len(document_paths)} documents")
    
    def query(self, question: str, n_results: int = 5, 
              conversation_history: List[Dict] = None) -> Dict:
        """Main query interface"""
        
        # Step 1: Retrieve relevant chunks
        search_results = self.embedding_system.search_similar_texts(question, n_results)
        
        # Step 2: Prepare context chunks
        context_chunks = []
        for i in range(len(search_results['documents'][0])):
            context_chunks.append({
                'text': search_results['documents'][0][i],
                'metadata': search_results['metadatas'][0][i],
                'distance': search_results['distances'][0][i]
            })
        
        # Step 3: Generate response
        response = self.llm_manager.generate_response(
            query=question,
            context_chunks=context_chunks,
            conversation_history=conversation_history
        )
        
        # Step 4: Add retrieval info to response
        response['retrieval_info'] = {
            'chunks_retrieved': len(context_chunks),
            'search_query': question,
            'avg_similarity': sum(search_results['distances'][0]) / len(search_results['distances'][0]) if search_results['distances'][0] else 0
        }
        
        return response
    
    def get_study_recommendations(self, weak_areas: List[str]) -> Dict:
        """Generate study recommendations based on weak areas"""
        recommendations = {}
        
        for area in weak_areas:
            search_results = self.embedding_system.search_similar_texts(
                f"study guide {area} radiology core exam", 
                n_results=3
            )
            
            recommendations[area] = {
                'relevant_documents': [],
                'key_topics': []
            }
            
            for doc, metadata in zip(search_results['documents'][0], search_results['metadatas'][0]):
                recommendations[area]['relevant_documents'].append({
                    'source': metadata.get('source'),
                    'section': metadata.get('section'),
                    'relevance': metadata.get('medical_relevance_score', 0)
                })
        
        return recommendations
'''

    # 6. Streamlit UI
    streamlit_ui_content = '''import streamlit as st
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
'''

    # 7. Configuration file
    config_content = '''app:
  name: "Radiology CORE Assistant"
  version: "1.0.0"

models:
  embedding:
    name: "all-MiniLM-L6-v2"
    # Alternative: "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
  
  llm:
    name: "llama3.1:8b"
    temperature: 0.1
    max_tokens: 1000
    
  multimodal:
    name: "llava:7b"  # For image analysis
    enabled: false

processing:
  chunk_size: 1000
  chunk_overlap: 200
  max_file_size_mb: 100
  
retrieval:
  default_k: 5
  similarity_threshold: 0.7
  rerank: true

storage:
  vector_db_path: "./data/embeddings"
  processed_docs_path: "./data/processed"
  logs_path: "./logs"

medical:
  core_exam_areas:
    - "Physics"
    - "Safety" 
    - "Informatics"
    - "Chest"
    - "Cardiac"
    - "Gastrointestinal"
    - "Genitourinary"
    - "Ultrasound"
    - "Mammography"
    - "Musculoskeletal"
    - "Neuroradiology"
    - "Nuclear Medicine"
    - "Pediatric"
    - "Interventional"
'''

    # 8. Requirements file
    requirements_content = '''langchain==0.1.0
langchain-community==0.0.10
chromadb==0.4.22
sentence-transformers==2.2.2
streamlit==1.29.0
ollama==0.1.7
pymupdf==1.23.14
python-pptx==0.6.23
opencv-python==4.9.0.80
pillow==10.2.0
pandas==2.2.0
numpy==1.26.3
'''

    # 9. Init files
    init_content = '''# This file makes Python treat the directory as a package
'''

    # Create all files
    files_to_create = [
        ('src/document_processor/pdf_processor.py', pdf_processor_content),
        ('src/document_processor/ppt_processor.py', ppt_processor_content),
        ('src/document_processor/__init__.py', init_content),
        ('src/embeddings/embedding_generator.py', embedding_generator_content),
        ('src/embeddings/__init__.py', init_content),
        ('src/llm/local_llm.py', llm_manager_content),
        ('src/llm/__init__.py', init_content),
        ('src/retrieval/rag_system.py', rag_system_content),
        ('src/retrieval/__init__.py', init_content),
        ('src/ui/streamlit_app.py', streamlit_ui_content),
        ('src/ui/__init__.py', init_content),
        ('src/__init__.py', init_content),
        ('config/config.yaml', config_content),
        ('requirements.txt', requirements_content)
    ]
    
    for filepath, content in files_to_create:
        create_file(filepath, content)
    
    print("\\n🎉 All project files created successfully!")
    print("\\nNext steps:")
    print("1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
    print("2. Pull the model: ollama pull llama3.1:8b")
    print("3. Install Python dependencies: pip install -r requirements.txt")
    print("4. Test the setup: python -c 'import src.ui.streamlit_app'")
    print("5. Run the app: streamlit run src/ui/streamlit_app.py")

if __name__ == "__main__":
    setup_project()
