# scripts/auto_ingest_data.py
"""
Automated data ingestion script for RadCore AI
Monitors local folders and automatically processes new documents
"""

import os
import sys
import time
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root / "src"))

try:
    from retrieval.rag_system import RadiologyRAGSystem
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: RAG system not available: {e}")
    RAG_AVAILABLE = False

class DataIngestionConfig:
    """Configuration for data ingestion"""
    
    def __init__(self, config_path: str = "scripts/ingestion_config.json"):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "watch_folders": [
                {
                    "path": "./data/incoming",
                    "description": "Main incoming folder for new documents",
                    "recursive": True,
                    "auto_process": True
                },
                {
                    "path": "./data/lecture_transcripts", 
                    "description": "Folder for lecture transcripts",
                    "recursive": False,
                    "auto_process": True
                }
            ],
            "supported_extensions": [".pdf", ".ppt", ".pptx", ".txt"],
            "processing": {
                "batch_size": 5,
                "delay_seconds": 30,
                "max_file_size_mb": 100,
                "backup_processed": True,
                "backup_folder": "./data/processed_backup"
            },
            "notifications": {
                "enable_console": True,
                "enable_file_log": True,
                "log_file": "./logs/ingestion.log",
                "enable_summary_report": True
            },
            "rag_system": {
                "embedding_model": "radiology_optimized",
                "llm_model": "llama3.1:8b",
                "auto_initialize": True
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                    
                # Merge with defaults for missing keys
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            else:
                self.config = default_config
                self.save_config()
                
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            self.config = default_config
    
    def save_config(self):
        """Save configuration to JSON file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

class DocumentTracker:
    """Track processed documents to avoid reprocessing"""
    
    def __init__(self, tracker_file: str = "./data/processed_documents.json"):
        self.tracker_file = tracker_file
        self.processed_files = self.load_tracker()
    
    def load_tracker(self) -> Dict:
        """Load tracker from file"""
        try:
            if os.path.exists(self.tracker_file):
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tracker file: {e}")
        return {}
    
    def save_tracker(self):
        """Save tracker to file"""
        try:
            os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
            with open(self.tracker_file, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            print(f"Error saving tracker: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file for change detection"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            print(f"Error hashing file {file_path}: {e}")
            return ""
    
    def is_processed(self, file_path: str) -> bool:
        """Check if file has been processed"""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return False
        
        abs_path = os.path.abspath(file_path)
        
        # Check if file exists in tracker and hash matches
        if abs_path in self.processed_files:
            return self.processed_files[abs_path].get('hash') == file_hash
        
        return False
    
    def mark_processed(self, file_path: str, processing_result: Dict):
        """Mark file as processed"""
        file_hash = self.get_file_hash(file_path)
        abs_path = os.path.abspath(file_path)
        
        self.processed_files[abs_path] = {
            'hash': file_hash,
            'processed_at': datetime.now().isoformat(),
            'result': processing_result,
            'file_size': os.path.getsize(file_path),
            'filename': os.path.basename(file_path)
        }
        
        self.save_tracker()
    
    def get_processed_stats(self) -> Dict:
        """Get statistics about processed files"""
        if not self.processed_files:
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        total = len(self.processed_files)
        successful = sum(1 for f in self.processed_files.values() 
                        if f.get('result', {}).get('success', False))
        failed = total - successful
        
        return {
            'total': total,
            'successful': successful, 
            'failed': failed,
            'success_rate': round((successful / total) * 100, 1) if total > 0 else 0
        }

class DocumentProcessor:
    """Process documents using the RAG system"""
    
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.rag_system = None
        self.logger = self._setup_logging()
        
        if RAG_AVAILABLE and config.get('rag_system', {}).get('auto_initialize', True):
            self.initialize_rag_system()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the processor"""
        logger = logging.getLogger('DocumentProcessor')
        logger.setLevel(logging.INFO)
        
        # Console handler
        if self.config.get('notifications', {}).get('enable_console', True):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if self.config.get('notifications', {}).get('enable_file_log', True):
            log_file = self.config.get('notifications', {}).get('log_file', './logs/ingestion.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def initialize_rag_system(self):
        """Initialize the RAG system"""
        if not RAG_AVAILABLE:
            self.logger.error("RAG system not available - install required dependencies")
            return False
        
        try:
            rag_config = self.config.get('rag_system', {})
            embedding_model = rag_config.get('embedding_model', 'radiology_optimized')
            llm_model = rag_config.get('llm_model', 'llama3.1:8b')
            
            self.rag_system = RadiologyRAGSystem(embedding_model, llm_model)
            self.logger.info(f"✅ RAG system initialized with {embedding_model} embeddings and {llm_model} LLM")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize RAG system: {e}")
            self.rag_system = None
            return False
    
    def process_file(self, file_path: str) -> Dict:
        """Process a single file"""
        try:
            # Check file size
            max_size = self.config.get('processing', {}).get('max_file_size_mb', 100) * 1024 * 1024
            file_size = os.path.getsize(file_path)
            
            if file_size > max_size:
                return {
                    'success': False,
                    'error': f'File too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024):.1f}MB',
                    'file_path': file_path
                }
            
            # Process with RAG system
            if self.rag_system:
                self.logger.info(f"🔄 Processing {os.path.basename(file_path)}...")
                result = self.rag_system.process_documents([file_path])
                
                if result.get('success', False):
                    self.logger.info(f"✅ Successfully processed {os.path.basename(file_path)} - {result.get('total_chunks', 0)} chunks created")
                    
                    # Backup processed file if enabled
                    if self.config.get('processing', {}).get('backup_processed', True):
                        self._backup_file(file_path)
                    
                    return {
                        'success': True,
                        'file_path': file_path,
                        'chunks_created': result.get('total_chunks', 0),
                        'processing_time': result.get('processing_time', 0),
                        'transcript_count': result.get('transcript_count', 0)
                    }
                else:
                    error_msg = result.get('error', 'Unknown processing error')
                    self.logger.error(f"❌ Failed to process {os.path.basename(file_path)}: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'file_path': file_path
                    }
            else:
                return {
                    'success': False,
                    'error': 'RAG system not available',
                    'file_path': file_path
                }
                
        except Exception as e:
            self.logger.error(f"❌ Exception processing {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _backup_file(self, file_path: str):
        """Backup processed file"""
        try:
            backup_folder = self.config.get('processing', {}).get('backup_folder', './data/processed_backup')
            os.makedirs(backup_folder, exist_ok=True)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_folder, backup_name)
            
            # Copy file to backup location
            import shutil
            shutil.copy2(file_path, backup_path)
            
            self.logger.info(f"📁 Backed up {filename} to {backup_name}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to backup {file_path}: {e}")

class FileWatcher(FileSystemEventHandler):
    """Watch for new files and queue them for processing"""
    
    def __init__(self, processor: DocumentProcessor, tracker: DocumentTracker, config: DataIngestionConfig):
        self.processor = processor
        self.tracker = tracker
        self.config = config
        self.pending_files = set()
        self.supported_extensions = config.get('supported_extensions', [])
        self.logger = logging.getLogger('FileWatcher')
    
    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory:
            self._handle_file(event.src_path, "created")
    
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            self._handle_file(event.src_path, "modified")
    
    def _handle_file(self, file_path: str, event_type: str):
        """Handle file events"""
        try:
            # Check if file has supported extension
            if not any(file_path.lower().endswith(ext) for ext in self.supported_extensions):
                return
            
            # Wait for file to be fully written (common issue with file watchers)
            time.sleep(2)
            
            # Check if file still exists and is readable
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return
            
            # Check if already processed
            if self.tracker.is_processed(file_path):
                self.logger.info(f"⏭️ Skipping {os.path.basename(file_path)} - already processed")
                return
            
            # Add to pending files
            self.pending_files.add(file_path)
            self.logger.info(f"📥 Queued {os.path.basename(file_path)} for processing ({event_type})")
            
        except Exception as e:
            self.logger.error(f"Error handling file event for {file_path}: {e}")
    
    def process_pending_files(self):
        """Process all pending files"""
        if not self.pending_files:
            return
        
        batch_size = self.config.get('processing', {}).get('batch_size', 5)
        files_to_process = list(self.pending_files)[:batch_size]
        
        if files_to_process:
            self.logger.info(f"🔄 Processing batch of {len(files_to_process)} files...")
            
            for file_path in files_to_process:
                try:
                    # Remove from pending
                    self.pending_files.discard(file_path)
                    
                    # Process file
                    result = self.processor.process_file(file_path)
                    
                    # Track result
                    self.tracker.mark_processed(file_path, result)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
    
    def get_pending_count(self) -> int:
        """Get number of pending files"""
        return len(self.pending_files)

class AutoDataIngestion:
    """Main class for automated data ingestion"""
    
    def __init__(self, config_path: str = None):
        self.config = DataIngestionConfig(config_path) if config_path else DataIngestionConfig()
        self.tracker = DocumentTracker()
        self.processor = DocumentProcessor(self.config)
        self.observer = None
        self.watchers = []
        self.logger = logging.getLogger('AutoDataIngestion')
        self.running = False
        
        # Setup watch folders
        self._setup_watch_folders()
    
    def _setup_watch_folders(self):
        """Setup folder monitoring"""
        self.observer = Observer()
        
        for folder_config in self.config.get('watch_folders', []):
            folder_path = folder_config['path']
            
            # Create folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            # Create watcher
            watcher = FileWatcher(self.processor, self.tracker, self.config)
            self.watchers.append(watcher)
            
            # Start watching
            recursive = folder_config.get('recursive', True)
            self.observer.schedule(watcher, folder_path, recursive=recursive)
            
            self.logger.info(f"👁️ Watching folder: {folder_path} (recursive: {recursive})")
    
    def scan_existing_files(self):
        """Scan for existing files that haven't been processed"""
        self.logger.info("🔍 Scanning for existing unprocessed files...")
        
        found_files = []
        supported_extensions = self.config.get('supported_extensions', [])
        
        for folder_config in self.config.get('watch_folders', []):
            folder_path = folder_config['path']
            recursive = folder_config.get('recursive', True)
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in Path(folder_path).glob(pattern):
                if file_path.is_file():
                    if any(str(file_path).lower().endswith(ext) for ext in supported_extensions):
                        if not self.tracker.is_processed(str(file_path)):
                            found_files.append(str(file_path))
        
        if found_files:
            self.logger.info(f"📁 Found {len(found_files)} unprocessed files")
            
            # Process in batches
            batch_size = self.config.get('processing', {}).get('batch_size', 5)
            for i in range(0, len(found_files), batch_size):
                batch = found_files[i:i + batch_size]
                
                self.logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(found_files) + batch_size - 1)//batch_size}")
                
                for file_path in batch:
                    result = self.processor.process_file(file_path)
                    self.tracker.mark_processed(file_path, result)
        else:
            self.logger.info("✅ No unprocessed files found")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        try:
            self.logger.info("🚀 Starting automated data ingestion...")
            
            # First scan existing files
            self.scan_existing_files()
            
            # Start file system observer
            self.observer.start()
            self.running = True
            
            # Main processing loop
            delay = self.config.get('processing', {}).get('delay_seconds', 30)
            
            self.logger.info(f"👁️ Monitoring started - checking every {delay} seconds")
            
            while self.running:
                try:
                    # Process pending files from all watchers
                    total_pending = 0
                    for watcher in self.watchers:
                        watcher.process_pending_files()
                        total_pending += watcher.get_pending_count()
                    
                    if total_pending > 0:
                        self.logger.info(f"⏳ {total_pending} files still pending processing")
                    
                    # Generate periodic summary
                    if hasattr(self, 'last_summary') and (datetime.now() - self.last_summary).seconds > 3600:  # Every hour
                        self.generate_summary_report()
                    elif not hasattr(self, 'last_summary'):
                        self.last_summary = datetime.now()
                    
                    time.sleep(delay)
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Received interrupt signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(delay)
        
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.logger.info("🛑 Monitoring stopped")
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate and log summary report"""
        stats = self.tracker.get_processed_stats()
        
        report = f"""
📊 INGESTION SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📁 Processing Statistics:
  • Total files processed: {stats['total']}
  • Successful: {stats['successful']}
  • Failed: {stats['failed']}
  • Success rate: {stats['success_rate']}%

👁️ Watch Folders:
"""
        
        for folder_config in self.config.get('watch_folders', []):
            report += f"  • {folder_config['path']} ({'recursive' if folder_config.get('recursive') else 'non-recursive'})\n"
        
        # Pending files
        total_pending = sum(watcher.get_pending_count() for watcher in self.watchers)
        if total_pending > 0:
            report += f"\n⏳ Pending files: {total_pending}"
        
        self.logger.info(report)
        self.last_summary = datetime.now()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Automated Data Ingestion for RadCore AI')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--scan-only', action='store_true', help='Only scan existing files, don\'t monitor')
    parser.add_argument('--setup', action='store_true', help='Create default configuration and folders')
    
    args = parser.parse_args()
    
    if args.setup:
        # Create default setup
        config = DataIngestionConfig(args.config)
        
        # Create watch folders
        for folder_config in config.get('watch_folders', []):
            os.makedirs(folder_config['path'], exist_ok=True)
            print(f"✅ Created folder: {folder_config['path']}")
        
        # Create logs folder
        os.makedirs('./logs', exist_ok=True)
        print("✅ Created logs folder")
        
        print(f"✅ Setup complete! Configuration saved to {config.config_path}")
        print("\nTo start ingestion:")
        print("python scripts/auto_ingest_data.py")
        
        return
    
    # Initialize ingestion system
    ingestion = AutoDataIngestion(args.config)
    
    if args.scan_only:
        ingestion.scan_existing_files()
    else:
        try:
            ingestion.start_monitoring()
        except KeyboardInterrupt:
            print("\n🛑 Stopping ingestion...")
            ingestion.stop_monitoring()

if __name__ == "__main__":
    main()
