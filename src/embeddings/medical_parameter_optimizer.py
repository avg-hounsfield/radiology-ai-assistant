# src/embeddings/medical_parameter_optimizer.py
"""
Medical parameter optimization for RadBERT embedding system
Enhances knowledge base with CORE exam focused parameters
"""

import json
import numpy as np
from typing import Dict, List, Tuple
import logging
from pathlib import Path
import re

class MedicalParameterOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # CORE exam weightings by section
        self.core_section_weights = {
            'Physics & Safety': 0.15,
            'Cardiothoracic': 0.20,
            'Neuroradiology': 0.15,
            'Musculoskeletal': 0.10,
            'Abdominal & Pelvic': 0.15,
            'Breast Imaging': 0.08,
            'Pediatric Radiology': 0.07,
            'Nuclear Medicine': 0.10
        }

        # High-yield CORE terms with scoring
        self.high_yield_terms = {
            # Physics (Critical for CORE)
            'radiation_safety': {
                'terms': ['dose', 'alara', 'radiation protection', 'shielding', 'pregnancy', 'pediatric dose'],
                'weight': 5.0,
                'category': 'physics'
            },
            'imaging_physics': {
                'terms': ['kvp', 'mas', 'ct number', 'hounsfield', 'signal intensity', 'contrast resolution'],
                'weight': 4.0,
                'category': 'physics'
            },

            # Emergency findings (High priority)
            'critical_findings': {
                'terms': ['acute', 'emergent', 'urgent', 'stat', 'tension pneumothorax', 'massive pe'],
                'weight': 4.5,
                'category': 'emergency'
            },

            # Reporting standards
            'structured_reporting': {
                'terms': ['bi-rads', 'lung-rads', 'pi-rads', 'ti-rads', 'acr', 'appropriateness criteria'],
                'weight': 3.5,
                'category': 'standards'
            },

            # Differential diagnosis
            'differentials': {
                'terms': ['differential diagnosis', 'ddx', 'most likely', 'pathognomonic', 'characteristic'],
                'weight': 3.0,
                'category': 'diagnosis'
            }
        }

        # Anatomy-specific parameters
        self.anatomy_parameters = {
            'chest': {
                'keywords': ['pneumonia', 'nodule', 'mass', 'consolidation', 'ground glass', 'pleural effusion'],
                'modalities': ['chest x-ray', 'chest ct', 'hrct'],
                'weight_multiplier': 1.2
            },
            'neuro': {
                'keywords': ['stroke', 'hemorrhage', 'ischemia', 'mass effect', 'midline shift', 'hydrocephalus'],
                'modalities': ['head ct', 'brain mri', 'ct angiography', 'mr angiography'],
                'weight_multiplier': 1.3
            },
            'cardiac': {
                'keywords': ['coronary artery', 'myocardial infarction', 'cardiomyopathy', 'pericardial'],
                'modalities': ['cardiac ct', 'cardiac mri', 'coronary angiography'],
                'weight_multiplier': 1.1
            },
            'abdomen': {
                'keywords': ['liver', 'pancreas', 'bowel obstruction', 'appendicitis', 'diverticulitis'],
                'modalities': ['ct abdomen', 'mr abdomen', 'abdominal ultrasound'],
                'weight_multiplier': 1.0
            }
        }

    def calculate_medical_relevance_score(self, text: str, metadata: Dict = None) -> float:
        """Calculate comprehensive medical relevance score"""

        text_lower = text.lower()
        base_score = 0.0

        # High-yield term scoring
        for category, term_data in self.high_yield_terms.items():
            for term in term_data['terms']:
                if term in text_lower:
                    base_score += term_data['weight'] * text_lower.count(term)

        # Anatomy-specific scoring
        for anatomy, params in self.anatomy_parameters.items():
            anatomy_score = 0

            # Check for anatomy keywords
            for keyword in params['keywords']:
                if keyword in text_lower:
                    anatomy_score += 1

            # Check for relevant modalities
            for modality in params['modalities']:
                if modality in text_lower:
                    anatomy_score += 0.5

            # Apply multiplier
            base_score += anatomy_score * params['weight_multiplier']

        # Metadata-based adjustments
        if metadata:
            # Source document scoring
            source = metadata.get('source', '').lower()
            if any(term in source for term in ['board', 'exam', 'core', 'review']):
                base_score *= 1.5

            # Content type scoring
            chunk_type = metadata.get('chunk_type', '')
            if chunk_type in ['case', 'physics', 'finding']:
                base_score *= 1.3

        return min(base_score, 100.0)  # Cap at 100

    def optimize_chunk_metadata(self, chunks: List[Dict]) -> List[Dict]:
        """Optimize chunk metadata with medical parameters"""

        optimized_chunks = []

        for chunk in chunks:
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})

            # Calculate medical relevance
            relevance_score = self.calculate_medical_relevance_score(text, metadata)

            # Determine CORE section
            core_section = self._classify_core_section(text)

            # Extract medical entities
            medical_entities = self._extract_medical_entities(text)

            # Enhanced metadata
            enhanced_metadata = {
                **metadata,
                'medical_relevance_score': relevance_score,
                'core_exam_section': core_section,
                'core_section_weight': self.core_section_weights.get(core_section, 0.05),
                'medical_entities': medical_entities,
                'high_yield_terms': self._identify_high_yield_terms(text),
                'optimization_version': '1.0'
            }

            # Create optimized chunk
            optimized_chunk = {
                'text': text,
                'metadata': enhanced_metadata,
                'optimization_score': relevance_score
            }

            optimized_chunks.append(optimized_chunk)

        # Sort by relevance for prioritized processing
        optimized_chunks.sort(key=lambda x: x['optimization_score'], reverse=True)

        self.logger.info(f"Optimized {len(optimized_chunks)} chunks with medical parameters")

        return optimized_chunks

    def _classify_core_section(self, text: str) -> str:
        """Classify text into CORE exam sections"""

        text_lower = text.lower()

        # Physics indicators
        if any(term in text_lower for term in ['dose', 'kvp', 'physics', 'radiation', 'safety', 'technique']):
            return 'Physics & Safety'

        # Cardiothoracic indicators
        elif any(term in text_lower for term in ['chest', 'lung', 'heart', 'pneumonia', 'cardiac']):
            return 'Cardiothoracic'

        # Neuro indicators
        elif any(term in text_lower for term in ['brain', 'head', 'neuro', 'stroke', 'hemorrhage']):
            return 'Neuroradiology'

        # MSK indicators
        elif any(term in text_lower for term in ['bone', 'joint', 'fracture', 'msk', 'musculoskeletal']):
            return 'Musculoskeletal'

        # Abdominal indicators
        elif any(term in text_lower for term in ['abdomen', 'liver', 'pancreas', 'bowel', 'gi']):
            return 'Abdominal & Pelvic'

        # Breast indicators
        elif any(term in text_lower for term in ['breast', 'mammography', 'birads']):
            return 'Breast Imaging'

        # Pediatric indicators
        elif any(term in text_lower for term in ['pediatric', 'child', 'infant', 'neonatal']):
            return 'Pediatric Radiology'

        # Nuclear medicine indicators
        elif any(term in text_lower for term in ['nuclear', 'pet', 'spect', 'scintigraphy']):
            return 'Nuclear Medicine'

        else:
            return 'General Radiology'

    def _extract_medical_entities(self, text: str) -> List[str]:
        """Extract medical entities from text"""

        entities = []
        text_lower = text.lower()

        # Anatomy entities
        anatomy_terms = [
            'heart', 'lung', 'liver', 'kidney', 'brain', 'spine', 'bone',
            'chest', 'abdomen', 'pelvis', 'head', 'neck', 'extremity'
        ]

        # Pathology entities
        pathology_terms = [
            'tumor', 'mass', 'lesion', 'nodule', 'cyst', 'inflammation',
            'infection', 'hemorrhage', 'infarct', 'edema', 'stenosis'
        ]

        # Modality entities
        modality_terms = [
            'ct', 'mri', 'x-ray', 'ultrasound', 'pet', 'spect',
            'mammography', 'fluoroscopy', 'angiography'
        ]

        all_terms = anatomy_terms + pathology_terms + modality_terms

        for term in all_terms:
            if term in text_lower:
                entities.append(term)

        return list(set(entities))  # Remove duplicates

    def _identify_high_yield_terms(self, text: str) -> List[str]:
        """Identify high-yield terms for CORE exam"""

        high_yield = []
        text_lower = text.lower()

        for category, term_data in self.high_yield_terms.items():
            for term in term_data['terms']:
                if term in text_lower:
                    high_yield.append(f"{category}:{term}")

        return high_yield

    def generate_optimization_report(self, chunks: List[Dict]) -> Dict:
        """Generate optimization report"""

        total_chunks = len(chunks)

        # Score distribution
        scores = [chunk.get('optimization_score', 0) for chunk in chunks]
        avg_score = np.mean(scores) if scores else 0

        # Section distribution
        section_counts = {}
        for chunk in chunks:
            section = chunk.get('metadata', {}).get('core_exam_section', 'Unknown')
            section_counts[section] = section_counts.get(section, 0) + 1

        # High-yield content percentage
        high_yield_chunks = sum(1 for chunk in chunks
                               if chunk.get('optimization_score', 0) > 10)
        high_yield_percentage = (high_yield_chunks / total_chunks * 100) if total_chunks > 0 else 0

        report = {
            'total_chunks': total_chunks,
            'average_relevance_score': round(avg_score, 2),
            'high_yield_percentage': round(high_yield_percentage, 1),
            'section_distribution': section_counts,
            'optimization_recommendations': self._generate_recommendations(chunks)
        }

        return report

    def _generate_recommendations(self, chunks: List[Dict]) -> List[str]:
        """Generate optimization recommendations"""

        recommendations = []

        # Check physics content
        physics_chunks = sum(1 for chunk in chunks
                           if chunk.get('metadata', {}).get('core_exam_section') == 'Physics & Safety')
        total_chunks = len(chunks)

        if physics_chunks / total_chunks < 0.15:
            recommendations.append("Consider adding more physics and safety content (current: {:.1%}, target: 15%)".format(physics_chunks / total_chunks))

        # Check high-yield content
        high_yield_chunks = sum(1 for chunk in chunks
                               if chunk.get('optimization_score', 0) > 15)

        if high_yield_chunks / total_chunks < 0.3:
            recommendations.append("Consider adding more high-yield CORE content")

        # Check for case-based content
        case_chunks = sum(1 for chunk in chunks
                         if 'case' in chunk.get('metadata', {}).get('chunk_type', '').lower())

        if case_chunks / total_chunks < 0.2:
            recommendations.append("Consider adding more case-based learning materials")

        return recommendations

    def save_optimization_parameters(self, file_path: str = "data/medical_optimization_params.json"):
        """Save optimization parameters to file"""

        params = {
            'core_section_weights': self.core_section_weights,
            'high_yield_terms': self.high_yield_terms,
            'anatomy_parameters': self.anatomy_parameters,
            'version': '1.0',
            'description': 'Medical parameter optimization for RadBERT embedding system'
        }

        Path(file_path).parent.mkdir(exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(params, f, indent=2)

        self.logger.info(f"Optimization parameters saved to {file_path}")

        return params