# src/retrieval/medical_rag_system.py
"""
Complete medical RAG system with RadBERT integration and advanced features
"""

from typing import List, Dict, Optional, Tuple
import logging
import sys
import os
from datetime import datetime, timedelta
import json
import pandas as pd

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embeddings.medical_embedding_generator import MedicalEmbeddingSystem
from llm.medical_llm import MedicalLLMManager
from config.medical_config import CORE_EXAM_CONFIG, RADIOLOGY_KEYWORDS, ADVANCED_FEATURES

class MedicalRadiologyRAGSystem:
    def __init__(self, embedding_model: str = "radiology_optimized", 
                 llm_model: str = "llama3.1:8b"):
        
        # Initialize core components with medical focus
        self.embedding_system = MedicalEmbeddingSystem(embedding_model)
        self.llm_manager = MedicalLLMManager(llm_model)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize advanced features
        self.study_analytics = StudyAnalytics()
        self.question_generator = QuestionGenerator(self.llm_manager)
        self.progress_tracker = ProgressTracker()
        
        # Log model information
        model_info = self.embedding_system.get_model_info()
        self.logger.info(f"Initialized with embedding model: {model_info['model_name']}")
        self.logger.info(f"Medical-specific model: {model_info['is_medical_specific']}")
    
    def process_documents(self, document_paths: List[str]) -> Dict:
        """Enhanced document processing with medical categorization"""
        from document_processor.pdf_processor import PDFProcessor
        from document_processor.ppt_processor import PPTProcessor
        
        pdf_processor = PDFProcessor()
        ppt_processor = PPTProcessor()
        
        all_chunks = []
        processing_stats = {
            'total_documents': len(document_paths),
            'processed_successfully': 0,
            'failed_documents': [],
            'chunk_categories': {'text': 0, 'cases': 0, 'physics': 0},
            'total_chunks': 0
        }
        
        for doc_path in document_paths:
            self.logger.info(f"Processing: {os.path.basename(doc_path)}")
            
            try:
                if doc_path.lower().endswith('.pdf'):
                    content = pdf_processor.extract_text_and_metadata(doc_path)
                    chunks = pdf_processor.semantic_chunking(content['text'], content['metadata'])
                elif doc_path.lower().endswith(('.ppt', '.pptx')):
                    content = ppt_processor.extract_content(doc_path)
                    chunks = ppt_processor.create_chunks(content)
                else:
                    self.logger.warning(f"Unsupported file type: {doc_path}")
                    continue
                
                # Medical preprocessing
                chunks = self._preprocess_medical_chunks(chunks)
                all_chunks.extend(chunks)
                processing_stats['processed_successfully'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {doc_path}: {str(e)}")
                processing_stats['failed_documents'].append({
                    'path': doc_path,
                    'error': str(e)
                })
        
        # Add medical keyword boosting
        all_chunks = self.embedding_system.add_medical_keywords_boost(all_chunks)
        
        # Categorize chunks for analytics
        for chunk in all_chunks:
            chunk_type = chunk['metadata'].get('chunk_type', 'text')
            if chunk_type in processing_stats['chunk_categories']:
                processing_stats['chunk_categories'][chunk_type] += 1
            else:
                processing_stats['chunk_categories']['text'] += 1
        
        # Add to vector store
        self.embedding_system.add_text_chunks(all_chunks)
        
        processing_stats['total_chunks'] = len(all_chunks)
        
        self.logger.info(f"""Processing complete:
        - Documents: {processing_stats['processed_successfully']}/{processing_stats['total_documents']}
        - Total chunks: {processing_stats['total_chunks']}
        - Categories: {processing_stats['chunk_categories']}""")
        
        return processing_stats
    
    def _preprocess_medical_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Preprocess chunks with medical-specific enhancements"""
        processed_chunks = []
        
        for chunk in chunks:
            # Add medical metadata
            chunk['metadata']['processed_timestamp'] = datetime.now().isoformat()
            chunk['metadata']['medical_domain'] = 'radiology'
            
            # Detect CORE exam areas
            detected_areas = self._detect_core_areas(chunk['text'])
            if detected_areas:
                chunk['metadata']['core_exam_areas'] = detected_areas
            
            # Detect urgency level
            urgency = self._detect_urgency_level(chunk['text'])
            chunk['metadata']['urgency_level'] = urgency
            
            # Detect modalities
            modalities = self._detect_imaging_modalities(chunk['text'])
            if modalities:
                chunk['metadata']['imaging_modalities'] = modalities
            
            processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _detect_core_areas(self, text: str) -> List[str]:
        """Detect which CORE exam areas are covered in the text"""
        text_lower = text.lower()
        detected_areas = []
        
        for area, config in CORE_EXAM_CONFIG['exam_areas'].items():
            keywords = config.get('keywords', []) + config.get('topics', [])
            if any(keyword.lower() in text_lower for keyword in keywords):
                detected_areas.append(area)
        
        return detected_areas
    
    def _detect_urgency_level(self, text: str) -> str:
        """Detect urgency level of medical content"""
        text_lower = text.lower()
        
        emergency_indicators = [
            'emergency', 'urgent', 'acute', 'stat', 'immediate',
            'stroke', 'mi', 'trauma', 'hemorrhage', 'rupture'
        ]
        
        if any(indicator in text_lower for indicator in emergency_indicators):
            return 'high'
        
        routine_indicators = [
            'screening', 'follow-up', 'routine', 'surveillance', 'wellness'
        ]
        
        if any(indicator in text_lower for indicator in routine_indicators):
            return 'low'
        
        return 'medium'
    
    def _detect_imaging_modalities(self, text: str) -> List[str]:
        """Detect imaging modalities mentioned in text"""
        text_lower = text.lower()
        modalities = []
        
        modality_patterns = {
            'ct': ['ct scan', 'computed tomography', 'ct', 'cta', 'ctpa'],
            'mri': ['mri', 'magnetic resonance', 'mra', 'mrcp', 'dwi', 'flair'],
            'ultrasound': ['ultrasound', 'sonography', 'doppler', 'echo'],
            'xray': ['x-ray', 'radiograph', 'plain film', 'chest x-ray'],
            'nuclear': ['pet', 'spect', 'bone scan', 'nuclear medicine'],
            'fluoroscopy': ['fluoroscopy', 'barium', 'upper gi', 'lower gi'],
            'mammography': ['mammography', 'tomosynthesis', 'breast imaging']
        }
        
        for modality, patterns in modality_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                modalities.append(modality)
        
        return modalities
    
    def query(self, question: str, n_results: int = 5,
              search_strategy: str = "adaptive",
              conversation_history: List[Dict] = None) -> Dict:
        """Enhanced query with medical intelligence"""
        
        # Analyze question for medical context
        question_analysis = self._analyze_medical_question(question)
        
        # Adaptive search based on question type
        if search_strategy == "adaptive":
            search_type = self._determine_search_strategy(question, question_analysis)
        else:
            search_type = search_strategy
        
        # Retrieve relevant chunks
        search_results = self.embedding_system.search_similar_texts(
            question, n_results, search_type
        )
        
        # Prepare context chunks with medical metadata
        context_chunks = []
        for i in range(len(search_results['documents'][0])):
            context_chunks.append({
                'text': search_results['documents'][0][i],
                'metadata': search_results['metadatas'][0][i],
                'similarity_score': 1 - search_results['distances'][0][i],  # Convert distance to similarity
                'rank': i + 1
            })
        
        # Determine response type based on question analysis
        response_type = self._determine_response_type(question_analysis)
        
        # Generate response
        response = self.llm_manager.generate_response(
            query=question,
            context_chunks=context_chunks,
            response_type=response_type,
            conversation_history=conversation_history
        )
        
        # Enhanced response with analytics
        response.update({
            'question_analysis': question_analysis,
            'search_strategy': search_type,
            'retrieval_info': {
                'chunks_retrieved': len(context_chunks),
                'search_query': question,
                'avg_similarity': sum(chunk['similarity_score'] for chunk in context_chunks) / len(context_chunks) if context_chunks else 0,
                'search_type': search_type
            },
            'medical_metadata': {
                'core_areas_covered': self._extract_core_areas_from_response(context_chunks),
                'modalities_discussed': self._extract_modalities_from_response(context_chunks),
                'urgency_level': max([chunk['metadata'].get('urgency_level', 'medium') for chunk in context_chunks], 
                                   key=['low', 'medium', 'high'].index, default='medium')
            }
        })
        
        # Update study analytics
        self.study_analytics.record_query(question, response, question_analysis)
        
        return response
    
    def _analyze_medical_question(self, question: str) -> Dict:
        """Analyze medical question for intelligent routing"""
        question_lower = question.lower()
        
        analysis = {
            'question_type': 'general',
            'core_areas': [],
            'modalities': [],
            'complexity_level': 'intermediate',
            'clinical_context': False,
            'physics_focus': False,
            'case_based': False
        }
        
        # Detect question type
        if any(indicator in question_lower for indicator in ['case', 'patient', 'year old']):
            analysis['question_type'] = 'case_study'
            analysis['case_based'] = True
        elif any(indicator in question_lower for indicator in ['physics', 'dose', 'technique']):
            analysis['question_type'] = 'physics'
            analysis['physics_focus'] = True
        elif any(indicator in question_lower for indicator in ['differential', 'diagnosis', 'consider']):
            analysis['question_type'] = 'differential'
        elif any(indicator in question_lower for indicator in ['protocol', 'how to', 'procedure']):
            analysis['question_type'] = 'protocol'
        
        # Detect CORE areas
        analysis['core_areas'] = self._detect_core_areas(question)
        
        # Detect modalities
        analysis['modalities'] = self._detect_imaging_modalities(question)
        
        # Assess complexity
        complexity_indicators = {
            'basic': ['what is', 'define', 'list', 'name'],
            'intermediate': ['explain', 'describe', 'compare', 'discuss'],
            'advanced': ['analyze', 'evaluate', 'differentiate', 'synthesize']
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in question_lower for indicator in indicators):
                analysis['complexity_level'] = level
                break
        
        # Clinical context
        clinical_indicators = ['patient', 'clinical', 'presentation', 'symptoms', 'history']
        analysis['clinical_context'] = any(indicator in question_lower for indicator in clinical_indicators)
        
        return analysis
    
    def _determine_search_strategy(self, question: str, analysis: Dict) -> str:
        """Determine optimal search strategy based on question analysis"""
        
        if analysis['physics_focus']:
            return "physics_focused"
        elif analysis['case_based']:
            return "case_focused"
        elif len(analysis['core_areas']) == 1:
            return "area_specific"
        else:
            return "comprehensive"
    
    def _determine_response_type(self, analysis: Dict) -> str:
        """Determine LLM response type based on question analysis"""
        
        if analysis['question_type'] == 'physics':
            return 'physics_focused'
        elif analysis['question_type'] == 'case_study':
            return 'case_based'
        elif analysis['question_type'] == 'differential':
            return 'differential_focused'
        else:
            return 'radiology_expert'
    
    def _extract_core_areas_from_response(self, context_chunks: List[Dict]) -> List[str]:
        """Extract CORE exam areas covered in the response"""
        areas = set()
        for chunk in context_chunks:
            chunk_areas = chunk['metadata'].get('core_exam_areas', [])
            areas.update(chunk_areas)
        return list(areas)
    
    def _extract_modalities_from_response(self, context_chunks: List[Dict]) -> List[str]:
        """Extract imaging modalities discussed in the response"""
        modalities = set()
        for chunk in context_chunks:
            chunk_modalities = chunk['metadata'].get('imaging_modalities', [])
            modalities.update(chunk_modalities)
        return list(modalities)
    
    def generate_study_recommendations(self, study_history: List[Dict]) -> Dict:
        """Generate personalized study recommendations"""
        
        # Analyze study patterns
        area_performance = self.study_analytics.analyze_area_performance(study_history)
        
        recommendations = {
            'weak_areas': [],
            'suggested_topics': [],
            'study_plan': {},
            'practice_questions': []
        }
        
        # Identify weak areas (< 70% performance)
        for area, stats in area_performance.items():
            if stats.get('accuracy', 100) < 70:
                recommendations['weak_areas'].append({
                    'area': area,
                    'current_score': stats.get('accuracy', 0),
                    'questions_attempted': stats.get('count', 0),
                    'focus_topics': CORE_EXAM_CONFIG['exam_areas'][area]['topics'][:3]
                })
        
        # Generate practice questions for weak areas
        for weak_area in recommendations['weak_areas'][:3]:  # Top 3 weak areas
            question = self.question_generator.generate_area_question(
                weak_area['area'], 
                difficulty="intermediate"
            )
            recommendations['practice_questions'].append(question)
        
        return recommendations
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        model_info = self.embedding_system.get_model_info()
        
        return {
            'embedding_model': model_info,
            'llm_model': self.llm_manager.model_name,
            'collections': {
                'text_documents': self.embedding_system.text_collection.count(),
                'case_studies': self.embedding_system.case_collection.count(),
                'physics_content': self.embedding_system.physics_collection.count()
            },
            'analytics': self.study_analytics.get_summary_stats(),
            'system_health': 'operational'
        }


class StudyAnalytics:
    """Track and analyze study patterns"""
    
    def __init__(self):
        self.query_log = []
        self.performance_data = {}
    
    def record_query(self, question: str, response: Dict, analysis: Dict):
        """Record query for analytics"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response_success': response.get('success', False),
            'question_type': analysis.get('question_type'),
            'core_areas': analysis.get('core_areas', []),
            'complexity': analysis.get('complexity_level'),
            'retrieval_quality': response.get('retrieval_info', {}).get('avg_similarity', 0)
        }
        
        self.query_log.append(record)
    
    def analyze_area_performance(self, study_history: List[Dict]) -> Dict:
        """Analyze performance by CORE area"""
        area_stats = {}
        
        for area in CORE_EXAM_CONFIG['exam_areas'].keys():
            area_questions = [q for q in self.query_log if area in q.get('core_areas', [])]
            
            area_stats[area] = {
                'count': len(area_questions),
                'success_rate': sum(1 for q in area_questions if q.get('response_success')) / max(len(area_questions), 1) * 100,
                'avg_complexity': self._calculate_avg_complexity(area_questions),
                'recent_activity': len([q for q in area_questions if self._is_recent(q['timestamp'])])
            }
        
        return area_stats
    
    def _calculate_avg_complexity(self, questions: List[Dict]) -> str:
        """Calculate average complexity level"""
        if not questions:
            return 'basic'
        
        complexity_scores = {'basic': 1, 'intermediate': 2, 'advanced': 3}
        avg_score = sum(complexity_scores.get(q.get('complexity', 'intermediate'), 2) for q in questions) / len(questions)
        
        if avg_score < 1.5:
            return 'basic'
        elif avg_score < 2.5:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """Check if timestamp is within recent days"""
        try:
            query_time = datetime.fromisoformat(timestamp)
            return (datetime.now() - query_time).days <= days
        except:
            return False
    
    def get_summary_stats(self) -> Dict:
        """Get summary analytics"""
        return {
            'total_queries': len(self.query_log),
            'success_rate': sum(1 for q in self.query_log if q.get('response_success')) / max(len(self.query_log), 1) * 100,
            'most_queried_areas': self._get_top_areas(),
            'recent_activity': len([q for q in self.query_log if self._is_recent(q['timestamp'])])
        }
    
    def _get_top_areas(self, limit: int = 5) -> List[Dict]:
        """Get most queried CORE areas"""
        area_counts = {}
        for query in self.query_log:
            for area in query.get('core_areas', []):
                area_counts[area] = area_counts.get(area, 0) + 1
        
        return sorted([{'area': area, 'count': count} for area, count in area_counts.items()], 
                     key=lambda x: x['count'], reverse=True)[:limit]


