#!/usr/bin/env python3
"""
Launch script for Multimedia Radiology Study System
Enhanced study experience with video and audio capabilities
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

def check_multimedia_dependencies():
    """Check multimedia-specific dependencies"""

    required_packages = [
        'streamlit', 'pandas', 'plotly', 'ollama',
        'sentence_transformers', 'chromadb', 'numpy'
    ]

    optional_packages = [
        'edge_tts',    # High-quality TTS
        'pyttsx3',     # Cross-platform TTS
        'ffmpeg',      # Video processing
        'opencv-python' # Video analysis
    ]

    missing_required = []
    missing_optional = []

    # Check required packages
    for package in required_packages:
        try:
            __import__(package)
            logging.info(f"OK {package} is available")
        except ImportError:
            missing_required.append(package)
            logging.error(f"REQUIRED {package} is missing")

    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package)
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

def check_multimedia_directories():
    """Create multimedia-specific directories"""

    directories = [
        "data/videos/lectures",
        "data/videos/cases",
        "data/videos/tutorials",
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

    # Create sample video structure info
    readme_path = Path("data/videos/README.md")
    if not readme_path.exists():
        with open(readme_path, 'w') as f:
            f.write("""# Video Directory Structure

## Supported Formats
- MP4, AVI, MKV, MOV, WMV, FLV, WebM

## Directory Organization
- `lectures/` - Full lectures and presentations
- `cases/` - Case-based learning videos
- `tutorials/` - Tutorial and how-to videos

## Adding Videos
1. Place video files in appropriate subdirectory
2. Use descriptive filenames (e.g., "Chest_CT_Pneumonia_Dr_Smith.mp4")
3. Run video scan in the multimedia interface
4. Videos will be automatically categorized and made searchable

## Online Resources
The system also integrates with:
- Radiopaedia.org educational content
- YouTube educational channels
- Direct video URL embedding
""")

    return True

def test_multimedia_systems():
    """Test multimedia system components"""

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

        # Test multimedia systems
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

        # Test audio functionality
        test_text = "This is a test of the audio narration system."
        audio_result = audio_mgr.generate_audio_file(test_text, "test_audio.mp3")
        if audio_result:
            logging.info("OK Audio generation successful")
        else:
            logging.warning("Audio generation using fallback method")

        return True

    except Exception as e:
        logging.error(f"Multimedia system test failed: {e}")
        return False

def launch_multimedia_interface():
    """Launch the multimedia study interface"""

    interface_path = Path(__file__).parent / "src" / "ui" / "multimedia_study_interface.py"

    if not interface_path.exists():
        logging.error(f"Interface file not found: {interface_path}")
        return False

    logging.info("LAUNCHING MULTIMEDIA RADIOLOGY STUDY SYSTEM...")

    # Launch Streamlit app
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(interface_path),
        "--server.port", "8503",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to launch multimedia interface: {e}")
        return False
    except KeyboardInterrupt:
        logging.info("Multimedia study session ended by user")
        return True

    return True

def main():
    """Main launch function"""

    print("=" * 60)
    print("MULTIMEDIA RADIOLOGY STUDY SYSTEM")
    print("Enhanced with Video and Audio Learning")
    print("=" * 60)

    logging.info("Starting multimedia system checks...")

    # System checks
    checks = [
        ("Multimedia Dependencies", check_multimedia_dependencies),
        ("Multimedia Directories", check_multimedia_directories),
        ("Multimedia Systems", test_multimedia_systems)
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
    print("PASSED All multimedia systems operational")
    print("Ready to launch enhanced study system")
    print("\nFEATURES AVAILABLE:")
    print("- Video lecture embedding and playback")
    print("- Audio narration of study materials")
    print("- Radiopaedia and YouTube integration")
    print("- Multimedia study playlists")
    print("- Audio-enhanced practice questions")
    print("- Hands-free learning capabilities")
    print("\n" + "=" * 60)

    # Launch interface
    success = launch_multimedia_interface()

    if success:
        print("\nMultimedia study session complete!")
        print("Continue your enhanced learning journey!")
    else:
        print("\nFailed to launch multimedia interface")
        print("Check system requirements and try again")

    return success

def show_usage_guide():
    """Show multimedia system usage guide"""

    print("""
MULTIMEDIA STUDY SYSTEM USAGE GUIDE

1. VIDEO LEARNING:
   - Place video files in data/videos/lectures/, data/videos/cases/, or data/videos/tutorials/
   - Supported formats: MP4, AVI, MKV, MOV, WMV, FLV, WebM
   - Use descriptive filenames for automatic categorization
   - Videos are automatically scanned and made searchable

2. AUDIO NARRATION:
   - Enable audio narration in settings
   - Listen to questions, explanations, and study materials
   - Adjust speed, volume, and voice settings
   - Perfect for multitasking and hands-free study

3. EDUCATIONAL RESOURCES:
   - Automatic Radiopaedia links for topics
   - YouTube educational video recommendations
   - Direct video URL embedding
   - Integrated resource playlists

4. STUDY PLAYLISTS:
   - Create multimedia playlists for topics
   - Combine local videos, online resources, and audio
   - Organize by difficulty and content type
   - Track learning progress across media types

5. AUDIO-ENHANCED QUESTIONS:
   - Listen to questions while reviewing
   - Audio explanations for answers
   - Configurable auto-play settings
   - Hands-free practice sessions

6. OPTIMAL USAGE:
   - Use video lectures for initial learning
   - Practice questions with audio for reinforcement
   - Listen to audio summaries during commutes
   - Create topic-specific multimedia playlists
   - Adjust audio settings for your preference

For technical support or feature requests, check the documentation
or contact support through the application interface.
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_usage_guide()
    else:
        success = main()
        sys.exit(0 if success else 1)