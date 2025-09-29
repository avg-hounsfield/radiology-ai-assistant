#!/usr/bin/env python3
"""
Test the VHL syndrome query using the RAG system
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from retrieval.rag_system import RadiologyRAGSystem

def test_vhl_query():
    """Test VHL syndrome question"""
    
    print("=== TESTING VHL SYNDROME QUERY ===")
    print("Initializing RAG system...")
    
    try:
        # Initialize the RAG system
        rag_system = RadiologyRAGSystem()
        print("RAG system initialized successfully!")
        
        # Your question about VHL syndrome
        question = "what are some common radiology findings for VHL syndrome?"
        
        print(f"\nAsking ECHO: {question}")
        print("Searching knowledge base...")
        
        # Query the system
        response = rag_system.query(
            question=question,
            n_results=5,
            conversation_history=[]
        )
        
        print("\n" + "="*60)
        print("ECHO RESPONSE:")
        print("="*60)
        print(response.get('answer', 'No response generated'))
        
        if response.get('sources'):
            print("\n" + "-"*40)
            print("SOURCES CONSULTED:")
            print("-"*40)
            for i, source in enumerate(response['sources'][:3], 1):
                source_name = source.get('source', 'Unknown').split('\\')[-1]
                print(f"{i}. {source_name}")
        
        print("\n" + "="*60)
        
        return response.get('success', False)
        
    except Exception as e:
        print(f"Error testing query: {e}")
        return False

if __name__ == "__main__":
    success = test_vhl_query()
    if success:
        print("✅ Query successful!")
    else:
        print("❌ Query failed")