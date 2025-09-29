#!/bin/bash
echo "Starting RadCore AI Data Ingestion..."
cd "$(dirname "$0")/.."
python scripts/auto_ingest_data.py
