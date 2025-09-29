# 🚀 ECHO App Deployment Guide

## Quick Network Access (Immediate)

### Option 1: Local Network Access
Run `deploy_network.bat` to make ECHO accessible on your local network:
- Access from other devices using your computer's IP address
- URL format: `http://[YOUR-IP]:8504`

### Option 2: Cloud Deployment

#### **Streamlit Community Cloud (Free)**
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy with one click

#### **Render (Free Tier)**
1. Create `requirements.txt`:
```txt
streamlit
torch
transformers
chromadb
sentence-transformers
plotly
pandas
numpy
pillow
pydicom
pyttsx3
edge-tts
```

2. Create `render.yaml`:
```yaml
services:
  - type: web
    name: echo-radiology
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run src/ui/echo_unified_system.py --server.port $PORT --server.address 0.0.0.0
```

#### **Railway (Free/Paid)**
1. Connect GitHub repo to Railway
2. Set environment variables
3. Deploy automatically

#### **Heroku (Paid)**
1. Create `Procfile`:
```
web: streamlit run src/ui/echo_unified_system.py --server.port $PORT --server.address 0.0.0.0
```

2. Add `runtime.txt`:
```
python-3.11.0
```

## Security Considerations

### For Public Deployment:
- Remove sensitive data/credentials
- Add authentication if needed
- Use environment variables for configuration
- Consider rate limiting

### Network Configuration:
- Windows Firewall: Allow port 8504
- Router: Port forwarding for external access
- VPN: Secure remote access option

## Mobile Optimization

Add to `echo_unified_system.py`:
```python
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@media (max-width: 768px) {
    .stSidebar { width: 100% !important; }
    .main .block-container { padding: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)
```

## Quick Start Commands

### Local Network:
```bash
# Make accessible on network
python -m streamlit run src/ui/echo_unified_system.py --server.address 0.0.0.0 --server.port 8504
```

### Production:
```bash
# With optimizations
python -m streamlit run src/ui/echo_unified_system.py --server.address 0.0.0.0 --server.port 8504 --server.headless true --server.runOnSave false
```