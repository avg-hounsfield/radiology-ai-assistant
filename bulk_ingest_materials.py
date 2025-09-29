#!/usr/bin/env python3
"""
Bulk ingestion script for radiology materials
Processes all PDF and PPT files from X:\Subfolders\Rads HDD
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
from document_processor.pdf_processor import PDFProcessor
from document_processor.ppt_processor import PPTProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_ingest.log'),
        logging.StreamHandler()
    ]
)

def find_radiology_files(root_directory: str) -> List[str]:
    """Find all PDF and PPT files in the directory structure"""
    supported_extensions = ['.pdf', '.ppt', '.pptx']
    found_files = []
    
    root_path = Path(root_directory)
    
    if not root_path.exists():
        logging.error(f"Directory does not exist: {root_directory}")
        return []
    
    logging.info(f"Scanning directory: {root_directory}")
    
    try:
        # Walk through all subdirectories
        for file_path in root_path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in supported_extensions and
                not file_path.name.startswith('._') and  # Skip macOS metadata files
                not file_path.name.startswith('.DS_Store')):  # Skip other system files
                found_files.append(str(file_path))
                
        logging.info(f"Found {len(found_files)} files to process")
        
        # Group by file type
        pdf_files = [f for f in found_files if f.lower().endswith('.pdf')]
        ppt_files = [f for f in found_files if f.lower().endswith(('.ppt', '.pptx'))]
        
        logging.info(f"  - PDF files: {len(pdf_files)}")
        logging.info(f"  - PowerPoint files: {len(ppt_files)}")
        
        return found_files
        
    except Exception as e:
        logging.error(f"Error scanning directory: {e}")
        return []

def process_files_in_batches(files: List[str], batch_size: int = 5) -> dict:
    """Process files in batches to avoid memory issues"""
    
    # Initialize the RAG system
    logging.info("Initializing RAG system...")
    try:
        rag_system = RadiologyRAGSystem()
        logging.info("RAG system initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize RAG system: {e}")
        return {"error": str(e), "processed": 0, "total": len(files)}
    
    total_files = len(files)
    processed_count = 0
    failed_files = []
    processing_stats = {
        "total_files": total_files,
        "processed": 0,
        "failed": 0,
        "failed_files": [],
        "processing_time": 0
    }
    
    start_time = time.time()
    
    # Process files in batches
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_files + batch_size - 1) // batch_size
        
        logging.info(f"\n--- Processing Batch {batch_num}/{total_batches} ---")
        logging.info(f"Files in this batch: {len(batch)}")
        
        try:
            # Process the batch
            result = rag_system.process_documents(batch)
            
            if result.get("success", False):
                batch_processed = result.get("processed", 0)
                processed_count += batch_processed
                logging.info(f"Batch {batch_num} completed: {batch_processed} files processed")
            else:
                logging.warning(f"Batch {batch_num} had issues: {result.get('error', 'Unknown error')}")
                failed_files.extend(batch)
                
        except Exception as e:
            logging.error(f"Error processing batch {batch_num}: {e}")
            failed_files.extend(batch)
            
        # Progress update
        percent_complete = (i + len(batch)) / total_files * 100
        logging.info(f"Overall progress: {percent_complete:.1f}% ({processed_count}/{total_files} files)")
        
        # Small delay between batches
        time.sleep(1)
    
    processing_time = time.time() - start_time
    
    processing_stats.update({
        "processed": processed_count,
        "failed": len(failed_files),
        "failed_files": failed_files,
        "processing_time": processing_time
    })
    
    return processing_stats

def main():
    """Main ingestion process"""
    
    # Configuration
    SOURCE_DIRECTORY = r"X:\Subfolders\Rads HDD"
    BATCH_SIZE = 2  # Process 2 files at a time to avoid memory issues with large collection
    
    logging.info("=== RADIOLOGY MATERIALS BULK INGESTION ===")
    logging.info(f"Source directory: {SOURCE_DIRECTORY}")
    
    # Step 1: Find all files
    logging.info("\n1. Scanning for radiology materials...")
    files_to_process = find_radiology_files(SOURCE_DIRECTORY)
    
    if not files_to_process:
        logging.warning("No files found to process. Exiting.")
        return
    
    # Show sample of files that will be processed
    logging.info("\nSample files found:")
    for i, file_path in enumerate(files_to_process[:10]):
        filename = os.path.basename(file_path)
        logging.info(f"  {i+1}. {filename}")
    
    if len(files_to_process) > 10:
        logging.info(f"  ... and {len(files_to_process) - 10} more files")
    
    # Confirmation
    print(f"\nFound {len(files_to_process)} files to process.")
    print("This process may take several hours depending on file sizes.")
    
    # For automated processing, comment out the input() line below
    # user_input = input("Continue with processing? (y/N): ")
    # if user_input.lower() != 'y':
    #     logging.info("Processing cancelled by user")
    #     return
    
    # Step 2: Process files
    logging.info(f"\n2. Starting bulk processing of {len(files_to_process)} files...")
    logging.info(f"Processing in batches of {BATCH_SIZE} files")
    
    results = process_files_in_batches(files_to_process, BATCH_SIZE)
    
    # Step 3: Report results
    logging.info("\n=== PROCESSING COMPLETE ===")
    logging.info(f"Total files found: {results['total_files']}")
    logging.info(f"Successfully processed: {results['processed']}")
    logging.info(f"Failed to process: {results['failed']}")
    logging.info(f"Processing time: {results['processing_time']:.1f} seconds")
    
    if results['failed_files']:
        logging.warning(f"\nFailed files ({len(results['failed_files'])}):")
        for failed_file in results['failed_files'][:10]:
            logging.warning(f"  - {os.path.basename(failed_file)}")
        if len(results['failed_files']) > 10:
            logging.warning(f"  ... and {len(results['failed_files']) - 10} more")
    
    # Save processing report
    try:
        import json
        report_file = "bulk_processing_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"\nDetailed report saved to: {report_file}")
    except Exception as e:
        logging.warning(f"Could not save report: {e}")
    
    logging.info(f"\nDatabase building complete! Processed {results['processed']} radiology materials.")
    logging.info("You can now use the Streamlit app with your comprehensive knowledge base.")

if __name__ == "__main__":
    main()