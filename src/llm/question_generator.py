# src/llm/question_generator.py
"""
CORE exam question generator for radiology preparation
"""

import ollama
from typing import List, Dict, Optional
import json
import logging
import random

class COREQuestionGenerator:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = ollama.Client()
        self.logger = logging.getLogger(__name__)
        
        # CORE exam topics and weights
        self.core_topics = {
            'Physics & Safety': {'weight': 15, 'keywords': ['dose', 'radiation', 'kvp', 'technique', 'safety', 'shielding']},
            'Cardiothoracic': {'weight': 20, 'keywords': ['pneumonia', 'nodules', 'consolidation', 'ground glass', 'heart', 'chest']},
            'Neuroradiology': {'weight': 15, 'keywords': ['brain', 'stroke', 'hemorrhage', 'midline shift', 'tumor', 'spine']},
            'Musculoskeletal (MSK)': {'weight': 10, 'keywords': ['bone', 'fracture', 'marrow edema', 'joint effusion', 'arthritis']},
            'Abdominal & Pelvic': {'weight': 15, 'keywords': ['bowel', 'liver', 'enhancement patterns', 'obstruction', 'abdomen']},
            'Breast Imaging': {'weight': 8, 'keywords': ['birads', 'mass', 'calcifications', 'mammography', 'breast']},
            'Pediatric Radiology': {'weight': 7, 'keywords': ['nicu', 'bowing fracture', 'intussusception', 'pediatric']},
            'Nuclear Medicine': {'weight': 10, 'keywords': ['pet', 'spect', 'hida', 'v/q scan', 'nuclear']}
        }
        
        # Download model if not exists
        try:
            self.client.show(model_name)
            self.logger.info(f"Question generator model {model_name} ready")
        except:
            self.logger.info(f"Downloading model {model_name} for question generation...")
            self.client.pull(model_name)
    
    def generate_quiz_questions(self, topic: str = "All Topics", num_questions: int = 5, 
                               context_chunks: List[Dict] = None) -> List[Dict]:
        """Generate CORE-style exam questions"""
        
        questions = []
        
        for i in range(num_questions):
            # Select topic
            if topic == "All Topics":
                selected_topic = random.choice(list(self.core_topics.keys()))
            else:
                selected_topic = topic
            
            # Generate question for the topic
            question = self._generate_single_question(selected_topic, context_chunks)
            if question:
                questions.append(question)
        
        return questions
    
    def _generate_single_question(self, topic: str, context_chunks: List[Dict] = None) -> Dict:
        """Generate a single CORE-style question"""
        
        # Use context if available, otherwise use topic-specific prompt
        if context_chunks and len(context_chunks) > 0:
            context = " ".join([chunk.get('text', '')[:500] for chunk in context_chunks[:3]])
            context_prompt = f"Based on this material: {context}\n\n"
        else:
            context_prompt = ""
        
        # Topic-specific keywords
        keywords = self.core_topics.get(topic, {}).get('keywords', [])
        keyword_hint = f"Focus on: {', '.join(keywords[:3])}" if keywords else ""
        
        system_prompt = """You are an expert radiology educator creating CORE exam questions. 
Create a single multiple-choice question that:
- Tests practical diagnostic radiology knowledge
- Has 4 plausible answer choices (A, B, C, D)
- Includes a brief explanation for the correct answer
- Matches CORE exam difficulty and style
- Is clinically relevant

Format your response as valid JSON:
{
  "question": "The question text",
  "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
  "correct_answer": "A) First option",
  "explanation": "Brief explanation of why this is correct",
  "topic": "Topic name"
}"""

        user_prompt = f"""{context_prompt}Create a {topic} question for radiology CORE exam preparation.
{keyword_hint}

The question should be appropriate for board-certified radiologists and test diagnostic reasoning."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.8,  # Some creativity for varied questions
                    "top_p": 0.9
                }
            )
            
            # Parse JSON response
            content = response['message']['content']
            
            # Try to extract JSON from response
            try:
                # Find JSON in response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    question_data = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ['question', 'options', 'correct_answer', 'explanation']
                    if all(field in question_data for field in required_fields):
                        question_data['topic'] = topic
                        return question_data
                    
            except json.JSONDecodeError:
                pass
            
            # Fallback: create question from text response
            return self._parse_text_response(content, topic)
            
        except Exception as e:
            self.logger.error(f"Failed to generate question: {e}")
            return self._get_fallback_question(topic)
    
    def _parse_text_response(self, content: str, topic: str) -> Dict:
        """Parse non-JSON text response into question format"""
        lines = content.strip().split('\n')
        
        question_text = ""
        options = []
        correct_answer = ""
        explanation = ""
        
        current_section = "question"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(marker in line.lower() for marker in ['question:', 'q:']):
                current_section = "question"
                question_text = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                options.append(line)
                if any(marker in line.lower() for marker in ['correct', '*']):
                    correct_answer = line
            elif any(marker in line.lower() for marker in ['answer:', 'correct:', 'explanation:']):
                current_section = "explanation"
                explanation = line.split(':', 1)[1].strip() if ':' in line else line
            elif current_section == "explanation":
                explanation += " " + line
        
        # Set correct answer if not found
        if not correct_answer and options:
            correct_answer = options[0]  # Default to first option
        
        return {
            "question": question_text or "Sample radiology question",
            "options": options or ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": correct_answer or "A) Option 1",
            "explanation": explanation or "This is the correct answer based on standard radiology practice.",
            "topic": topic
        }
    
    def _get_fallback_question(self, topic: str) -> Dict:
        """Return a fallback question if generation fails"""
        
        fallback_questions = {
            'Physics & Safety': {
                "question": "What is the typical patient dose for a chest CT scan?",
                "options": ["A) 1-2 mSv", "B) 7-10 mSv", "C) 15-20 mSv", "D) 25-30 mSv"],
                "correct_answer": "B) 7-10 mSv",
                "explanation": "A typical chest CT scan delivers approximately 7-10 mSv of radiation dose to the patient."
            },
            'Cardiothoracic': {
                "question": "What is the most common cause of acute pulmonary edema?",
                "options": ["A) Pneumonia", "B) Heart failure", "C) ARDS", "D) Pulmonary embolism"],
                "correct_answer": "B) Heart failure",
                "explanation": "Heart failure is the most common cause of acute pulmonary edema, leading to fluid accumulation in the lungs."
            },
            'Neuroradiology': {
                "question": "Which MRI sequence is most sensitive for acute stroke detection?",
                "options": ["A) T1-weighted", "B) T2-weighted", "C) DWI", "D) FLAIR"],
                "correct_answer": "C) DWI",
                "explanation": "Diffusion-weighted imaging (DWI) is most sensitive for detecting acute ischemic stroke within hours of onset."
            }
        }
        
        default_question = {
            "question": f"What is a key imaging consideration in {topic}?",
            "options": ["A) Technical factors", "B) Patient positioning", "C) Image interpretation", "D) All of the above"],
            "correct_answer": "D) All of the above",
            "explanation": f"All factors are important in {topic} imaging and interpretation."
        }
        
        question_data = fallback_questions.get(topic, default_question)
        question_data['topic'] = topic
        return question_data

    def generate_random_question(self) -> str:
        """Generate a random question prompt"""
        topics = list(self.core_topics.keys())
        topic = random.choice(topics)
        keywords = self.core_topics[topic]['keywords']
        keyword = random.choice(keywords)
        
        prompts = [
            f"Explain the key imaging findings in {keyword} on {topic.lower()} studies",
            f"What are the differential diagnoses for {keyword} in {topic.lower()}?",
            f"Describe the optimal imaging protocol for evaluating {keyword}",
            f"What are the pitfalls in interpreting {keyword} on imaging?"
        ]
        
        return random.choice(prompts)

    def generate_physics_question(self) -> str:
        """Generate a physics-focused question"""
        physics_topics = [
            "CT radiation dose optimization techniques",
            "MRI safety considerations and contraindications", 
            "Ultrasound physics principles and artifacts",
            "X-ray beam characteristics and filtration",
            "Digital radiography image processing",
            "Contrast agent pharmacokinetics and safety"
        ]
        
        return f"Explain the physics behind {random.choice(physics_topics)}"