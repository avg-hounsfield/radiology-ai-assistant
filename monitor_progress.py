#!/usr/bin/env python3
"""
Monitor the progress of the ingestion process
"""

import os
import time
from pathlib import Path

def monitor_ingestion():
    """Monitor ingestion progress"""
    
    log_file = "selective_ingest.log"
    embeddings_dir = Path("data/embeddings")
    
    print("=== INGESTION PROGRESS MONITOR ===")
    print("Press Ctrl+C to exit monitoring\n")
    
    last_position = 0
    
    try:
        while True:
            # Check if log file exists and show recent entries
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    if new_lines:
                        for line in new_lines:
                            if any(keyword in line for keyword in ['INFO', 'ERROR', 'WARNING']):
                                print(line.strip())
                        last_position = f.tell()
            
            # Check database size
            if embeddings_dir.exists():
                try:
                    total_size = sum(f.stat().st_size for f in embeddings_dir.rglob('*') if f.is_file())
                    size_mb = total_size / (1024 * 1024)
                    print(f"Current database size: {size_mb:.1f} MB")
                except:
                    pass
            
            print("---")
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_ingestion()