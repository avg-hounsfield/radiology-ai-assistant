# src/study/board_study_system.py
"""
Comprehensive board study system for radiology residency
Includes practice questions, progress tracking, spaced repetition, and exam simulation
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import logging
import numpy as np

class BoardStudySystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # CORE exam structure and weighting
        self.core_sections = {
            'Physics & Safety': {
                'weight': 0.15,
                'topics': [
                    'Radiation Physics', 'Radiation Safety', 'X-ray Production',
                    'CT Physics', 'MR Physics', 'Ultrasound Physics',
                    'Nuclear Medicine Physics', 'Radiation Biology',
                    'Quality Assurance', 'Dose Optimization'
                ]
            },
            'Cardiothoracic': {
                'weight': 0.20,
                'topics': [
                    'Chest X-ray', 'Chest CT', 'Pulmonary Embolism',
                    'Pneumonia', 'Lung Nodules', 'Lung Cancer',
                    'Cardiac Imaging', 'Coronary CTA', 'Pulmonary Edema',
                    'Pneumothorax', 'Pleural Disease'
                ]
            },
            'Neuroradiology': {
                'weight': 0.15,
                'topics': [
                    'Acute Stroke', 'Brain Hemorrhage', 'Head Trauma',
                    'Brain Tumors', 'Spine Imaging', 'Spinal Trauma',
                    'CNS Infections', 'Demyelinating Disease',
                    'Pediatric Neuro', 'Vascular Malformations'
                ]
            },
            'Musculoskeletal': {
                'weight': 0.10,
                'topics': [
                    'Fractures', 'Joint Disease', 'Bone Tumors',
                    'Soft Tissue Masses', 'Spine Pathology',
                    'Sports Injuries', 'Arthritis', 'Osteomyelitis',
                    'Metabolic Bone Disease', 'Congenital Anomalies'
                ]
            },
            'Abdominal & Pelvic': {
                'weight': 0.15,
                'topics': [
                    'Liver Imaging', 'Pancreatic Disease', 'Biliary Tract',
                    'Bowel Obstruction', 'Appendicitis', 'Diverticulitis',
                    'Pelvic Imaging', 'Renal Masses', 'Urinary Tract',
                    'Gynecologic Imaging'
                ]
            },
            'Breast Imaging': {
                'weight': 0.08,
                'topics': [
                    'Mammography', 'Breast MRI', 'Breast Ultrasound',
                    'BI-RADS Classification', 'Breast Cancer',
                    'Benign Breast Disease', 'High-Risk Lesions',
                    'Breast Interventions', 'Male Breast Disease'
                ]
            },
            'Pediatric Radiology': {
                'weight': 0.07,
                'topics': [
                    'Congenital Anomalies', 'Pediatric Trauma',
                    'Pediatric Chest', 'Pediatric Abdomen',
                    'Pediatric CNS', 'Growth and Development',
                    'Non-accidental Trauma', 'Pediatric MSK'
                ]
            },
            'Nuclear Medicine': {
                'weight': 0.10,
                'topics': [
                    'Bone Scintigraphy', 'Cardiac Nuclear',
                    'Thyroid Imaging', 'PET/CT', 'Renal Scintigraphy',
                    'Hepatobiliary Imaging', 'Pulmonary Scintigraphy',
                    'Radiopharmaceuticals', 'Therapy Applications'
                ]
            }
        }

        # Study progress tracking
        self.data_dir = Path("data/study_progress")
        self.data_dir.mkdir(exist_ok=True)

        # Load or initialize study data
        self.study_history = self.load_study_history()
        self.question_bank = self.load_question_bank()
        self.weak_areas = self.load_weak_areas()

    def load_study_history(self) -> Dict:
        """Load study session history"""
        history_file = self.data_dir / "study_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return {
            'sessions': [],
            'total_questions': 0,
            'correct_answers': 0,
            'section_performance': {},
            'daily_goals': {},
            'study_streak': 0,
            'last_study_date': None
        }

    def load_question_bank(self) -> Dict:
        """Load generated question bank"""
        qbank_file = self.data_dir / "question_bank.json"
        if qbank_file.exists():
            with open(qbank_file, 'r') as f:
                return json.load(f)
        return {'questions': [], 'last_updated': None}

    def load_weak_areas(self) -> Dict:
        """Load identified weak areas for targeted study"""
        weak_file = self.data_dir / "weak_areas.json"
        if weak_file.exists():
            with open(weak_file, 'r') as f:
                return json.load(f)
        return {}

    def save_study_data(self):
        """Save all study data"""
        # Save study history
        history_file = self.data_dir / "study_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.study_history, f, indent=2)

        # Save question bank
        qbank_file = self.data_dir / "question_bank.json"
        with open(qbank_file, 'w') as f:
            json.dump(self.question_bank, f, indent=2)

        # Save weak areas
        weak_file = self.data_dir / "weak_areas.json"
        with open(weak_file, 'w') as f:
            json.dump(self.weak_areas, f, indent=2)

    def create_study_session(self, section: str = None, question_count: int = 10,
                           difficulty: str = "mixed", focus_weak_areas: bool = False) -> Dict:
        """Create a customized study session"""

        session = {
            'session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'date': datetime.now().isoformat(),
            'section': section,
            'question_count': question_count,
            'difficulty': difficulty,
            'focus_weak_areas': focus_weak_areas,
            'questions': [],
            'completed': False,
            'score': 0,
            'time_spent': 0
        }

        # Generate questions for session
        if section:
            # Section-specific study
            topics = self.core_sections[section]['topics']
            session['questions'] = self.generate_section_questions(section, topics, question_count, difficulty)
        elif focus_weak_areas:
            # Focus on weak areas
            session['questions'] = self.generate_weak_area_questions(question_count, difficulty)
        else:
            # Mixed comprehensive study
            session['questions'] = self.generate_comprehensive_questions(question_count, difficulty)

        return session

    def generate_section_questions(self, section: str, topics: List[str],
                                 count: int, difficulty: str) -> List[Dict]:
        """Generate questions focused on specific section"""
        questions = []

        # Import question generator
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            from llm.advanced_question_generator import AdvancedBoardQuestionGenerator

            generator = AdvancedBoardQuestionGenerator()

            for i in range(count):
                # Select topic
                topic = random.choice(topics)

                # Adjust difficulty
                if difficulty == "mixed":
                    q_difficulty = random.choice(["easy", "intermediate", "hard"])
                else:
                    q_difficulty = difficulty

                # Generate question
                question_data = generator.generate_comprehensive_question(
                    section=section.lower(),
                    difficulty=q_difficulty
                )

                if question_data.get('success', False):
                    questions.append({
                        'id': f"{section}_{i+1}",
                        'section': section,
                        'topic': topic,
                        'difficulty': q_difficulty,
                        'question_text': question_data['question'],
                        'user_answer': None,
                        'correct': None,
                        'time_spent': 0,
                        'explanation_viewed': False
                    })

        except Exception as e:
            self.logger.error(f"Error generating questions: {e}")
            # Fallback to basic questions
            questions = []
            for i in range(count):
                questions.append({
                    'id': f"fallback_{i+1}",
                    'section': section,
                    'topic': 'general',
                    'difficulty': difficulty,
                    'question_text': f"Sample question {i+1} for {section}",
                    'user_answer': None,
                    'correct': None,
                    'time_spent': 0,
                    'explanation_viewed': False
                })

        return questions

    def generate_weak_area_questions(self, count: int, difficulty: str) -> List[Dict]:
        """Generate questions targeting identified weak areas"""
        questions = []

        if not self.weak_areas:
            # No weak areas identified yet, generate comprehensive
            return self.generate_comprehensive_questions(count, difficulty)

        # Sort weak areas by performance (worst first)
        sorted_weak = sorted(self.weak_areas.items(),
                           key=lambda x: x[1].get('accuracy', 0))

        # Focus on top 3 weakest areas
        focus_areas = [area for area, _ in sorted_weak[:3]]

        for i in range(count):
            area = random.choice(focus_areas)

            # Generate targeted question
            # Implementation would connect to question generator
            questions.append({
                'id': f"weak_{i+1}",
                'section': area,
                'topic': 'targeted_review',
                'difficulty': difficulty,
                'question_text': f"Targeted review question for {area}",
                'user_answer': None,
                'correct': None,
                'time_spent': 0,
                'explanation_viewed': False
            })

        return questions

    def generate_comprehensive_questions(self, count: int, difficulty: str) -> List[Dict]:
        """Generate mixed questions across all sections"""
        questions = []

        # Weight questions by CORE exam percentages
        section_weights = [(section, data['weight'])
                          for section, data in self.core_sections.items()]

        for i in range(count):
            # Select section based on weights
            section = self.weighted_random_choice(section_weights)
            topics = self.core_sections[section]['topics']
            topic = random.choice(topics)

            questions.append({
                'id': f"comp_{i+1}",
                'section': section,
                'topic': topic,
                'difficulty': difficulty if difficulty != "mixed" else random.choice(["easy", "intermediate", "hard"]),
                'question_text': f"Comprehensive question about {topic} in {section}",
                'user_answer': None,
                'correct': None,
                'time_spent': 0,
                'explanation_viewed': False
            })

        return questions

    def weighted_random_choice(self, weighted_choices: List[Tuple[str, float]]) -> str:
        """Select item based on weights"""
        total_weight = sum(weight for _, weight in weighted_choices)
        r = random.uniform(0, total_weight)

        for choice, weight in weighted_choices:
            if r <= weight:
                return choice
            r -= weight

        return weighted_choices[-1][0]  # Fallback

    def record_answer(self, session_id: str, question_id: str,
                     user_answer: str, correct: bool, time_spent: float):
        """Record user's answer and update progress"""

        # Update study history
        session = self.find_session(session_id)
        if session:
            # Find and update question
            for question in session['questions']:
                if question['id'] == question_id:
                    question['user_answer'] = user_answer
                    question['correct'] = correct
                    question['time_spent'] = time_spent
                    break

            # Update session stats
            total_correct = sum(1 for q in session['questions'] if q.get('correct'))
            total_answered = sum(1 for q in session['questions'] if q.get('user_answer'))

            if total_answered > 0:
                session['score'] = total_correct / total_answered

        # Update weak areas
        question = self.find_question(session_id, question_id)
        if question:
            section = question['section']
            if section not in self.weak_areas:
                self.weak_areas[section] = {
                    'total_questions': 0,
                    'correct_answers': 0,
                    'accuracy': 0,
                    'last_studied': None
                }

            self.weak_areas[section]['total_questions'] += 1
            if correct:
                self.weak_areas[section]['correct_answers'] += 1

            self.weak_areas[section]['accuracy'] = (
                self.weak_areas[section]['correct_answers'] /
                self.weak_areas[section]['total_questions']
            )
            self.weak_areas[section]['last_studied'] = datetime.now().isoformat()

        # Save progress
        self.save_study_data()

    def find_session(self, session_id: str) -> Optional[Dict]:
        """Find session by ID"""
        for session in self.study_history['sessions']:
            if session['session_id'] == session_id:
                return session
        return None

    def find_question(self, session_id: str, question_id: str) -> Optional[Dict]:
        """Find question by session and question ID"""
        session = self.find_session(session_id)
        if session:
            for question in session['questions']:
                if question['id'] == question_id:
                    return question
        return None

    def complete_session(self, session_id: str) -> Dict:
        """Complete study session and generate analytics"""
        session = self.find_session(session_id)
        if not session:
            return {'error': 'Session not found'}

        session['completed'] = True
        session['completion_date'] = datetime.now().isoformat()

        # Calculate comprehensive stats
        total_questions = len(session['questions'])
        correct_answers = sum(1 for q in session['questions'] if q.get('correct'))
        accuracy = correct_answers / total_questions if total_questions > 0 else 0

        # Section-wise performance
        section_stats = {}
        for question in session['questions']:
            section = question['section']
            if section not in section_stats:
                section_stats[section] = {'total': 0, 'correct': 0}

            section_stats[section]['total'] += 1
            if question.get('correct'):
                section_stats[section]['correct'] += 1

        # Time analysis
        total_time = sum(q.get('time_spent', 0) for q in session['questions'])
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 0

        # Study recommendations
        recommendations = self.generate_study_recommendations(session, section_stats)

        analytics = {
            'session_id': session_id,
            'overall_accuracy': accuracy,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'total_time_minutes': total_time / 60,
            'avg_time_per_question_seconds': avg_time_per_question,
            'section_performance': section_stats,
            'recommendations': recommendations,
            'areas_to_review': [section for section, stats in section_stats.items()
                              if stats['correct'] / stats['total'] < 0.7]
        }

        # Update overall study history
        self.study_history['total_questions'] += total_questions
        self.study_history['correct_answers'] += correct_answers
        self.study_history['sessions'].append(session)

        # Update study streak
        self.update_study_streak()

        self.save_study_data()
        return analytics

    def generate_study_recommendations(self, session: Dict, section_stats: Dict) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []

        # Performance-based recommendations
        weak_sections = [section for section, stats in section_stats.items()
                        if stats['correct'] / stats['total'] < 0.6]

        if weak_sections:
            recommendations.append(f"Focus additional study time on: {', '.join(weak_sections)}")

        # Time-based recommendations
        slow_questions = [q for q in session['questions'] if q.get('time_spent', 0) > 120]
        if len(slow_questions) > len(session['questions']) * 0.3:
            recommendations.append("Consider timing practice to improve speed")

        # Difficulty recommendations
        hard_questions = [q for q in session['questions'] if q.get('difficulty') == 'hard']
        hard_accuracy = sum(1 for q in hard_questions if q.get('correct')) / len(hard_questions) if hard_questions else 1

        if hard_accuracy < 0.5:
            recommendations.append("Review advanced concepts and practice more difficult questions")

        return recommendations

    def update_study_streak(self):
        """Update consecutive study days streak"""
        today = datetime.now().date()
        last_study = self.study_history.get('last_study_date')

        if last_study:
            last_date = datetime.fromisoformat(last_study).date()
            days_diff = (today - last_date).days

            if days_diff == 1:
                # Consecutive day
                self.study_history['study_streak'] += 1
            elif days_diff > 1:
                # Streak broken
                self.study_history['study_streak'] = 1
            # Same day = no change
        else:
            # First study session
            self.study_history['study_streak'] = 1

        self.study_history['last_study_date'] = today.isoformat()

    def get_study_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive study analytics"""

        # Recent performance
        recent_sessions = [s for s in self.study_history['sessions']
                          if self.is_recent_session(s, days)]

        if not recent_sessions:
            return {'message': 'No recent study sessions found'}

        # Overall metrics
        total_recent_questions = sum(len(s['questions']) for s in recent_sessions)
        total_recent_correct = sum(sum(1 for q in s['questions'] if q.get('correct'))
                                 for s in recent_sessions)

        recent_accuracy = total_recent_correct / total_recent_questions if total_recent_questions > 0 else 0

        # Section performance
        section_performance = {}
        for section in self.core_sections.keys():
            section_questions = []
            for session in recent_sessions:
                section_questions.extend([q for q in session['questions'] if q['section'] == section])

            if section_questions:
                correct = sum(1 for q in section_questions if q.get('correct'))
                section_performance[section] = {
                    'total_questions': len(section_questions),
                    'correct_answers': correct,
                    'accuracy': correct / len(section_questions),
                    'target_accuracy': 0.75  # Target for board readiness
                }

        # Progress trends
        daily_performance = self.calculate_daily_trends(recent_sessions)

        # Board readiness assessment
        readiness_score = self.calculate_board_readiness(section_performance)

        return {
            'period_days': days,
            'total_sessions': len(recent_sessions),
            'total_questions': total_recent_questions,
            'overall_accuracy': recent_accuracy,
            'study_streak': self.study_history['study_streak'],
            'section_performance': section_performance,
            'daily_trends': daily_performance,
            'board_readiness_score': readiness_score,
            'weak_areas': self.get_priority_weak_areas(),
            'recommendations': self.get_study_plan_recommendations(section_performance)
        }

    def calculate_board_readiness(self, section_performance: Dict) -> Dict:
        """Calculate overall board readiness score"""

        if not section_performance:
            return {'score': 0, 'level': 'Needs significant preparation'}

        # Weight by CORE exam percentages
        weighted_score = 0
        total_weight = 0

        for section, performance in section_performance.items():
            section_weight = self.core_sections[section]['weight']
            section_score = performance['accuracy']

            weighted_score += section_score * section_weight
            total_weight += section_weight

        overall_score = weighted_score / total_weight if total_weight > 0 else 0

        # Readiness levels
        if overall_score >= 0.85:
            level = "Excellent - Board ready"
        elif overall_score >= 0.75:
            level = "Good - Nearly board ready"
        elif overall_score >= 0.65:
            level = "Fair - More preparation needed"
        else:
            level = "Needs significant preparation"

        return {
            'score': overall_score,
            'level': level,
            'target_score': 0.75,
            'sections_ready': [s for s, p in section_performance.items() if p['accuracy'] >= 0.75],
            'sections_need_work': [s for s, p in section_performance.items() if p['accuracy'] < 0.65]
        }

    def is_recent_session(self, session: Dict, days: int) -> bool:
        """Check if session is within recent days"""
        if not session.get('date'):
            return False

        session_date = datetime.fromisoformat(session['date']).date()
        cutoff_date = datetime.now().date() - timedelta(days=days)

        return session_date >= cutoff_date

    def calculate_daily_trends(self, sessions: List[Dict]) -> Dict:
        """Calculate daily performance trends"""
        daily_data = {}

        for session in sessions:
            date = datetime.fromisoformat(session['date']).date().isoformat()

            if date not in daily_data:
                daily_data[date] = {'questions': 0, 'correct': 0, 'sessions': 0}

            daily_data[date]['sessions'] += 1
            daily_data[date]['questions'] += len(session['questions'])
            daily_data[date]['correct'] += sum(1 for q in session['questions'] if q.get('correct'))

        # Calculate accuracies
        for date_data in daily_data.values():
            date_data['accuracy'] = date_data['correct'] / date_data['questions'] if date_data['questions'] > 0 else 0

        return daily_data

    def get_priority_weak_areas(self) -> List[Dict]:
        """Get prioritized list of weak areas for focused study"""
        weak_list = []

        for section, data in self.weak_areas.items():
            if data['accuracy'] < 0.7:  # Below target
                priority_score = (0.7 - data['accuracy']) * self.core_sections[section]['weight']

                weak_list.append({
                    'section': section,
                    'accuracy': data['accuracy'],
                    'target': 0.75,
                    'priority_score': priority_score,
                    'exam_weight': self.core_sections[section]['weight'],
                    'questions_studied': data['total_questions']
                })

        # Sort by priority score (highest first)
        weak_list.sort(key=lambda x: x['priority_score'], reverse=True)

        return weak_list[:5]  # Top 5 priorities

    def get_study_plan_recommendations(self, section_performance: Dict) -> List[str]:
        """Generate specific study plan recommendations"""
        recommendations = []

        # Identify patterns and give specific advice
        weak_sections = [s for s, p in section_performance.items() if p['accuracy'] < 0.65]
        strong_sections = [s for s, p in section_performance.items() if p['accuracy'] >= 0.8]

        if len(weak_sections) > 4:
            recommendations.append("Consider extending study timeline - multiple areas need significant work")

        if 'Physics & Safety' in weak_sections:
            recommendations.append("Physics is high-yield (15% of exam) - prioritize this area immediately")

        if 'Cardiothoracic' in weak_sections:
            recommendations.append("Cardiothoracic is 20% of exam - focus on chest imaging fundamentals")

        if strong_sections:
            recommendations.append(f"Maintain proficiency in strong areas: {', '.join(strong_sections[:2])}")

        # Study frequency recommendations
        total_questions = sum(p['total_questions'] for p in section_performance.values())
        if total_questions < 100:
            recommendations.append("Increase study frequency - aim for 20-30 questions daily")

        return recommendations

    def generate_exam_simulation(self, exam_length: int = 200, time_limit: int = 240) -> Dict:
        """Generate full board exam simulation"""

        simulation = {
            'simulation_id': f"exam_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'exam_length': exam_length,
            'time_limit_minutes': time_limit,
            'questions': [],
            'started': False,
            'completed': False,
            'start_time': None,
            'end_time': None
        }

        # Generate questions following CORE proportions
        questions_per_section = {}
        for section, data in self.core_sections.items():
            questions_per_section[section] = int(exam_length * data['weight'])

        # Adjust for rounding
        total_assigned = sum(questions_per_section.values())
        if total_assigned < exam_length:
            # Add remaining questions to largest sections
            largest_sections = sorted(questions_per_section.keys(),
                                    key=lambda x: questions_per_section[x], reverse=True)
            for section in largest_sections[:exam_length - total_assigned]:
                questions_per_section[section] += 1

        # Generate questions for each section
        question_id = 1
        for section, count in questions_per_section.items():
            topics = self.core_sections[section]['topics']

            for i in range(count):
                topic = random.choice(topics)
                difficulty = random.choices(['easy', 'intermediate', 'hard'],
                                          weights=[0.3, 0.5, 0.2])[0]

                simulation['questions'].append({
                    'id': question_id,
                    'section': section,
                    'topic': topic,
                    'difficulty': difficulty,
                    'question_text': f"Exam simulation question {question_id} - {topic}",
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': random.choice(['A', 'B', 'C', 'D']),
                    'user_answer': None,
                    'correct': None,
                    'time_spent': 0,
                    'marked_for_review': False
                })
                question_id += 1

        # Shuffle questions
        random.shuffle(simulation['questions'])

        return simulation