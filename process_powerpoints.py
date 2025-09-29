#!/usr/bin/env python3
"""
Process PowerPoint files for the radiology AI assistant
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from retrieval.rag_system import RadiologyRAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('powerpoint_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def process_powerpoint_files():
    """Process PowerPoint files in the data/raw directory"""
    logger = logging.getLogger(__name__)
    
    # Find PowerPoint files
    data_dir = Path('./data/raw')
    ppt_files = []
    
    for ext in ['*.ppt', '*.pptx']:
        ppt_files.extend(data_dir.glob(ext))
    
    if not ppt_files:
        logger.info("No PowerPoint files found to process")
        return
    
    logger.info(f"Found {len(ppt_files)} PowerPoint files to process:")
    for ppt_file in ppt_files:
        logger.info(f"  - {ppt_file.name}")
    
    # Initialize RAG system
    logger.info("Initializing RadiologyRAGSystem...")
    rag_system = RadiologyRAGSystem()
    
    # Process PowerPoint files
    ppt_paths = [str(ppt_file) for ppt_file in ppt_files]
    
    try:
        logger.info("Starting PowerPoint processing...")
        result = rag_system.process_documents(ppt_paths)
        
        logger.info("=== POWERPOINT PROCESSING COMPLETE ===")
        logger.info(f"Files processed: {result.get('files_processed', 0)}")
        logger.info(f"Total chunks created: {result.get('total_chunks', 0)}")
        logger.info(f"Processing time: {result.get('processing_time', 0):.2f} seconds")
        
        if result.get('failed_files'):
            logger.warning(f"Failed files: {result['failed_files']}")
            
    except Exception as e:
        logger.error(f"Error during PowerPoint processing: {e}")
        raise

if __name__ == "__main__":
    process_powerpoint_files()