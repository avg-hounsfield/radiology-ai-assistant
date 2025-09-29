#!/usr/bin/env python3
"""
Selective ingestion of high-priority radiology materials
Start with the most important directories first
"""

import os
import sys
from pathlib import Path
import logging
from typing import List
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from retrieval.rag_system import RadiologyRAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selective_ingest.log'),
        logging.StreamHandler()
    ]
)

# Priority directories (most important first)
PRIORITY_DIRS = [
    "Board Prep",           # Board exam materials first
    "Physics",              # Physics - important for CORE
    "Study Material 2016",  # Structured study materials
    "AIRP Handouts",        # Quality teaching materials
    "UCSD Radiology Review 2019", # Recent review materials
    "Articles"              # Select journal articles
]

def process_priority_directories():
    """Process the most important directories first"""
    
    source_root = Path(r"X:\Subfolders\Rads HDD")
    
    logging.info("=== SELECTIVE RADIOLOGY INGESTION ===")
    logging.info("Processing high-priority directories first...")
    
    # Initialize RAG system
    try:
        rag_system = RadiologyRAGSystem()
        logging.info("RAG system initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize RAG system: {e}")
        return
    
    total_processed = 0
    
    for priority_dir in PRIORITY_DIRS:
        dir_path = source_root / priority_dir
        
        if not dir_path.exists():
            logging.warning(f"Priority directory not found: {priority_dir}")
            continue
            
        logging.info(f"\n=== PROCESSING: {priority_dir} ===")
        
        # Find files in this directory
        files_in_dir = []
        supported_extensions = {'.pdf', '.ppt', '.pptx'}
        
        for file_path in dir_path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in supported_extensions and
                not file_path.name.startswith('._') and  # Skip macOS metadata files
                not file_path.name.startswith('.DS_Store')):  # Skip other system files
                files_in_dir.append(str(file_path))
        
        logging.info(f"Found {len(files_in_dir)} files in {priority_dir}")
        
        if not files_in_dir:
            continue
            
        # Process files in small batches
        batch_size = 2
        processed_in_dir = 0
        
        for i in range(0, len(files_in_dir), batch_size):
            batch = files_in_dir[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(files_in_dir) + batch_size - 1) // batch_size
            
            logging.info(f"Processing batch {batch_num}/{total_batches} from {priority_dir}")
            
            try:
                result = rag_system.process_documents(batch)
                
                if result.get("success", False):
                    batch_processed = result.get("processed", 0)
                    processed_in_dir += batch_processed
                    total_processed += batch_processed
                    logging.info(f"Batch completed: {batch_processed} files processed")
                else:
                    logging.warning(f"Batch failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logging.error(f"Error processing batch: {e}")
            
            # Progress update
            percent_dir = (i + len(batch)) / len(files_in_dir) * 100
            logging.info(f"Directory progress: {percent_dir:.1f}% ({processed_in_dir}/{len(files_in_dir)})")
            
            # Small delay between batches
            time.sleep(2)
        
        logging.info(f"Completed {priority_dir}: {processed_in_dir}/{len(files_in_dir)} files processed")
    
    logging.info(f"\n=== SELECTIVE PROCESSING COMPLETE ===")
    logging.info(f"Total files processed: {total_processed}")
    logging.info("High-priority materials have been added to your knowledge base!")
    
    # Show next steps
    remaining_dirs = ["USC Stuff", "Books", "Random"]  # Large directories to process later
    remaining_files = 0
    
    for remaining_dir in remaining_dirs:
        dir_path = source_root / remaining_dir
        if dir_path.exists():
            count = sum(1 for f in dir_path.rglob('*') if f.is_file() and f.suffix.lower() in {'.pdf', '.ppt', '.pptx'})
            remaining_files += count
    
    logging.info(f"\nNext steps:")
    logging.info(f"- You now have the core materials processed ({total_processed} files)")
    logging.info(f"- Test the system with the Streamlit app")
    logging.info(f"- If you want more content, run the full bulk_ingest_materials.py")
    logging.info(f"- Remaining large directories contain ~{remaining_files} additional files")

if __name__ == "__main__":
    process_priority_directories()