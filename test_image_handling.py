#!/usr/bin/env python3
"""
Test the enhanced image handling and tagging capabilities
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from embeddings.radbert_embedding_system import RadBERTEmbeddingSystem
from document_processor.ppt_processor import PPTProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_handling_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def test_image_handling():
    """Test image processing and tagging capabilities"""
    logger = logging.getLogger(__name__)
    
    # Find PowerPoint files
    data_dir = Path('./data/raw')
    ppt_files = list(data_dir.glob('*.pptx'))
    
    if not ppt_files:
        logger.warning("No PowerPoint files found for testing")
        return
    
    # Initialize processors
    logger.info("Initializing image handling test...")
    ppt_processor = PPTProcessor()
    embedding_system = RadBERTEmbeddingSystem()
    
    # Process one PowerPoint file to extract images
    test_file = ppt_files[0]
    logger.info(f"Testing with: {test_file.name}")
    
    # Extract content including images
    content = ppt_processor.extract_content(str(test_file))
    chunks = ppt_processor.create_chunks(content)
    
    # Analyze chunks
    text_chunks = [c for c in chunks if c.get('metadata', {}).get('chunk_type') != 'image']
    image_chunks = [c for c in chunks if c.get('metadata', {}).get('chunk_type') == 'image']
    
    logger.info(f"Found {len(text_chunks)} text chunks and {len(image_chunks)} image chunks")
    
    # Test image processing
    if image_chunks:
        logger.info("Testing image chunk processing...")
        for i, img_chunk in enumerate(image_chunks[:3]):  # Test first 3 images
            logger.info(f"Image {i+1}: {img_chunk.get('text', 'No description')}")
            logger.info(f"  Metadata: {img_chunk.get('metadata', {})}")
            
        # Process through embedding system
        embedding_system.add_text_chunks(chunks)
        
        # Test image search
        logger.info("\nTesting image search capabilities...")
        test_queries = [
            "medical image",
            "ct scan", 
            "heart diagram",
            "slide figure"
        ]
        
        for query in test_queries:
            logger.info(f"\nSearching for: '{query}'")
            results = embedding_system.search_similar_texts(query, n_results=3)
            
            if results['documents'][0]:
                for j, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    content_type = meta.get('content_type', 'text')
                    source = meta.get('source', 'unknown')
                    logger.info(f"  {j+1}. [{content_type}] {doc[:100]}... (from {source})")
            else:
                logger.info("  No results found")
    else:
        logger.warning("No image chunks found in test file")
    
    logger.info("\n=== IMAGE HANDLING TEST COMPLETE ===")

if __name__ == "__main__":
    test_image_handling()