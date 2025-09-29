# src/study/study_suggester.py
"""
Interactive study suggester system for radiology topics
"""

import ollama
import random
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

class RadiologyStudySuggester:
    def __init__(self, llm_model: str = "llama3.1:8b"):
        self.llm_model = llm_model
        self.client = ollama.Client()
        self.logger = logging.getLogger(__name__)
        
        # Comprehensive radiology topic database
        self.topic_database = {
            'chest': {
                'basic': [
                    'chest x-ray anatomy', 'normal chest x-ray', 'chest x-ray technique',
                    'pneumonia basics', 'pleural effusion', 'pneumothorax'
                ],
                'intermediate': [
                    'pulmonary nodules', 'lung masses', 'interstitial lung disease',
                    'pulmonary embolism', 'chest ct interpretation', 'mediastinal masses'
                ],
                'advanced': [
                    'lung cancer staging', 'hrct patterns', 'pulmonary function correlation',
                    'complex pneumonia', 'rare chest pathology', 'chest emergencies'
                ]
            },
            'cardiac': {
                'basic': [
                    'cardiac anatomy', 'chest x-ray heart evaluation', 'basic echo',
                    'cardiac silhouette', 'pulmonary edema', 'cardiomegaly'
                ],
                'intermediate': [
                    'coronary cta', 'cardiac mri basics', 'valvular disease imaging',
                    'pericardial disease', 'cardiac ct calcium scoring', 'stress testing'
                ],
                'advanced': [
                    'complex congenital heart disease', 'cardiac mri advanced',
                    'interventional cardiology imaging', 'cardiac emergencies'
                ]
            },
            'neuro': {
                'basic': [
                    'brain anatomy', 'normal ct head', 'stroke basics',
                    'head trauma', 'brain hemorrhage', 'hydrocephalus'
                ],
                'intermediate': [
                    'brain tumors', 'mri sequences', 'spine imaging basics',
                    'multiple sclerosis', 'seizure workup', 'headache imaging'
                ],
                'advanced': [
                    'advanced mri techniques', 'complex spine pathology',
                    'pediatric neuro', 'neurodegenerative diseases'
                ]
            },
            'gi': {
                'basic': [
                    'abdominal anatomy', 'bowel obstruction', 'appendicitis',
                    'gallbladder disease', 'basic liver imaging', 'kidney stones'
                ],
                'intermediate': [
                    'liver lesions', 'pancreatic imaging', 'inflammatory bowel disease',
                    'gi bleeding workup', 'biliary obstruction', 'acute abdomen'
                ],
                'advanced': [
                    'liver transplant imaging', 'pancreatic cancer staging',
                    'complex gi pathology', 'pediatric gi imaging'
                ]
            },
            'physics': {
                'basic': [
                    'x-ray physics', 'radiation safety', 'image formation',
                    'contrast agents', 'radiation dose', 'quality assurance'
                ],
                'intermediate': [
                    'ct physics', 'mri physics basics', 'ultrasound physics',
                    'digital imaging', 'pacs systems', 'image optimization'
                ],
                'advanced': [
                    'advanced mri physics', 'pet physics', 'dose optimization',
                    'ai in radiology', 'advanced reconstruction'
                ]
            }
        }
        
        # Study session templates with the three core questions framework
        self.session_templates = {
            'comprehensive': {
                'duration': 30,
                'sections': ['what_is_it', 'what_next_step', 'what_associated', 'clinical_pearls', 'questions'],
                'question_count': 5
            },
            'focused': {
                'duration': 15,
                'sections': ['what_is_it', 'what_next_step', 'what_associated', 'questions'],
                'question_count': 3
            },
            'quick_review': {
                'duration': 10,
                'sections': ['what_is_it', 'what_next_step', 'what_associated'],
                'question_count': 2
            }
        }
        
        # Core question framework for radiology education
        self.core_questions_framework = {
            'what_is_it': {
                'purpose': 'Understanding and Recognition',
                'focus': 'Definition, imaging appearance, key characteristics',
                'clinical_relevance': 'Diagnostic recognition and interpretation'
            },
            'what_next_step': {
                'purpose': 'Clinical Decision Making', 
                'focus': 'Management, follow-up imaging, immediate actions',
                'clinical_relevance': 'Patient care and workflow decisions'
            },
            'what_associated': {
                'purpose': 'Comprehensive Understanding',
                'focus': 'Associated conditions, complications, differential diagnosis',
                'clinical_relevance': 'Broader clinical context and relationships'
            }
        }
    
    def search_topics(self, query: str, difficulty: str = "all") -> List[Dict]:
        """Search for relevant topics based on query"""
        query_lower = query.lower()
        results = []
        
        for category, difficulties in self.topic_database.items():
            for diff, topics in difficulties.items():
                if difficulty != "all" and diff != difficulty:
                    continue
                    
                for topic in topics:
                    # Calculate relevance score
                    score = 0
                    topic_words = topic.lower().split()
                    query_words = query_lower.split()
                    
                    for q_word in query_words:
                        for t_word in topic_words:
                            if q_word in t_word or t_word in q_word:
                                score += 2
                            elif q_word == t_word:
                                score += 5
                    
                    # Check category match
                    if query_lower in category:
                        score += 3
                    
                    if score > 0:
                        results.append({
                            'topic': topic,
                            'category': category,
                            'difficulty': diff,
                            'relevance_score': score
                        })
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:10]
    
    def generate_study_session(self, topic: str, session_type: str = "comprehensive", 
                             difficulty: str = "intermediate") -> Dict:
        """Generate a complete interactive study session"""
        
        template = self.session_templates.get(session_type, self.session_templates['comprehensive'])
        
        # Generate the study content
        study_content = self._generate_topic_content(topic, template['sections'], difficulty)
        
        # Generate interactive questions
        questions = self._generate_interactive_questions(topic, difficulty, template['question_count'])
        
        session = {
            'topic': topic,
            'difficulty': difficulty,
            'session_type': session_type,
            'estimated_duration': template['duration'],
            'generated_at': datetime.now().isoformat(),
            'content': study_content,
            'questions': questions,
            'session_id': f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        return session
    
    def _generate_topic_content(self, topic: str, sections: List[str], difficulty: str) -> Dict:
        """Generate comprehensive content for a topic"""
        
        content = {}
        
        for section in sections:
            section_content = self._generate_section_content(topic, section, difficulty)
            content[section] = section_content
        
        return content
    
    def _generate_section_content(self, topic: str, section: str, difficulty: str) -> str:
        """Generate content for a specific section"""
        
        section_prompts = {
            'what_is_it': f"""Answer "What is it?" for {topic} in radiology.
                             Target audience: {difficulty} level medical students/residents.
                             
                             Include:
                             • Definition and pathophysiology
                             • Key imaging characteristics and appearances
                             • Typical patient presentation
                             • Prevalence and demographics
                             • How to recognize it on imaging
                             
                             Format: Clear, systematic explanation focusing on recognition and understanding.
                             Start with: "This is..." or "{topic} is..."
                             """,
            
            'what_next_step': f"""Answer "What is the next step?" for {topic}.
                                Level: {difficulty}
                                
                                Include:
                                • Immediate management decisions
                                • Follow-up imaging recommendations
                                • Additional studies needed
                                • Clinical actions required
                                • Timeframe for follow-up
                                • When to involve other specialists
                                
                                Format: Action-oriented, practical guidance.
                                Structure as: Immediate actions → Follow-up → Long-term management
                                """,
            
            'what_associated': f"""Answer "What is it associated with?" for {topic}.
                                 Level: {difficulty}
                                 
                                 Include:
                                 • Associated conditions and comorbidities  
                                 • Potential complications
                                 • Related pathologies
                                 • Risk factors and predisposing conditions
                                 • Differential diagnosis considerations
                                 • Syndromes or patterns it's part of
                                 
                                 Format: Comprehensive associations organized by category.
                                 Structure: Primary associations → Complications → Differentials
                                 """,
            
            'clinical_pearls': f"""Provide high-yield clinical pearls for {topic}.
                                 Level: {difficulty}
                                 
                                 Include:
                                 • Key teaching points
                                 • Common pitfalls to avoid
                                 • Board exam high-yield facts
                                 • Memory aids or mnemonics
                                 • "Don't miss" diagnoses
                                 
                                 Format: Bulleted pearls, each 1-2 sentences.
                                 Focus on practical, memorable insights.
                                 """,
            
            # Legacy sections for backward compatibility
            'overview': f"""Provide a concise overview of {topic} in radiology.
                           Target audience: {difficulty} level medical students/residents.
                           Include: definition, clinical relevance, and why it's important to understand.
                           Format: 2-3 paragraphs, educational tone.""",
            
            'key_concepts': f"""List and explain the key concepts for {topic}.
                              Focus on {difficulty} level understanding.
                              Include: fundamental principles, terminology, and core knowledge.
                              Format: Bulleted list with brief explanations.""",
            
            'clinical_application': f"""Describe the clinical applications of {topic}.
                                     Include: when to order studies, clinical scenarios, patient presentation.
                                     Level: {difficulty}
                                     Format: Practical, scenario-based explanation.""",
            
            'imaging_findings': f"""Describe the key imaging findings for {topic}.
                                  Include: what to look for, normal vs abnormal, characteristic appearances.
                                  Level: {difficulty} 
                                  Format: Systematic description with key features.""",
            
            'differential': f"""Provide differential diagnosis considerations for {topic}.
                              Include: main differentials, distinguishing features, how to differentiate.
                              Level: {difficulty}
                              Format: Organized list with key differentiating points.""",
            
            'key_points': f"""Summarize the most important points about {topic}.
                            High-yield information for {difficulty} level.
                            Format: Concise bullet points, exam-focused."""
        }
        
        prompt = section_prompts.get(section, f"Provide information about {section} for {topic}")
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a radiology attending physician creating educational content using the three-question framework:
                                     1. What is it? (Recognition and understanding)
                                     2. What is the next step? (Clinical decision making)  
                                     3. What is it associated with? (Comprehensive relationships)
                                     
                                     Provide accurate, clinically relevant information appropriate for medical education.
                                     Focus on high-yield information relevant for radiology training and board exams.
                                     Use clear, systematic explanations that build clinical reasoning skills."""
                    },
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 800
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error generating {section} content: {e}")
            return f"Error generating {section} content for {topic}"
    
    def _generate_interactive_questions(self, topic: str, difficulty: str, count: int) -> List[Dict]:
        """Generate interactive questions using the three-question framework"""
        
        questions = []
        
        # Ensure we ask the three core questions
        core_question_types = [
            'what_is_it_question',
            'what_next_step_question', 
            'what_associated_question'
        ]
        
        # Add additional question types if we need more questions
        additional_types = [
            'multiple_choice',
            'clinical_scenario', 
            'image_interpretation'
        ]
        
        # Generate core questions first
        for i, q_type in enumerate(core_question_types[:count]):
            question = self._generate_core_framework_question(topic, difficulty, q_type, i+1)
            questions.append(question)
        
        # Add additional questions if needed
        remaining_count = count - len(questions)
        if remaining_count > 0:
            for i in range(remaining_count):
                q_type = random.choice(additional_types)
                question = self._generate_single_question(topic, difficulty, q_type, len(questions)+1)
                questions.append(question)
        
        return questions
    
    def _generate_core_framework_question(self, topic: str, difficulty: str, question_type: str, q_number: int) -> Dict:
        """Generate questions based on the three-question framework"""
        
        framework_prompts = {
            'what_is_it_question': f"""Create a {difficulty} level question testing "What is it?" knowledge for {topic}.
                                     
                                     The question should test:
                                     • Recognition and identification
                                     • Key characteristics 
                                     • Imaging appearance
                                     • Definition understanding
                                     
                                     Format:
                                     Question: [Test recognition or characteristics]
                                     A) [Option A]
                                     B) [Option B] 
                                     C) [Option C]
                                     D) [Option D]
                                     Correct Answer: [Letter]
                                     Explanation: [Why this represents the correct "what is it" understanding]
                                     """,
            
            'what_next_step_question': f"""Create a {difficulty} level question testing "What is the next step?" for {topic}.
                                        
                                        The question should test:
                                        • Immediate management decisions
                                        • Follow-up imaging choices
                                        • Clinical workflow decisions
                                        • Appropriate time frames
                                        
                                        Format:
                                        Clinical Scenario: [Patient with {topic}]
                                        Question: What is the most appropriate next step?
                                        A) [Management option A]
                                        B) [Management option B]
                                        C) [Management option C] 
                                        D) [Management option D]
                                        Correct Answer: [Letter]
                                        Explanation: [Why this is the correct next step]
                                        """,
            
            'what_associated_question': f"""Create a {difficulty} level question testing "What is it associated with?" for {topic}.
                                         
                                         The question should test:
                                         • Associated conditions
                                         • Complications
                                         • Risk factors
                                         • Related pathologies
                                         • Differential considerations
                                         
                                         Format:
                                         Question: {topic} is most commonly associated with which of the following?
                                         A) [Association A]
                                         B) [Association B]
                                         C) [Association C]
                                         D) [Association D]
                                         Correct Answer: [Letter]
                                         Explanation: [Why this association is most important]
                                         """
        }
        
        prompt = framework_prompts.get(question_type, framework_prompts['what_is_it_question'])
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are creating educational questions for radiology training using the three-question framework:
                                    1. What is it? - Tests recognition and understanding
                                    2. What is the next step? - Tests clinical decision making  
                                    3. What is it associated with? - Tests comprehensive knowledge
                                    
                                    Make questions clinically relevant, educational, and appropriate for board exam preparation.
                                    Ensure explanations reinforce the framework and clinical reasoning."""
                    },
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "num_predict": 600
                }
            )
            
            return {
                'question_number': q_number,
                'type': question_type,
                'framework_type': question_type.replace('_question', ''),
                'content': response['message']['content'],
                'topic': topic,
                'difficulty': difficulty,
                'answered': False,
                'user_answer': None,
                'start_time': None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating {question_type} question {q_number}: {e}")
            return {
                'question_number': q_number,
                'type': question_type,
                'framework_type': question_type.replace('_question', ''),
                'content': f"Error generating {question_type} about {topic}",
                'topic': topic,
                'difficulty': difficulty,
                'error': str(e)
            }
    
    def _generate_single_question(self, topic: str, difficulty: str, q_type: str, q_number: int) -> Dict:
        """Generate a single interactive question"""
        
        type_prompts = {
            'multiple_choice': f"""Create a {difficulty} level multiple choice question about {topic}.
                                 Format:
                                 Question: [Clear clinical or educational question]
                                 A) [Option A]
                                 B) [Option B] 
                                 C) [Option C]
                                 D) [Option D]
                                 Correct Answer: [Letter]
                                 Explanation: [Why this is correct and others are wrong]""",
            
            'true_false': f"""Create a {difficulty} level true/false question about {topic}.
                            Format:
                            Statement: [Clear statement about the topic]
                            Answer: [True or False]
                            Explanation: [Why this is true or false]""",
            
            'clinical_scenario': f"""Create a {difficulty} level clinical scenario question about {topic}.
                                   Format:
                                   Scenario: [Patient presentation with relevant details]
                                   Question: [What is the most likely diagnosis/next step/finding?]
                                   Answer: [Correct response]
                                   Explanation: [Clinical reasoning]""",
            
            'image_interpretation': f"""Create a {difficulty} level image interpretation question about {topic}.
                                      Format:
                                      Scenario: [Brief clinical context]
                                      Image Description: [What would be seen on the study]
                                      Question: [What does this represent/what is the diagnosis?]
                                      Answer: [Correct interpretation]
                                      Key Features: [What to look for]"""
        }
        
        prompt = type_prompts.get(q_type, type_prompts['multiple_choice'])
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are creating educational questions for radiology training.
                                    Make questions clinically relevant, educational, and appropriate for board exam preparation.
                                    Ensure explanations are thorough and educational."""
                    },
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "num_predict": 600
                }
            )
            
            return {
                'question_number': q_number,
                'type': q_type,
                'content': response['message']['content'],
                'topic': topic,
                'difficulty': difficulty,
                'answered': False,
                'user_answer': None,
                'start_time': None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating question {q_number}: {e}")
            return {
                'question_number': q_number,
                'type': q_type,
                'content': f"Error generating question about {topic}",
                'topic': topic,
                'difficulty': difficulty,
                'error': str(e)
            }
    
    def get_suggested_topics(self, category: str = "all", difficulty: str = "all", 
                           limit: int = 10) -> List[Dict]:
        """Get suggested topics for study"""
        
        suggestions = []
        
        for cat, difficulties in self.topic_database.items():
            if category != "all" and cat != category:
                continue
                
            for diff, topics in difficulties.items():
                if difficulty != "all" and diff != difficulty:
                    continue
                
                for topic in topics:
                    suggestions.append({
                        'topic': topic,
                        'category': cat,
                        'difficulty': diff,
                        'estimated_time': 20 + (10 if diff == 'advanced' else 0),
                        'description': f"{diff.title()} level {cat} topic"
                    })
        
        # Randomize and return limited results
        random.shuffle(suggestions)
        return suggestions[:limit]
    
    def create_custom_session(self, topics: List[str], session_name: str = "Custom Session") -> Dict:
        """Create a custom study session from multiple topics"""
        
        session = {
            'session_name': session_name,
            'topics': topics,
            'created_at': datetime.now().isoformat(),
            'estimated_duration': len(topics) * 15,
            'topic_summaries': {},
            'combined_questions': []
        }
        
        # Generate summary for each topic
        for topic in topics:
            try:
                summary = self._generate_section_content(topic, 'key_points', 'intermediate')
                session['topic_summaries'][topic] = summary
                
                # Add 1 question per topic
                question = self._generate_single_question(topic, 'intermediate', 'multiple_choice', len(session['combined_questions']) + 1)
                session['combined_questions'].append(question)
                
            except Exception as e:
                self.logger.error(f"Error processing topic {topic}: {e}")
        
        return session
    
    def evaluate_session_performance(self, session: Dict, user_answers: List[Dict]) -> Dict:
        """Evaluate user performance in a study session"""
        
        total_questions = len(session.get('questions', []))
        if total_questions == 0:
            return {"error": "No questions to evaluate"}
        
        correct_answers = 0
        answer_times = []
        topic_performance = {}
        
        for answer in user_answers:
            q_num = answer.get('question_number', 0)
            if q_num <= len(session['questions']):
                question = session['questions'][q_num - 1]
                topic = question.get('topic', 'unknown')
                
                # Check if answer is correct (simplified - would need more sophisticated checking)
                is_correct = answer.get('correct', False)
                if is_correct:
                    correct_answers += 1
                
                # Track time
                if answer.get('time_taken'):
                    answer_times.append(answer['time_taken'])
                
                # Track by topic
                if topic not in topic_performance:
                    topic_performance[topic] = {'correct': 0, 'total': 0}
                topic_performance[topic]['total'] += 1
                if is_correct:
                    topic_performance[topic]['correct'] += 1
        
        # Calculate performance metrics
        accuracy = (correct_answers / total_questions) * 100
        avg_time = sum(answer_times) / len(answer_times) if answer_times else 0
        
        # Generate study recommendations
        weak_areas = []
        strong_areas = []
        
        for topic, perf in topic_performance.items():
            topic_accuracy = (perf['correct'] / perf['total']) * 100 if perf['total'] > 0 else 0
            if topic_accuracy < 70:
                weak_areas.append(topic)
            elif topic_accuracy > 85:
                strong_areas.append(topic)
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'accuracy_percentage': round(accuracy, 1),
            'average_time_per_question': round(avg_time, 1),
            'topic_performance': topic_performance,
            'weak_areas': weak_areas,
            'strong_areas': strong_areas,
            'recommendations': self._generate_study_recommendations(weak_areas, strong_areas),
            'overall_grade': self._calculate_grade(accuracy)
        }
    
    def _generate_study_recommendations(self, weak_areas: List[str], strong_areas: List[str]) -> List[str]:
        """Generate personalized study recommendations"""
        
        recommendations = []
        
        if weak_areas:
            recommendations.append(f"Focus additional study time on: {', '.join(weak_areas)}")
            recommendations.append("Review fundamental concepts in your weak areas before moving to advanced topics")
            recommendations.append("Consider creating flashcards for topics you missed")
        
        if strong_areas:
            recommendations.append(f"You demonstrated strong knowledge in: {', '.join(strong_areas)}")
            recommendations.append("Consider advancing to more complex cases in your strong areas")
        
        if not weak_areas:
            recommendations.append("Excellent performance! Consider tackling more advanced topics")
        
        recommendations.append("Review explanations for all questions, including ones you got correct")
        recommendations.append("Consider spacing out review of this material over several days")
        
        return recommendations
    
    def _calculate_grade(self, accuracy: float) -> str:
        """Calculate letter grade from accuracy"""
        if accuracy >= 90:
            return "A"
        elif accuracy >= 80:
            return "B"
        elif accuracy >= 70:
            return "C"
        elif accuracy >= 60:
            return "D"
        else:
            return "F"