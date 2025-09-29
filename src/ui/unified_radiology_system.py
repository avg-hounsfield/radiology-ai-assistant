#!/usr/bin/env python3
"""
Unified Radiology Study System
Comprehensive platform combining all radiology learning tools
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import time
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core system imports
from retrieval.rag_system import RadiologyRAGSystem
from study.board_study_system import BoardStudySystem
from study.performance_tracker import PerformanceTracker
from study.spaced_repetition import SpacedRepetitionSystem
from multimedia.video_manager import VideoManager
from multimedia.audio_narrator import AudioNarrator

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Radiology Study System",
    page_icon="🩻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .video-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_systems():
    """Initialize all core systems"""
    try:
        # Initialize systems
        rag_system = RadiologyRAGSystem()
        board_study = BoardStudySystem()
        performance_tracker = PerformanceTracker()
        spaced_repetition = SpacedRepetitionSystem()
        video_manager = VideoManager()
        audio_narrator = AudioNarrator()

        return {
            'rag': rag_system,
            'board_study': board_study,
            'performance': performance_tracker,
            'spaced_repetition': spaced_repetition,
            'video': video_manager,
            'audio': audio_narrator
        }
    except Exception as e:
        st.error(f"Error initializing systems: {e}")
        return None

def render_dashboard(systems):
    """Render main dashboard"""
    st.markdown('<h1 class="main-header">Radiology Study System</h1>', unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Study Streak", f"{systems['performance'].performance_data.get('current_streak', 0)} days")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_questions = systems['performance'].performance_data.get('total_questions_answered', 0)
        st.metric("Questions Answered", total_questions)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        videos = systems['video'].scan_local_videos()
        total_videos = sum(len(v) for v in videos.values())
        st.metric("Videos Available", total_videos)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        accuracy = 0
        if systems['performance'].performance_data.get('total_questions_answered', 0) > 0:
            correct = systems['performance'].performance_data.get('total_questions_correct', 0)
            accuracy = (correct / total_questions) * 100
        st.metric("Accuracy", f"{accuracy:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent activity
    st.subheader("Recent Study Activity")
    daily_activity = systems['performance'].performance_data.get('daily_activity', {})

    if daily_activity:
        activity_df = pd.DataFrame([
            {
                'Date': data['date'],
                'Questions': data.get('total_questions', 0),
                'Study Time': data.get('study_time_minutes', 0),
                'Topics': len(data.get('topics_studied', []))
            }
            for data in daily_activity.values()
        ])

        if not activity_df.empty:
            activity_df['Date'] = pd.to_datetime(activity_df['Date'])
            activity_df = activity_df.sort_values('Date').tail(14)  # Last 14 days

            fig = px.line(activity_df, x='Date', y='Questions',
                         title="Daily Question Practice", height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start studying to see your progress here!")

def render_study_tab(systems):
    """Render study interface"""
    st.header("Board Study Session")

    # Study mode selection
    study_mode = st.selectbox(
        "Select Study Mode",
        ["Practice Questions", "Topic Review", "Weak Areas Focus", "Exam Simulation"]
    )

    # Audio settings
    with st.sidebar:
        st.subheader("Audio Settings")
        enable_audio = st.checkbox("Enable Audio Narration", value=False)

        if enable_audio:
            audio_speed = st.slider("Audio Speed", 0.5, 2.0, 1.0, 0.1)
            auto_play = st.checkbox("Auto-play Questions", value=True)

    # Topic selection
    topics = [
        "Chest", "Abdomen", "Musculoskeletal", "Neuroradiology",
        "Nuclear Medicine", "Breast Imaging", "Interventional",
        "Pediatric", "Physics", "Non-interpretive Skills"
    ]

    selected_topics = st.multiselect("Select Topics", topics, default=["Chest"])

    if st.button("Start Study Session", type="primary"):
        if selected_topics:
            # Start study session
            session_id = systems['performance'].start_study_session("practice")
            st.session_state['current_session'] = session_id
            st.session_state['study_mode'] = study_mode
            st.session_state['selected_topics'] = selected_topics
            st.session_state['enable_audio'] = enable_audio
            st.rerun()

    # Active study session
    if hasattr(st.session_state, 'current_session') and st.session_state.current_session:
        render_active_study_session(systems)

def render_active_study_session(systems):
    """Render active study session"""
    st.subheader("Active Study Session")

    # Generate question if not exists
    if 'current_question' not in st.session_state:
        try:
            # Generate question based on selected topics
            topic = st.session_state.selected_topics[0] if st.session_state.selected_topics else "Chest"
            question_data = systems['board_study'].generate_board_question(topic)
            st.session_state.current_question = question_data
        except Exception as e:
            st.error(f"Error generating question: {e}")
            return

    question = st.session_state.current_question

    # Display question
    st.markdown("### Question")
    st.write(question.get('question', 'Question not available'))

    # Audio playback for question
    if st.session_state.get('enable_audio', False):
        if st.button("🔊 Play Question Audio"):
            try:
                audio_file = systems['audio'].generate_audio_file(
                    question.get('question', ''),
                    "current_question.mp3"
                )
                if audio_file:
                    st.audio(audio_file)
            except Exception as e:
                st.error(f"Audio generation failed: {e}")

    # Display options
    options = question.get('options', [])
    if options:
        st.markdown("### Answer Choices")

        # Create radio button for answers
        answer_choice = st.radio(
            "Select your answer:",
            options,
            key="answer_selection"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Submit Answer", type="primary"):
                st.session_state.answer_submitted = True
                st.session_state.selected_answer = answer_choice
                st.rerun()

        with col2:
            if st.button("Skip Question"):
                st.session_state.current_question = None
                st.rerun()

        with col3:
            if st.button("End Session"):
                systems['performance'].end_study_session(st.session_state.current_session)
                del st.session_state.current_session
                st.success("Study session completed!")
                st.rerun()

    # Show answer and explanation if submitted
    if st.session_state.get('answer_submitted', False):
        render_answer_explanation(systems, question)

def render_answer_explanation(systems, question):
    """Render answer explanation"""
    correct_answer = question.get('correct_answer', '')
    explanation = question.get('explanation', 'No explanation available.')
    selected_answer = st.session_state.get('selected_answer', '')

    # Check if answer is correct
    is_correct = selected_answer == correct_answer

    if is_correct:
        st.success(f"Correct! The answer is: {correct_answer}")
    else:
        st.error(f"Incorrect. The correct answer is: {correct_answer}")
        st.write(f"You selected: {selected_answer}")

    # Show explanation
    st.markdown("### Explanation")
    st.write(explanation)

    # Audio for explanation
    if st.session_state.get('enable_audio', False):
        if st.button("🔊 Play Explanation Audio"):
            try:
                audio_file = systems['audio'].generate_audio_file(
                    explanation,
                    "current_explanation.mp3"
                )
                if audio_file:
                    st.audio(audio_file)
            except Exception as e:
                st.error(f"Audio generation failed: {e}")

    # Record performance
    try:
        systems['performance'].record_question_result(
            question.get('topic', 'General'),
            is_correct,
            question.get('difficulty', 'medium')
        )
    except Exception as e:
        st.error(f"Error recording performance: {e}")

    # Next question button
    if st.button("Next Question", type="primary"):
        # Clear current question and answer state
        st.session_state.current_question = None
        st.session_state.answer_submitted = False
        if 'selected_answer' in st.session_state:
            del st.session_state.selected_answer
        st.rerun()

def render_videos_tab(systems):
    """Render video learning interface"""
    st.header("Video Learning Center")

    # Scan for videos
    videos = systems['video'].scan_local_videos()

    if not any(videos.values()):
        st.warning("No videos found. Add videos to data/videos/ directories.")
        return

    # Video filters
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Filters")

        # Category filter
        categories = [cat for cat, vids in videos.items() if vids]
        selected_category = st.selectbox("Category", ["All"] + categories)

        # Search
        search_term = st.text_input("Search videos")

    with col2:
        st.subheader("Available Videos")

        # Filter videos based on selection
        filtered_videos = {}
        if selected_category == "All":
            filtered_videos = videos
        else:
            filtered_videos = {selected_category: videos.get(selected_category, [])}

        # Apply search filter
        if search_term:
            for category in filtered_videos:
                filtered_videos[category] = [
                    video for video in filtered_videos[category]
                    if search_term.lower() in video['filename'].lower()
                ]

        # Display videos
        for category, video_list in filtered_videos.items():
            if video_list:
                st.markdown(f"**{category.title()}** ({len(video_list)} videos)")

                for video in video_list[:10]:  # Limit display
                    with st.container():
                        st.markdown('<div class="video-container">', unsafe_allow_html=True)

                        col_info, col_action = st.columns([3, 1])

                        with col_info:
                            st.write(f"**{video['filename']}**")
                            st.write(f"Size: {video['size_mb']:.1f} MB")
                            st.write(f"Category: {video['category']}")

                        with col_action:
                            if st.button(f"▶️ Play", key=f"play_{video['filename']}"):
                                st.session_state.current_video = video
                                st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)

    # Video player
    if hasattr(st.session_state, 'current_video') and st.session_state.current_video:
        render_video_player(systems)

def render_video_player(systems):
    """Render video player interface"""
    video = st.session_state.current_video

    st.markdown("---")
    st.subheader(f"Now Playing: {video['filename']}")

    # Video file path
    video_path = video['file_path']

    try:
        # Check if video file exists and is accessible
        if os.path.exists(video_path):
            # For local files, we can show file info but not embed directly
            st.info(f"Video location: {video_path}")
            st.write("Note: To play this video, open it with your preferred video player.")

            # Provide download link if possible
            if st.button("📁 Open Video Location"):
                import subprocess
                subprocess.run(f'explorer /select,"{video_path}"', shell=True)
        else:
            st.error("Video file not accessible. Check file location.")

    except Exception as e:
        st.error(f"Error accessing video: {e}")

    # Related study materials
    st.subheader("Related Study Materials")

    # Generate related questions based on video topic
    video_topic = video.get('category', 'General')

    if st.button("Generate Questions for This Topic"):
        try:
            question = systems['board_study'].generate_board_question(video_topic)
            st.session_state.video_question = question
            st.rerun()
        except Exception as e:
            st.error(f"Error generating question: {e}")

    # Display video-related question
    if hasattr(st.session_state, 'video_question'):
        question = st.session_state.video_question

        st.markdown("### Related Practice Question")
        st.write(question.get('question', ''))

        # Show options
        options = question.get('options', [])
        if options:
            answer = st.radio("Your answer:", options, key="video_question_answer")

            if st.button("Check Answer"):
                correct = question.get('correct_answer', '')
                if answer == correct:
                    st.success(f"Correct! {question.get('explanation', '')}")
                else:
                    st.error(f"Incorrect. Correct answer: {correct}")
                    st.write(question.get('explanation', ''))

def render_search_tab(systems):
    """Render knowledge base search"""
    st.header("Knowledge Base Search")

    # Search interface
    query = st.text_input("Enter your radiology question or topic:", placeholder="e.g., pneumonia on chest CT")

    if query:
        if st.button("Search", type="primary"):
            with st.spinner("Searching knowledge base..."):
                try:
                    # Perform RAG search
                    results = systems['rag'].query(query)

                    if results:
                        st.subheader("Search Results")

                        # Display results
                        for i, result in enumerate(results[:5], 1):
                            with st.expander(f"Result {i}"):
                                st.write(result.get('content', 'No content available'))

                                # Show metadata if available
                                metadata = result.get('metadata', {})
                                if metadata:
                                    st.write("**Source:**", metadata.get('source', 'Unknown'))

                        # Audio narration of results
                        if st.checkbox("Enable audio narration of results"):
                            summary = " ".join([r.get('content', '')[:200] for r in results[:3]])
                            if st.button("🔊 Play Results Summary"):
                                try:
                                    audio_file = systems['audio'].generate_audio_file(
                                        summary, "search_results.mp3"
                                    )
                                    if audio_file:
                                        st.audio(audio_file)
                                except Exception as e:
                                    st.error(f"Audio generation failed: {e}")

                    else:
                        st.info("No results found. Try a different search term.")

                except Exception as e:
                    st.error(f"Search error: {e}")

def render_progress_tab(systems):
    """Render progress tracking and analytics"""
    st.header("Study Progress & Analytics")

    # Performance overview
    perf_data = systems['performance'].performance_data

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Overall Performance")

        total_questions = perf_data.get('total_questions_answered', 0)
        correct_questions = perf_data.get('total_questions_correct', 0)

        if total_questions > 0:
            accuracy = (correct_questions / total_questions) * 100

            # Accuracy gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = accuracy,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Overall Accuracy"},
                delta = {'reference': 70},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some practice questions to see your performance analytics.")

    with col2:
        st.subheader("Study Streak")

        current_streak = perf_data.get('current_streak', 0)
        longest_streak = perf_data.get('longest_streak', 0)

        st.metric("Current Streak", f"{current_streak} days")
        st.metric("Longest Streak", f"{longest_streak} days")

        # Study time
        total_time = perf_data.get('total_study_time_minutes', 0)
        st.metric("Total Study Time", f"{total_time // 60}h {total_time % 60}m")

    # Topic performance
    st.subheader("Performance by Topic")

    topics_performance = perf_data.get('topics_performance', {})
    if topics_performance:
        topic_df = pd.DataFrame([
            {
                'Topic': topic,
                'Questions': data.get('questions_answered', 0),
                'Accuracy': (data.get('questions_correct', 0) / max(data.get('questions_answered', 1), 1)) * 100,
                'Avg Time': data.get('avg_time_seconds', 0)
            }
            for topic, data in topics_performance.items()
        ])

        if not topic_df.empty:
            fig = px.bar(topic_df, x='Topic', y='Accuracy',
                        title="Accuracy by Topic", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Show detailed table
            st.dataframe(topic_df, use_container_width=True)
    else:
        st.info("Complete questions across different topics to see topic-specific performance.")

def main():
    """Main application function"""

    # Initialize systems
    if 'systems' not in st.session_state:
        with st.spinner("Initializing Radiology Study System..."):
            systems = initialize_systems()
            if systems:
                st.session_state.systems = systems
                st.success("System initialized successfully!")
            else:
                st.error("Failed to initialize system. Check logs for details.")
                return

    systems = st.session_state.systems

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")

        tab_selection = st.radio(
            "Select Module:",
            ["🏠 Dashboard", "📚 Study", "🎥 Videos", "🔍 Search", "📊 Progress"],
            index=0
        )

        st.markdown("---")

        # Quick actions
        st.subheader("Quick Actions")

        if st.button("🚀 Start Quick Study", use_container_width=True):
            st.session_state.quick_study = True

        if st.button("📈 View Today's Progress", use_container_width=True):
            tab_selection = "📊 Progress"

        st.markdown("---")

        # System status
        st.subheader("System Status")
        st.success("✅ All systems operational")

        # Audio controls
        st.subheader("Global Audio Settings")
        st.session_state.global_audio = st.checkbox("Enable Audio", value=False)

    # Main content based on tab selection
    if tab_selection == "🏠 Dashboard":
        render_dashboard(systems)
    elif tab_selection == "📚 Study":
        render_study_tab(systems)
    elif tab_selection == "🎥 Videos":
        render_videos_tab(systems)
    elif tab_selection == "🔍 Search":
        render_search_tab(systems)
    elif tab_selection == "📊 Progress":
        render_progress_tab(systems)

    # Handle quick study
    if st.session_state.get('quick_study', False):
        st.session_state.quick_study = False
        # Switch to study tab
        render_study_tab(systems)

if __name__ == "__main__":
    main()