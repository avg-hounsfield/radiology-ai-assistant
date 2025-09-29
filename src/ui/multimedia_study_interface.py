import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from study.board_study_system import BoardStudySystem
from llm.advanced_question_generator import AdvancedBoardQuestionGenerator
from retrieval.rag_system import RadiologyRAGSystem
from multimedia.video_manager import VideoManager
from multimedia.audio_narrator import AudioNarrator

# Page configuration
st.set_page_config(
    page_title="Multimedia Radiology Study System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply enhanced multimedia theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00BFFF;
        text-align: center;
        margin-bottom: 2rem;
    }
    .multimedia-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252a3a 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #2d3748;
        margin: 1rem 0;
        box-shadow: 0 0 30px rgba(0, 191, 255, 0.15);
    }
    .video-container {
        background: #1a1f2e;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #4a5568;
    }
    .audio-enhanced {
        border-left: 4px solid #00BFFF;
        background: rgba(0, 191, 255, 0.1);
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
    }
    .resource-link {
        background: #2a3441;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        display: block;
        text-decoration: none;
        color: #ffffff;
        transition: all 0.3s ease;
    }
    .resource-link:hover {
        border-color: #00BFFF;
        background: #3a4451;
        transform: translateY(-2px);
    }
    .multimedia-controls {
        background: #252a3a;
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
        border: 1px solid #4a5568;
    }
    .study-playlist {
        background: #1e2631;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #4a5568;
    }
