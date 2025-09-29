@echo off
echo Starting RadCore AI Data Ingestion...
cd /d "%~dp0.."
python scripts/auto_ingest_data.py
pause
