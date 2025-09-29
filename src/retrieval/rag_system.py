# src/retrieval/rag_system.py
"""
Clean RAG system without circular import issues
"""

from typing import List, Dict, Optional
import logging
import os
import re

class RadiologyRAGSystem:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", 
                 llm_model: str = "llama3.1:8b"):
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components lazily to avoid circular imports
        self.embedding_system = None
        self.llm_manager = None
        self.question_generator = None  # Add question generator
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
            
            # Try RadBERT system first
            try:
                from embeddings.radbert_embedding_system import RadBERTEmbeddingSystem
                self.embedding_system = RadBERTEmbeddingSystem(self.embedding_model_name)
                self.logger.info("✅ RadBERT embedding system initialized")
                return self.embedding_system
            except ImportError:
                # Fallback to regular system
                from embeddings.embedding_generator import EmbeddingSystem
                self.embedding_system = EmbeddingSystem(self.embedding_model_name)
                self.logger.info("✅ Regular embedding system initialized")
                return self.embedding_system
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import EmbeddingSystem: {e}")
            self.embedding_system = "unavailable"
            return None
    
    def _init_question_generator(self):
        """Lazy initialization of question generator"""
        if self.question_generator is not None:
            return self.question_generator
            
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from llm.question_generator import COREQuestionGenerator
            self.question_generator = COREQuestionGenerator(self.llm_model_name)
            self.logger.info("✅ Question generator initialized")
            return self.question_generator
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import COREQuestionGenerator: {e}")
            self.question_generator = "unavailable"
            return None
        except Exception as e:
            self.logger.error(f"❌ Question generator initialization failed: {e}")
            self.question_generator = "failed"
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
            
            from llm.medical_llm import MedicalLLMManager
            self.llm_manager = MedicalLLMManager(self.llm_model_name)
            self.logger.info("✅ LLM manager initialized")
            return self.llm_manager
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import MedicalLLMManager: {e}")
            # Try fallback LLM
            try:
                from llm.fallback_llm import FallbackLLMManager
                self.llm_manager = FallbackLLMManager()
                self.logger.info("✅ Using fallback LLM for cloud deployment")
                return self.llm_manager
            except Exception as fallback_error:
                self.logger.error(f"❌ Fallback LLM also failed: {fallback_error}")
                self.llm_manager = "unavailable"
                return None
        except Exception as e:
            self.logger.error(f"❌ LLM manager initialization failed: {e}")
            # Try fallback LLM
            try:
                from llm.fallback_llm import FallbackLLMManager
                self.llm_manager = FallbackLLMManager()
                self.logger.info("✅ Using fallback LLM due to main LLM failure")
                return self.llm_manager
            except Exception as fallback_error:
                self.logger.error(f"❌ Fallback LLM also failed: {fallback_error}")
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
            from document_processor.transcript_processor import LectureTranscriptProcessor
            
        except ImportError as e:
            error_msg = f"Document processors not available: {e}"
            self.logger.error(f"❌ {error_msg}")
            return {"error": error_msg, "processed": 0, "success": False}
        
        # Process documents
        pdf_processor = PDFProcessor()
        ppt_processor = PPTProcessor()
        transcript_processor = LectureTranscriptProcessor()
        
        all_chunks = []
        processed_count = 0
        errors = []
        transcript_count = 0
        
        for doc_path in document_paths:
            self.logger.info(f"Processing: {os.path.basename(doc_path)}")
            
            try:
                if doc_path.lower().endswith('.pdf'):
                    content = pdf_processor.extract_text_and_metadata(doc_path)
                    chunks = pdf_processor.semantic_chunking(content['text'], content['metadata'])
                    
                elif doc_path.lower().endswith(('.ppt', '.pptx')):
                    content = ppt_processor.extract_content(doc_path)
                    chunks = ppt_processor.create_chunks(content)
                    
                elif doc_path.lower().endswith('.txt'):
                    # Check if it's a lecture transcript
                    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                        sample = f.read(1000)
                    
                    # Heuristic: if it has timestamps or speaker patterns, treat as transcript
                    if (re.search(r'\d{1,2}:\d{2}', sample) or 
                        re.search(r'^[A-Z][a-z]+\s*:', sample, re.MULTILINE) or
                        'transcript' in os.path.basename(doc_path).lower()):
                        
                        self.logger.info(f"📺 Processing as lecture transcript")
                        transcript_data = transcript_processor.process_transcript(doc_path)
                        chunks = transcript_processor.create_chunks(transcript_data)
                        transcript_count += 1
                        
                        # Add transcript stats to metadata
                        stats = transcript_data.get('processing_stats', {})
                        self.logger.info(f"📊 Transcript stats: {stats.get('total_segments', 0)} segments, "
                                       f"estimated {stats.get('estimated_duration', 'unknown')} duration")
                    else:
                        # Regular text file
                        self.logger.info(f"📄 Processing as regular text file")
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        chunks = [{
                            'text': content,
                            'metadata': {
                                'source': doc_path,
                                'chunk_type': 'text_file',
                                'file_type': 'plain_text'
                            }
                        }]
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
            "transcript_count": transcript_count,
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
            # Step 1: Retrieve relevant chunks from documents
            search_results = embedding_system.search_similar_texts(question, n_results)

            # Step 2: Search relevant flashcards
            flashcard_results = self._search_flashcards(question, n_results=3)

            # Step 3: Search relevant images
            image_results = self._search_images(question, n_results=2)

            # Step 4: Prepare context chunks
            context_chunks = []

            # Add document results
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
                        'distance': distances[i] if i < len(distances) else 0,
                        'source_type': 'document'
                    })

            # Add flashcard results
            if flashcard_results:
                for card in flashcard_results:
                    context_chunks.append({
                        'text': f"Q: {card['front']}\nA: {card['back']}",
                        'metadata': {
                            'source': f"Flashcard: {card['deck_name']}",
                            'card_id': card['card_id'],
                            'tags': card.get('tags', [])
                        },
                        'distance': 0,  # Flashcards are always relevant if found
                        'source_type': 'flashcard'
                    })

            # Add image results
            if image_results:
                for image in image_results:
                    image_description = f"Medical Image: {image.get('modality', 'Unknown')} of {image.get('body_part', 'Unknown')}"
                    if image.get('extracted_text'):
                        image_description += f"\nContext: {image['extracted_text']}"

                    context_chunks.append({
                        'text': image_description,
                        'metadata': {
                            'source': f"Image: {image.get('file_path', '')}",
                            'image_id': image.get('image_id'),
                            'modality': image.get('modality', ''),
                            'body_part': image.get('body_part', ''),
                            'tags': image.get('tags', [])
                        },
                        'distance': 0,  # Images are always relevant if found
                        'source_type': 'image'
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
            
            # Step 4: Add retrieval info and sources
            if 'retrieval_info' not in response:
                response['retrieval_info'] = {}

            response['retrieval_info'].update({
                'chunks_retrieved': len(context_chunks),
                'search_query': question,
                'avg_distance': sum(chunk['distance'] for chunk in context_chunks) / len(context_chunks) if context_chunks else 0
            })

            # Step 5: Build sources list including flashcards and images
            sources = []
            for chunk in context_chunks:
                if chunk.get('source_type') == 'flashcard':
                    sources.append({
                        'type': 'flashcard',
                        'title': f"Flashcard: {chunk['metadata'].get('source', 'Unknown')}",
                        'card_id': chunk['metadata'].get('card_id'),
                        'deck_name': chunk['metadata'].get('source', '').replace('Flashcard: ', ''),
                        'content': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                        'tags': chunk['metadata'].get('tags', [])
                    })
                elif chunk.get('source_type') == 'image':
                    sources.append({
                        'type': 'image',
                        'title': f"Image: {chunk['metadata'].get('modality', 'Medical')} - {chunk['metadata'].get('body_part', 'Unknown')}",
                        'image_id': chunk['metadata'].get('image_id'),
                        'file_path': chunk['metadata'].get('source', '').replace('Image: ', ''),
                        'modality': chunk['metadata'].get('modality', ''),
                        'body_part': chunk['metadata'].get('body_part', ''),
                        'tags': chunk['metadata'].get('tags', [])
                    })
                else:
                    # Regular document source
                    sources.append({
                        'type': 'document',
                        'filename': chunk['metadata'].get('filename', 'Document'),
                        'section': chunk['metadata'].get('section', ''),
                        'medical_relevance': chunk['metadata'].get('medical_relevance', 3)
                    })

            response['sources'] = sources
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
    
    def generate_practice_question(self, core_area: str = None, difficulty: str = "intermediate") -> Dict:
        """Generate CORE exam practice questions"""
        question_generator = self._init_question_generator()
        
        if question_generator is None:
            return {
                "question": "❌ Question generator not available. Please check setup.",
                "success": False,
                "error": "Question generator unavailable"
            }
        
        try:
            return question_generator.generate_practice_question(core_area, difficulty)
        except Exception as e:
            return {
                "question": f"❌ Error generating question: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def generate_case_question(self, modality: str = None) -> Dict:
        """Generate case-based questions"""
        question_generator = self._init_question_generator()
        
        if question_generator is None:
            return {
                "question": "❌ Question generator not available.",
                "success": False
            }
        
        try:
            return question_generator.generate_case_based_question(modality)
        except Exception as e:
            return {
                "question": f"❌ Error generating case: {str(e)}",
                "success": False,
                "error": str(e)
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

    def _search_flashcards(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant flashcards based on query"""
        try:
            # Import flashcard system
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from study.flashcard_system import FlashcardManager
            flashcard_manager = FlashcardManager()

            # Simple keyword-based search in flashcard content
            relevant_cards = []
            query_words = query.lower().split()

            for card_id, card in flashcard_manager.cards.items():
                # Search in front, back, and tags
                searchable_text = f"{card.front} {card.back} {' '.join(card.tags)}".lower()

                # Check if any query words are in the card content
                relevance_score = 0
                for word in query_words:
                    if word in searchable_text:
                        relevance_score += 1

                # Include cards with at least some relevance
                if relevance_score > 0:
                    relevant_cards.append({
                        'card_id': card.card_id,
                        'deck_name': card.deck_name,
                        'front': card.front,
                        'back': card.back,
                        'tags': card.tags,
                        'relevance_score': relevance_score
                    })

            # Sort by relevance and return top results
            relevant_cards.sort(key=lambda x: x['relevance_score'], reverse=True)
            return relevant_cards[:n_results]

        except Exception as e:
            self.logger.warning(f"Error searching flashcards: {e}")
            return []

    def _search_images(self, query: str, n_results: int = 2) -> List[Dict]:
        """Search for relevant images based on query"""
        try:
            # Import image processor
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from multimedia.image_processor import RadiologyImageManager
            image_manager = RadiologyImageManager()

            # Use the image manager's search functionality
            results = image_manager.search_images(query, limit=n_results)

            # Convert to list format
            image_results = []
            for result in results:
                image_results.append({
                    'image_id': result.image_id,
                    'file_path': result.file_path,
                    'modality': result.modality,
                    'body_part': result.body_part,
                    'tags': result.tags,
                    'extracted_text': result.extracted_text,
                    'similarity': result.metadata.get('similarity_score', 0.0)
                })

            return image_results

        except Exception as e:
            self.logger.warning(f"Error searching images: {e}")
            return []