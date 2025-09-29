# src/retrieval/rag_system.py
"""
Clean RAG system without circular import issues
"""

from typing import List, Dict, Optional
import logging
import os

class RadiologyRAGSystem:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", 
                 llm_model: str = "llama3.1:8b"):
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components lazily to avoid circular imports
        self.embedding_system = None
        self.llm_manager = None
        self.embedding_model_name = embedding_model
        self.llm_model_name = llm_model
        
        self.logger.info(f"RadiologyRAGSystem initialized with models: {embedding_model}, {llm_model}")
    
    def _init_embedding_system(self):
        """Lazy initialization of embedding system"""
        if self.embedding_system is not None:
            return self.embedding_system
            
        try:
            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from embeddings.embedding_generator import EmbeddingSystem
            self.embedding_system = EmbeddingSystem(self.embedding_model_name)
            self.logger.info("✅ Embedding system initialized")
            return self.embedding_system
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import EmbeddingSystem: {e}")
            self.embedding_system = "unavailable"
            return None
        except Exception as e:
            self.logger.error(f"❌ Embedding system initialization failed: {e}")
            self.embedding_system = "failed"
            return None
    
    def _init_llm_manager(self):
        """Lazy initialization of LLM manager"""
        if self.llm_manager is not None:
            return self.llm_manager
            
        try:
            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from llm.local_llm import LocalLLMManager
            self.llm_manager = LocalLLMManager(self.llm_model_name)
            self.logger.info("✅ LLM manager initialized")
            return self.llm_manager
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import LocalLLMManager: {e}")
            self.llm_manager = "unavailable"
            return None
        except Exception as e:
            self.logger.error(f"❌ LLM manager initialization failed: {e}")
            self.llm_manager = "failed"
            return None
    
    def process_documents(self, document_paths: List[str]) -> Dict:
        """Process and index all documents"""
        
        # Initialize embedding system
        embedding_system = self._init_embedding_system()
        if embedding_system is None:
            error_msg = "Cannot process documents: embedding system not available"
            self.logger.error(f"❌ {error_msg}")
            return {"error": error_msg, "processed": 0, "success": False}
        
        # Import document processors here to avoid circular imports
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from document_processor.pdf_processor import PDFProcessor
            from document_processor.ppt_processor import PPTProcessor
            
        except ImportError as e:
            error_msg = f"Document processors not available: {e}"
            self.logger.error(f"❌ {error_msg}")
            return {"error": error_msg, "processed": 0, "success": False}
        
        # Process documents
        pdf_processor = PDFProcessor()
        ppt_processor = PPTProcessor()
        
        all_chunks = []
        processed_count = 0
        errors = []
        
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
                
                # Add medical keyword boosting
                chunks = self._add_medical_boost(chunks)
                all_chunks.extend(chunks)
                processed_count += 1
                
            except Exception as e:
                error_msg = f"Error processing {os.path.basename(doc_path)}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # Add to vector store
        if all_chunks:
            try:
                embedding_system.add_text_chunks(all_chunks)
                self.logger.info(f"✅ Processed {len(all_chunks)} chunks from {processed_count} documents")
            except Exception as e:
                error_msg = f"Vector store error: {e}"
                self.logger.error(f"❌ {error_msg}")
                return {"error": error_msg, "processed": processed_count, "success": False}
        
        return {
            "processed": processed_count,
            "total_chunks": len(all_chunks),
            "errors": errors,
            "success": True
        }
    
    def _add_medical_boost(self, chunks: List[Dict]) -> List[Dict]:
        """Add medical keyword boosting to chunks"""
        medical_keywords = [
            'radiology', 'imaging', 'ct', 'mri', 'x-ray', 'ultrasound', 'pet', 'spect',
            'diagnosis', 'findings', 'pathology', 'clinical', 'patient', 'case',
            'contrast', 'enhancement', 'lesion', 'mass', 'nodule', 'tumor',
            'pneumonia', 'fracture', 'hemorrhage', 'stroke', 'cancer', 'benign',
            'malignant', 'acute', 'chronic', 'bilateral', 'unilateral',
            'dose', 'radiation', 'safety', 'protocol', 'technique', 'quality'
        ]
        
        for chunk in chunks:
            boost_score = 0
            text_lower = chunk.get('text', '').lower()
            
            for keyword in medical_keywords:
                if keyword in text_lower:
                    boost_score += text_lower.count(keyword)
            
            if 'metadata' not in chunk:
                chunk['metadata'] = {}
            chunk['metadata']['medical_relevance_score'] = boost_score
        
        return chunks
    
    def query(self, question: str, n_results: int = 5, 
              conversation_history: List[Dict] = None) -> Dict:
        """Main query interface"""
        
        # Initialize systems
        embedding_system = self._init_embedding_system()
        llm_manager = self._init_llm_manager()
        
        if embedding_system is None:
            return {
                "answer": "❌ Embedding system not available. Please check the setup.",
                "sources": [],
                "success": False,
                "error": "Missing embedding system"
            }
            
        if llm_manager is None:
            return {
                "answer": "❌ LLM manager not available. Please check Ollama installation and model.",
                "sources": [],
                "success": False,
                "error": "Missing LLM manager"
            }
        
        try:
            # Step 1: Retrieve relevant chunks
            search_results = embedding_system.search_similar_texts(question, n_results)
            
            # Step 2: Prepare context chunks
            context_chunks = []
            if (search_results and 
                search_results.get('documents') and 
                search_results['documents'] and
                search_results['documents'][0]):
                
                docs = search_results['documents'][0]
                metadatas = search_results.get('metadatas', [[{}] * len(docs)])[0]
                distances = search_results.get('distances', [[0] * len(docs)])[0]
                
                for i in range(len(docs)):
                    context_chunks.append({
                        'text': docs[i],
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'distance': distances[i] if i < len(distances) else 0
                    })
            
            # Step 3: Generate response
            if not context_chunks:
                return {
                    "answer": "I couldn't find relevant information in your documents for this question. Try uploading more materials or rephrasing your question.",
                    "sources": [],
                    "success": True,
                    "retrieval_info": {
                        "chunks_retrieved": 0,
                        "search_query": question
                    }
                }
            
            response = llm_manager.generate_response(
                query=question,
                context_chunks=context_chunks,
                conversation_history=conversation_history or []
            )
            
            # Step 4: Add retrieval info
            if 'retrieval_info' not in response:
                response['retrieval_info'] = {}
                
            response['retrieval_info'].update({
                'chunks_retrieved': len(context_chunks),
                'search_query': question,
                'avg_distance': sum(chunk['distance'] for chunk in context_chunks) / len(context_chunks) if context_chunks else 0
            })
            
            return response
            
        except Exception as e:
            error_msg = f"Query processing error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {
                "answer": f"❌ Error processing your question: {str(e)}",
                "sources": [],
                "success": False,
                "error": error_msg
            }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        
        # Check embedding system
        embedding_status = "not_initialized"
        if self.embedding_system == "unavailable":
            embedding_status = "unavailable"
        elif self.embedding_system == "failed":
            embedding_status = "failed"
        elif self.embedding_system is not None:
            embedding_status = "ready"
        
        # Check LLM manager
        llm_status = "not_initialized"
        if self.llm_manager == "unavailable":
            llm_status = "unavailable"
        elif self.llm_manager == "failed":
            llm_status = "failed"
        elif self.llm_manager is not None:
            llm_status = "ready"
        
        return {
            'class_loaded': True,
            'embedding_system': embedding_status,
            'llm_manager': llm_status,
            'ready_for_documents': embedding_status in ["ready", "not_initialized"],
            'ready_for_queries': embedding_status in ["ready"] and llm_status in ["ready"],
            'models': {
                'embedding_model': self.embedding_model_name,
                'llm_model': self.llm_model_name
            }
        }