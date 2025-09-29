#!/usr/bin/env python3
"""
Script to check the persistence status of your RAG system
Run this to see what documents and embeddings are currently stored
"""

import os
import json
import sqlite3

def check_embeddings_storage():
    """Check ChromaDB persistent storage"""
    embeddings_path = "./data/embeddings"
    chroma_db_path = "./data/embeddings/chroma.sqlite3"
    
    print("=== EMBEDDINGS STORAGE STATUS ===")
    
    if not os.path.exists(embeddings_path):
        print("❌ Embeddings directory not found")
        return
    
    if os.path.exists(chroma_db_path):
        file_size = os.path.getsize(chroma_db_path) / (1024*1024)  # MB
        print(f"✅ ChromaDB found: {file_size:.1f} MB")
        
        # Check collections in ChromaDB
        try:
            conn = sqlite3.connect(chroma_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Database tables: {len(tables)}")
            
            # Check collections table if it exists
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='collections';")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT name, id FROM collections;")
                collections = cursor.fetchall()
                print(f"📚 Collections found: {len(collections)}")
                for name, coll_id in collections:
                    print(f"  • {name} (ID: {coll_id})")
            
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not read ChromaDB details: {e}")
    else:
        print("❌ ChromaDB file not found")

def check_document_tracking():
    """Check document tracking persistence"""
    doc_list_path = "./data/processed_documents.json"
    raw_path = "./data/raw"
    
    print("\n=== DOCUMENT TRACKING STATUS ===")
    
    if os.path.exists(doc_list_path):
        try:
            with open(doc_list_path, 'r') as f:
                docs = json.load(f)
            print(f"✅ Document list found: {len(docs)} documents tracked")
            
            existing_docs = [doc for doc in docs if os.path.exists(doc)]
            missing_docs = [doc for doc in docs if not os.path.exists(doc)]
            
            print(f"📄 Existing files: {len(existing_docs)}")
            print(f"🗑️  Missing files: {len(missing_docs)}")
            
            if existing_docs:
                print("📁 Tracked documents:")
                for doc in existing_docs[:10]:  # Show first 10
                    print(f"  • {os.path.basename(doc)}")
                if len(existing_docs) > 10:
                    print(f"  ... and {len(existing_docs)-10} more")
                    
        except Exception as e:
            print(f"❌ Could not read document list: {e}")
    else:
        print("📝 No document list found (will be created on first upload)")
    
    # Check raw files directory
    if os.path.exists(raw_path):
        raw_files = [f for f in os.listdir(raw_path) if f.endswith(('.pdf', '.ppt', '.pptx'))]
        print(f"📂 Raw files directory: {len(raw_files)} files")
    else:
        print("📂 Raw files directory: Not found")

def main():
    print("🔍 RADIOLOGY AI ASSISTANT - PERSISTENCE CHECK")
    print("=" * 50)
    
    check_embeddings_storage()
    check_document_tracking()
    
    print("\n=== SUMMARY ===")
    print("Your system should retain:")
    print("✅ Document embeddings (ChromaDB)")
    print("✅ Raw uploaded files (./data/raw/)")
    print("✅ Document processing history (JSON)")
    print("\nAfter restarting Streamlit, previously uploaded documents")
    print("will still be available for querying!")

if __name__ == "__main__":
    main()