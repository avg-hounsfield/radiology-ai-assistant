#!/usr/bin/env python3
"""
Local data ingestion for radiology materials
Works with local data directories and improves knowledge base
"""

import os
import sys
from pathlib import Path
import logging
from typing import List, Dict
import time
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from retrieval.rag_system import RadiologyRAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('local_ingest.log'),
        logging.StreamHandler()
    ]
)

class LocalRadiologyIngestor:
    def __init__(self):
        self.rag_system = RadiologyRAGSystem()
        self.processed_files = self.load_processed_files()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_chunks': 0
        }

    def load_processed_files(self) -> Dict:
        """Load record of already processed files"""
        processed_file = Path("data/processed_documents.json")
        if processed_file.exists():
            try:
                with open(processed_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_processed_files(self):
        """Save record of processed files"""
        processed_file = Path("data/processed_documents.json")
        processed_file.parent.mkdir(exist_ok=True)
        with open(processed_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def find_local_documents(self) -> List[str]:
        """Find all supported documents in local directories"""

        # Local directories to scan
        local_dirs = [
            "data/incoming",
            "data/lecture_transcripts",
            "data/raw",
            "data/processed"
        ]

        # Supported file extensions
        extensions = ['.pdf', '.ppt', '.pptx', '.txt']

        documents = []

        for dir_path in local_dirs:
            if os.path.exists(dir_path):
                logging.info(f"Scanning {dir_path}...")

                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in extensions):
                            full_path = os.path.join(root, file)

                            # Skip if already processed (check file modification time too)
                            file_key = f"{full_path}:{os.path.getmtime(full_path)}"
                            if file_key not in self.processed_files:
                                documents.append(full_path)
                                logging.info(f"Found: {file}")
                            else:
                                logging.debug(f"Already processed: {file}")
                                self.stats['skipped'] += 1

        logging.info(f"Found {len(documents)} new documents to process")
        return documents

    def process_documents_batch(self, documents: List[str], batch_size: int = 5):
        """Process documents in batches for better memory management"""

        total_batches = (len(documents) + batch_size - 1) // batch_size

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1

            logging.info(f"Processing batch {batch_num}/{total_batches}")

            try:
                result = self.rag_system.process_documents(batch)

                if result.get('success', False):
                    self.stats['successful'] += result.get('processed', 0)
                    self.stats['total_chunks'] += result.get('total_chunks', 0)

                    # Mark files as processed
                    for doc_path in batch:
                        file_key = f"{doc_path}:{os.path.getmtime(doc_path)}"
                        self.processed_files[file_key] = {
                            'processed_date': time.time(),
                            'file_size': os.path.getsize(doc_path),
                            'file_name': os.path.basename(doc_path)
                        }
                else:
                    self.stats['failed'] += len(batch)
                    logging.error(f"Batch processing failed: {result.get('error', 'Unknown error')}")

                # Save progress after each batch
                self.save_processed_files()

                # Brief pause between batches
                time.sleep(1)

            except Exception as e:
                logging.error(f"Error processing batch {batch_num}: {e}")
                self.stats['failed'] += len(batch)

        self.stats['total_processed'] = self.stats['successful'] + self.stats['failed']

    def enhance_embeddings(self):
        """Enhance the embedding system with medical parameters"""

        logging.info("=== ENHANCING EMBEDDINGS WITH MEDICAL PARAMETERS ===")

        # Medical-specific enhancement parameters
        medical_enhancements = {
            'anatomy_terms': [
                'heart', 'lung', 'liver', 'kidney', 'brain', 'spine', 'bone',
                'chest', 'abdomen', 'pelvis', 'extremity', 'head', 'neck'
            ],
            'pathology_terms': [
                'tumor', 'mass', 'lesion', 'nodule', 'consolidation', 'effusion',
                'hemorrhage', 'infarct', 'edema', 'inflammation', 'infection',
                'fracture', 'dislocation', 'stenosis', 'dilatation'
            ],
            'imaging_terms': [
                'contrast', 'enhancement', 'signal', 'density', 'attenuation',
                'hyperintense', 'hypointense', 'hyperechoic', 'hypoechoic',
                'homogeneous', 'heterogeneous', 'isointense', 'hyperdense'
            ],
            'clinical_terms': [
                'diagnosis', 'differential', 'findings', 'impression', 'history',
                'symptoms', 'signs', 'treatment', 'prognosis', 'follow-up'
            ]
        }

        # Save enhancement parameters
        enhancement_file = Path("data/medical_enhancements.json")
        enhancement_file.parent.mkdir(exist_ok=True)
        with open(enhancement_file, 'w') as f:
            json.dump(medical_enhancements, f, indent=2)

        logging.info("Medical enhancement parameters saved")
        return medical_enhancements

    def generate_performance_report(self):
        """Generate a performance report of the ingestion process"""

        report = {
            'ingestion_stats': self.stats,
            'timestamp': time.time(),
            'system_status': self.rag_system.get_system_status(),
            'total_files_in_db': len(self.processed_files)
        }

        # Save report
        report_file = Path("data/performance_data.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logging.info("=== INGESTION REPORT ===")
        logging.info(f"Total processed: {self.stats['total_processed']}")
        logging.info(f"Successful: {self.stats['successful']}")
        logging.info(f"Failed: {self.stats['failed']}")
        logging.info(f"Skipped: {self.stats['skipped']}")
        logging.info(f"Total chunks: {self.stats['total_chunks']}")
        logging.info(f"Files in database: {len(self.processed_files)}")

        return report

def main():
    """Main ingestion process"""

    ingestor = LocalRadiologyIngestor()

    try:
        # Step 1: Find documents
        documents = ingestor.find_local_documents()

        if not documents:
            logging.info("No new documents found to process")
            return

        # Step 2: Enhance embeddings with medical parameters
        ingestor.enhance_embeddings()

        # Step 3: Process documents
        ingestor.process_documents_batch(documents)

        # Step 4: Generate report
        ingestor.generate_performance_report()

        logging.info("=== INGESTION COMPLETED ===")

    except Exception as e:
        logging.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()