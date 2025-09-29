# src/embeddings/radbert_embedding_system.py
"""
RadBERT-enhanced embedding system with medical specialization
"""

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict
import uuid
import logging
import torch
import random

class RadBERTEmbeddingSystem:
    def __init__(self, model_preference: str = "radiology_optimized"):
        self.logger = logging.getLogger(__name__)
        
        # RadBERT model hierarchy (best to fallback)
        self.model_options = {
            "radiology_optimized": [
                "zzxslp/RadBERT-RoBERTa-4m",  # Best: Actual RadBERT model
                "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",  # Medical
                "emilyalsentzer/Bio_ClinicalBERT",  # Clinical
                "sentence-transformers/all-MiniLM-L6-v2"  # Fallback
            ]
        }
        
        # Try to load RadBERT with fallbacks
        self.embedding_model = self._load_best_medical_model(model_preference)
        
        # Initialize ChromaDB with medical collections
        self.chroma_client = chromadb.PersistentClient(
            path="./data/embeddings",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Specialized medical collections
        self.text_collection = self._get_or_create_collection("radiology_texts_radbert")
        self.cases_collection = self._get_or_create_collection("radiology_cases")
        self.physics_collection = self._get_or_create_collection("radiology_physics")
        self.image_collection = self._get_or_create_collection("radiology_images_radbert")
    
    def _load_best_medical_model(self, preference: str):
        """Load the best available medical model"""
        models_to_try = self.model_options.get(preference, self.model_options["radiology_optimized"])
        
        for i, model_name in enumerate(models_to_try):
            try:
                self.logger.info(f"Attempting to load model {i+1}/{len(models_to_try)}: {model_name}")
                
                if "RadBERT" in model_name:
                    self.logger.info("🏥 Loading RadBERT - specialized for radiology!")
                    
                model = SentenceTransformer(model_name)
                self.logger.info(f"✅ Successfully loaded: {model_name}")
                
                # Test the model
                test_embedding = model.encode(["radiology test"], show_progress_bar=False)
                self.logger.info(f"📊 Model dimension: {len(test_embedding[0])}")
                
                return model
                
            except Exception as e:
                self.logger.warning(f"❌ Failed to load {model_name}: {e}")
                if i == len(models_to_try) - 1:
                    self.logger.error("All models failed! Using basic fallback.")
                    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                continue
    
    def _get_or_create_collection(self, name: str):
        """Create specialized medical collections"""
        return self.chroma_client.get_or_create_collection(
            name=name,
            metadata={
                "description": f"Medical collection: {name}",
                "model": str(self.embedding_model),
                "medical_optimized": True
            }
        )
    
    def add_text_chunks(self, chunks: List[Dict]):
        """Add chunks with medical categorization, optimization, and image handling"""
        # Import and initialize optimizer
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from embeddings.medical_parameter_optimizer import MedicalParameterOptimizer

            optimizer = MedicalParameterOptimizer()
            # Optimize chunks with medical parameters
            chunks = optimizer.optimize_chunk_metadata(chunks)
            self.logger.info(f"🧠 Applied medical parameter optimization to {len(chunks)} chunks")

        except ImportError as e:
            self.logger.warning(f"Medical optimizer not available: {e}")

        # Separate text and image chunks
        text_chunks = []
        image_chunks = []

        for chunk in chunks:
            if chunk.get('metadata', {}).get('chunk_type') == 'image' or 'image_data' in chunk:
                image_chunks.append(chunk)
            else:
                text_chunks.append(chunk)
        
        # Process text chunks
        general_chunks = []
        case_chunks = []  
        physics_chunks = []
        
        for chunk in text_chunks:
            category = self._categorize_medical_content(chunk)
            if category == "case":
                case_chunks.append(chunk)
            elif category == "physics":
                physics_chunks.append(chunk)
            else:
                general_chunks.append(chunk)
        
        # Add to appropriate collections
        if general_chunks:
            self._add_to_collection(general_chunks, self.text_collection)
        if case_chunks:
            self._add_to_collection(case_chunks, self.cases_collection)
        if physics_chunks:
            self._add_to_collection(physics_chunks, self.physics_collection)
        
        # Process image chunks
        if image_chunks:
            self._add_image_chunks(image_chunks)
        
        self.logger.info(f"📚 Added: {len(general_chunks)} general, {len(case_chunks)} cases, {len(physics_chunks)} physics, {len(image_chunks)} images")
    
    def _categorize_medical_content(self, chunk: Dict) -> str:
        """Categorize medical content using RadBERT understanding"""
        text = chunk.get('text', '').lower()
        
        # Physics indicators (high priority for CORE)
        physics_terms = [
            'radiation dose', 'kvp', 'mas', 'ct number', 'hounsfield', 
            'signal intensity', 'magnetic field', 'frequency', 'wavelength',
            'attenuation', 'beam hardening', 'scatter', 'collimation'
        ]
        
        if any(term in text for term in physics_terms):
            return "physics"
        
        # Case study indicators
        case_terms = [
            'patient presents', 'year old', 'clinical history', 'case study',
            'findings show', 'differential diagnosis', 'impression:', 'recommendation:'
        ]
        
        if any(term in text for term in case_terms):
            return "case"
        
        return "general"
    
    def _add_to_collection(self, chunks: List[Dict], collection):
        """Add chunks to collection with RadBERT embeddings"""
        if not chunks:
            return
        
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            if chunk.get('metadata', {}).get('chunk_type') in ['text', 'slide']:
                texts.append(chunk['text'])
                metadatas.append(chunk['metadata'])
                ids.append(str(uuid.uuid4()))
        
        if texts:
            # Generate embeddings in batches
            batch_size = 16  # Smaller batches for RadBERT
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                self.logger.info(f"🧠 Generating RadBERT embeddings for batch {i//batch_size + 1}")
                embeddings = self.embedding_model.encode(
                    batch_texts, 
                    show_progress_bar=True,
                    convert_to_numpy=True
                )
                
                collection.add(
                    embeddings=embeddings.tolist(),
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
    
    def _add_image_chunks(self, image_chunks: List[Dict]):
        """Add image chunks with appropriate tagging and metadata"""
        for chunk in image_chunks:
            try:
                # Extract image metadata and description
                description = chunk.get('text', 'Medical image')
                image_data = chunk.get('image_data', '')
                metadata = chunk.get('metadata', {})
                
                # Enhance metadata for images
                enhanced_metadata = {
                    **metadata,
                    'content_type': 'image',
                    'image_format': metadata.get('image_format', 'unknown'),
                    'has_image_data': bool(image_data),
                    'slide_number': metadata.get('slide_number', 0),
                    'source_document': metadata.get('source', 'unknown'),
                    'medical_tags': ', '.join(self._generate_medical_image_tags(description))  # Convert list to string
                }
                
                # Use description for embedding (since RadBERT is text-based)
                enhanced_description = self._enhance_image_description(description, metadata)
                
                # Generate embedding for the enhanced description
                embedding = self.embedding_model.encode([enhanced_description], show_progress_bar=False)
                
                # Add to image collection
                self.image_collection.add(
                    embeddings=embedding.tolist(),
                    documents=[enhanced_description],
                    metadatas=[enhanced_metadata],
                    ids=[str(uuid.uuid4())]
                )
                
                self.logger.info(f"🖼️  Added image: {metadata.get('slide_title', 'Untitled')} from slide {metadata.get('slide_number', '?')}")
                
            except Exception as e:
                self.logger.error(f"Failed to process image chunk: {e}")
    
    def _generate_medical_image_tags(self, description: str) -> List[str]:
        """Generate relevant medical tags for images"""
        text = description.lower()
        tags = []
        
        # Anatomy tags
        anatomy_terms = [
            'chest', 'abdomen', 'pelvis', 'head', 'brain', 'heart', 'lung', 'liver',
            'kidney', 'spine', 'bone', 'joint', 'muscle', 'vessel', 'artery', 'vein'
        ]
        
        # Imaging modality tags  
        modality_terms = [
            'ct', 'mri', 'x-ray', 'ultrasound', 'nuclear', 'pet', 'mammography',
            'fluoroscopy', 'angiography', 'radiograph'
        ]
        
        # Pathology tags
        pathology_terms = [
            'mass', 'lesion', 'tumor', 'fracture', 'inflammation', 'infection',
            'stenosis', 'occlusion', 'hemorrhage', 'edema', 'ischemia'
        ]
        
        for term in anatomy_terms + modality_terms + pathology_terms:
            if term in text:
                tags.append(term)
                
        return tags if tags else ['medical_image']
    
    def _enhance_image_description(self, description: str, metadata: dict) -> str:
        """Enhance image description with contextual information"""
        enhanced = description
        
        # Add slide context
        if metadata.get('slide_title'):
            enhanced = f"Image from slide '{metadata['slide_title']}': {enhanced}"
        
        # Add source document context
        if metadata.get('source'):
            doc_name = metadata['source'].split('/')[-1].replace('.pptx', '').replace('.ppt', '')
            enhanced = f"[{doc_name}] {enhanced}"
            
        # Add imaging context clues
        if any(term in enhanced.lower() for term in ['ct', 'mri', 'x-ray', 'ultrasound']):
            enhanced = f"Medical imaging: {enhanced}"
        elif any(term in enhanced.lower() for term in ['anatomy', 'diagram', 'chart']):
            enhanced = f"Medical diagram: {enhanced}"
        else:
            enhanced = f"Medical illustration: {enhanced}"
            
        return enhanced
    
    def search_similar_texts(self, query: str, n_results: int = 5, search_type: str = "comprehensive") -> Dict:
        """Enhanced search with medical routing"""
        
        # Determine search strategy
        collections_to_search = self._get_search_collections(query, search_type)
        
        query_embedding = self.embedding_model.encode([query])
        all_results = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        # Search across relevant collections
        for collection, weight in collections_to_search:
            try:
                results = collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=max(1, n_results // len(collections_to_search)),
                    include=['documents', 'metadatas', 'distances']
                )
                
                if results['documents'][0]:
                    # Apply collection weighting
                    weighted_distances = [d * weight for d in results['distances'][0]]
                    
                    all_results['documents'][0].extend(results['documents'][0])
                    all_results['metadatas'][0].extend(results['metadatas'][0])
                    all_results['distances'][0].extend(weighted_distances)
                    
            except Exception as e:
                self.logger.warning(f"Search error in collection: {e}")
        
        # Sort by relevance and limit results
        if all_results['documents'][0]:
            combined = list(zip(
                all_results['documents'][0],
                all_results['metadatas'][0], 
                all_results['distances'][0]
            ))
            combined.sort(key=lambda x: x[2])  # Sort by distance (lower = more similar)
            combined = combined[:n_results]
            
            all_results['documents'][0] = [x[0] for x in combined]
            all_results['metadatas'][0] = [x[1] for x in combined]
            all_results['distances'][0] = [x[2] for x in combined]
        
        return all_results
    
    def _get_search_collections(self, query: str, search_type: str) -> List[tuple]:
        """Smart collection selection based on query with image support"""
        query_lower = query.lower()
        collections = []
        
        # Image-related queries get image collection priority
        if any(term in query_lower for term in ['image', 'picture', 'figure', 'slide', 'diagram', 'scan', 'x-ray', 'ct', 'mri']):
            collections.append((self.image_collection, 0.7))  # Highest priority for images
            collections.append((self.text_collection, 1.1))
            
        # Physics queries get physics collection priority
        elif any(term in query_lower for term in ['physics', 'dose', 'kvp', 'technique', 'radiation']):
            collections.append((self.physics_collection, 0.8))  # Higher priority
            collections.append((self.text_collection, 1.2))
            collections.append((self.image_collection, 1.3))  # Include images for physics
            
        # Case-based queries get cases priority  
        elif any(term in query_lower for term in ['case', 'patient', 'diagnosis', 'findings']):
            collections.append((self.cases_collection, 0.8))
            collections.append((self.text_collection, 1.1))
            collections.append((self.image_collection, 1.2))  # Include images for cases
            
        # Comprehensive search (default)
        else:
            collections.append((self.text_collection, 1.0))
            collections.append((self.cases_collection, 1.1))
            collections.append((self.physics_collection, 1.2))
            collections.append((self.image_collection, 1.3))  # Include all collections
        
        return collections
    
    def add_medical_keywords_boost(self, chunks: List[Dict]) -> List[Dict]:
        """Enhanced medical keyword boosting with CORE focus"""
        
        core_exam_keywords = [
            # High-yield CORE terms
            'differential diagnosis', 'first-line imaging', 'contraindication',
            'radiation dose', 'contrast reaction', 'patient safety',
            'bi-rads', 'lung-rads', 'pi-rads', 'ti-rads', 'acr appropriateness',
            
            # Critical findings
            'acute', 'emergent', 'malignant', 'pathognomonic',
            'consolidation', 'ground glass', 'mass effect', 'midline shift',
            
            # Modalities
            'ct angiography', 'mr angiography', 'pet-ct', 'dual energy',
            'contrast enhanced', 'non-contrast', 'arterial phase', 'portal venous'
        ]
        
        for chunk in chunks:
            boost_score = 0
            text_lower = chunk.get('text', '').lower()
            
            # CORE keyword boosting
            for keyword in core_exam_keywords:
                if keyword in text_lower:
                    boost_score += text_lower.count(keyword) * 5  # High boost for CORE terms
            
            chunk['metadata'] = chunk.get('metadata', {})
            chunk['metadata']['radbert_relevance_score'] = boost_score
            chunk['metadata']['embedding_model'] = str(self.embedding_model)
        
        return chunks
    
    def get_model_info(self) -> Dict:
        """Get detailed model information"""
        model_str = str(self.embedding_model)
        is_radbert = "radbert" in model_str.lower()
        
        return {
            'model_name': model_str,
            'is_radbert': is_radbert,
            'is_medical_specific': any(term in model_str.lower() 
                                     for term in ['radbert', 'biobert', 'clinical', 'pubmed', 'biomedical']),
            'embedding_dimension': self.embedding_model.get_sentence_embedding_dimension(),
            'max_sequence_length': getattr(self.embedding_model, 'max_seq_length', 512),
            'device': str(getattr(self.embedding_model, 'device', 'cpu')),
            'collections': {
                'general': self.text_collection.count() if hasattr(self.text_collection, 'count') else 0,
                'cases': self.cases_collection.count() if hasattr(self.cases_collection, 'count') else 0,
                'physics': self.physics_collection.count() if hasattr(self.physics_collection, 'count') else 0
            }
        }


# src/llm/question_generator.py
"""
CORE exam practice question generator
"""

import ollama
import random
from typing import List, Dict
import json

class COREQuestionGenerator:
    def __init__(self, llm_model: str = "llama3.1:8b"):
        self.llm_model = llm_model
        self.client = ollama.Client()
        
        # CORE exam question templates by area
        self.question_templates = {
            'physics': [
                "Calculate the half-value layer for {energy} keV X-rays in {material}",
                "What is the relationship between kVp and {parameter} in {modality}?",
                "A patient receives {dose} mGy during a {procedure}. What is the effective dose?",
                "Explain the physics principle behind {technique} in {modality}"
            ],
            
            'chest': [
                "A {age}-year-old {gender} presents with {symptoms}. Chest X-ray shows {findings}. What is the most likely diagnosis?",
                "What are the key CT findings that distinguish {condition1} from {condition2}?",
                "A patient with {clinical_context} has bilateral {pattern} on chest CT. List the differential diagnosis.",
                "What is the first-line imaging for suspected {condition} in {patient_type}?"
            ],
            
            'cardiac': [
                "What are the MRI sequences used to evaluate {cardiac_condition}?",
                "A patient has chest pain and troponin elevation. The ECG shows {findings}. What imaging is indicated?",
                "Describe the CT coronary angiography findings in {condition}",
                "What are the contraindications to cardiac MRI with gadolinium?"
            ],
            
            'neuro': [
                "A patient presents with acute {neurological_symptom}. What is the first-line imaging?",
                "What are the MRI findings in acute {condition} within {timeframe}?",
                "Differentiate between {condition1} and {condition2} on {modality}",
                "What sequences are essential for evaluating suspected {pathology}?"
            ]
        }
        
        # Question difficulty levels
        self.difficulty_modifiers = {
            'easy': "This is a straightforward question testing basic knowledge",
            'intermediate': "This question requires clinical correlation and differential thinking", 
            'hard': "This is a complex scenario requiring advanced interpretation and management decisions"
        }
    
    def generate_practice_question(self, core_area: str = None, difficulty: str = "intermediate") -> Dict:
        """Generate a CORE exam style practice question"""
        
        if not core_area:
            core_area = random.choice(['physics', 'chest', 'cardiac', 'neuro', 'gi', 'gu', 'msk'])
        
        system_prompt = f"""You are a radiology attending physician creating CORE exam questions.

Create a realistic, high-yield question for the {core_area} section at {difficulty} level.

Requirements:
- Use realistic clinical scenarios
- Include appropriate medical terminology  
- Test both knowledge and clinical reasoning
- Provide 4 multiple choice options (A-D)
- Include a detailed explanation with teaching points
- Focus on high-yield CORE exam topics

Format:
**Question:** [Clinical scenario and question]

**Options:**
A) [Option A]  
B) [Option B]
C) [Option C]
D) [Option D]

**Correct Answer:** [Letter] - [Brief explanation]

**Teaching Points:**
• [Key point 1]
• [Key point 2] 
• [Key point 3]

**CORE Relevance:** [Why this is important for CORE exam]
"""

        # Generate specific prompt based on area
        if core_area in self.question_templates:
            template = random.choice(self.question_templates[core_area])
            user_prompt = f"Create a {difficulty} level question for {core_area}. Use this as inspiration: {template}"
        else:
            user_prompt = f"Create a {difficulty} level radiology question about {core_area} suitable for CORE exam preparation."
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.7,  # Higher for creativity
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            )
            
            return {
                "question": response['message']['content'],
                "core_area": core_area,
                "difficulty": difficulty,
                "success": True,
                "type": "practice_question"
            }
            
        except Exception as e:
            return {
                "question": f"Error generating question: {str(e)}",
                "core_area": core_area, 
                "difficulty": difficulty,
                "success": False,
                "error": str(e)
            }
    
    def generate_case_based_question(self, modality: str = None) -> Dict:
        """Generate a case-based question with imaging findings"""
        
        modalities = ['CT', 'MRI', 'X-ray', 'Ultrasound', 'Nuclear Medicine'] if not modality else [modality]
        chosen_modality = random.choice(modalities)
        
        system_prompt = f"""You are creating a case-based radiology question for CORE exam preparation.

Create a realistic clinical case with {chosen_modality} findings.

Requirements:
- Start with patient demographics and presentation
- Describe relevant imaging findings systematically
- Ask for differential diagnosis or next step
- Provide detailed answer with reasoning
- Include teaching points about the condition
- Focus on CORE-relevant pathology

Format:
**Clinical Case:**
[Age, gender, presentation, relevant history]

**{chosen_modality} Findings:**
[Systematic description of imaging findings]

**Question:** What is the most likely diagnosis?

**Answer:** [Diagnosis with supporting evidence]

**Key Teaching Points:**
• [Teaching point 1]
• [Teaching point 2]
• [Teaching point 3]

**Differential Considerations:** [Brief list of alternatives]
"""
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a case-based question using {chosen_modality}"}
                ],
                options={
                    "temperature": 0.6,
                    "top_p": 0.9, 
                    "num_predict": 1200
                }
            )
            
            return {
                "question": response['message']['content'],
                "modality": chosen_modality,
                "success": True,
                "type": "case_based"
            }
            
        except Exception as e:
            return {
                "question": f"Error generating case: {str(e)}",
                "modality": chosen_modality,
                "success": False,
                "error": str(e)
            }
    
    def generate_physics_calculation(self) -> Dict:
        """Generate a physics calculation question"""
        
        system_prompt = """You are creating a physics calculation question for the CORE exam.

Requirements:
- Include specific numerical values
- Test understanding of physics principles
- Show step-by-step calculation
- Relate to clinical imaging
- Focus on radiation safety, dose, or image quality

Format:
**Physics Problem:**
[Problem statement with given values]

**Calculate:** [What needs to be calculated]

**Solution:**
Step 1: [First step with explanation]
Step 2: [Second step]  
Step 3: [Final calculation]

**Answer:** [Numerical result with units]

**Clinical Relevance:** [Why this matters in practice]
"""
        
        try:
            response = self.client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Create a physics calculation problem suitable for CORE exam"}
                ],
                options={
                    "temperature": 0.3,  # Lower for precise calculations
                    "num_predict": 800
                }
            )
            
            return {
                "question": response['message']['content'],
                "success": True,
                "type": "physics_calculation"
            }
            
        except Exception as e:
            return {
                "question": f"Error generating physics problem: {str(e)}",
                "success": False,
                "error": str(e)
            }