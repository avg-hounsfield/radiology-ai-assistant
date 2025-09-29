#!/usr/bin/env python3
"""
Radiology Dictation Practice System
Provides structured dictation practice with AI-powered scoring
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
import re

@dataclass
class DictationCase:
    """Represents a dictation practice case"""
    case_id: str
    title: str
    modality: str  # "XR", "CT", "MR", "US", etc.
    body_part: str  # "Chest", "Abdomen", "Head", etc.
    clinical_history: str
    images: List[str]  # List of image file paths
    ground_truth_findings: str
    ground_truth_impression: str
    difficulty: str  # "Basic", "Intermediate", "Advanced"
    tags: List[str]
    created_date: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class DictationAttempt:
    """Represents a user's dictation attempt"""
    attempt_id: str
    case_id: str
    user_findings: str
    user_impression: str
    timestamp: str
    findings_score: float
    impression_score: float
    overall_score: float
    feedback: Dict[str, str]
    time_taken_seconds: int

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class DictationCaseManager:
    """Manages dictation cases and user attempts"""

    def __init__(self, cases_dir: str = "data/dictation_cases"):
        self.cases_dir = Path(cases_dir)
        self.cases_dir.mkdir(parents=True, exist_ok=True)

        self.attempts_dir = Path("data/dictation_attempts")
        self.attempts_dir.mkdir(parents=True, exist_ok=True)

        self.cases_file = self.cases_dir / "cases.json"
        self.attempts_file = self.attempts_dir / "attempts.json"

        self.cases = self._load_cases()
        self.attempts = self._load_attempts()

        logging.info(f"DictationCaseManager initialized with {len(self.cases)} cases")

    def _load_cases(self) -> Dict[str, DictationCase]:
        """Load dictation cases from file"""
        if not self.cases_file.exists():
            # Create some sample cases
            sample_cases = self._create_sample_cases()
            self._save_cases(sample_cases)
            return sample_cases

        try:
            with open(self.cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {case_id: DictationCase.from_dict(case_data)
                   for case_id, case_data in data.items()}
        except Exception as e:
            logging.error(f"Error loading dictation cases: {e}")
            return {}

    def _save_cases(self, cases: Dict[str, DictationCase]):
        """Save dictation cases to file"""
        try:
            data = {case_id: case.to_dict() for case_id, case in cases.items()}
            with open(self.cases_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving dictation cases: {e}")

    def _load_attempts(self) -> List[DictationAttempt]:
        """Load dictation attempts from file"""
        if not self.attempts_file.exists():
            return []

        try:
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [DictationAttempt.from_dict(attempt_data) for attempt_data in data]
        except Exception as e:
            logging.error(f"Error loading dictation attempts: {e}")
            return []

    def _save_attempts(self):
        """Save dictation attempts to file"""
        try:
            data = [attempt.to_dict() for attempt in self.attempts]
            with open(self.attempts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving dictation attempts: {e}")

    def _create_sample_cases(self) -> Dict[str, DictationCase]:
        """Create sample dictation cases for demonstration"""
        sample_cases = {}

        # Sample Chest X-ray case
        case1 = DictationCase(
            case_id="sample_cxr_001",
            title="Chest X-ray - Pneumonia",
            modality="XR",
            body_part="Chest",
            clinical_history="45-year-old male with cough and fever for 3 days",
            images=["sample_cxr_pneumonia.jpg"],  # Placeholder - user can add actual images
            ground_truth_findings="""
FINDINGS:
PA and lateral chest radiographs demonstrate a focal consolidation in the right lower lobe.
The consolidation has an air bronchogram pattern consistent with pneumonia.
The remainder of the lungs are clear with no evidence of pleural effusion or pneumothorax.
Heart size and mediastinal contours are normal.
Osseous structures appear intact.
            """.strip(),
            ground_truth_impression="""
IMPRESSION:
Right lower lobe pneumonia.
            """.strip(),
            difficulty="Basic",
            tags=["pneumonia", "chest", "infection", "consolidation"],
            created_date=datetime.now().isoformat()
        )
        sample_cases[case1.case_id] = case1

        # Sample CT Head case
        case2 = DictationCase(
            case_id="sample_ct_head_001",
            title="CT Head - Acute Stroke",
            modality="CT",
            body_part="Head",
            clinical_history="68-year-old female with acute onset left-sided weakness and speech difficulty",
            images=["sample_ct_head_stroke.jpg"],
            ground_truth_findings="""
FINDINGS:
Non-contrast CT of the head demonstrates a hypodense area in the right middle cerebral artery territory
involving the right frontal and temporal lobes. There is loss of gray-white matter differentiation
and mild mass effect with effacement of the right lateral ventricle.
No hemorrhage is identified. The remaining brain parenchyma appears normal.
No midline shift is present.
            """.strip(),
            ground_truth_impression="""
IMPRESSION:
Acute right middle cerebral artery territory infarct with mild mass effect.
            """.strip(),
            difficulty="Intermediate",
            tags=["stroke", "infarct", "MCA", "acute", "neuro"],
            created_date=datetime.now().isoformat()
        )
        sample_cases[case2.case_id] = case2

        # Sample Abdominal CT case
        case3 = DictationCase(
            case_id="sample_ct_abdomen_001",
            title="CT Abdomen - Appendicitis",
            modality="CT",
            body_part="Abdomen",
            clinical_history="22-year-old male with right lower quadrant pain and fever",
            images=["sample_ct_appendicitis.jpg"],
            ground_truth_findings="""
FINDINGS:
Contrast-enhanced CT of the abdomen and pelvis demonstrates a dilated appendix measuring 12 mm
in diameter with wall thickening and surrounding fat stranding.
A small amount of free fluid is present in the pelvis.
The remainder of the bowel appears normal with no evidence of obstruction.
The solid organs including liver, spleen, pancreas, and kidneys are unremarkable.
            """.strip(),
            ground_truth_impression="""
IMPRESSION:
Acute appendicitis with surrounding inflammatory changes.
            """.strip(),
            difficulty="Basic",
            tags=["appendicitis", "abdomen", "inflammation", "RLQ"],
            created_date=datetime.now().isoformat()
        )
        sample_cases[case3.case_id] = case3

        return sample_cases

    def get_cases_by_modality(self, modality: str = None) -> List[DictationCase]:
        """Get cases filtered by modality"""
        if modality is None:
            return list(self.cases.values())
        return [case for case in self.cases.values() if case.modality == modality]

    def get_cases_by_body_part(self, body_part: str = None) -> List[DictationCase]:
        """Get cases filtered by body part"""
        if body_part is None:
            return list(self.cases.values())
        return [case for case in self.cases.values() if case.body_part == body_part]

    def get_cases_by_difficulty(self, difficulty: str = None) -> List[DictationCase]:
        """Get cases filtered by difficulty"""
        if difficulty is None:
            return list(self.cases.values())
        return [case for case in self.cases.values() if case.difficulty == difficulty]

    def get_case(self, case_id: str) -> Optional[DictationCase]:
        """Get a specific case by ID"""
        return self.cases.get(case_id)

    def add_case(self, case: DictationCase):
        """Add a new dictation case"""
        self.cases[case.case_id] = case
        self._save_cases(self.cases)
        logging.info(f"Added new dictation case: {case.title}")

    def save_attempt(self, attempt: DictationAttempt):
        """Save a dictation attempt"""
        self.attempts.append(attempt)
        self._save_attempts()
        logging.info(f"Saved dictation attempt for case {attempt.case_id}")

    def get_user_attempts(self, case_id: str = None) -> List[DictationAttempt]:
        """Get user attempts, optionally filtered by case"""
        if case_id is None:
            return self.attempts
        return [attempt for attempt in self.attempts if attempt.case_id == case_id]

    def get_user_statistics(self) -> Dict[str, any]:
        """Get user performance statistics"""
        if not self.attempts:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "best_score": 0,
                "improvement_trend": 0
            }

        scores = [attempt.overall_score for attempt in self.attempts]
        recent_scores = scores[-10:] if len(scores) > 10 else scores
        early_scores = scores[:10] if len(scores) > 10 else scores

        improvement_trend = 0
        if len(scores) > 5:
            improvement_trend = sum(recent_scores) / len(recent_scores) - sum(early_scores) / len(early_scores)

        return {
            "total_attempts": len(self.attempts),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "recent_average": sum(recent_scores) / len(recent_scores),
            "improvement_trend": improvement_trend
        }

class DictationScorer:
    """AI-powered dictation scoring system"""

    def __init__(self, rag_system=None):
        self.rag_system = rag_system
        self.scoring_criteria = {
            "findings": {
                "anatomical_accuracy": 0.3,
                "pathology_identification": 0.4,
                "completeness": 0.2,
                "clarity": 0.1
            },
            "impression": {
                "diagnostic_accuracy": 0.5,
                "clinical_relevance": 0.3,
                "conciseness": 0.2
            }
        }

    def score_dictation(self, user_findings: str, user_impression: str,
                       ground_truth_findings: str, ground_truth_impression: str) -> Tuple[float, float, Dict[str, str]]:
        """Score user dictation against ground truth"""

        # Score findings
        findings_score = self._score_text_similarity(user_findings, ground_truth_findings)

        # Score impression
        impression_score = self._score_text_similarity(user_impression, ground_truth_impression)

        # Generate feedback
        feedback = self._generate_feedback(
            user_findings, user_impression,
            ground_truth_findings, ground_truth_impression,
            findings_score, impression_score
        )

        return findings_score, impression_score, feedback

    def _score_text_similarity(self, user_text: str, ground_truth: str) -> float:
        """Calculate similarity score between user text and ground truth"""
        # Simple scoring based on key terms and structure
        # In a real implementation, this would use more sophisticated NLP

        user_text = user_text.lower().strip()
        ground_truth = ground_truth.lower().strip()

        if not user_text:
            return 0.0

        # Extract key medical terms
        ground_truth_terms = set(re.findall(r'\b[a-z]{3,}\b', ground_truth))
        user_terms = set(re.findall(r'\b[a-z]{3,}\b', user_text))

        # Calculate term overlap
        if not ground_truth_terms:
            return 0.5  # Neutral score if no ground truth terms

        overlap = len(ground_truth_terms.intersection(user_terms))
        term_score = overlap / len(ground_truth_terms)

        # Length similarity (penalize too short or too long)
        length_ratio = min(len(user_text), len(ground_truth)) / max(len(user_text), len(ground_truth))
        length_score = length_ratio

        # Combine scores
        final_score = (term_score * 0.7 + length_score * 0.3)

        return min(1.0, max(0.0, final_score))

    def _generate_feedback(self, user_findings: str, user_impression: str,
                          ground_truth_findings: str, ground_truth_impression: str,
                          findings_score: float, impression_score: float) -> Dict[str, str]:
        """Generate detailed feedback for the user"""

        feedback = {}

        # Findings feedback
        if findings_score >= 0.8:
            feedback["findings"] = "Excellent findings section! Your description is comprehensive and accurate."
        elif findings_score >= 0.6:
            feedback["findings"] = "Good findings section. Consider adding more detail about anatomical structures and findings."
        elif findings_score >= 0.4:
            feedback["findings"] = "Adequate findings but missing some key observations. Review the ground truth for comparison."
        else:
            feedback["findings"] = "Findings section needs improvement. Focus on systematic description of all structures."

        # Impression feedback
        if impression_score >= 0.8:
            feedback["impression"] = "Excellent impression! Clear, concise, and clinically relevant."
        elif impression_score >= 0.6:
            feedback["impression"] = "Good impression. Consider being more specific about the diagnosis."
        elif impression_score >= 0.4:
            feedback["impression"] = "Impression is on the right track but could be more precise."
        else:
            feedback["impression"] = "Impression needs work. Focus on the primary diagnosis and clinical significance."

        # Overall feedback
        overall_score = (findings_score + impression_score) / 2
        if overall_score >= 0.8:
            feedback["overall"] = "Outstanding dictation! You demonstrate excellent radiological reporting skills."
        elif overall_score >= 0.6:
            feedback["overall"] = "Good dictation overall. Continue practicing to refine your reporting style."
        elif overall_score >= 0.4:
            feedback["overall"] = "Satisfactory attempt. Focus on systematic observation and clear communication."
        else:
            feedback["overall"] = "Keep practicing! Review sample reports and focus on structured reporting."

        return feedback

if __name__ == "__main__":
    # Test the dictation system
    case_manager = DictationCaseManager()
    scorer = DictationScorer()

    # Get sample cases
    cases = case_manager.get_cases_by_modality()
    print(f"Loaded {len(cases)} dictation cases")

    for case in cases[:2]:
        print(f"\nCase: {case.title}")
        print(f"Modality: {case.modality}")
        print(f"Clinical History: {case.clinical_history}")