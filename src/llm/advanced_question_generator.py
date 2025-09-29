# src/llm/advanced_question_generator.py
"""
Advanced question generator for board preparation
Creates high-quality, board-style questions with detailed explanations
"""

import ollama
import random
import json
from typing import List, Dict, Optional
import logging

class AdvancedBoardQuestionGenerator:
    def __init__(self, llm_model: str = "llama3.1:8b"):
        self.llm_model = llm_model
        self.client = ollama.Client()
        self.logger = logging.getLogger(__name__)

        # Board-style question templates with clinical vignettes
        self.clinical_templates = {
            'chest': {
                'pneumonia': [
                    "A {age}-year-old {gender} presents to the emergency department with {symptoms}. Vital signs show {vitals}. Chest X-ray demonstrates {findings}.",
                    "A {age}-year-old {gender} with history of {comorbidity} develops {symptoms} over {duration}. Physical exam reveals {physical_findings}. CT chest shows {ct_findings}."
                ],
                'pe': [
                    "A {age}-year-old {gender} presents with acute onset {symptoms}. Recent history includes {risk_factor}. D-dimer is {dimer_value}. CTPA demonstrates {ctpa_findings}.",
                    "A postoperative {age}-year-old {gender} develops {symptoms} on postop day {day}. Wells score is {wells_score}. Imaging reveals {findings}."
                ],
                'nodules': [
                    "A {age}-year-old {smoking_history} has an incidental {size}mm {location} pulmonary nodule on chest CT. The nodule shows {characteristics}.",
                    "Follow-up CT in a {age}-year-old shows a {location} nodule that has {change} from {size1}mm to {size2}mm over {timeframe}."
                ]
            },
            'neuro': {
                'stroke': [
                    "A {age}-year-old {gender} presents with acute onset {neuro_symptoms}. NIHSS score is {nihss}. Onset time was {time_hours} hours ago. Non-contrast head CT shows {ct_findings}.",
                    "A {age}-year-old with history of {cardiovascular_risk} develops {symptoms} witnessed at {time}. Exam shows {neuro_exam}. MRI demonstrates {mri_findings}."
                ],
                'hemorrhage': [
                    "A {age}-year-old presents with sudden severe headache and {symptoms}. Blood pressure is {bp}. Non-contrast head CT demonstrates {hemorrhage_pattern}.",
                    "A {age}-year-old on {anticoagulant} presents after {mechanism} with {symptoms}. Glasgow Coma Scale is {gcs}. CT head shows {findings}."
                ],
                'trauma': [
                    "A {age}-year-old involved in {mechanism} presents with {symptoms}. GCS is {gcs}. CT head demonstrates {trauma_findings}.",
                    "A {age}-year-old pedestrian struck by vehicle presents with {symptoms}. Cervical spine CT shows {spine_findings}."
                ]
            },
            'abdomen': {
                'appendicitis': [
                    "A {age}-year-old {gender} presents with {symptom_progression} abdominal pain. Physical exam shows {exam_findings}. WBC count is {wbc}. CT abdomen reveals {ct_findings}.",
                    "A {age}-year-old with {duration} of abdominal pain, nausea, and {symptoms}. Alvarado score is {alvarado}. Ultrasound shows {us_findings}."
                ],
                'bowel_obstruction': [
                    "A {age}-year-old with history of {surgical_history} presents with {symptoms} for {duration}. Physical exam reveals {exam}. CT abdomen demonstrates {findings}.",
                    "A {age}-year-old develops {symptoms} after {precipitant}. Abdominal X-ray shows {xray_findings}. CT confirms {ct_findings}."
                ],
                'liver': [
                    "A {age}-year-old with known {liver_disease} undergoes surveillance imaging. MRI liver shows a {size}cm lesion in segment {segment} with {enhancement_pattern}.",
                    "A {age}-year-old with elevated {lab_values} undergoes abdominal CT. A {size}cm {location} hepatic lesion demonstrates {imaging_characteristics}."
                ]
            },
            'msk': {
                'fractures': [
                    "A {age}-year-old sustains injury to the {anatomic_site} after {mechanism}. Physical exam shows {exam_findings}. X-rays demonstrate {fracture_pattern}.",
                    "A {age}-year-old athlete presents with {symptoms} after {sports_mechanism}. MRI shows {mri_findings} involving the {structure}."
                ],
                'arthritis': [
                    "A {age}-year-old with {duration} of joint pain affecting {joints}. Morning stiffness lasts {stiffness_duration}. Hand X-rays show {radiographic_findings}.",
                    "A {age}-year-old presents with acute {joint} pain and swelling. Synovial fluid analysis shows {fluid_findings}. Imaging demonstrates {findings}."
                ]
            },
            'physics': {
                'radiation_safety': [
                    "A pregnant radiology technologist is concerned about fetal radiation exposure. She works in {modality} and estimates {exposure_scenario}.",
                    "A {age}-year-old patient requires {exam_type}. The estimated radiation dose is {dose}. Patient asks about {radiation_concern}."
                ],
                'ct_physics': [
                    "A CT scanner operates at {kvp} kVp and {mas} mAs. The patient effective diameter is {diameter}cm. Calculate the {physics_parameter}.",
                    "CT image shows significant {artifact_type} artifact. The scanning parameters were {parameters}. What is the most likely cause?"
                ]
            }
        }

        # Answer choice templates for different question types
        self.answer_templates = {
            'diagnosis': [
                "Most likely diagnosis",
                "Next most appropriate diagnosis",
                "Differential diagnosis includes all EXCEPT",
                "Most appropriate next step in diagnosis"
            ],
            'management': [
                "Most appropriate next step in management",
                "Best initial treatment",
                "Most appropriate follow-up",
                "Recommended management approach"
            ],
            'imaging': [
                "Most appropriate imaging modality",
                "Next best imaging study",
                "Most cost-effective imaging approach",
                "Best imaging for follow-up"
            ],
            'anatomy': [
                "Structure most likely involved",
                "Anatomic location",
                "Most likely anatomic variant",
                "Structure best visualized on this sequence"
            ]
        }

    def generate_comprehensive_question(self, section: str, difficulty: str = "intermediate",
                                      question_type: str = "diagnosis") -> Dict:
        """Generate comprehensive board-style question"""

        try:
            # Select appropriate template
            section_templates = self.clinical_templates.get(section.lower(), {})
            if not section_templates:
                return self.generate_generic_question(section, difficulty)

            # Select random topic within section
            topic = random.choice(list(section_templates.keys()))
            template = random.choice(section_templates[topic])

            # Generate clinical vignette
            vignette = self.populate_clinical_template(template, section, topic, difficulty)

            # Generate question stem
            question_stem = self.generate_question_stem(section, topic, question_type)

            # Generate answer choices
            answer_choices = self.generate_answer_choices(section, topic, question_type, difficulty)

            # Create complete question
            question_text = f"{vignette}\n\n{question_stem}"

            # Select correct answer
            correct_answer = random.choice(['A', 'B', 'C', 'D'])

            # Generate explanation
            explanation = self.generate_detailed_explanation(
                section, topic, vignette, question_stem, answer_choices, correct_answer
            )

            return {
                'question': question_text,
                'options': {
                    'A': answer_choices[0],
                    'B': answer_choices[1],
                    'C': answer_choices[2],
                    'D': answer_choices[3]
                },
                'correct_answer': correct_answer,
                'explanation': explanation,
                'section': section,
                'topic': topic,
                'difficulty': difficulty,
                'question_type': question_type,
                'success': True
            }

        except Exception as e:
            self.logger.error(f"Error generating question: {e}")
            return {
                'question': f"Error generating question: {str(e)}",
                'success': False,
                'error': str(e)
            }

    def populate_clinical_template(self, template: str, section: str, topic: str, difficulty: str) -> str:
        """Fill in clinical template with realistic values"""

        # Age ranges by difficulty
        age_ranges = {
            'easy': (30, 70),
            'intermediate': (20, 80),
            'hard': (1, 90)  # Include pediatric/elderly
        }

        age_min, age_max = age_ranges[difficulty]
        age = random.randint(age_min, age_max)
        gender = random.choice(['male', 'female'])

        # Topic-specific values
        values = {
            'age': age,
            'gender': gender,
            'symptoms': self.get_topic_symptoms(topic),
            'vitals': self.get_realistic_vitals(),
            'findings': self.get_imaging_findings(topic),
            'comorbidity': self.get_comorbidity(),
            'duration': random.choice(['2 hours', '6 hours', '2 days', '1 week']),
            'size': random.randint(5, 40),
            'location': self.get_anatomic_location(section),
            'mechanism': self.get_trauma_mechanism(),
            'bp': f"{random.randint(90, 200)}/{random.randint(60, 120)}",
            'gcs': random.randint(3, 15),
            'wbc': f"{random.randint(5, 25)},000",
            'dose': f"{random.randint(1, 50)} mSv"
        }

        # Replace template placeholders
        try:
            return template.format(**values)
        except KeyError as e:
            # Handle missing keys gracefully
            return template.replace('{' + str(e).strip("'") + '}', '[clinical_detail]')

    def get_topic_symptoms(self, topic: str) -> str:
        """Get realistic symptoms for topic"""
        symptom_map = {
            'pneumonia': random.choice(['fever and cough', 'dyspnea and pleuritic chest pain', 'productive cough and fever']),
            'pe': random.choice(['acute dyspnea and chest pain', 'sudden onset dyspnea', 'chest pain and hemoptysis']),
            'stroke': random.choice(['left-sided weakness', 'aphasia and right hemiparesis', 'facial droop and dysarthria']),
            'appendicitis': random.choice(['periumbilical pain migrating to RLQ', 'right lower quadrant pain', 'abdominal pain and vomiting']),
            'fractures': random.choice(['pain and swelling', 'deformity and inability to bear weight', 'pain and limited range of motion'])
        }
        return symptom_map.get(topic, 'pain and associated symptoms')

    def get_realistic_vitals(self) -> str:
        """Generate realistic vital signs"""
        temp = random.choice(['98.6°F', '100.2°F', '101.8°F', '99.1°F'])
        hr = random.randint(60, 120)
        bp_sys = random.randint(90, 180)
        bp_dia = random.randint(60, 100)
        rr = random.randint(12, 24)
        spo2 = random.randint(88, 100)

        return f"T {temp}, HR {hr}, BP {bp_sys}/{bp_dia}, RR {rr}, SpO2 {spo2}%"

    def get_imaging_findings(self, topic: str) -> str:
        """Get realistic imaging findings"""
        findings_map = {
            'pneumonia': random.choice(['right lower lobe consolidation', 'bilateral infiltrates', 'left upper lobe opacity with air bronchograms']),
            'pe': random.choice(['filling defect in right main pulmonary artery', 'segmental pulmonary emboli bilaterally', 'saddle embolus']),
            'stroke': random.choice(['hypodense region in left MCA territory', 'restricted diffusion in right basal ganglia', 'loss of gray-white differentiation']),
            'appendicitis': random.choice(['appendiceal wall thickening with periappendiceal fat stranding', 'dilated appendix with appendicolith', 'fluid around the appendix'])
        }
        return findings_map.get(topic, 'abnormal findings consistent with clinical presentation')

    def get_comorbidity(self) -> str:
        """Get realistic comorbidity"""
        return random.choice(['diabetes', 'hypertension', 'COPD', 'coronary artery disease', 'chronic kidney disease'])

    def get_anatomic_location(self, section: str) -> str:
        """Get anatomic location by section"""
        location_map = {
            'chest': random.choice(['right upper lobe', 'left lower lobe', 'right middle lobe', 'bilateral']),
            'neuro': random.choice(['frontal lobe', 'parietal lobe', 'basal ganglia', 'cerebellum']),
            'abdomen': random.choice(['right hepatic lobe', 'left hepatic lobe', 'pancreatic head', 'pancreatic tail']),
            'msk': random.choice(['proximal femur', 'distal radius', 'cervical spine', 'lumbar spine'])
        }
        return location_map.get(section, 'anatomic region')

    def get_trauma_mechanism(self) -> str:
        """Get trauma mechanism"""
        return random.choice(['motor vehicle collision', 'fall from height', 'sports injury', 'pedestrian versus vehicle'])

    def generate_question_stem(self, section: str, topic: str, question_type: str) -> str:
        """Generate appropriate question stem"""

        stems = {
            'diagnosis': [
                "What is the most likely diagnosis?",
                "Which of the following is the most appropriate next step in diagnosis?",
                "The differential diagnosis includes all of the following EXCEPT:",
                "Based on the clinical presentation and imaging findings, what is the most likely diagnosis?"
            ],
            'management': [
                "What is the most appropriate next step in management?",
                "Which of the following treatments is most appropriate?",
                "The best initial management is:",
                "What is the most appropriate follow-up?"
            ],
            'imaging': [
                "What is the most appropriate next imaging study?",
                "Which imaging modality is best for this clinical scenario?",
                "The most cost-effective imaging approach is:",
                "What imaging finding would you expect to see?"
            ]
        }

        return random.choice(stems.get(question_type, stems['diagnosis']))

    def generate_answer_choices(self, section: str, topic: str, question_type: str, difficulty: str) -> List[str]:
        """Generate realistic answer choices"""

        # Use LLM to generate contextually appropriate choices
        prompt = f"""Generate 4 realistic answer choices for a {difficulty} level radiology board question about {topic} in {section}.

Question type: {question_type}

Requirements:
- Medical accuracy
- Appropriate for radiology board exam
- One clearly correct answer
- Plausible distractors
- Professional medical terminology

Format: Return only the 4 answer choices as a simple list."""

        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a radiology attending creating board exam questions."},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 400
                }
            )

            # Parse response into choices
            answer_text = response['message']['content']
            choices = self.parse_answer_choices(answer_text)

            if len(choices) == 4:
                return choices
            else:
                # Fallback to generic choices
                return self.generate_fallback_choices(section, topic, question_type)

        except Exception as e:
            self.logger.error(f"Error generating answer choices: {e}")
            return self.generate_fallback_choices(section, topic, question_type)

    def parse_answer_choices(self, text: str) -> List[str]:
        """Parse answer choices from LLM response"""
        lines = text.strip().split('\n')
        choices = []

        for line in lines:
            line = line.strip()
            if line and (line.startswith(('A)', 'B)', 'C)', 'D)', '1.', '2.', '3.', '4.', '-', '•'))):
                # Clean up the choice
                clean_choice = line.split(')', 1)[-1].split('.', 1)[-1].strip(' -•')
                if clean_choice:
                    choices.append(clean_choice)

        return choices[:4]  # Return first 4 valid choices

    def generate_fallback_choices(self, section: str, topic: str, question_type: str) -> List[str]:
        """Generate fallback answer choices"""
        fallback_choices = {
            'chest': [
                "Community-acquired pneumonia",
                "Pulmonary embolism",
                "Lung cancer",
                "Pulmonary edema"
            ],
            'neuro': [
                "Acute ischemic stroke",
                "Intracranial hemorrhage",
                "Brain tumor",
                "Metabolic encephalopathy"
            ],
            'abdomen': [
                "Acute appendicitis",
                "Diverticulitis",
                "Bowel obstruction",
                "Inflammatory bowel disease"
            ],
            'physics': [
                "Increase technique factors",
                "Decrease patient dose",
                "Improve image quality",
                "Reduce scan time"
            ]
        }

        return fallback_choices.get(section, [
            "Option A - Primary consideration",
            "Option B - Alternative diagnosis",
            "Option C - Less likely possibility",
            "Option D - Unlikely diagnosis"
        ])

    def generate_detailed_explanation(self, section: str, topic: str, vignette: str,
                                    question_stem: str, answer_choices: List[str],
                                    correct_answer: str) -> str:
        """Generate comprehensive explanation"""

        explanation_prompt = f"""Create a detailed explanation for this radiology board question:

Clinical Vignette: {vignette}

Question: {question_stem}

Answer Choices:
A) {answer_choices[0]}
B) {answer_choices[1]}
C) {answer_choices[2]}
D) {answer_choices[3]}

Correct Answer: {correct_answer}

Provide a comprehensive explanation including:
1. Why the correct answer is right
2. Why other options are incorrect
3. Key teaching points
4. Relevant imaging pearls
5. Clinical significance

Keep explanation focused and educational for board preparation."""

        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a radiology attending providing detailed explanations for board questions."},
                    {"role": "user", "content": explanation_prompt}
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 800
                }
            )

            return response['message']['content']

        except Exception as e:
            self.logger.error(f"Error generating explanation: {e}")
            return f"The correct answer is {correct_answer}. This question tests knowledge of {topic} in {section}."

    def generate_generic_question(self, section: str, difficulty: str) -> Dict:
        """Generate generic question when specific templates not available"""

        generic_prompt = f"""Create a {difficulty} level radiology board question for {section}.

Requirements:
- Clinical vignette format
- 4 multiple choice options
- Detailed explanation
- Board-appropriate content
- Focus on high-yield topics

Format your response as a complete question with options A-D."""

        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are creating radiology board exam questions."},
                    {"role": "user", "content": generic_prompt}
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 1000
                }
            )

            return {
                'question': response['message']['content'],
                'section': section,
                'difficulty': difficulty,
                'success': True,
                'type': 'generic'
            }

        except Exception as e:
            return {
                'question': f"Error generating question: {str(e)}",
                'success': False,
                'error': str(e)
            }