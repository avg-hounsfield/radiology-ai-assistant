# src/study/performance_tracker.py
"""
Performance tracking system for radiology CORE preparation
Tracks study streaks, quiz performance, time spent, and learning analytics
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import pandas as pd
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class StudySession:
    """Represents a single study session"""
    date: str
    start_time: str
    end_time: str
    duration_minutes: int
    questions_answered: int
    questions_correct: int
    topics_studied: List[str]
    activity_type: str  # 'quiz', 'search', 'random_question', 'physics_focus'
    documents_used: List[str]

@dataclass
class QuizResult:
    """Represents quiz performance"""
    date: str
    quiz_type: str
    topic: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score_percentage: float
    time_taken_minutes: int
    questions_details: List[Dict]

@dataclass
class PerformanceMetrics:
    """Current performance metrics"""
    total_study_days: int
    current_streak: int
    longest_streak: int
    total_questions_answered: int
    total_questions_correct: int
    overall_accuracy: float
    total_study_time_hours: float
    average_daily_questions: float
    topics_mastery: Dict[str, float]
    weak_areas: List[Dict]
    recent_performance: List[Dict]

class PerformanceTracker:
    """Comprehensive performance and streak tracking system"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.performance_file = os.path.join(data_dir, "performance_data.json")
        self.study_sessions_file = os.path.join(data_dir, "study_sessions.json")
        self.quiz_results_file = os.path.join(data_dir, "quiz_results.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self.performance_data = self._load_performance_data()
        self.study_sessions = self._load_study_sessions()
        self.quiz_results = self._load_quiz_results()
    
    def _load_performance_data(self) -> Dict:
        """Load performance data from JSON file"""
        default_structure = {
            "first_study_date": None,
            "last_study_date": None,
            "total_study_days": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "total_questions_answered": 0,
            "total_questions_correct": 0,
            "total_study_time_minutes": 0,
            "topics_performance": {},
            "daily_activity": {},
            "achievements": []
        }

        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)
                    # Ensure all required keys exist (for backward compatibility)
                    for key, default_value in default_structure.items():
                        if key not in data:
                            data[key] = default_value
                    return data
            except Exception as e:
                print(f"Error loading performance data: {e}")

        # Return default structure
        return default_structure
    
    def _load_study_sessions(self) -> List[StudySession]:
        """Load study sessions from JSON file"""
        if os.path.exists(self.study_sessions_file):
            try:
                with open(self.study_sessions_file, 'r') as f:
                    data = json.load(f)
                    return [StudySession(**session) for session in data]
            except Exception as e:
                print(f"Error loading study sessions: {e}")
        return []
    
    def _load_quiz_results(self) -> List[QuizResult]:
        """Load quiz results from JSON file"""
        if os.path.exists(self.quiz_results_file):
            try:
                with open(self.quiz_results_file, 'r') as f:
                    data = json.load(f)
                    return [QuizResult(**quiz) for quiz in data]
            except Exception as e:
                print(f"Error loading quiz results: {e}")
        return []
    
    def _save_performance_data(self):
        """Save performance data to JSON file"""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_data, f, indent=2)
        except Exception as e:
            print(f"Error saving performance data: {e}")
    
    def _save_study_sessions(self):
        """Save study sessions to JSON file"""
        try:
            with open(self.study_sessions_file, 'w') as f:
                sessions_data = [asdict(session) for session in self.study_sessions]
                json.dump(sessions_data, f, indent=2)
        except Exception as e:
            print(f"Error saving study sessions: {e}")
    
    def _save_quiz_results(self):
        """Save quiz results to JSON file"""
        try:
            with open(self.quiz_results_file, 'w') as f:
                quiz_data = [asdict(quiz) for quiz in self.quiz_results]
                json.dump(quiz_data, f, indent=2)
        except Exception as e:
            print(f"Error saving quiz results: {e}")
    
    def start_study_session(self, activity_type: str = "search") -> str:
        """Start a new study session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Update daily activity
        today = date.today().isoformat()
        if today not in self.performance_data["daily_activity"]:
            self.performance_data["daily_activity"][today] = {
                "date": today,
                "study_started": True,
                "sessions": [],
                "total_questions": 0,
                "correct_questions": 0,
                "study_time_minutes": 0,
                "topics_studied": [],
                "activity_types": []
            }
        
        self.performance_data["daily_activity"][today]["sessions"].append({
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "activity_type": activity_type
        })
        
        self._update_streak()
        self._save_performance_data()
        
        return session_id
    
    def end_study_session(self, session_id: str, questions_answered: int = 0, 
                         questions_correct: int = 0, topics_studied: List[str] = None,
                         documents_used: List[str] = None):
        """End a study session and update metrics"""
        today = date.today().isoformat()
        now = datetime.now()
        
        if today in self.performance_data["daily_activity"]:
            daily_data = self.performance_data["daily_activity"][today]
            
            # Find the session
            for session in daily_data["sessions"]:
                if session["session_id"] == session_id:
                    start_time = datetime.fromisoformat(session["start_time"])
                    duration = int((now - start_time).total_seconds() / 60)  # minutes
                    
                    session["end_time"] = now.isoformat()
                    session["duration_minutes"] = duration
                    session["questions_answered"] = questions_answered
                    session["questions_correct"] = questions_correct
                    
                    # Update daily totals
                    daily_data["total_questions"] += questions_answered
                    daily_data["correct_questions"] += questions_correct
                    daily_data["study_time_minutes"] += duration
                    
                    if topics_studied:
                        daily_data["topics_studied"].extend(topics_studied)
                        daily_data["topics_studied"] = list(set(daily_data["topics_studied"]))
                    
                    # Create StudySession object
                    study_session = StudySession(
                        date=today,
                        start_time=session["start_time"],
                        end_time=now.isoformat(),
                        duration_minutes=duration,
                        questions_answered=questions_answered,
                        questions_correct=questions_correct,
                        topics_studied=topics_studied or [],
                        activity_type=session["activity_type"],
                        documents_used=documents_used or []
                    )
                    
                    self.study_sessions.append(study_session)
                    break
        
        # Update global metrics
        self.performance_data["total_questions_answered"] += questions_answered
        self.performance_data["total_questions_correct"] += questions_correct
        self.performance_data["last_study_date"] = today
        
        if self.performance_data["first_study_date"] is None:
            self.performance_data["first_study_date"] = today
        
        # Update topics performance
        if topics_studied:
            for topic in topics_studied:
                if topic not in self.performance_data["topics_performance"]:
                    self.performance_data["topics_performance"][topic] = {
                        "total_questions": 0,
                        "correct_questions": 0,
                        "accuracy": 0.0,
                        "last_studied": today
                    }
                
                topic_data = self.performance_data["topics_performance"][topic]
                topic_data["total_questions"] += questions_answered
                topic_data["correct_questions"] += questions_correct
                topic_data["accuracy"] = (topic_data["correct_questions"] / 
                                        max(topic_data["total_questions"], 1)) * 100
                topic_data["last_studied"] = today
        
        self._save_performance_data()
        self._save_study_sessions()
    
    def record_quiz_result(self, quiz_type: str, topic: str, total_questions: int,
                          correct_answers: int, time_taken_minutes: int,
                          questions_details: List[Dict] = None) -> QuizResult:
        """Record quiz results"""
        today = date.today().isoformat()
        score_percentage = (correct_answers / max(total_questions, 1)) * 100
        
        quiz_result = QuizResult(
            date=today,
            quiz_type=quiz_type,
            topic=topic,
            total_questions=total_questions,
            correct_answers=correct_answers,
            wrong_answers=total_questions - correct_answers,
            score_percentage=score_percentage,
            time_taken_minutes=time_taken_minutes,
            questions_details=questions_details or []
        )
        
        self.quiz_results.append(quiz_result)
        self._save_quiz_results()
        
        # Update performance data
        self.end_study_session(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            questions_answered=total_questions,
            questions_correct=correct_answers,
            topics_studied=[topic]
        )
        
        return quiz_result
    
    def _update_streak(self):
        """Update study streak based on daily activity"""
        today = date.today()
        daily_activity = self.performance_data["daily_activity"]
        
        # Calculate current streak
        current_streak = 0
        check_date = today
        
        while True:
            date_str = check_date.isoformat()
            if date_str in daily_activity and daily_activity[date_str]["study_started"]:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
            else:
                break
        
        self.performance_data["current_streak"] = current_streak
        
        # Update longest streak
        if current_streak > self.performance_data["longest_streak"]:
            self.performance_data["longest_streak"] = current_streak
        
        # Update total study days
        self.performance_data["total_study_days"] = len([
            day for day in daily_activity.values() 
            if day["study_started"]
        ])
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        
        # Calculate overall accuracy
        total_questions = self.performance_data["total_questions_answered"]
        total_correct = self.performance_data["total_questions_correct"]
        overall_accuracy = (total_correct / max(total_questions, 1)) * 100
        
        # Calculate total study time
        total_minutes = sum([
            day["study_time_minutes"] 
            for day in self.performance_data["daily_activity"].values()
        ])
        total_hours = total_minutes / 60
        
        # Calculate average daily questions
        study_days = max(self.performance_data["total_study_days"], 1)
        avg_daily_questions = total_questions / study_days
        
        # Get topics mastery
        topics_mastery = {
            topic: data["accuracy"]
            for topic, data in self.performance_data["topics_performance"].items()
        }
        
        # Identify weak areas (accuracy < 70%)
        weak_areas = [
            {
                "topic": topic,
                "accuracy": data["accuracy"],
                "total_questions": data["total_questions"]
            }
            for topic, data in self.performance_data["topics_performance"].items()
            if data["accuracy"] < 70 and data["total_questions"] >= 3
        ]
        
        # Sort weak areas by accuracy (worst first)
        weak_areas.sort(key=lambda x: x["accuracy"])
        
        # Get recent performance (last 7 days)
        recent_date = date.today() - timedelta(days=7)
        recent_performance = []
        
        for day_str, day_data in self.performance_data["daily_activity"].items():
            day_date = date.fromisoformat(day_str)
            if day_date >= recent_date:
                recent_performance.append({
                    "date": day_str,
                    "questions": day_data["total_questions"],
                    "accuracy": (day_data["correct_questions"] / 
                               max(day_data["total_questions"], 1)) * 100,
                    "study_time": day_data["study_time_minutes"]
                })
        
        recent_performance.sort(key=lambda x: x["date"])
        
        return PerformanceMetrics(
            total_study_days=self.performance_data["total_study_days"],
            current_streak=self.performance_data["current_streak"],
            longest_streak=self.performance_data["longest_streak"],
            total_questions_answered=total_questions,
            total_questions_correct=total_correct,
            overall_accuracy=overall_accuracy,
            total_study_time_hours=total_hours,
            average_daily_questions=avg_daily_questions,
            topics_mastery=topics_mastery,
            weak_areas=weak_areas[:5],  # Top 5 weak areas
            recent_performance=recent_performance
        )
    
    def get_study_streak_info(self) -> Dict:
        """Get detailed study streak information"""
        metrics = self.get_current_metrics()
        
        return {
            "current_streak": metrics.current_streak,
            "longest_streak": metrics.longest_streak,
            "total_study_days": metrics.total_study_days,
            "streak_status": self._get_streak_status(metrics.current_streak),
            "next_milestone": self._get_next_milestone(metrics.current_streak),
            "consistency_score": self._calculate_consistency_score()
        }
    
    def _get_streak_status(self, streak: int) -> str:
        """Get motivational streak status message"""
        if streak == 0:
            return "Start your learning journey today!"
        elif streak < 3:
            return "Building momentum!"
        elif streak < 7:
            return "Great consistency!"
        elif streak < 14:
            return "Excellent dedication!"
        elif streak < 30:
            return "Outstanding commitment!"
        else:
            return "Exceptional mastery discipline!"
    
    def _get_next_milestone(self, streak: int) -> Dict:
        """Get next streak milestone"""
        milestones = [3, 7, 14, 30, 60, 100, 365]
        
        for milestone in milestones:
            if streak < milestone:
                return {
                    "target": milestone,
                    "days_to_go": milestone - streak,
                    "description": f"{milestone} day streak milestone"
                }
        
        return {
            "target": streak + 30,
            "days_to_go": 30,
            "description": "Next 30-day milestone"
        }
    
    def _calculate_consistency_score(self) -> float:
        """Calculate consistency score based on recent activity (0-100)"""
        # Look at last 14 days
        recent_date = date.today() - timedelta(days=14)
        active_days = 0
        
        for i in range(14):
            check_date = (date.today() - timedelta(days=i)).isoformat()
            if (check_date in self.performance_data["daily_activity"] and 
                self.performance_data["daily_activity"][check_date]["study_started"]):
                active_days += 1
        
        return (active_days / 14) * 100