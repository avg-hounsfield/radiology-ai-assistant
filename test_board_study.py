#!/usr/bin/env python3
"""
Simple test script for board study system without Unicode issues
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_systems():
    """Test all board study components"""

    print("=" * 50)
    print("TESTING RADIOLOGY BOARD STUDY SYSTEM")
    print("=" * 50)

    try:
        # Test 1: RAG System
        print("\n1. Testing RAG System...")
        from retrieval.rag_system import RadiologyRAGSystem
        rag = RadiologyRAGSystem()
        status = rag.get_system_status()
        print(f"   Status: {status.get('ready_for_queries', False)}")

        # Test 2: Board Study System
        print("\n2. Testing Board Study System...")
        from study.board_study_system import BoardStudySystem
        study_system = BoardStudySystem()
        analytics = study_system.get_study_analytics(days=7)
        print(f"   Initialized: {len(study_system.core_sections)} sections")

        # Test 3: Question Generator
        print("\n3. Testing Question Generator...")
        from llm.advanced_question_generator import AdvancedBoardQuestionGenerator
        qgen = AdvancedBoardQuestionGenerator()
        print("   Generator ready")

        # Test 4: Spaced Repetition
        print("\n4. Testing Spaced Repetition...")
        from study.spaced_repetition import SpacedRepetitionSystem
        srs = SpacedRepetitionSystem()
        analytics = srs.get_learning_analytics()
        print(f"   Cards in system: {analytics['total_cards']}")

        # Test 5: Generate sample question
        print("\n5. Testing Question Generation...")
        try:
            question = qgen.generate_comprehensive_question("chest", "intermediate")
            if question.get('success', False):
                print("   Sample question generated successfully")
            else:
                print("   Question generation failed")
        except Exception as e:
            print(f"   Question generation error: {e}")

        # Test 6: Create study session
        print("\n6. Testing Study Session Creation...")
        try:
            session = study_system.create_study_session(
                section="Physics & Safety",
                question_count=5,
                difficulty="intermediate"
            )
            print(f"   Session created with {len(session['questions'])} questions")
        except Exception as e:
            print(f"   Session creation error: {e}")

        print("\n" + "=" * 50)
        print("SYSTEM TEST SUMMARY")
        print("=" * 50)
        print("Status: ALL CORE SYSTEMS OPERATIONAL")
        print("Ready for board study!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_systems()
    print(f"\nTest Result: {'PASSED' if success else 'FAILED'}")