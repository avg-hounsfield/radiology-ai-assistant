# ECHO Performance Optimization Guide

## Current Performance Issues

Your system is running slowly due to several factors:

### 1. Multiple Running Instances
- **Problem**: You have 12+ Streamlit instances running simultaneously on different ports
- **Impact**: Each instance consumes 500MB-2GB RAM + significant CPU
- **Solution**: Kill unnecessary instances

### 2. Heavy AI Models Loading
- **CLIP Model**: ~400MB for image embeddings
- **Sentence Transformers**: ~500MB for text embeddings
- **RAG System**: Vector database operations are CPU intensive
- **LLM Operations**: Large language model inference

### 3. System Resource Usage
- **Estimated RAM usage**: 8-16GB for all running instances
- **CPU Usage**: High due to AI model operations

## Quick Performance Fixes

### Stop Unnecessary Instances
```bash
# Kill extra Streamlit processes
taskkill /f /im python.exe
# Then run only one instance:
python -m streamlit run src/ui/echo_unified_system.py --server.port 8501
```

### Hardware Recommendations
- **Minimum**: 16GB RAM, 4-core CPU
- **Recommended**: 32GB RAM, 8-core CPU, SSD storage
- **Optimal**: 64GB RAM, GPU for AI acceleration

### Performance Settings
1. **Reduce model loading**: Set `LAZY_LOADING=true` in environment
2. **Limit concurrent users**: Use `--server.maxUploadSize=1000`
3. **Cache optimization**: Models cache on first load

### User Accounts Created
- **admin** / echo2024 (full access to uploads, scans, etc.)
- **matulich** / echo2024 (study mode access only)

## Authentication Features Added
✅ Login UI completely fades out after authentication
✅ Admin-only functions (upload images, scan directories, upload documents)
✅ Role-based access control
✅ Hidden Streamlit menu/footer after login
✅ Smooth transitions and animations

## Expected Performance After Optimization
- **First load**: 10-30 seconds (model loading)
- **Regular use**: 1-3 seconds per interaction
- **Image processing**: 2-5 seconds per image
- **Search queries**: 1-2 seconds