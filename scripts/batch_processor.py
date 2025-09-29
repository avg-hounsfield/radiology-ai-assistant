# scripts/batch_process.py
"""
Simple batch processing script for feeding data into RadCore AI
Use this for one-time processing of a folder of documents
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root / "src"))

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('./logs/batch_process.log')
        ]
    )
    return logging.getLogger('BatchProcessor')

def find_documents(folder_path: str, extensions: list = None) -> list:
    """Find all documents in folder"""
    if extensions is None:
        extensions = ['.pdf', '.ppt', '.pptx', '.txt']
    
    documents = []
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Find all files with supported extensions
    for ext in extensions:
        documents.extend(folder.glob(f"**/*{ext}"))
    
    return [str(doc) for doc in documents]

def process_documents(documents: list, logger) -> dict:
    """Process documents with RAG system"""
    try:
        # Import RAG system
        from retrieval.rag_system import RadiologyRAGSystem
        
        # Initialize system
        logger.info("🤖 Initializing RadCore AI system...")
        rag_system = RadiologyRAGSystem()
        
        # Process documents
        logger.info(f"🔄 Processing {len(documents)} documents...")
        start_time = datetime.now()
        
        result = rag_system.process_documents(documents)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Add timing info
        result['processing_time_seconds'] = processing_time
        result['processing_time_formatted'] = f"{processing_time/60:.1f} minutes"
        result['documents_processed'] = len(documents)
        
        return result
        
    except ImportError as e:
        logger.error(f"❌ Could not import RAG system: {e}")
        return {"success": False, "error": f"Import error: {e}"}
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Main batch processing function"""
    parser = argparse.ArgumentParser(description='Batch process documents for RadCore AI')
    parser.add_argument('folder', help='Folder containing documents to process')
    parser.add_argument('--extensions', nargs='+', default=['.pdf', '.ppt', '.pptx', '.txt'],
                        help='File extensions to process (default: .pdf .ppt .pptx .txt)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    
    args = parser.parse_args()
    
    # Setup logging
    os.makedirs('./logs', exist_ok=True)
    logger = setup_logging()
    
    logger.info("🚀 Starting batch processing...")
    logger.info(f"📁 Source folder: {args.folder}")
    logger.info(f"📄 Extensions: {args.extensions}")
    
    try:
        # Find documents
        documents = find_documents(args.folder, args.extensions)
        
        if not documents:
            logger.warning(f"⚠️ No documents found in {args.folder}")
            return
        
        logger.info(f"📋 Found {len(documents)} documents:")
        for doc in documents:
            logger.info(f"  • {os.path.basename(doc)}")
        
        if args.dry_run:
            logger.info("🔍 Dry run complete - no processing performed")
            return
        
        # Confirm processing
        print(f"\n🤔 Ready to process {len(documents)} documents.")
        response = input("Continue? (y/N): ").lower().strip()
        
        if response != 'y':
            logger.info("❌ Processing cancelled by user")
            return
        
        # Process documents
        result = process_documents(documents, logger)
        
        # Show results
        if result.get('success'):
            logger.info("✅ Processing completed successfully!")
            logger.info(f"📊 Results:")
            logger.info(f"  • Documents processed: {result.get('documents_processed', 0)}")
            logger.info(f"  • Text chunks created: {result.get('total_chunks', 0)}")
            logger.info(f"  • Processing time: {result.get('processing_time_formatted', 'Unknown')}")
            
            if result.get('transcript_count', 0) > 0:
                logger.info(f"  • Lecture transcripts: {result['transcript_count']}")
            
            if result.get('errors'):
                logger.warning(f"  • Errors encountered: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    logger.warning(f"    - {error}")
        else:
            logger.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
