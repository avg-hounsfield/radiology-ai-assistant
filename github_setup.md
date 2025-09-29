# 📂 GitHub Repository Setup for avg-hounsfield

## 🎯 **Step-by-Step GitHub Setup**

### **1. Initialize Git Repository**

```bash
cd C:\Users\Patrick\radiology-ai-assistant

# Initialize git
git init

# Create .gitignore
echo "# ECHO Radiology System - Ignore sensitive files
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
ENV/
env.bak/
venv.bak/

# Data directories (contains large files and user data)
data/
!data/.gitkeep

# Cache and temp files
.cache/
temp/
.streamlit/
*.log

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Large model files
*.bin
*.safetensors
models/
!models/.gitkeep

# User-specific files
config/user_*.json
secrets.toml" > .gitignore

# Create data directory structure with .gitkeep files
mkdir -p data/flashcards data/dictation_cases data/dictation_attempts data/videos/lectures data/videos/cases data/videos/tutorials
echo "" > data/.gitkeep
echo "" > data/flashcards/.gitkeep
echo "" > data/dictation_cases/.gitkeep
echo "" > data/dictation_attempts/.gitkeep
echo "" > data/videos/.gitkeep
echo "" > data/videos/lectures/.gitkeep
echo "" > data/videos/cases/.gitkeep
echo "" > data/videos/tutorials/.gitkeep

# Add and commit initial files
git add .
git commit -m "Initial commit: ECHO Unified Radiology System

- Complete Anki-compatible flashcard system (14,000+ imported cards)
- Spaced repetition learning with SM-2 algorithm
- AI-powered RAG search system
- Board study questions with audio narration
- Video library with enhanced metadata parsing
- Practice dictation with AI scoring
- Performance analytics and progress tracking
- Multi-device sync capabilities
- Professional ECHO theme and UI"

# Create remote repository (you'll need to do this manually on GitHub)
echo "✅ Local repository initialized!"
echo "🌐 Next: Create repository on GitHub..."
```

### **2. Create GitHub Repository**

**Manual Steps:**
1. Go to https://github.com/new
2. **Repository name**: `echo-radiology-system`
3. **Description**: `ECHO Unified Radiology Study System - Comprehensive board prep with flashcards, AI search, and spaced repetition`
4. **Visibility**: Private (recommended) or Public
5. **Initialize**: Don't initialize (we already have files)
6. Click **Create Repository**

**Then connect your local repo:**
```bash
# Add remote origin
git remote add origin https://github.com/avg-hounsfield/echo-radiology-system.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### **3. Configure for Streamlit Deployment**

Create deployment configuration:
```bash
# Create .streamlit directory and config
mkdir -p .streamlit
echo "[theme]
primaryColor = '#00BFFF'
backgroundColor = '#0B121A'
secondaryBackgroundColor = '#1a1f2e'
textColor = '#EAEAEA'

[server]
headless = true
enableCORS = false
enableXsrfProtection = false" > .streamlit/config.toml
```

### **4. Streamlit Community Cloud Deployment**

1. Visit https://share.streamlit.io
2. Click **"New app"**
3. Connect your GitHub account
4. Select repository: `avg-hounsfield/echo-radiology-system`
5. Branch: `main`
6. Main file path: `src/ui/echo_unified_system.py`
7. **App URL**: Will be `https://echo-radiology-system.streamlit.app`

Your app will be live at: **`https://echo-radiology-system.streamlit.app`**

## ⚙️ **Environment Variables for Cloud Deployment**

In Streamlit Cloud, add these secrets (App Settings > Secrets):

```toml
# Streamlit Cloud Secrets
[secrets]
# Optional: Add authentication
ADMIN_PASSWORD = "your_secure_password"

# Optional: Cloud sync credentials
DROPBOX_ACCESS_TOKEN = "your_dropbox_token"
GOOGLE_APPLICATION_CREDENTIALS = "path_to_credentials.json"

# Optional: Analytics
ANALYTICS_KEY = "your_analytics_key"
```