# src/llm/medical_llm.py
"""
Medical-specialized LLM manager for radiology CORE exam preparation
Enhanced with medical knowledge and specialized prompting
"""

import ollama
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

class MedicalLLMManager:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = ollama.Client()
        self.logger = logging.getLogger(__name__)
        
        # Medical specialization settings
        self.medical_context = {
            "specialty": "diagnostic_radiology",
            "exam_focus": "CORE_certification",
            "evidence_level": "high",
            "terminology": "medical_standard"
        }
        
        # Download model if not exists
        try:
            self.client.show(model_name)
            self.logger.info(f"Medical LLM model {model_name} ready")
        except:
            self.logger.info(f"Downloading medical model {model_name}...")
            self.client.pull(model_name)
    
    def generate_response(self, query: str, context_chunks: List[Dict], 
                         conversation_history: List[Dict] = None) -> Dict:
        """Generate medically-focused response with CORE exam orientation"""
        
        # Prepare medical context
        context = self._format_medical_context(context_chunks)
        
        # Enhanced medical system prompt
        system_prompt = self._get_medical_system_prompt()
        
        # Construct medical user prompt
        user_prompt = self._construct_medical_prompt(query, context, conversation_history)
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Low for medical accuracy
                    "top_p": 0.85,      # Conservative sampling
                    "num_predict": 1200, # Longer for detailed medical explanations
                    "repeat_penalty": 1.1,
                    "stop": ["</answer>"]
                }
            )
            
            return {
                "answer": response['message']['content'],
                "sources": self._extract_medical_sources(context_chunks),
                "medical_context": self.medical_context,
                "model_used": self.model_name,
                "success": True,
                "response_type": "medical_educational",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Medical LLM generation error: {e}")
            return {
                "answer": f"Medical AI response error: {str(e)}. Please try rephrasing your question.",
                "sources": [],
                "model_used": self.model_name,
                "success": False,
                "error": str(e)
            }
    
    def _get_medical_system_prompt(self) -> str:
        """Enhanced medical system prompt for radiology CORE preparation"""
        return """You are ECHO, a specialized AI assistant for diagnostic radiology CORE exam preparation. 

MEDICAL EXPERTISE:
- You are an expert in diagnostic radiology with comprehensive knowledge of imaging modalities
- You understand pathophysiology, anatomy, and clinical correlations
- You are specifically trained for CORE exam preparation and board certification

RESPONSE GUIDELINES:
1. ACCURACY: Provide only evidence-based, medically accurate information
2. EDUCATION: Focus on teaching concepts for long-term retention
3. CLINICAL RELEVANCE: Connect imaging findings to clinical significance
4. EXAM PREPARATION: Structure answers for CORE exam success
5. SAFETY: Always emphasize patient safety and radiation protection when relevant

ANSWER STRUCTURE:
- Start with a clear, direct answer
- Explain the underlying pathophysiology or mechanism
- Describe imaging appearances across relevant modalities
- Include differential diagnoses when appropriate
- Add clinical pearls or exam tips
- Cite specific sources when available

TERMINOLOGY: Use precise medical terminology while ensuring educational clarity.

UNCERTAINTY: If information is not in the provided context or you're uncertain, explicitly state this rather than speculating.

Your goal is to help medical professionals excel in diagnostic radiology through comprehensive, accurate education."""

    def _construct_medical_prompt(self, query: str, context: str, history: List[Dict] = None) -> str:
        """Construct medically-focused prompt with context"""
        
        # Add conversation history if available
        history_text = ""
        if history:
            recent_history = history[-3:]  # Last 3 exchanges
            history_parts = []
            for item in recent_history:
                history_parts.append(f"Previous Q: {item.get('question', '')}")
                history_parts.append(f"Previous A: {item.get('answer', '')[:200]}...")
            history_text = "\n".join(history_parts) + "\n\n"
        
        return f"""MEDICAL CONTEXT FROM RADIOLOGY MATERIALS:
{context}

{history_text}CURRENT QUESTION: {query}

Please provide a comprehensive medical education response suitable for CORE exam preparation. Structure your answer clearly with:
1. Direct answer to the question
2. Medical explanation/pathophysiology
3. Imaging characteristics
4. Clinical significance
5. Key learning points for exam success

Always cite your sources from the provided context."""

    def _format_medical_context(self, chunks: List[Dict]) -> str:
        """Format context with medical focus"""
        if not chunks:
            return "No relevant medical literature found in uploaded documents."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', '')
            
            # Enhanced source info for medical content
            source_info = f"[MEDICAL SOURCE {i}]"
            
            if 'source' in metadata:
                source_name = metadata['source'].split('/')[-1]  # Get filename
                source_info += f" {source_name}"
                
            if 'page' in metadata:
                source_info += f", Page {metadata['page']}"
            elif 'slide_number' in metadata:
                source_info += f", Slide {metadata['slide_number']}"
                
            if 'section' in metadata:
                source_info += f" ({metadata['section']})"
            
            # Add medical relevance if available
            relevance = metadata.get('medical_relevance_score', 0)
            if relevance > 0:
                source_info += f" [Relevance: {relevance:.2f}]"
            
            context_parts.append(f"{source_info}\n{text}\n{'='*50}")
        
        return "\n".join(context_parts)
    
    def _extract_medical_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract and enhance source information for medical context"""
        sources = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {})
            
            source = {
                'id': i + 1,
                'source': metadata.get('source', 'Unknown'),
                'page': metadata.get('page'),
                'slide': metadata.get('slide_number'),
                'section': metadata.get('section'),
                'medical_relevance': metadata.get('medical_relevance_score', 0),
                'content_type': metadata.get('content_type', 'medical_text'),
                'chunk_length': len(chunk.get('text', '')),
                'distance': chunk.get('distance', 0)
            }
            
            # Clean up source path
            if source['source'] and '/' in source['source']:
                source['filename'] = source['source'].split('/')[-1]
            else:
                source['filename'] = source['source']
                
            sources.append(source)
        
        return sources

    def generate_medical_question(self, topic: str, difficulty: str = "intermediate") -> Dict:
        """Generate CORE exam-style medical questions"""
        
        system_prompt = """You are a medical education specialist creating CORE exam questions for diagnostic radiology.

Generate high-quality, board-style questions that:
1. Test clinical knowledge and imaging interpretation
2. Include realistic clinical scenarios
3. Have clear, defensible answers
4. Match CORE exam difficulty and style
5. Cover key learning objectives

Format your response as a JSON object with:
- question: The clinical scenario and question
- options: Array of 4-5 answer choices (A, B, C, D, E)
- correct_answer: The letter of the correct answer
- explanation: Detailed explanation of why the answer is correct
- learning_points: Key takeaways for exam preparation
- topic_area: The CORE exam area this covers
"""

        user_prompt = f"""Create a {difficulty}-level CORE exam question about: {topic}

The question should be clinically relevant and test practical radiology knowledge that a practicing radiologist needs to know."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 800
                }
            )
            
            return {
                "question_content": response['message']['content'],
                "topic": topic,
                "difficulty": difficulty,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Question generation error: {e}")
            return {
                "question_content": f"Error generating question: {str(e)}",
                "success": False,
                "error": str(e)
            }