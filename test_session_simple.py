#!/usr/bin/env python3
"""
Simple test for session persistence functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from persistence.session_manager import SessionManager
from datetime import datetime

def test_session_persistence():
    """Test session persistence functionality"""
    
    print("=== TESTING SESSION PERSISTENCE ===")
    
    # Initialize session manager
    session_manager = SessionManager()
    print("Session manager initialized")
    
    # Test conversation history
    print("\n1. Testing conversation history...")
    test_conversations = [
        {
            'question': 'What is VHL syndrome?',
            'answer': 'Von Hippel-Lindau syndrome is a rare genetic disorder...',
            'timestamp': datetime.now().isoformat(),
            'sources': []
        }
    ]
    
    # Save and load
    success = session_manager.save_conversation_history(test_conversations)
    print(f"Save conversations: {success}")
    
    loaded = session_manager.load_conversation_history()
    print(f"Loaded {len(loaded)} conversations")
    
    if loaded and loaded[0]['question'] == test_conversations[0]['question']:
        print("Conversation persistence working!")
    else:
        print("Conversation persistence failed!")
        return False
    
    # Test performance data
    print("\n2. Testing performance data...")
    test_performance = {'total_questions': 25, 'accuracy': 80.0}
    
    success = session_manager.save_performance_data(test_performance)
    print(f"Save performance: {success}")
    
    loaded_perf = session_manager.load_performance_data()
    if loaded_perf.get('total_questions') == 25:
        print("Performance persistence working!")
    else:
        print("Performance persistence failed!")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("Session persistence is working correctly!")
    return True

if __name__ == "__main__":
    try:
        success = test_session_persistence()
        if success:
            print("\nSession persistence is ready!")
        else:
            print("\nSession persistence tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1)