class QuestionGenerator:
    """Generate practice questions"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
    
    def generate_area_question(self, area: str, difficulty: str = "intermediate") -> Dict:
        """Generate question for specific CORE area"""
        area_config = CORE_EXAM_CONFIG['exam_areas'].get(area, {})
        topics = area_config.get('topics', [area])
        
        return self.llm_manager.generate_practice_question(
            topic=f"{area} radiology - {', '.join(topics[:3])}", 
            difficulty=difficulty
        )


class ProgressTracker:
    """Track learning progress"""
    
    def __init__(self):
        self.progress_data = {}
        self.milestones = {}
    
    def update_progress(self, area: str, performance_score: float):
        """Update progress for CORE area"""
        if area not in self.progress_data:
            self.progress_data[area] = {
                'scores': [],
                'trend': 'stable',
                'last_updated': datetime.now().isoformat()
            }
        
        self.progress_data[area]['scores'].append({
            'score': performance_score,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update trend
        if len(self.progress_data[area]['scores']) >= 3:
            recent_scores = [s['score'] for s in self.progress_data[area]['scores'][-3:]]
            if recent_scores[-1] > recent_scores[0]:
                self.progress_data[area]['trend'] = 'improving'
            elif recent_scores[-1] < recent_scores[0]:
                self.progress_data[area]['trend'] = 'declining'
            else:
                self.progress_data[area]['trend'] = 'stable'
    
    def get_progress_summary(self) -> Dict:
        """Get progress summary"""
        return {
            'areas_tracked': len(self.progress_data),
            'overall_trend': self._calculate_overall_trend(),
            'areas_improving': [area for area, data in self.progress_data.items() 
                              if data['trend'] == 'improving'],
            'areas_needing_attention': [area for area, data in self.progress_data.items() 
                                      if data['trend'] == 'declining']
        }
    
    def _calculate_overall_trend(self) -> str:
        """Calculate overall learning trend"""
        if not self.progress_data:
            return 'no_data'
        
        trends = [data['trend'] for data in self.progress_data.values()]
        improving_count = trends.count('improving')
        declining_count = trends.count('declining')
        
        if improving_count > declining_count:
            return 'improving'
        elif declining_count > improving_count:
            return 'declining'
        else:
            return 'stable'