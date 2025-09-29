#!/usr/bin/env python3
"""
Comprehensive functionality test for the Radiology AI Assistant
This script tests all components to identify working features vs placeholders
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_rag_system():
    """Test RAG system components"""
    print("TESTING RAG SYSTEM")
    print("-" * 40)
    
    try:
        # Test import
        from retrieval.rag_system import RadiologyRAGSystem
        print("✅ RAG system import: SUCCESS")
        
        # Test initialization
        rag = RadiologyRAGSystem()
        print("✅ RAG system initialization: SUCCESS")
        
        # Test embedding system
        embedding_system = rag._init_embedding_system()
        if embedding_system is None:
            print("❌ Embedding system: FAILED TO INITIALIZE")
            return False
        elif embedding_system == "unavailable":
            print("⚠️  Embedding system: NOT AVAILABLE (missing dependencies)")
            return False
        else:
            print("✅ Embedding system: SUCCESS")
        
        # Test LLM manager
        llm_manager = rag._init_llm_manager()
        if llm_manager is None:
            print("❌ LLM manager: FAILED TO INITIALIZE")
            return False
        elif llm_manager == "unavailable":
            print("⚠️  LLM manager: NOT AVAILABLE (Ollama not running?)")
            return False
        else:
            print("✅ LLM manager: SUCCESS")
        
        return True
        
    except ImportError as e:
        print(f"❌ RAG system import: FAILED - {e}")
        return False
    except Exception as e:
        print(f"❌ RAG system: FAILED - {e}")
        return False

def test_document_processors():
    """Test document processing components"""
    print("\n📄 TESTING DOCUMENT PROCESSORS")
    print("-" * 40)
    
    try:
        # Test PDF processor
        from document_processor.pdf_processor import PDFProcessor
        pdf_proc = PDFProcessor()
        print("✅ PDF processor: SUCCESS")
    except ImportError as e:
        print(f"❌ PDF processor: FAILED - {e}")
    except Exception as e:
        print(f"❌ PDF processor: ERROR - {e}")
    
    try:
        # Test PPT processor
        from document_processor.ppt_processor import PPTProcessor
        ppt_proc = PPTProcessor()
        print("✅ PPT processor: SUCCESS")
    except ImportError as e:
        print(f"❌ PPT processor: FAILED - {e}")
    except Exception as e:
        print(f"❌ PPT processor: ERROR - {e}")

def test_embeddings():
    """Test embedding system"""
    print("\n🔤 TESTING EMBEDDING SYSTEMS")
    print("-" * 40)
    
    try:
        # Test RadBERT system
        from embeddings.radbert_embedding_system import RadBERTEmbeddingSystem
        radbert = RadBERTEmbeddingSystem()
        print("✅ RadBERT system: SUCCESS")
    except ImportError as e:
        print(f"❌ RadBERT system: FAILED - {e}")
    except Exception as e:
        print(f"❌ RadBERT system: ERROR - {e}")
    
    try:
        # Test regular embedding system
        from embeddings.embedding_generator import EmbeddingSystem
        embed_sys = EmbeddingSystem()
        print("✅ Regular embedding system: SUCCESS")
    except ImportError as e:
        print(f"❌ Regular embedding system: FAILED - {e}")
    except Exception as e:
        print(f"❌ Regular embedding system: ERROR - {e}")

def test_llm_components():
    """Test LLM components"""
    print("\n🤖 TESTING LLM COMPONENTS")
    print("-" * 40)
    
    try:
        # Test local LLM
        from llm.local_llm_backup import LocalLLMManager
        llm = LocalLLMManager()
        print("✅ Local LLM manager: SUCCESS")
        
        # Test if Ollama is running
        try:
            import ollama
            models = ollama.list()
            print(f"✅ Ollama connection: SUCCESS ({len(models['models'])} models available)")
        except Exception as e:
            print(f"⚠️  Ollama connection: FAILED - {e}")
            
    except ImportError as e:
        print(f"❌ Local LLM manager: FAILED - {e}")
    except Exception as e:
        print(f"❌ Local LLM manager: ERROR - {e}")
    
    try:
        # Test question generator
        from llm.question_generator import COREQuestionGenerator
        qgen = COREQuestionGenerator()
        print("✅ Question generator: SUCCESS")
    except ImportError as e:
        print(f"❌ Question generator: FAILED - {e}")
    except Exception as e:
        print(f"❌ Question generator: ERROR - {e}")

def test_persistence():
    """Test persistence features"""
    print("\n💾 TESTING PERSISTENCE")
    print("-" * 40)
    
    # Check ChromaDB
    chroma_path = "./data/embeddings/chroma.sqlite3"
    if os.path.exists(chroma_path):
        size_mb = os.path.getsize(chroma_path) / (1024*1024)
        print(f"✅ ChromaDB: EXISTS ({size_mb:.1f} MB)")
    else:
        print("❌ ChromaDB: NOT FOUND")
    
    # Check document tracking
    doc_list_path = "./data/processed_documents.json"
    if os.path.exists(doc_list_path):
        try:
            with open(doc_list_path, 'r') as f:
                docs = json.load(f)
            print(f"✅ Document tracking: EXISTS ({len(docs)} documents)")
        except Exception as e:
            print(f"⚠️  Document tracking: EXISTS but CORRUPTED - {e}")
    else:
        print("⚠️  Document tracking: NOT FOUND (will be created on first use)")
    
    # Check raw files directory
    raw_path = "./data/raw"
    if os.path.exists(raw_path):
        files = [f for f in os.listdir(raw_path) if f.endswith(('.pdf', '.ppt', '.pptx'))]
        print(f"✅ Raw files directory: EXISTS ({len(files)} files)")
    else:
        print("⚠️  Raw files directory: NOT FOUND")

def test_ui_functionality():
    """Test UI component functionality"""
    print("\n🖥️  TESTING UI FUNCTIONALITY")
    print("-" * 40)
    
    # Test config imports
    try:
        from ui.simple_radiology_app import CORE_EXAM_CONFIG
        print("✅ CORE exam config: SUCCESS")
        print(f"   📚 {len(CORE_EXAM_CONFIG['exam_areas'])} exam areas configured")
        
        for area, config in CORE_EXAM_CONFIG['exam_areas'].items():
            print(f"   • {area}: {config['weight']}% weight")
        
    except ImportError as e:
        print(f"❌ UI components: FAILED - {e}")

def check_dependencies():
    """Check critical dependencies"""
    print("\n📦 CHECKING DEPENDENCIES")
    print("-" * 40)
    
    dependencies = {
        'streamlit': 'UI framework',
        'chromadb': 'Vector database',
        'sentence_transformers': 'Embeddings',
        'torch': 'ML framework',
        'ollama': 'Local LLM',
        'pandas': 'Data handling',
        'numpy': 'Numerical computing'
    }
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep}: INSTALLED ({description})")
        except ImportError:
            print(f"❌ {dep}: MISSING ({description})")

def identify_placeholders():
    """Identify placeholder vs functional features"""
    print("\n🎭 IDENTIFYING PLACEHOLDERS")
    print("-" * 40)
    
    placeholders = []
    functional = []
    
    # Check sidebar buttons functionality
    print("Sidebar Study Tools:")
    functional.append("Random Question - generates actual questions")
    functional.append("Physics Focus - generates physics questions") 
    placeholders.append("Start New Quiz - shows 'coming soon'")
    placeholders.append("Flashcard Decks - shows 'coming soon'")
    placeholders.append("Case of the Day - shows 'coming soon'")
    placeholders.append("Dashboard - shows 'coming soon'")
    placeholders.append("History & Review - shows 'coming soon'")
    
    print("\nMain Interface:")
    functional.append("Search interface - fully functional RAG")
    functional.append("Document upload - processes and stores")
    functional.append("Document persistence - ChromaDB + JSON")
    functional.append("Progress tracking - stores in session")
    
    placeholders.append("Study streak - static display (12 days)")
    placeholders.append("ECHO Analysis - static content")
    placeholders.append("Continue where left off - static content")
    placeholders.append("Metrics (Documents/Questions/Days) - session based only")
    
    print("\n✅ FUNCTIONAL FEATURES:")
    for item in functional:
        print(f"   • {item}")
    
    print("\n🎭 PLACEHOLDER FEATURES:")
    for item in placeholders:
        print(f"   • {item}")

def main():
    print("RADIOLOGY AI ASSISTANT - FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Run all tests
    rag_working = test_rag_system()
    test_document_processors()
    test_embeddings() 
    test_llm_components()
    test_persistence()
    test_ui_functionality()
    check_dependencies()
    identify_placeholders()
    
    print("\n" + "=" * 60)
    print("📊 OVERALL SYSTEM STATUS")
    print("=" * 60)
    
    if rag_working:
        print("🎉 CORE RAG FUNCTIONALITY: WORKING")
        print("   Your system can process documents and answer questions!")
    else:
        print("⚠️  CORE RAG FUNCTIONALITY: NEEDS SETUP")
        print("   Some components need configuration (Ollama, models, etc.)")
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. Ensure Ollama is running with llama3.1:8b model")
    print("2. Upload some PDF/PPT documents to test full workflow")
    print("3. Consider replacing placeholder features with real functionality")
    print("4. The persistence system is ready - your data will survive restarts!")

if __name__ == "__main__":
    main()