</style>
""", unsafe_allow_html=True)

# Initialize systems
@st.cache_resource
def init_multimedia_systems():
    try:
        study_system = BoardStudySystem()
        question_generator = AdvancedBoardQuestionGenerator()
        rag_system = RadiologyRAGSystem()
        video_manager = VideoManager()
        audio_narrator = AudioNarrator()
        return study_system, question_generator, rag_system, video_manager, audio_narrator
    except Exception as e:
        st.error(f"Error initializing multimedia systems: {e}")
        return None, None, None, None, None

study_system, question_generator, rag_system, video_manager, audio_narrator = init_multimedia_systems()

# Session state initialization
if 'audio_enabled' not in st.session_state:
    st.session_state.audio_enabled = True
if 'current_audio_session' not in st.session_state:
    st.session_state.current_audio_session = None
if 'multimedia_playlist' not in st.session_state:
    st.session_state.multimedia_playlist = None

def main():
    # Header
    st.markdown('<div class="main-header">🎬 Multimedia Radiology Study System</div>', unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("📚 Study Modes")
    study_mode = st.sidebar.selectbox(
        "Choose Study Experience",
        [
            "🎬 Multimedia Dashboard",
            "🔊 Audio-Enhanced Questions",
            "🎥 Video Learning Center",
            "📻 Audio Study Sessions",
            "🌐 Educational Resources",
            "⚙️ Audio & Video Settings"
        ]
    )

    # Audio controls in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔊 Audio Controls")

        audio_enabled = st.toggle("Enable Audio Narration", value=st.session_state.audio_enabled)
        st.session_state.audio_enabled = audio_enabled

        if audio_enabled and audio_narrator:
            col1, col2 = st.columns(2)
            with col1:
                speed = st.slider("Speech Speed (WPM)", 50, 300, audio_narrator.audio_settings['speed'])
            with col2:
                volume = st.slider("Volume", 0.0, 1.0, audio_narrator.audio_settings['volume'])

            if st.button("💾 Save Audio Settings"):
                audio_narrator.set_voice_settings(speed=speed, volume=volume)
                st.success("Audio settings saved!")

    # Route to appropriate interface
    if study_mode == "🎬 Multimedia Dashboard":
        show_multimedia_dashboard()
    elif study_mode == "🔊 Audio-Enhanced Questions":
        show_audio_enhanced_questions()
    elif study_mode == "🎥 Video Learning Center":
        show_video_learning_center()
    elif study_mode == "📻 Audio Study Sessions":
        show_audio_study_sessions()
    elif study_mode == "🌐 Educational Resources":
        show_educational_resources()
    elif study_mode == "⚙️ Audio & Video Settings":
        show_settings()

def show_multimedia_dashboard():
    st.markdown('<div class="section-header">🎬 Multimedia Study Dashboard</div>', unsafe_allow_html=True)

    if not all([study_system, video_manager, audio_narrator]):
        st.error("Multimedia systems not available")
        return

    # Scan for local videos
    if st.button("🔍 Scan for Local Videos"):
        with st.spinner("Scanning for video files..."):
            videos = video_manager.scan_local_videos()
            st.success(f"Found {sum(len(v) for v in videos.values())} videos")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        local_videos = len(video_manager.video_database.get('local_videos', {}))
        st.markdown(f"""
        <div class="multimedia-card">
            <h3 style="color: #00BFFF;">📹 Local Videos</h3>
            <h2 style="color: #FFFFFF;">{local_videos}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        playlists = len(video_manager.video_database.get('playlists', {}))
        st.markdown(f"""
        <div class="multimedia-card">
            <h3 style="color: #00BFFF;">📋 Study Playlists</h3>
            <h2 style="color: #FFFFFF;">{playlists}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        audio_files = len(list(audio_narrator.audio_cache_dir.glob("*.mp3"))) if audio_narrator.audio_cache_dir.exists() else 0
        st.markdown(f"""
        <div class="multimedia-card">
            <h3 style="color: #00BFFF;">🔊 Audio Files</h3>
            <h2 style="color: #FFFFFF;">{audio_files}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        engine_name = audio_narrator.active_engine['engine'] if audio_narrator.active_engine else 'None'
        st.markdown(f"""
        <div class="multimedia-card">
            <h3 style="color: #00BFFF;">🎙️ TTS Engine</h3>
            <h2 style="color: #FFFFFF;">{engine_name}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Create study playlist
    st.markdown("### 🎵 Create Study Playlist")
    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input("Study Topic", placeholder="e.g., pneumonia, stroke, fractures")
    with col2:
        include_online = st.checkbox("Include online resources", value=True)

    if st.button("🎬 Create Multimedia Playlist") and topic:
        with st.spinner("Creating multimedia playlist..."):
            playlist = video_manager.create_study_playlist(topic, include_online=include_online)
            st.session_state.multimedia_playlist = playlist
            st.success(f"Created playlist for '{topic}' with {len(playlist['local_videos'])} videos and {len(playlist['online_resources'])} online resources")

    # Display current playlist
    if st.session_state.multimedia_playlist:
        display_multimedia_playlist(st.session_state.multimedia_playlist)

def show_audio_enhanced_questions():
    st.markdown('<div class="section-header">🔊 Audio-Enhanced Practice Questions</div>', unsafe_allow_html=True)

    if not all([study_system, question_generator, audio_narrator]):
        st.error("Required systems not available")
        return

    st.info("📻 Listen to questions and explanations while studying - perfect for multitasking!")

    # Question configuration
    with st.expander("🎯 Configure Audio Question Session", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            section = st.selectbox("Focus Area", ["Mixed"] + list(study_system.core_sections.keys()))
        with col2:
            question_count = st.slider("Questions", 5, 20, 10)
        with col3:
            difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Intermediate", "Hard"])

        auto_play = st.checkbox("🔄 Auto-play next question", value=True)
        read_options = st.checkbox("📖 Read answer options aloud", value=True)

        if st.button("🎵 Start Audio Question Session", type="primary"):
            create_audio_question_session(section, question_count, difficulty, auto_play, read_options)

    # Display current audio session
    if st.session_state.current_audio_session:
        display_audio_question_session()

def show_video_learning_center():
    st.markdown('<div class="section-header">🎥 Video Learning Center</div>', unsafe_allow_html=True)

    if not video_manager:
        st.error("Video manager not available")
        return

    # Video categories
    video_categories = ['lectures', 'cases', 'tutorials']

    selected_category = st.selectbox("📂 Video Category", video_categories)

    # Display videos by category
    local_videos = video_manager.video_database.get('local_videos', {})
    category_videos = [v for v in local_videos.values() if v.get('category') == selected_category]

    if category_videos:
        st.markdown(f"### 📹 {selected_category.title()} ({len(category_videos)} videos)")

        for i, video in enumerate(category_videos):
            with st.expander(f"🎬 {video['title']}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Video player
                    if os.path.exists(video['path']):
                        video_html = video_manager.get_video_embed_html(video['path'])
                        st.markdown(video_html, unsafe_allow_html=True)
                    else:
                        st.error(f"Video file not found: {video['path']}")

                with col2:
                    st.markdown("**Video Details:**")
                    st.write(f"**Duration:** {video.get('duration', 'Unknown')}")
                    st.write(f"**Difficulty:** {video.get('difficulty', 'Intermediate')}")
                    st.write(f"**Topics:** {', '.join(video.get('topics', []))}")
                    st.write(f"**Speaker:** {video.get('speaker', 'Unknown')}")

                    if st.session_state.audio_enabled and audio_narrator:
                        if st.button(f"🔊 Audio Summary", key=f"audio_{i}"):
                            summary_text = f"Video: {video['title']}. Topics covered: {', '.join(video.get('topics', []))}. Difficulty level: {video.get('difficulty', 'intermediate')}."
                            audio_html = audio_narrator.get_audio_player_html("", summary_text)
                            st.markdown(audio_html, unsafe_allow_html=True)

    else:
        st.info(f"No videos found in {selected_category} category. Add videos to data/videos/{selected_category}/ directory.")

    # Add video URL
    st.markdown("### ➕ Add Educational Video")
    col1, col2 = st.columns(2)

    with col1:
        video_url = st.text_input("Video URL (YouTube, etc.)", placeholder="https://youtube.com/watch?v=...")
    with col2:
        video_topic = st.text_input("Topic", placeholder="e.g., chest CT, stroke imaging")

    if st.button("📎 Add Video Resource") and video_url and video_topic:
        resource_id = video_manager.add_online_resource("youtube", video_topic, video_url, f"Educational video: {video_topic}")
        st.success(f"Added video resource: {resource_id}")

def show_audio_study_sessions():
    st.markdown('<div class="section-header">📻 Audio Study Sessions</div>', unsafe_allow_html=True)

    if not audio_narrator:
        st.error("Audio narrator not available")
        return

    st.info("🎧 Perfect for listening while commuting, exercising, or doing other activities!")

    # Create audio study material
    st.markdown("### 🎙️ Create Audio Study Session")

    topic = st.text_input("Study Topic", placeholder="Enter radiology topic for audio session")

    if topic and st.button("🎵 Generate Audio Study Material"):
        with st.spinner("Creating audio study session..."):
            # Query knowledge base for content
            if rag_system:
                result = rag_system.query(f"Comprehensive overview of {topic} in radiology", n_results=5)

                if result.get('success', False):
                    content = result.get('answer', '')

                    # Create audio session
                    audio_session = audio_narrator.create_study_material_audio(content, f"{topic} Study Guide")

                    # Display audio session
                    st.markdown(f"### 🎧 {audio_session['title']}")
                    st.write(f"**Duration:** {audio_session['total_duration_estimate']:.1f} minutes")
                    st.write(f"**Chunks:** {audio_session['navigation']['total_chunks']}")

                    # Audio controls
                    chunk_index = st.selectbox("Select Chapter:",
                                              range(len(audio_session['chunks'])),
                                              format_func=lambda x: f"Chapter {x+1} ({len(audio_session['chunks'][x]['text'].split())} words)")

                    # Display current chunk
                    current_chunk = audio_session['chunks'][chunk_index]

                    # Audio player for chunk
                    if current_chunk['audio_file']:
                        if isinstance(current_chunk['audio_file'], str) and current_chunk['audio_file'].endswith('.mp3'):
                            st.audio(current_chunk['audio_file'])
                        else:
                            # Browser-based TTS
                            st.markdown(current_chunk['audio_file'], unsafe_allow_html=True)

                    # Show text content
                    with st.expander("📖 View Text Content"):
                        st.write(current_chunk['text'])

                else:
                    st.error("Could not generate study content for this topic")
            else:
                st.error("Knowledge base not available")

    # Audio settings
    st.markdown("### ⚙️ Audio Playback Settings")
    if audio_narrator:
        settings_html = audio_narrator.get_audio_settings_interface()
        st.markdown(settings_html, unsafe_allow_html=True)

def show_educational_resources():
    st.markdown('<div class="section-header">🌐 Educational Resources</div>', unsafe_allow_html=True)

    if not video_manager:
        st.error("Video manager not available")
        return

    # Search for resources
    st.markdown("### 🔍 Find Educational Resources")

    col1, col2 = st.columns(2)
    with col1:
        search_topic = st.text_input("Topic", placeholder="e.g., pneumonia, stroke")
    with col2:
        section = st.selectbox("Section", [None] + list(study_system.core_sections.keys()) if study_system else [None])

    if search_topic:
        # Radiopaedia links
        st.markdown("#### 📚 Radiopaedia Resources")
        radiopaedia_links = video_manager.get_radiopaedia_links(search_topic, section)

        for link in radiopaedia_links[:5]:
            st.markdown(f"""
            <a href="{link['url']}" target="_blank" class="resource-link">
                <strong>📖 {link['title']}</strong><br>
                <small>Relevance: {link['relevance']:.2f}</small>
            </a>
            """, unsafe_allow_html=True)

        # YouTube recommendations
        st.markdown("#### 🎥 YouTube Educational Videos")
        youtube_links = video_manager.get_youtube_recommendations(search_topic, section)

        for link in youtube_links:
            st.markdown(f"""
            <a href="{link['url']}" target="_blank" class="resource-link">
                <strong>🎬 {link['title']}</strong><br>
                <small>Search: {link.get('query', 'Educational content')}</small>
            </a>
            """, unsafe_allow_html=True)

def show_settings():
    st.markdown('<div class="section-header">⚙️ Multimedia Settings</div>', unsafe_allow_html=True)

    # Audio settings
    st.markdown("### 🔊 Audio Narration Settings")

    if audio_narrator:
        # Voice selection
        available_voices = audio_narrator.get_available_voices()
        voice_names = [f"{voice['name']} ({voice['language']})" for voice in available_voices]

        current_voice_index = 0
        for i, voice in enumerate(available_voices):
            if voice['id'] == audio_narrator.audio_settings.get('voice', 'default'):
                current_voice_index = i
                break

        selected_voice_index = st.selectbox("Voice", range(len(voice_names)),
                                          format_func=lambda x: voice_names[x],
                                          index=current_voice_index)

        selected_voice = available_voices[selected_voice_index]['id']

        # Speed and volume
        col1, col2 = st.columns(2)
        with col1:
            speed = st.slider("Speech Speed (WPM)", 50, 300, audio_narrator.audio_settings['speed'])
        with col2:
            volume = st.slider("Volume", 0.0, 1.0, audio_narrator.audio_settings['volume'])

        # Audio format
        audio_format = st.selectbox("Audio Format", ['mp3', 'wav'],
                                  index=0 if audio_narrator.audio_settings['format'] == 'mp3' else 1)

        if st.button("💾 Save Audio Settings"):
            audio_narrator.set_voice_settings(
                voice=selected_voice,
                speed=speed,
                volume=volume
            )
            audio_narrator.audio_settings['format'] = audio_format
            audio_narrator.save_audio_settings()
            st.success("Audio settings saved!")

        # Test audio
        if st.button("🎵 Test Audio Settings"):
            test_text = "This is a test of your audio settings. You are studying radiology board preparation materials."
            if audio_narrator.active_engine['engine'] == 'built_in':
                test_html = audio_narrator.generate_builtin_audio_html(test_text)
                st.markdown(test_html, unsafe_allow_html=True)
            else:
                test_audio = audio_narrator.generate_audio_file(test_text, "settings_test.mp3")
                if test_audio:
                    st.audio(test_audio)

    # Video settings
    st.markdown("### 🎥 Video Settings")

    if video_manager:
        # Video directories
        st.markdown("**Video Directories:**")
        for directory in video_manager.video_dirs:
            exists = os.path.exists(directory)
            status = "✅" if exists else "❌"
            st.write(f"{status} {directory}")

        # Create missing directories
        if st.button("📁 Create Missing Directories"):
            for directory in video_manager.video_dirs:
                Path(directory).mkdir(parents=True, exist_ok=True)
            st.success("Created missing directories")

        # Clear cache
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Audio Cache"):
                if audio_narrator and audio_narrator.audio_cache_dir.exists():
                    for file in audio_narrator.audio_cache_dir.glob("*.mp3"):
                        file.unlink()
                    st.success("Audio cache cleared")

        with col2:
            if st.button("🔄 Rescan Videos"):
                videos = video_manager.scan_local_videos()
                st.success(f"Rescanned and found {sum(len(v) for v in videos.values())} videos")

def create_audio_question_session(section, question_count, difficulty, auto_play, read_options):
    """Create an audio-enhanced question session"""

    # Create study session
    session = study_system.create_study_session(
        section=None if section == "Mixed" else section,
        question_count=question_count,
        difficulty=difficulty.lower() if difficulty != "Mixed" else "mixed"
    )

    # Enhance with audio
    audio_session = {
        'session': session,
        'auto_play': auto_play,
        'read_options': read_options,
        'current_question': 0,
        'audio_components': {}
    }

    st.session_state.current_audio_session = audio_session
    st.success(f"Created audio question session with {len(session['questions'])} questions")

def display_audio_question_session():
    """Display the audio-enhanced question session"""

    audio_session = st.session_state.current_audio_session
    session = audio_session['session']
    current_q_idx = audio_session['current_question']

    if current_q_idx >= len(session['questions']):
        st.success("🎉 Audio question session completed!")
        if st.button("🔄 Start New Session"):
            st.session_state.current_audio_session = None
            st.rerun()
        return

    question = session['questions'][current_q_idx]

    # Progress
    progress = (current_q_idx + 1) / len(session['questions'])
    st.progress(progress)
    st.write(f"🎵 Audio Question {current_q_idx + 1} of {len(session['questions'])}")

    # Generate question if needed
    if 'generated_content' not in question:
        with st.spinner("🎬 Generating multimedia question..."):
            generated = question_generator.generate_comprehensive_question(
                section=question['section'],
                difficulty=question['difficulty']
            )
            question['generated_content'] = generated

    generated = question.get('generated_content', {})

    if not generated.get('success', False):
        st.error("❌ Error generating question")
        return

    # Audio-enhanced question display
    st.markdown(f"""
    <div class="audio-enhanced">
        <h4>🎯 {question['section']} - {question['difficulty'].title()}</h4>
        <div style="margin: 15px 0;">
            {generated.get('question', 'Question not available')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Audio controls for question
    if st.session_state.audio_enabled and audio_narrator:
        question_text = generated.get('question', '')
        if question_text:
            question_audio = audio_narrator.generate_audio_file(
                question_text,
                f"question_{current_q_idx}.mp3"
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                if isinstance(question_audio, str) and question_audio.endswith('.mp3'):
                    st.audio(question_audio, format="audio/mp3")
                else:
                    st.markdown(question_audio, unsafe_allow_html=True)

            with col2:
                if st.button("🔊 Replay Question"):
                    st.rerun()

    # Answer choices with audio
    if 'options' in generated:
        options = generated['options']

        # Audio for options if enabled
        if st.session_state.audio_enabled and audio_session['read_options']:
            options_text = "Answer choices: "
            for key, value in options.items():
                options_text += f"Option {key}: {value}. "

            options_audio = audio_narrator.generate_audio_file(options_text, f"options_{current_q_idx}.mp3")

            if st.button("🎧 Listen to Answer Choices"):
                if isinstance(options_audio, str) and options_audio.endswith('.mp3'):
                    st.audio(options_audio, format="audio/mp3")
                else:
                    st.markdown(options_audio, unsafe_allow_html=True)

        # Answer selection
        user_answer = st.radio(
            "Select your answer:",
            options=['A', 'B', 'C', 'D'],
            format_func=lambda x: f"{x}) {options.get(x, 'Option not available')}",
            key=f"audio_answer_{current_q_idx}"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("✅ Submit Answer", type="primary"):
                # Record answer and show explanation
                correct = user_answer == generated.get('correct_answer', 'A')

                if correct:
                    st.success(f"🎉 Correct! The answer is {generated.get('correct_answer', 'A')}")
                else:
                    st.error(f"❌ Incorrect. The correct answer is {generated.get('correct_answer', 'A')}")

                # Audio explanation
                explanation = generated.get('explanation', '')
                if explanation and st.session_state.audio_enabled:
                    explanation_audio = audio_narrator.generate_audio_file(explanation, f"explanation_{current_q_idx}.mp3")

                    st.markdown("### 🎙️ Audio Explanation")
                    if isinstance(explanation_audio, str) and explanation_audio.endswith('.mp3'):
                        st.audio(explanation_audio, format="audio/mp3")
                    else:
                        st.markdown(explanation_audio, unsafe_allow_html=True)

                # Show text explanation
                with st.expander("📖 Read Explanation"):
                    st.write(explanation)

        with col2:
            if st.button("⏭️ Next Question"):
                audio_session['current_question'] += 1
                st.rerun()

def display_multimedia_playlist(playlist):
    """Display multimedia study playlist"""

    st.markdown(f"""
    <div class="study-playlist">
        <h3>🎵 Study Playlist: {playlist['topic']}</h3>
        <p><strong>Total Duration:</strong> {playlist.get('total_duration', 0)} minutes</p>
    </div>
    """, unsafe_allow_html=True)

    # Local videos
    if playlist['local_videos']:
        st.markdown("#### 📹 Local Videos")
        for video in playlist['local_videos']:
            with st.expander(f"🎬 {video['title']}"):
                if os.path.exists(video['path']):
                    video_html = video_manager.get_video_embed_html(video['path'])
                    st.markdown(video_html, unsafe_allow_html=True)
                else:
                    st.error("Video file not found")

    # Online resources
    if playlist['online_resources']:
        st.markdown("#### 🌐 Online Resources")
        for resource in playlist['online_resources']:
            st.markdown(f"""
            <a href="{resource['url']}" target="_blank" class="resource-link">
                <strong>{resource['title']}</strong><br>
                <small>Type: {resource['type']}</small>
            </a>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()