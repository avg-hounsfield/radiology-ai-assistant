#!/usr/bin/env python3
"""
Launch script for Radiology Board Study System
Comprehensive study tool for radiology board preparation
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_dependencies():
    """Check if all required dependencies are available"""

    required_packages = [
        'streamlit', 'pandas', 'plotly', 'ollama',
        'sentence_transformers', 'chromadb', 'numpy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logging.info(f"OK {package} is available")
        except ImportError:
            missing_packages.append(package)
            logging.error(f"MISSING {package} is missing")

    if missing_packages:
        logging.error(f"Missing packages: {', '.join(missing_packages)}")
        logging.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False

    return True

def check_ollama_service():
    """Check if Ollama service is running"""

    try:
        import ollama
        client = ollama.Client()

        # Try to list models
        models = client.list()
        logging.info("OK Ollama service is running")

        # Check for required model
        model_names = [model['name'] for model in models['models']]
        if 'llama3.1:8b' in model_names:
            logging.info("OK llama3.1:8b model is available")
        else:
            logging.warning("WARNING llama3.1:8b model not found. You may need to run: ollama pull llama3.1:8b")

        return True

    except Exception as e:
        logging.error(f"ERROR Ollama service error: {e}")
        logging.info("Please start Ollama service and ensure llama3.1:8b model is available")
        return False

def check_data_directories():
    """Ensure all required data directories exist"""

    directories = [
        "data/embeddings",
        "data/study_progress",
        "data/spaced_repetition",
        "data/incoming",
        "data/lecture_transcripts",
        "data/sessions"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logging.info(f"OK Created/verified directory: {directory}")

def test_core_systems():
    """Test core systems functionality"""

    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Test RAG system
        from retrieval.rag_system import RadiologyRAGSystem
        rag = RadiologyRAGSystem()
        status = rag.get_system_status()
        logging.info(f"OK RAG System Status: {status}")

        # Test study system
        from study.board_study_system import BoardStudySystem
        study = BoardStudySystem()
        logging.info("OK Board Study System initialized")

        # Test question generator
        from llm.advanced_question_generator import AdvancedBoardQuestionGenerator
        qgen = AdvancedBoardQuestionGenerator()
        logging.info("OK Question Generator initialized")

        # Test spaced repetition
        from study.spaced_repetition import SpacedRepetitionSystem
        srs = SpacedRepetitionSystem()
        logging.info("OK Spaced Repetition System initialized")

        return True

    except Exception as e:
        logging.error(f"ERROR System test failed: {e}")
        return False

def launch_study_interface():
    """Launch the board study interface"""

    interface_path = Path(__file__).parent / "src" / "ui" / "board_study_interface.py"

    if not interface_path.exists():
        logging.error(f"ERROR Interface file not found: {interface_path}")
        return False

    logging.info("LAUNCHING Radiology Board Study System...")

    # Launch Streamlit app
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(interface_path),
        "--server.port", "8502",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"ERROR Failed to launch interface: {e}")
        return False
    except KeyboardInterrupt:
        logging.info("Study session ended by user")
        return True

    return True

def main():
    """Main launch function"""

    print("=" * 60)
    print("RADIOLOGY BOARD STUDY SYSTEM")
    print("Comprehensive AI-Powered Board Preparation Tool")
    print("=" * 60)

    logging.info("Starting system checks...")

    # System checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Data Directories", check_data_directories),
        ("Ollama Service", check_ollama_service),
        ("Core Systems", test_core_systems)
    ]

    all_passed = True
    for check_name, check_func in checks:
        logging.info(f"Checking {check_name}...")
        try:
            if not check_func():
                all_passed = False
                logging.error(f"FAILED {check_name} check failed")
            else:
                logging.info(f"PASSED {check_name} check passed")
        except Exception as e:
            logging.error(f"ERROR {check_name} check failed with error: {e}")
            all_passed = False

    if not all_passed:
        logging.error("WARNING Some system checks failed. Please resolve issues before proceeding.")
        print("\nSYSTEM CHECK SUMMARY:")
        print("FAILED Some components need attention")
        print("Check the logs above for specific issues")
        return False

    print("\nSYSTEM CHECK SUMMARY:")
    print("PASSED All systems operational")
    print("Ready to launch board study system")
    print("\n" + "=" * 60)

    # Launch interface
    success = launch_study_interface()

    if success:
        print("\nStudy session complete!")
        print("Check your progress in the dashboard")
        print("Keep up the great work on your board preparation!")
    else:
        print("\nFailed to launch study interface")
        print("Check system requirements and try again")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)