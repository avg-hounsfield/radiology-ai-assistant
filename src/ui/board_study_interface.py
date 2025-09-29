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

# Page configuration
st.set_page_config(
    page_title="Radiology Board Study System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply dark theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00BFFF;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #33A1FF;
        margin: 1.5rem 0 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252a3a 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2d3748;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0, 191, 255, 0.1);
    }
    .study-progress {
        background: linear-gradient(90deg, #00BFFF 0%, #33A1FF 100%);
        height: 20px;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .weak-area {
        background: rgba(239, 68, 68, 0.2);
        border-left: 4px solid #EF4444;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .strong-area {
        background: rgba(16, 185, 129, 0.2);
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .question-card {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
    }
    .answer-option {
        background: #252a3a;
        border: 1px solid #2d3748;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .answer-option:hover {
        border-color: #00BFFF;
        background: #2a3441;
    }
    .correct-answer {
        border-color: #10B981;
        background: rgba(16, 185, 129, 0.2);
    }
    .incorrect-answer {
        border-color: #EF4444;
        background: rgba(239, 68, 68, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize systems
@st.cache_resource
def init_study_systems():
    try:
        study_system = BoardStudySystem()
        question_generator = AdvancedBoardQuestionGenerator()
        rag_system = RadiologyRAGSystem()
        return study_system, question_generator, rag_system
    except Exception as e:
        st.error(f"Error initializing study systems: {e}")
        return None, None, None

study_system, question_generator, rag_system = init_study_systems()

# Session state initialization
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'session_answers' not in st.session_state:
    st.session_state.session_answers = {}
if 'show_explanation' not in st.session_state:
    st.session_state.show_explanation = False

def main():
    # Header
    st.markdown('<div class="main-header">🎯 Radiology Board Study System</div>', unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Study Navigation")
    study_mode = st.sidebar.selectbox(
        "Choose Study Mode",
        [
            "📊 Dashboard & Analytics",
            "📚 Practice Questions",
            "🎯 Targeted Review",
            "⏱️ Exam Simulation",
            "📈 Progress Tracking",
            "🧠 Knowledge Base Query"
        ]
    )

    if study_mode == "📊 Dashboard & Analytics":
        show_dashboard()
    elif study_mode == "📚 Practice Questions":
        show_practice_questions()
    elif study_mode == "🎯 Targeted Review":
        show_targeted_review()
    elif study_mode == "⏱️ Exam Simulation":
        show_exam_simulation()
    elif study_mode == "📈 Progress Tracking":
        show_progress_tracking()
    elif study_mode == "🧠 Knowledge Base Query":
        show_knowledge_base()

def show_dashboard():
    st.markdown('<div class="section-header">Study Dashboard</div>', unsafe_allow_html=True)

    if not study_system:
        st.error("Study system not available")
        return

    # Get study analytics
    analytics = study_system.get_study_analytics(days=30)

    if 'message' in analytics:
        st.info("📚 Start your study journey! No recent study sessions found.")
        st.info("Use the Practice Questions section to begin studying.")
        return

    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #00BFFF;">Study Streak</h3>
            <h2 style="color: #FFFFFF;">{analytics['study_streak']} days</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        accuracy = analytics['overall_accuracy'] * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #00BFFF;">Overall Accuracy</h3>
            <h2 style="color: #FFFFFF;">{accuracy:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #00BFFF;">Questions Completed</h3>
            <h2 style="color: #FFFFFF;">{analytics['total_questions']}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        readiness = analytics['board_readiness_score']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #00BFFF;">Board Readiness</h3>
            <h2 style="color: #FFFFFF;">{readiness['score']*100:.0f}%</h2>
            <p style="color: #9CA3AF;">{readiness['level']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Section performance chart
    if analytics['section_performance']:
        st.markdown('<div class="section-header">Section Performance</div>', unsafe_allow_html=True)

        section_data = []
        for section, perf in analytics['section_performance'].items():
            section_data.append({
                'Section': section,
                'Accuracy': perf['accuracy'] * 100,
                'Questions': perf['total_questions'],
                'Target': 75
            })

        df = pd.DataFrame(section_data)

        fig = px.bar(
            df,
            x='Section',
            y='Accuracy',
            title="Performance by Section",
            color='Accuracy',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig.add_hline(y=75, line_dash="dash", line_color="white",
                     annotation_text="Target: 75%")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Weak areas
    weak_areas = analytics.get('weak_areas', [])
    if weak_areas:
        st.markdown('<div class="section-header">Priority Areas for Improvement</div>', unsafe_allow_html=True)

        for i, area in enumerate(weak_areas[:3]):  # Top 3
            st.markdown(f"""
            <div class="weak-area">
                <strong>#{i+1}: {area['section']}</strong><br>
                Current: {area['accuracy']*100:.1f}% | Target: {area['target']*100:.0f}% |
                Questions Studied: {area['questions_studied']} |
                Priority Score: {area['priority_score']:.2f}
            </div>
            """, unsafe_allow_html=True)

    # Study recommendations
    if analytics.get('recommendations'):
        st.markdown('<div class="section-header">Study Recommendations</div>', unsafe_allow_html=True)
        for rec in analytics['recommendations']:
            st.info(f"💡 {rec}")

def show_practice_questions():
    st.markdown('<div class="section-header">Practice Questions</div>', unsafe_allow_html=True)

    if not study_system or not question_generator:
        st.error("Study systems not available")
        return

    # Study session configuration
    with st.expander("📝 Configure Study Session", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            section = st.selectbox(
                "Focus Area",
                ["All Sections (Comprehensive)"] + list(study_system.core_sections.keys())
            )

        with col2:
            question_count = st.slider("Number of Questions", 5, 50, 15)

        with col3:
            difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Intermediate", "Hard"])

        focus_weak = st.checkbox("Focus on weak areas", value=False)

        if st.button("🚀 Start Study Session", type="primary"):
            # Create new study session
            session_section = None if section == "All Sections (Comprehensive)" else section
            difficulty_clean = difficulty.lower() if difficulty != "Mixed" else "mixed"

            session = study_system.create_study_session(
                section=session_section,
                question_count=question_count,
                difficulty=difficulty_clean,
                focus_weak_areas=focus_weak
            )

            st.session_state.current_session = session
            st.session_state.current_question_index = 0
            st.session_state.session_answers = {}
            st.session_state.show_explanation = False
            st.rerun()

    # Display current session
    if st.session_state.current_session:
        display_question_session()

def display_question_session():
    session = st.session_state.current_session
    current_q_idx = st.session_state.current_question_index

    if current_q_idx >= len(session['questions']):
        # Session complete
        display_session_results()
        return

    question = session['questions'][current_q_idx]

    # Progress bar
    progress = (current_q_idx + 1) / len(session['questions'])
    st.progress(progress)
    st.write(f"Question {current_q_idx + 1} of {len(session['questions'])}")

    # Generate actual question content
    if 'generated_content' not in question:
        with st.spinner("Generating question..."):
            generated = question_generator.generate_comprehensive_question(
                section=question['section'],
                difficulty=question['difficulty'],
                question_type="diagnosis"
            )
            question['generated_content'] = generated

    generated = question.get('generated_content', {})

    if not generated.get('success', False):
        st.error("Error generating question. Skipping to next.")
        st.session_state.current_question_index += 1
        st.rerun()
        return

    # Display question
    st.markdown(f"""
    <div class="question-card">
        <div style="color: #00BFFF; font-weight: bold; margin-bottom: 1rem;">
            {question['section']} - {question['difficulty'].title()} Level
        </div>
        <div style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 2rem;">
            {generated.get('question', 'Question text not available')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Answer choices
    if 'options' in generated:
        answer_key = f"answer_{current_q_idx}"

        options = generated['options']
        user_answer = st.radio(
            "Select your answer:",
            options=['A', 'B', 'C', 'D'],
            format_func=lambda x: f"{x}) {options.get(x, 'Option not available')}",
            key=answer_key
        )

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("Submit Answer", type="primary"):
                # Record answer
                correct = user_answer == generated.get('correct_answer', 'A')
                st.session_state.session_answers[current_q_idx] = {
                    'user_answer': user_answer,
                    'correct': correct,
                    'correct_answer': generated.get('correct_answer', 'A')
                }
                st.session_state.show_explanation = True
                st.rerun()

        if st.session_state.show_explanation and current_q_idx in st.session_state.session_answers:
            # Show explanation
            answer_data = st.session_state.session_answers[current_q_idx]

            if answer_data['correct']:
                st.success(f"✅ Correct! The answer is {answer_data['correct_answer']}")
            else:
                st.error(f"❌ Incorrect. The correct answer is {answer_data['correct_answer']}")

            # Display explanation
            if 'explanation' in generated:
                st.markdown("### Explanation")
                st.write(generated['explanation'])

            with col2:
                if st.button("Next Question"):
                    st.session_state.current_question_index += 1
                    st.session_state.show_explanation = False
                    st.rerun()

def display_session_results():
    session = st.session_state.current_session
    answers = st.session_state.session_answers

    st.markdown('<div class="section-header">Session Complete! 🎉</div>', unsafe_allow_html=True)

    # Calculate results
    total_questions = len(session['questions'])
    correct_answers = sum(1 for ans in answers.values() if ans['correct'])
    accuracy = correct_answers / total_questions if total_questions > 0 else 0

    # Display overall results
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Questions", total_questions)
    with col2:
        st.metric("Correct", correct_answers)
    with col3:
        st.metric("Accuracy", f"{accuracy*100:.1f}%")

    # Detailed breakdown
    if answers:
        # Record session in study system
        for q_idx, answer_data in answers.items():
            study_system.record_answer(
                session['session_id'],
                session['questions'][q_idx]['id'],
                answer_data['user_answer'],
                answer_data['correct'],
                60  # Default time spent
            )

        # Complete session and get analytics
        analytics = study_system.complete_session(session['session_id'])

        if 'error' not in analytics:
            # Show section performance
            if analytics.get('section_performance'):
                st.markdown("### Section Performance")
                for section, perf in analytics['section_performance'].items():
                    accuracy = perf['correct'] / perf['total'] if perf['total'] > 0 else 0
                    st.write(f"**{section}**: {perf['correct']}/{perf['total']} ({accuracy*100:.0f}%)")

            # Show recommendations
            if analytics.get('recommendations'):
                st.markdown("### Study Recommendations")
                for rec in analytics['recommendations']:
                    st.info(f"💡 {rec}")

    if st.button("Start New Session", type="primary"):
        st.session_state.current_session = None
        st.session_state.current_question_index = 0
        st.session_state.session_answers = {}
        st.session_state.show_explanation = False
        st.rerun()

def show_targeted_review():
    st.markdown('<div class="section-header">Targeted Review</div>', unsafe_allow_html=True)

    if not study_system:
        st.error("Study system not available")
        return

    # Get weak areas
    analytics = study_system.get_study_analytics(days=30)
    weak_areas = analytics.get('weak_areas', [])

    if not weak_areas:
        st.info("📚 Complete some practice questions first to identify areas for targeted review.")
        return

    st.write("Focus your study time on areas that need the most improvement:")

    for i, area in enumerate(weak_areas[:5]):
        with st.expander(f"#{i+1}: {area['section']} - {area['accuracy']*100:.1f}% accuracy"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Current Performance**: {area['accuracy']*100:.1f}%")
                st.write(f"**Target**: {area['target']*100:.0f}%")
                st.write(f"**Questions Studied**: {area['questions_studied']}")
                st.write(f"**Exam Weight**: {area['exam_weight']*100:.0f}%")

            with col2:
                if st.button(f"Study {area['section']}", key=f"study_{i}"):
                    # Create focused session
                    session = study_system.create_study_session(
                        section=area['section'],
                        question_count=10,
                        difficulty="mixed",
                        focus_weak_areas=True
                    )
                    st.session_state.current_session = session
                    st.session_state.current_question_index = 0
                    st.session_state.session_answers = {}
                    st.session_state.show_explanation = False
                    st.rerun()

def show_exam_simulation():
    st.markdown('<div class="section-header">Board Exam Simulation</div>', unsafe_allow_html=True)

    if not study_system:
        st.error("Study system not available")
        return

    st.write("Practice with full-length board exam simulations:")

    col1, col2 = st.columns(2)

    with col1:
        exam_length = st.selectbox("Exam Length", [50, 100, 200], index=2)
        time_limit = st.selectbox("Time Limit (minutes)", [60, 120, 240], index=2)

    with col2:
        st.info(f"""
        **Exam Configuration:**
        - {exam_length} questions
        - {time_limit} minutes
        - {time_limit/exam_length:.1f} minutes per question
        - Questions weighted by CORE percentages
        """)

    if st.button("🚀 Start Exam Simulation", type="primary"):
        simulation = study_system.generate_exam_simulation(exam_length, time_limit)
        st.session_state.current_session = simulation
        st.session_state.current_question_index = 0
        st.session_state.session_answers = {}
        st.rerun()

def show_progress_tracking():
    st.markdown('<div class="section-header">Progress Tracking</div>', unsafe_allow_html=True)

    if not study_system:
        st.error("Study system not available")
        return

    # Time period selection
    period = st.selectbox("Analysis Period", ["Last 7 days", "Last 30 days", "Last 90 days"])
    days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
    days = days_map[period]

    analytics = study_system.get_study_analytics(days=days)

    if 'message' in analytics:
        st.info(analytics['message'])
        return

    # Daily performance trend
    if analytics.get('daily_trends'):
        st.markdown("### Daily Performance Trend")

        daily_data = analytics['daily_trends']
        dates = list(daily_data.keys())
        accuracies = [data['accuracy'] * 100 for data in daily_data.values()]
        questions = [data['questions'] for data in daily_data.values()]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=accuracies, mode='lines+markers',
            name='Accuracy %', line=dict(color='#00BFFF', width=3)
        ))
        fig.add_trace(go.Bar(
            x=dates, y=questions, name='Questions',
            yaxis='y2', opacity=0.6, marker_color='#33A1FF'
        ))

        fig.update_layout(
            title="Daily Study Progress",
            xaxis_title="Date",
            yaxis=dict(title="Accuracy (%)", side="left"),
            yaxis2=dict(title="Questions", side="right", overlaying="y"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Board readiness progress
    readiness = analytics.get('board_readiness_score', {})
    if readiness:
        st.markdown("### Board Readiness Assessment")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Readiness Score",
                f"{readiness['score']*100:.1f}%",
                f"Target: {readiness['target_score']*100:.0f}%"
            )
            st.write(f"**Level**: {readiness['level']}")

        with col2:
            ready_sections = readiness.get('sections_ready', [])
            need_work = readiness.get('sections_need_work', [])

            if ready_sections:
                st.success(f"**Ready**: {', '.join(ready_sections)}")
            if need_work:
                st.error(f"**Need Work**: {', '.join(need_work)}")

def show_knowledge_base():
    st.markdown('<div class="section-header">Knowledge Base Query</div>', unsafe_allow_html=True)

    if not rag_system:
        st.error("Knowledge base system not available")
        return

    st.write("Ask questions about radiology concepts, cases, or board topics:")

    query = st.text_input("Enter your question:", placeholder="e.g., What are the signs of pneumonia on chest X-ray?")

    if query:
        with st.spinner("Searching knowledge base..."):
            result = rag_system.query(query, n_results=5)

        if result.get('success', False):
            st.markdown("### Answer")
            st.write(result.get('answer', 'No answer available'))

            # Show sources
            sources = result.get('sources', [])
            if sources:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(sources, 1):
                        st.write(f"**Source {i}**: {source}")

            # Show retrieval info
            retrieval_info = result.get('retrieval_info', {})
            if retrieval_info:
                st.info(f"Retrieved {retrieval_info.get('chunks_retrieved', 0)} relevant chunks")
        else:
            st.error("Error processing query. Please try again.")

if __name__ == "__main__":
    main()