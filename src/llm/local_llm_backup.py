import ollama
from typing import List, Dict, Optional
import json

class LocalLLMManager:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = ollama.Client()
        
        # Download model if not exists
        try:
            self.client.show(model_name)
        except:
            print(f"Downloading {model_name}...")
            self.client.pull(model_name)
    
    def generate_response(self, query: str, context_chunks: List[Dict], 
                         conversation_history: List[Dict] = None) -> Dict:
        
        # Prepare context
        context = self._format_context(context_chunks)
        
        # Create medical-focused prompt
        system_prompt = """You are a specialized AI assistant helping medical professionals study diagnostic radiology for the CORE exam. 

Key guidelines:
- Provide accurate, evidence-based medical information
- Always cite your sources from the provided context
- If you're uncertain, say so explicitly
- Focus on educational value for radiology training
- Use appropriate medical terminology
- Structure answers clearly with key points
- When discussing imaging findings, be specific about modalities and techniques

Always end your response with source citations in the format: [Source: filename, page/slide number]"""

        user_prompt = f"""Based on the following context from radiology materials:

{context}

Question: {query}

Please provide a comprehensive answer suitable for CORE exam preparation."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Lower for medical accuracy
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            )
            
            return {
                "answer": response['message']['content'],
                "sources": self._extract_sources(context_chunks),
                "model_used": self.model_name,
                "success": True
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "model_used": self.model_name,
                "success": False
            }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            source_info = f"Source {i}: {metadata.get('source', 'Unknown')}"
            
            if 'page' in metadata:
                source_info += f", Page {metadata['page']}"
            elif 'slide_number' in metadata:
                source_info += f", Slide {metadata['slide_number']}"
            
            context_parts.append(f"{source_info}\n{chunk['text']}\n---")
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        sources = []
        for chunk in chunks:
            metadata = chunk['metadata']
            sources.append({
                'source': metadata.get('source', 'Unknown'),
                'page': metadata.get('page'),
                'slide': metadata.get('slide_number'),
                'section': metadata.get('section'),
                'relevance_score': metadata.get('medical_relevance_score', 0)
            })
        return sources
