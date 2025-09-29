# 🌐 ECHO Remote Access & Sync Guide

## 📊 **Progress Sync Across Devices**

### **Option 1: Cloud Sync (Recommended)**

Set up automatic progress syncing with cloud storage:

#### **Dropbox Setup:**
1. Create Dropbox App at https://www.dropbox.com/developers/apps
2. Generate access token
3. Add to environment variables:
```bash
set DROPBOX_ACCESS_TOKEN=your_token_here
```

#### **Google Cloud Setup:**
1. Create Google Cloud Storage bucket
2. Download service account credentials
3. Set environment variables:
```bash
set GOOGLE_APPLICATION_CREDENTIALS=path\to\credentials.json
set GCS_BUCKET_NAME=your_bucket_name
```

#### **Network Share Setup:**
For local network sync (NAS/shared folder):
```bash
set ECHO_NETWORK_SYNC_PATH=\\your-nas\ECHO_Data
```

## 🌍 **Remote Access Options**

### **Option 1: Streamlit Community Cloud (FREE)**

**Best for: Public deployment, always accessible**

1. **Prepare Repository:**
```bash
# Push your code to GitHub
git init
git add .
git commit -m "ECHO Radiology System"
git remote add origin https://github.com/yourusername/echo-radiology.git
git push -u origin main
```

2. **Create requirements.txt:**
```txt
streamlit>=1.28.0
torch>=1.13.0
transformers>=4.21.0
sentence-transformers>=2.2.2
chromadb>=0.4.0
plotly>=5.15.0
pandas>=1.5.0
numpy>=1.24.0
pillow>=9.5.0
pyttsx3>=2.90
edge-tts>=6.1.0
```

3. **Deploy to Streamlit Cloud:**
   - Visit https://share.streamlit.io
   - Connect your GitHub repo
   - Deploy with one click
   - Get public URL like: https://your-app.streamlit.app

### **Option 2: Railway (FREE/PAID)**

**Best for: Easy deployment with custom domain**

1. **Connect to Railway:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

2. **Environment Variables in Railway:**
- Add all your sync tokens in Railway dashboard
- Set PORT=8504

### **Option 3: Render (FREE/PAID)**

**Best for: Reliable hosting with auto-deploy**

1. **Create render.yaml:**
```yaml
services:
  - type: web
    name: echo-radiology
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run src/ui/echo_unified_system.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: DROPBOX_ACCESS_TOKEN
        sync: false
```

### **Option 4: VPS/Cloud Server (ADVANCED)**

**Best for: Full control, custom domain**

#### **DigitalOcean Droplet Setup:**
```bash
# Create Ubuntu 22.04 droplet
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt update
apt install python3 python3-pip nginx -y

# Clone your repo
git clone https://github.com/yourusername/echo-radiology.git
cd echo-radiology

# Install requirements
pip3 install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/echo.service > /dev/null <<EOF
[Unit]
Description=ECHO Radiology System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/echo-radiology
ExecStart=/usr/bin/python3 -m streamlit run src/ui/echo_unified_system.py --server.port 8504 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl enable echo
sudo systemctl start echo
```

#### **Nginx Reverse Proxy:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8504;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Option 5: Ngrok Tunnel (QUICK)**

**Best for: Temporary remote access**

```bash
# Install ngrok
# Download from https://ngrok.com/

# Start your ECHO system locally
python -m streamlit run src/ui/echo_unified_system.py --server.port 8504

# In another terminal, create tunnel
ngrok http 8504

# Get public URL like: https://abc123.ngrok.io
```

### **Option 6: Tailscale VPN (SECURE)**

**Best for: Secure access from your devices only**

1. Install Tailscale on all devices
2. Run ECHO on your home computer
3. Access from anywhere via Tailscale IP

## 🔒 **Security Considerations**

### **For Public Deployment:**
- Remove sensitive data/credentials
- Add authentication if needed
- Use HTTPS (Let's Encrypt)
- Consider rate limiting

### **Authentication Setup:**
```python
# Add to your streamlit app
import streamlit_authenticator as stauth

# Simple password protection
def check_password():
    def password_entered():
        if st.session_state["password"] == "your_password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True

if check_password():
    # Your ECHO app code here
```

## 📱 **Mobile Optimization**

Add mobile-friendly CSS to your app:

```python
st.markdown("""
<style>
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }
    .stButton > button {
        width: 100%;
        margin-bottom: 10px;
    }
}
</style>
""", unsafe_allow_html=True)
```

## 🚀 **Quick Start Commands**

### **Local Network Access:**
```bash
# Run on all network interfaces
streamlit run src/ui/echo_unified_system.py --server.address 0.0.0.0 --server.port 8504

# Access from other devices: http://YOUR-IP:8504
```

### **Ngrok Quick Deploy:**
```bash
# Terminal 1: Start ECHO
streamlit run src/ui/echo_unified_system.py --server.port 8504

# Terminal 2: Create tunnel
ngrok http 8504
```

### **Docker Deployment:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8504

CMD ["streamlit", "run", "src/ui/echo_unified_system.py", "--server.port", "8504", "--server.address", "0.0.0.0"]
```

## 🔄 **Progress Sync Setup**

1. **Choose cloud provider** (Dropbox recommended for simplicity)
2. **Set environment variables** with your credentials
3. **Automatic sync** happens on app startup and shutdown
4. **Manual sync** available in settings

Your progress, flashcard reviews, study sessions, and all data will sync automatically across all devices! 🎉