# scripts/setup_ingestion.py
"""
Setup script for automated data ingestion
Creates folders, configuration, and provides instructions
"""

import os
import json
from pathlib import Path

def create_folder_structure():
    """Create necessary folder structure"""
    folders = [
        './data/incoming',
        './data/lecture_transcripts', 
        './data/processed_backup',
        './logs',
        './scripts'
    ]
    
    created_folders = []
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            created_folders.append(folder)
            print(f"✅ Created folder: {folder}")
        else:
            print(f"📁 Folder already exists: {folder}")
    
    return created_folders

def create_config_file():
    """Create default configuration file"""
    config = {
        "watch_folders": [
            {
                "path": "./data/incoming",
                "description": "Main incoming folder - drop new documents here",
                "recursive": True,
                "auto_process": True
            },
            {
                "path": "./data/lecture_transcripts",
                "description": "Folder for lecture transcript .txt files",
                "recursive": False,
                "auto_process": True
            }
        ],
        "supported_extensions": [".pdf", ".ppt", ".pptx", ".txt"],
        "processing": {
            "batch_size": 3,
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
    
    config_path = "./scripts/ingestion_config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created configuration file: {config_path}")
    return config_path

def create_batch_scripts():
    """Create helpful batch scripts"""
    
    # Windows batch file
    windows_script = """@echo off
echo Starting RadCore AI Data Ingestion...
cd /d "%~dp0.."
python scripts/auto_ingest_data.py
pause
"""
    
    with open('./scripts/start_ingestion.bat', 'w') as f:
        f.write(windows_script)
    
    # Linux/Mac shell script  
    unix_script = """#!/bin/bash
echo "Starting RadCore AI Data Ingestion..."
cd "$(dirname "$0")/.."
python scripts/auto_ingest_data.py
"""
    
    with open('./scripts/start_ingestion.sh', 'w') as f:
        f.write(unix_script)
    
    # Make shell script executable
    try:
        os.chmod('./scripts/start_ingestion.sh', 0o755)
    except:
        pass
    
    print("✅ Created startup scripts:")
    print("  • start_ingestion.bat (Windows)")
    print("  • start_ingestion.sh (Linux/Mac)")

def create_readme():
    """Create README for data ingestion"""
    readme_content = """# RadCore AI - Automated Data Ingestion

## Quick Start

### Option 1: Automatic Monitoring
Monitor folders and automatically process new files:
```bash
python scripts/auto_ingest_data.py
```

### Option 2: Batch Processing
Process a specific folder of documents:
```bash
python scripts/batch_process.py /path/to/your/documents
```

## Folder Structure

- `data/incoming/` - Drop new documents here for automatic processing
- `data/lecture_transcripts/` - Place lecture transcript .txt files here
- `data/processed_backup/` - Automatically created backups of processed files
- `logs/` - Processing logs and reports

## Supported File Types

- PDF documents (.pdf)
- PowerPoint presentations (.ppt, .pptx) 
- Text transcripts (.txt)

## Configuration

Edit `scripts/ingestion_config.json` to customize:
- Watch folders
- Processing settings
- File size limits
- Backup options

## Usage Examples

**Automatic monitoring:**
```bash
# Start monitoring (runs continuously)
python scripts/auto_ingest_data.py

# Scan existing files only (one-time)
python scripts/auto_ingest_data.py --scan-only
```

**Batch processing:**
```bash
# Process all supported files in a folder
python scripts/batch_process.py /path/to/documents

# Preview what would be processed
python scripts/batch_process.py /path/to/documents --dry-run

# Process only specific file types
python scripts/batch_process.py /path/to/documents --extensions .pdf .txt
```

## What Happens During Processing

1. **Document Analysis**: Files are analyzed for type and content
2. **Text Extraction**: Text and metadata extracted from documents
3. **Image Archiving**: Images extracted and tagged (PDFs)
4. **Transcript Processing**: Lecture transcripts parsed for speakers/timestamps
5. **Embedding Generation**: Content converted to searchable embeddings using RadBERT
6. **Vector Storage**: Embeddings stored in searchable database
7. **Backup**: Original files backed up automatically

## Monitoring

- **Console Output**: Real-time processing status
- **Log Files**: Detailed logs in `logs/ingestion.log`
- **Summary Reports**: Periodic processing statistics

## Tips

- **Large Files**: Files over 100MB are skipped by default (configurable)
- **Duplicates**: Files are tracked by content hash to avoid reprocessing
- **Interruption**: Safe to stop/restart - won't reprocess existing files
- **Performance**: Adjust batch_size in config for your hardware
"""

    with open('./DATA_INGESTION_README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ Created documentation: DATA_INGESTION_README.md")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing required dependencies...")
    
    dependencies = [
        'watchdog'  # For file system monitoring
    ]
    
    for dep in dependencies:
        try:
            import subprocess
            result = subprocess.run(['pip', 'install', dep], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Installed {dep}")
            else:
                print(f"⚠️ Failed to install {dep}: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Could not install {dep}: {e}")
            print(f"   Please run: pip install {dep}")

def main():
    """Main setup function"""
    print("🚀 Setting up RadCore AI Data Ingestion System\n")
    
    # Create folder structure
    print("📁 Creating folder structure...")
    create_folder_structure()
    print()
    
    # Create configuration
    print("⚙️ Creating configuration...")
    config_path = create_config_file()
    print()
    
    # Create batch scripts
    print("📜 Creating startup scripts...")
    create_batch_scripts()
    print()
    
    # Create documentation
    print("📚 Creating documentation...")
    create_readme()
    print()
    
    # Install dependencies
    install_dependencies()
    print()
    
    # Final instructions
    print("🎉 Setup Complete!")
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("="*50)
    print()
    print("1. 📁 Add documents to watch folders:")
    print("   • ./data/incoming/ - for PDFs, PowerPoints")
    print("   • ./data/lecture_transcripts/ - for .txt transcripts")
    print()
    print("2. 🚀 Start automatic ingestion:")
    print("   python scripts/auto_ingest_data.py")
    print()
    print("3. 📖 Or process existing folder:")
    print("   python scripts/batch_process.py /path/to/your/documents")
    print()
    print("4. 🔧 Customize settings:")
    print(f"   Edit {config_path}")
    print()
    print("5. 📚 Read full documentation:")
    print("   DATA_INGESTION_README.md")
    print()
    print("💡 The system will automatically:")
    print("   ✅ Extract text and images")
    print("   ✅ Generate searchable embeddings")
    print("   ✅ Process lecture transcripts")
    print("   ✅ Avoid duplicate processing")
    print("   ✅ Create backups")
    print()

if __name__ == "__main__":
    main()
