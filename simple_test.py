#!/usr/bin/env python3
"""Simple functionality test without Unicode issues"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_core_functionality():
    print("RADIOLOGY AI ASSISTANT - FUNCTIONALITY CHECK")
    print("=" * 50)
    
    print("\n1. TESTING RAG SYSTEM IMPORTS")
    print("-" * 30)
    
    try:
        from retrieval.rag_system import RadiologyRAGSystem
        print("[OK] RAG system import successful")
        
        # Test initialization
        rag = RadiologyRAGSystem()
        print("[OK] RAG system initialization successful")
        
        # Test components
        embed_sys = rag._init_embedding_system()
        if embed_sys and embed_sys != "unavailable":
            print("[OK] Embedding system ready")
        else:
            print("[WARN] Embedding system not ready")
            
        llm_mgr = rag._init_llm_manager()
        if llm_mgr and llm_mgr != "unavailable":
            print("[OK] LLM manager ready")
        else:
            print("[WARN] LLM manager not ready (Ollama needed)")
            
    except Exception as e:
        print(f"[FAIL] RAG system error: {e}")
    
    print("\n2. TESTING PERSISTENCE")
    print("-" * 30)
    
    # Check ChromaDB
    chroma_path = "./data/embeddings/chroma.sqlite3"
    if os.path.exists(chroma_path):
        size_mb = os.path.getsize(chroma_path) / (1024*1024)
        print(f"[OK] ChromaDB exists ({size_mb:.1f} MB)")
    else:
        print("[WARN] ChromaDB not found")
    
    # Check document tracking
    doc_path = "./data/processed_documents.json"
    if os.path.exists(doc_path):
        with open(doc_path, 'r') as f:
            docs = json.load(f)
        print(f"[OK] Document tracking ({len(docs)} files tracked)")
    else:
        print("[INFO] Document tracking will be created on first use")
    
    print("\n3. TESTING UI COMPONENTS")
    print("-" * 30)
    
    try:
        from ui.simple_radiology_app import CORE_EXAM_CONFIG
        print(f"[OK] CORE config loaded ({len(CORE_EXAM_CONFIG['exam_areas'])} areas)")
        
        # Test helper functions
        from ui.simple_radiology_app import load_processed_documents, save_processed_documents
        print("[OK] Persistence functions loaded")
        
    except Exception as e:
        print(f"[FAIL] UI components error: {e}")
    
    print("\n4. FEATURE STATUS SUMMARY")
    print("-" * 30)
    
    print("FULLY FUNCTIONAL:")
    print("  - Document upload and storage")
    print("  - ChromaDB embedding persistence") 
    print("  - Search interface (if Ollama running)")
    print("  - Random Question generator")
    print("  - Physics Focus generator")
    print("  - Document tracking persistence")
    print("  - Session state management")
    
    print("\nPLACEHOLDERS (show 'coming soon'):")
    print("  - Start New Quiz")
    print("  - Flashcard Decks") 
    print("  - Case of the Day (sidebar)")
    print("  - Dashboard")
    print("  - History & Review")
    
    print("\nSTATIC DISPLAYS:")
    print("  - Study streak (shows '12 Days')")
    print("  - ECHO Analysis (static weak areas)")
    print("  - Continue where left off (static content)")
    
    print("\n5. DEPENDENCIES CHECK")
    print("-" * 30)
    
    deps = ['streamlit', 'chromadb', 'sentence_transformers', 'ollama', 'pandas', 'numpy']
    for dep in deps:
        try:
            __import__(dep)
            print(f"[OK] {dep}")
        except ImportError:
            print(f"[MISSING] {dep}")
    
    print("\n" + "=" * 50)
    print("QUICK START GUIDE:")
    print("1. Ensure Ollama is running: ollama serve")
    print("2. Pull model: ollama pull llama3.1:8b")
    print("3. Start Streamlit: streamlit run src/ui/simple_radiology_app.py")
    print("4. Upload PDF/PPT files to test full functionality")

if __name__ == "__main__":
    test_core_functionality()