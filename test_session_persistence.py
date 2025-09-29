#!/usr/bin/env python3
"""
Test script to verify session persistence functionality
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
    print("Session manager initialized successfully")
    
    # Test conversation history
    print("\n1. Testing conversation history...")
    test_conversations = [
        {
            'question': 'What is VHL syndrome?',
            'answer': 'Von Hippel-Lindau syndrome is a rare genetic disorder...',
            'timestamp': datetime.now().isoformat(),
            'sources': []
        },
        {
            'question': 'What are common CT findings in pneumonia?',
            'answer': 'Common CT findings include consolidation, ground glass opacities...',
            'timestamp': datetime.now().isoformat(),
            'sources': []
        }
    ]
    
    # Save conversations
    success = session_manager.save_conversation_history(test_conversations)
    if success:
        print("Conversations saved successfully")
    else:
        print("Failed to save conversations")
        return False
    
    # Load conversations
    loaded_conversations = session_manager.load_conversation_history()
    if len(loaded_conversations) == 2:
        print("Conversations loaded successfully")
        print(f"   - First question: {loaded_conversations[0]['question']}")
        print(f"   - Second question: {loaded_conversations[1]['question']}")
    else:
        print(f"Expected 2 conversations, got {len(loaded_conversations)}")
        return False
    
    # Test performance data
    print("\n2. Testing performance data...")
    test_performance = {
        'total_questions': 25,
        'correct_answers': 20,
        'accuracy': 80.0,
        'weak_areas': [
            {'topic': 'Neuroradiology', 'accuracy': 65.0},
            {'topic': 'Chest Imaging', 'accuracy': 70.0}
        ]
    }
    
    success = session_manager.save_performance_data(test_performance)
    if success:
        print("✅ Performance data saved successfully")
    else:
        print("❌ Failed to save performance data")
        return False
    
    loaded_performance = session_manager.load_performance_data()
    if loaded_performance.get('total_questions') == 25:
        print("✅ Performance data loaded successfully")
        print(f"   - Total questions: {loaded_performance['total_questions']}")
        print(f"   - Accuracy: {loaded_performance['accuracy']}%")
    else:
        print("❌ Failed to load performance data correctly")
        return False
    
    # Test quiz progress
    print("\n3. Testing quiz progress...")
    test_quiz_data = {
        'quiz_score': 85,
        'questions_today': 12,
        'study_progress': {
            'Neuroradiology': 75,
            'Chest Imaging': 90,
            'Abdominal': 60
        }
    }
    
    success = session_manager.save_quiz_progress(test_quiz_data)
    if success:
        print("✅ Quiz progress saved successfully")
    else:
        print("❌ Failed to save quiz progress")
        return False
    
    loaded_quiz = session_manager.load_quiz_progress()
    if loaded_quiz.get('quiz_score') == 85:
        print("✅ Quiz progress loaded successfully")
        print(f"   - Quiz score: {loaded_quiz['quiz_score']}")
        print(f"   - Questions today: {loaded_quiz['questions_today']}")
    else:
        print("❌ Failed to load quiz progress correctly")
        return False
    
    # Test data summary
    print("\n4. Testing data summary...")
    summary = session_manager.get_data_summary()
    print("✅ Data summary generated:")
    print(f"   - Conversations: {summary['conversations_count']}")
    print(f"   - Has performance data: {summary['has_performance_data']}")
    print(f"   - Has quiz progress: {summary['quiz_progress']}")
    print(f"   - Total data size: {sum([summary.get(f'{name}_size_kb', 0) for name in ['conversations', 'performance', 'quiz', 'settings']]):.1f} KB")
    
    # Test all data save/load
    print("\n5. Testing bulk save/load...")
    session_data = {
        'conversation_history': test_conversations,
        'performance_data': test_performance,
        'quiz_score': 95,
        'questions_today': 15,
        'current_mode': 'main'
    }
    
    success = session_manager.save_all_session_data(session_data)
    if success:
        print("✅ All session data saved successfully")
    else:
        print("❌ Failed to save all session data")
        return False
    
    loaded_all = session_manager.load_all_session_data()
    if (len(loaded_all['conversation_history']) == 2 and 
        loaded_all['quiz_score'] == 95 and
        loaded_all['questions_today'] == 15):
        print("✅ All session data loaded successfully")
    else:
        print("❌ Failed to load all session data correctly")
        return False
    
    print("\n=== ALL TESTS PASSED! ===")
    print("Session persistence is working correctly!")
    print("\nData is saved to: data/sessions/")
    print("- conversation_history.json")
    print("- performance_data.json")  
    print("- quiz_progress.json")
    print("- user_settings.json")
    
    return True

if __name__ == "__main__":
    try:
        success = test_session_persistence()
        if success:
            print("\n🎉 Session persistence is ready for use!")
        else:
            print("\n❌ Session persistence tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        sys.exit(1)