from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Optional
import uuid
import logging

class EmbeddingSystem:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding system with medical-aware features"""
        self.logger = logging.getLogger(__name__)
        
        # Use medical-specific embeddings if available
        self.embedding_model = SentenceTransformer(model_name)
        self.logger.info(f"Initialized embedding model: {model_name}")
        
        # Initialize ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient(
                path="./data/embeddings",
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create collections
            self.text_collection = self.chroma_client.get_or_create_collection(
                name="radiology_texts",
                metadata={"description": "Radiology text content"}
            )
            
            self.image_collection = self.chroma_client.get_or_create_collection(
                name="radiology_images", 
                metadata={"description": "Radiology images and descriptions"}
            )
            
            self.logger.info("ChromaDB collections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def add_text_chunks(self, chunks: List[Dict]):
        """Add text chunks to the embedding database"""
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            chunk_type = chunk['metadata'].get('chunk_type', 'text')
            if chunk_type in ['text', 'slide', 'paragraph']:
                texts.append(chunk['text'])
                metadatas.append(chunk['metadata'])
                ids.append(str(uuid.uuid4()))
        
        if texts:
            try:
                # Generate embeddings
                embeddings = self.embedding_model.encode(texts)
                
                # Add to ChromaDB
                self.text_collection.add(
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                self.logger.info(f"Added {len(texts)} text chunks to database")
                
            except Exception as e:
                self.logger.error(f"Failed to add text chunks: {e}")
                raise
    
    def search_similar_texts(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar texts using embedding similarity"""
        try:
            query_embedding = self.embedding_model.encode([query])
            
            results = self.text_collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            self.logger.info(f"Found {len(results['documents'][0])} similar texts for query")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    
    def add_medical_keywords_boost(self, chunks: List[Dict]) -> List[Dict]:
        """Boost chunks containing important medical terms"""
        medical_keywords = [
            'pathology', 'diagnosis', 'imaging', 'radiograph', 'ct scan', 'mri',
            'ultrasound', 'contrast', 'lesion', 'mass', 'nodule', 'tumor',
            'anatomy', 'physiology', 'syndrome', 'disease', 'treatment',
            'pneumonia', 'fracture', 'hemorrhage', 'stroke', 'cancer',
            'birads', 'consolidation', 'atelectasis', 'pneumothorax'
        ]
        
        for chunk in chunks:
            boost_score = 0
            text_lower = chunk['text'].lower()
            
            for keyword in medical_keywords:
                if keyword in text_lower:
                    boost_score += text_lower.count(keyword)
            
            chunk['metadata']['medical_relevance_score'] = boost_score
        
        return chunks

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collections"""
        try:
            text_count = self.text_collection.count()
            image_count = self.image_collection.count()
            
            return {
                'text_chunks': text_count,
                'image_chunks': image_count,
                'total_chunks': text_count + image_count
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {'text_chunks': 0, 'image_chunks': 0, 'total_chunks': 0}