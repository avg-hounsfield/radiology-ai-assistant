# src/study/spaced_repetition.py
"""
Spaced repetition system for optimal board exam preparation
Based on evidence-based learning science for maximum retention
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

class SpacedRepetitionSystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Spaced repetition intervals (in days)
        # Based on SuperMemo SM-2 algorithm with modifications for medical education
        self.base_intervals = [1, 3, 7, 14, 30, 60, 120, 240]

        # Performance thresholds
        self.mastery_threshold = 0.85  # 85% accuracy for mastery
        self.review_threshold = 0.70   # Below 70% needs immediate review

        # Data storage
        self.data_dir = Path("data/spaced_repetition")
        self.data_dir.mkdir(exist_ok=True)

        # Load or initialize data
        self.card_data = self.load_card_data()
        self.review_schedule = self.load_review_schedule()

    def load_card_data(self) -> Dict:
        """Load flashcard data and performance history"""
        card_file = self.data_dir / "cards.json"
        if card_file.exists():
            with open(card_file, 'r') as f:
                return json.load(f)
        return {}

    def load_review_schedule(self) -> Dict:
        """Load review schedule"""
        schedule_file = self.data_dir / "schedule.json"
        if schedule_file.exists():
            with open(schedule_file, 'r') as f:
                return json.load(f)
        return {'daily_reviews': {}, 'next_review_dates': {}}

    def save_data(self):
        """Save all spaced repetition data"""
        # Save card data
        card_file = self.data_dir / "cards.json"
        with open(card_file, 'w') as f:
            json.dump(self.card_data, f, indent=2)

        # Save schedule
        schedule_file = self.data_dir / "schedule.json"
        with open(schedule_file, 'w') as f:
            json.dump(self.review_schedule, f, indent=2)

    def add_card(self, card_id: str, content: Dict) -> None:
        """Add new flashcard to spaced repetition system"""

        if card_id not in self.card_data:
            self.card_data[card_id] = {
                'content': content,
                'created_date': datetime.now().isoformat(),
                'review_count': 0,
                'correct_count': 0,
                'last_review': None,
                'next_review': datetime.now().isoformat(),  # Review immediately
                'interval_index': 0,  # Start with first interval
                'ease_factor': 2.5,   # SuperMemo ease factor
                'difficulty': content.get('difficulty', 'intermediate'),
                'section': content.get('section', 'general'),
                'mastery_level': 'learning',  # learning, reviewing, mastered
                'average_response_time': 0,
                'last_response_times': [],
                'priority_score': self.calculate_priority_score(content)
            }

            self.schedule_review(card_id, datetime.now())
            self.save_data()
            self.logger.info(f"Added card {card_id} to spaced repetition system")

    def calculate_priority_score(self, content: Dict) -> float:
        """Calculate priority score based on content importance"""

        base_score = 1.0

        # Higher priority for board exam sections
        section_weights = {
            'Physics & Safety': 1.5,
            'Cardiothoracic': 1.4,
            'Neuroradiology': 1.3,
            'Abdominal & Pelvic': 1.3,
            'Nuclear Medicine': 1.2,
            'Musculoskeletal': 1.1,
            'Breast Imaging': 1.1,
            'Pediatric Radiology': 1.0
        }

        section = content.get('section', 'general')
        section_weight = section_weights.get(section, 1.0)

        # Higher priority for difficult content
        difficulty_weights = {
            'hard': 1.3,
            'intermediate': 1.0,
            'easy': 0.8
        }

        difficulty = content.get('difficulty', 'intermediate')
        difficulty_weight = difficulty_weights.get(difficulty, 1.0)

        # Higher priority for high-yield topics
        high_yield_keywords = [
            'emergency', 'critical', 'acute', 'radiation safety', 'dose',
            'contrast reaction', 'differential diagnosis', 'first-line'
        ]

        content_text = str(content).lower()
        high_yield_bonus = sum(0.1 for keyword in high_yield_keywords
                              if keyword in content_text)

        priority_score = base_score * section_weight * difficulty_weight + high_yield_bonus

        return min(priority_score, 3.0)  # Cap at 3.0

    def record_review(self, card_id: str, correct: bool, response_time: float) -> Dict:
        """Record review result and update spaced repetition schedule"""

        if card_id not in self.card_data:
            return {'error': 'Card not found'}

        card = self.card_data[card_id]
        now = datetime.now()

        # Update review statistics
        card['review_count'] += 1
        card['last_review'] = now.isoformat()

        if correct:
            card['correct_count'] += 1

        # Update response times
        card['last_response_times'].append(response_time)
        if len(card['last_response_times']) > 5:
            card['last_response_times'] = card['last_response_times'][-5:]

        card['average_response_time'] = sum(card['last_response_times']) / len(card['last_response_times'])

        # Calculate current accuracy
        accuracy = card['correct_count'] / card['review_count']

        # Update spaced repetition parameters
        self.update_repetition_schedule(card_id, correct, accuracy, response_time)

        # Update mastery level
        self.update_mastery_level(card_id, accuracy)

        self.save_data()

        return {
            'card_id': card_id,
            'accuracy': accuracy,
            'mastery_level': card['mastery_level'],
            'next_review': card['next_review'],
            'interval_days': self.get_current_interval_days(card)
        }

    def update_repetition_schedule(self, card_id: str, correct: bool,
                                 accuracy: float, response_time: float):
        """Update card's review schedule using modified SuperMemo algorithm"""

        card = self.card_data[card_id]

        if correct:
            # Correct answer - increase interval
            if card['review_count'] == 1:
                # First review
                interval_days = self.base_intervals[0]
                card['interval_index'] = 0
            elif card['review_count'] == 2:
                # Second review
                interval_days = self.base_intervals[1]
                card['interval_index'] = 1
            else:
                # Subsequent reviews - use ease factor
                current_interval = self.get_current_interval_days(card)
                interval_days = current_interval * card['ease_factor']

                # Update ease factor based on performance
                self.update_ease_factor(card, accuracy, response_time)

                # Advance interval index if within base intervals
                if card['interval_index'] < len(self.base_intervals) - 1:
                    card['interval_index'] += 1
        else:
            # Incorrect answer - reset to short interval
            interval_days = self.base_intervals[0]
            card['interval_index'] = 0

            # Reduce ease factor for difficult cards
            card['ease_factor'] = max(1.3, card['ease_factor'] - 0.2)

        # Apply difficulty adjustment
        difficulty_multiplier = {
            'easy': 0.8,
            'intermediate': 1.0,
            'hard': 1.3
        }

        difficulty = card.get('difficulty', 'intermediate')
        interval_days *= difficulty_multiplier.get(difficulty, 1.0)

        # Apply priority adjustment (high priority items reviewed more frequently)
        priority_adjustment = 1.0 / (card.get('priority_score', 1.0) ** 0.5)
        interval_days *= priority_adjustment

        # Set minimum and maximum intervals
        interval_days = max(1, min(interval_days, 365))

        # Schedule next review
        next_review = datetime.now() + timedelta(days=interval_days)
        card['next_review'] = next_review.isoformat()

        self.schedule_review(card_id, next_review)

    def update_ease_factor(self, card: Dict, accuracy: float, response_time: float):
        """Update ease factor based on performance quality"""

        # Base ease factor adjustment
        if accuracy >= 0.9 and response_time <= 30:  # Quick and correct
            ease_adjustment = 0.1
        elif accuracy >= 0.8:
            ease_adjustment = 0.05
        elif accuracy >= 0.6:
            ease_adjustment = 0.0
        else:
            ease_adjustment = -0.2

        # Response time adjustment
        avg_response_time = card.get('average_response_time', 30)
        if response_time > avg_response_time * 1.5:  # Significantly slower
            ease_adjustment -= 0.05
        elif response_time < avg_response_time * 0.5:  # Significantly faster
            ease_adjustment += 0.05

        # Update ease factor
        card['ease_factor'] = max(1.3, min(3.0, card['ease_factor'] + ease_adjustment))

    def update_mastery_level(self, card_id: str, accuracy: float):
        """Update mastery level based on performance"""

        card = self.card_data[card_id]
        review_count = card['review_count']

        if accuracy >= self.mastery_threshold and review_count >= 5:
            card['mastery_level'] = 'mastered'
        elif accuracy >= self.review_threshold and review_count >= 3:
            card['mastery_level'] = 'reviewing'
        else:
            card['mastery_level'] = 'learning'

    def get_current_interval_days(self, card: Dict) -> float:
        """Get current interval in days"""

        interval_index = card.get('interval_index', 0)
        if interval_index < len(self.base_intervals):
            return self.base_intervals[interval_index]
        else:
            # Beyond base intervals, use last interval * ease factor
            return self.base_intervals[-1] * card.get('ease_factor', 2.5)

    def schedule_review(self, card_id: str, review_date: datetime):
        """Schedule card for review on specific date"""

        date_str = review_date.date().isoformat()

        if date_str not in self.review_schedule['daily_reviews']:
            self.review_schedule['daily_reviews'][date_str] = []

        if card_id not in self.review_schedule['daily_reviews'][date_str]:
            self.review_schedule['daily_reviews'][date_str].append(card_id)

        self.review_schedule['next_review_dates'][card_id] = review_date.isoformat()

    def get_due_cards(self, date: Optional[datetime] = None) -> List[str]:
        """Get cards due for review on specified date"""

        if date is None:
            date = datetime.now()

        date_str = date.date().isoformat()
        due_cards = []

        # Check all dates up to and including target date
        for review_date_str, card_ids in self.review_schedule['daily_reviews'].items():
            if review_date_str <= date_str:
                due_cards.extend(card_ids)

        return list(set(due_cards))  # Remove duplicates

    def get_daily_review_count(self, date: Optional[datetime] = None) -> int:
        """Get number of cards due for review today"""

        due_cards = self.get_due_cards(date)
        return len(due_cards)

    def get_study_session(self, max_cards: int = 20,
                         focus_section: Optional[str] = None) -> List[Dict]:
        """Get optimized study session based on spaced repetition"""

        due_cards = self.get_due_cards()
        session_cards = []

        # Filter by section if specified
        if focus_section:
            due_cards = [card_id for card_id in due_cards
                        if self.card_data.get(card_id, {}).get('section') == focus_section]

        # Sort by priority (overdue cards, high priority, learning level)
        sorted_cards = self.sort_cards_by_priority(due_cards)

        # Select cards for session
        for card_id in sorted_cards[:max_cards]:
            if card_id in self.card_data:
                card_data = self.card_data[card_id].copy()
                card_data['card_id'] = card_id
                session_cards.append(card_data)

        return session_cards

    def sort_cards_by_priority(self, card_ids: List[str]) -> List[str]:
        """Sort cards by review priority"""

        def priority_key(card_id: str) -> Tuple[int, float, int]:
            if card_id not in self.card_data:
                return (999, 0, 0)

            card = self.card_data[card_id]

            # Priority factors:
            # 1. Days overdue (most important)
            next_review = datetime.fromisoformat(card.get('next_review', datetime.now().isoformat()))
            days_overdue = (datetime.now() - next_review).days

            # 2. Mastery level (learning > reviewing > mastered)
            mastery_priority = {
                'learning': 0,
                'reviewing': 1,
                'mastered': 2
            }
            mastery_level = mastery_priority.get(card.get('mastery_level', 'learning'), 0)

            # 3. Priority score (higher is more important)
            priority_score = card.get('priority_score', 1.0)

            return (-days_overdue, mastery_level, -priority_score)

        return sorted(card_ids, key=priority_key)

    def get_learning_analytics(self, days: int = 30) -> Dict:
        """Get spaced repetition learning analytics"""

        now = datetime.now()
        cutoff_date = now - timedelta(days=days)

        analytics = {
            'total_cards': len(self.card_data),
            'cards_due_today': self.get_daily_review_count(),
            'mastery_distribution': {'learning': 0, 'reviewing': 0, 'mastered': 0},
            'section_distribution': {},
            'average_accuracy': 0,
            'retention_rate': 0,
            'daily_review_trend': {},
            'difficult_cards': [],
            'mastered_cards': []
        }

        total_reviews = 0
        total_correct = 0

        for card_id, card in self.card_data.items():
            # Mastery distribution
            mastery_level = card.get('mastery_level', 'learning')
            analytics['mastery_distribution'][mastery_level] += 1

            # Section distribution
            section = card.get('section', 'general')
            analytics['section_distribution'][section] = analytics['section_distribution'].get(section, 0) + 1

            # Performance metrics
            if card['review_count'] > 0:
                total_reviews += card['review_count']
                total_correct += card['correct_count']

                accuracy = card['correct_count'] / card['review_count']

                # Identify difficult cards (low accuracy, high review count)
                if accuracy < 0.6 and card['review_count'] >= 3:
                    analytics['difficult_cards'].append({
                        'card_id': card_id,
                        'accuracy': accuracy,
                        'review_count': card['review_count'],
                        'section': section
                    })

                # Identify mastered cards
                if mastery_level == 'mastered':
                    analytics['mastered_cards'].append({
                        'card_id': card_id,
                        'accuracy': accuracy,
                        'section': section
                    })

        # Calculate overall metrics
        if total_reviews > 0:
            analytics['average_accuracy'] = total_correct / total_reviews

        # Calculate retention rate (cards still remembered after multiple reviews)
        retained_cards = sum(1 for card in self.card_data.values()
                           if card.get('mastery_level') in ['reviewing', 'mastered'])
        analytics['retention_rate'] = retained_cards / len(self.card_data) if self.card_data else 0

        return analytics

    def get_study_recommendations(self) -> List[str]:
        """Get personalized study recommendations"""

        recommendations = []
        analytics = self.get_learning_analytics()

        # Cards due today
        due_today = analytics['cards_due_today']
        if due_today > 50:
            recommendations.append(f"⚠️ {due_today} cards due today - consider extending study time")
        elif due_today > 0:
            recommendations.append(f"📚 {due_today} cards due for review today")

        # Mastery distribution
        learning_pct = analytics['mastery_distribution']['learning'] / analytics['total_cards'] * 100
        if learning_pct > 60:
            recommendations.append("Focus on consistent daily review to move cards from learning to reviewing")

        # Difficult cards
        difficult_count = len(analytics['difficult_cards'])
        if difficult_count > 0:
            recommendations.append(f"🎯 {difficult_count} cards need extra attention - consider creating additional study materials")

        # Retention rate
        if analytics['retention_rate'] < 0.7:
            recommendations.append("Consider reducing daily new cards and focusing on review")
        elif analytics['retention_rate'] > 0.9:
            recommendations.append("Excellent retention! You can increase daily new cards")

        return recommendations

    def create_flashcard_from_question(self, question_data: Dict,
                                     user_performance: Dict) -> str:
        """Create flashcard from answered question for spaced repetition"""

        card_id = f"q_{question_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Extract key information for flashcard
        flashcard_content = {
            'type': 'question_review',
            'original_question': question_data.get('question_text', ''),
            'correct_answer': question_data.get('correct_answer', ''),
            'explanation': question_data.get('explanation', ''),
            'section': question_data.get('section', 'general'),
            'topic': question_data.get('topic', ''),
            'difficulty': question_data.get('difficulty', 'intermediate'),
            'user_answered_correctly': user_performance.get('correct', False),
            'user_answer': user_performance.get('user_answer', ''),
            'response_time': user_performance.get('response_time', 0)
        }

        # Add to spaced repetition system
        self.add_card(card_id, flashcard_content)

        self.logger.info(f"Created flashcard {card_id} from question for spaced repetition")

        return card_id