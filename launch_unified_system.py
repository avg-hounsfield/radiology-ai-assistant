#!/usr/bin/env python3
"""
Unified Radiology Study System Launcher
Complete all-in-one radiology learning platform
"""

import os
import sys
import subprocess
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_dependencies():
    """Check all required dependencies"""

    required_packages = [
        'streamlit', 'pandas', 'plotly', 'ollama',
        'sentence_transformers', 'chromadb', 'numpy',
        'pillow', 'pyyaml'
    ]

    optional_packages = [
        'edge_tts',      # High-quality TTS
        'pyttsx3',       # Cross-platform TTS
        'opencv-python'  # Video processing
    ]

    missing_required = []
    missing_optional = []

    # Check required packages
    for package in required_packages:
        try:
            # Handle special import names
            import_name = package.replace('-', '_')
            if package == 'pillow':
                import_name = 'PIL'
            elif package == 'pyyaml':
                import_name = 'yaml'

            __import__(import_name)
            logging.info(f"OK {package} is available")
        except ImportError:
            missing_required.append(package)
            logging.error(f"REQUIRED {package} is missing")

    # Check optional packages
    for package in optional_packages:
        try:
            # Handle special import names
            import_name = package.replace('-', '_')
            if package == 'opencv-python':
                import_name = 'cv2'

            __import__(import_name)
            logging.info(f"OK {package} is available (enhanced features)")
        except ImportError:
            missing_optional.append(package)
            logging.warning(f"OPTIONAL {package} is missing (reduced functionality)")

    if missing_required:
        logging.error(f"Missing required packages: {', '.join(missing_required)}")
        logging.info("Install with: pip install " + " ".join(missing_required))
        return False

    if missing_optional:
        logging.info("For enhanced features, install optional packages:")
        logging.info("pip install " + " ".join(missing_optional))

    return True

def check_directories():
    """Create necessary directories"""

    directories = [
        "data/videos/lectures",
        "data/videos/cases",
        "data/videos/tutorials",
        "data/videos/reviews",
        "data/videos/physics",
        "data/videos/uncategorized",
        "data/audio_cache",
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

    return True

def test_core_systems():
    """Test core system components"""

    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Test core systems
        from retrieval.rag_system import RadiologyRAGSystem
        rag = RadiologyRAGSystem()
        logging.info("OK RAG System initialized")

        from study.board_study_system import BoardStudySystem
        study = BoardStudySystem()
        logging.info("OK Board Study System initialized")

        from study.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker()
        logging.info("OK Performance Tracker initialized")

        from multimedia.video_manager import VideoManager
        video_mgr = VideoManager()
        logging.info("OK Video Manager initialized")

        from multimedia.audio_narrator import AudioNarrator
        audio_mgr = AudioNarrator()
        logging.info(f"OK Audio Narrator initialized (engine: {audio_mgr.active_engine['engine'] if audio_mgr.active_engine else 'None'})")

        # Test video scanning
        videos = video_mgr.scan_local_videos()
        total_videos = sum(len(v) for v in videos.values())
        logging.info(f"OK Found {total_videos} local videos")

        return True

    except Exception as e:
        logging.error(f"System test failed: {e}")
        return False

def launch_unified_interface():
    """Launch the unified study interface"""

    interface_path = Path(__file__).parent / "src" / "ui" / "unified_radiology_system.py"

    if not interface_path.exists():
        logging.error(f"Interface file not found: {interface_path}")
        return False

    logging.info("LAUNCHING UNIFIED RADIOLOGY STUDY SYSTEM...")

    # Launch Streamlit app
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(interface_path),
        "--server.port", "8504",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to launch unified interface: {e}")
        return False
    except KeyboardInterrupt:
        logging.info("Study session ended by user")
        return True

    return True

def main():
    """Main launch function"""

    print("=" * 60)
    print("UNIFIED RADIOLOGY STUDY SYSTEM")
    print("Complete All-in-One Learning Platform")
    print("=" * 60)

    logging.info("Starting system initialization...")

    # System checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
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
        logging.error("Some system checks failed. Please resolve issues before proceeding.")
        print("\nSYSTEM CHECK SUMMARY:")
        print("FAILED Some components need attention")
        print("Check the logs above for specific issues")
        return False

    print("\nSYSTEM CHECK SUMMARY:")
    print("PASSED All systems operational")
    print("Ready to launch unified study platform")

    print("\nUNIFIED PLATFORM FEATURES:")
    print("- Comprehensive dashboard with study analytics")
    print("- Interactive board study questions with audio")
    print("- Video learning center with 1,300+ videos")
    print("- Knowledge base search with RAG system")
    print("- Progress tracking and performance analytics")
    print("- Spaced repetition learning system")
    print("- Audio narration for hands-free study")
    print("- Integrated multimedia learning experience")
    print("\n" + "=" * 60)

    # Launch interface
    success = launch_unified_interface()

    if success:
        print("\nUnified study system session complete!")
        print("Continue your radiology board preparation!")
    else:
        print("\nFailed to launch unified interface")
        print("Check system requirements and try again")

    return success

def show_help():
    """Show system help and features"""

    print("""
UNIFIED RADIOLOGY STUDY SYSTEM - HELP

OVERVIEW:
This unified platform combines all radiology learning tools into a single,
comprehensive interface for optimal board preparation.

MAIN MODULES:

1. DASHBOARD
   - Study progress overview and analytics
   - Quick access to all features
   - Performance metrics and streak tracking
   - Recent activity visualization

2. STUDY MODULE
   - Interactive board-style questions
   - Multiple study modes (Practice, Review, Simulation)
   - Audio-enhanced question sessions
   - Real-time performance tracking
   - Spaced repetition integration

3. VIDEO CENTER
   - Access to 1,300+ imported radiology videos
   - Organized by category (Lectures, Cases, Physics, etc.)
   - Search and filter capabilities
   - Related question generation
   - Video-based learning sessions

4. KNOWLEDGE SEARCH
   - RAG-powered search through radiology knowledge base
   - Natural language queries
   - Audio narration of search results
   - Related content suggestions

5. PROGRESS ANALYTICS
   - Detailed performance tracking
   - Topic-specific analytics
   - Study streak monitoring
   - Weak area identification
   - Goal setting and achievement tracking

AUDIO FEATURES:
- Text-to-speech for all content
- Hands-free study sessions
- Adjustable audio speed and settings
- Audio explanations and narration

VIDEO FEATURES:
- Local video library integration
- Educational resource links
- Video-based question generation
- Multimedia study playlists

USAGE TIPS:
- Start with the Dashboard to see your progress
- Use Study Module for focused question practice
- Browse Video Center for visual learning
- Search knowledge base for specific topics
- Monitor progress in Analytics section

OPTIMAL STUDY WORKFLOW:
1. Check Dashboard for daily goals
2. Practice questions in Study Module
3. Watch related videos for difficult topics
4. Search knowledge base for clarification
5. Review progress and adjust study plan

KEYBOARD SHORTCUTS:
- Use sidebar navigation for quick module switching
- Enable global audio settings for consistent experience
- Use Quick Actions for common tasks

For technical support or questions, check the system logs
or contact support through the application interface.
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        show_help()
    else:
        success = main()
        sys.exit(0 if success else 1)