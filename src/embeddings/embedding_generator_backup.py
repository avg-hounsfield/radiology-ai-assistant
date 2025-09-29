from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict
import uuid

class EmbeddingSystem:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Use medical-specific embeddings if available
        # Consider: "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
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
    
    def add_text_chunks(self, chunks: List[Dict]):
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            if chunk['metadata']['chunk_type'] == 'text' or chunk['metadata']['chunk_type'] == 'slide':
                texts.append(chunk['text'])
                metadatas.append(chunk['metadata'])
                ids.append(str(uuid.uuid4()))
        
        if texts:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Add to ChromaDB
            self.text_collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    def search_similar_texts(self, query: str, n_results: int = 5) -> Dict:
        query_embedding = self.embedding_model.encode([query])
        
        results = self.text_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        return results
    
    def add_medical_keywords_boost(self, chunks: List[Dict]) -> List[Dict]:
        """Boost chunks containing important medical terms"""
        medical_keywords = [
            'pathology', 'diagnosis', 'imaging', 'radiograph', 'ct scan', 'mri',
            'ultrasound', 'contrast', 'lesion', 'mass', 'nodule', 'tumor',
            'anatomy', 'physiology', 'syndrome', 'disease', 'treatment'
        ]
        
        for chunk in chunks:
            boost_score = 0
            text_lower = chunk['text'].lower()
            
            for keyword in medical_keywords:
                if keyword in text_lower:
                    boost_score += text_lower.count(keyword)
            
            chunk['metadata']['medical_relevance_score'] = boost_score
        
        return chunks
