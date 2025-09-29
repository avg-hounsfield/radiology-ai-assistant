# RadCore AI - Automated Data Ingestion

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
