# ECHO Radiology Assistant

A comprehensive AI-powered radiology study platform with advanced features including flashcards, image processing, RAG-based question answering, and board exam preparation.

## 🚀 Live Demo

Deploy this app to Streamlit Community Cloud:

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

## ✨ Features

### Study Tools
- **Flashcard System**: Anki-compatible spaced repetition with 13,800+ medical cards
- **Crack the Core Method**: Systematic pathology review for board exam prep
- **Video Learning**: Educational content with AI-enhanced metadata
- **Audio Teaching**: Text-to-speech for auditory learning

### Reference Tools
- **RAG Search**: AI-powered search through medical literature
- **Differential Diagnosis**: Clinical decision support
- **AJR Articles**: Integrated medical journal content
- **Imaging Guides**: Best practice recommendations

### Advanced Features
- **Image Processing**: CLIP-based visual search for medical images
- **Document Processing**: PDF/PowerPoint content extraction
- **User Authentication**: Role-based access control
- **Performance Tracking**: Study progress analytics

## 🔧 Technology Stack

- **Frontend**: Streamlit with custom CSS theming
- **AI/ML**: OpenAI CLIP, Sentence Transformers, RAG system
- **Database**: ChromaDB for vector storage
- **Authentication**: Custom user management system
- **Image Processing**: OpenCV, Pillow, PyMuPDF

## 📋 Prerequisites

- Python 3.8+
- 8GB+ RAM (16GB recommended)
- Internet connection for AI model downloads

## 🚀 Quick Start

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd radiology-ai-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

### Default Login
- **Admin**: `admin` / `echo2024` (full access)
- **User**: `matulich` / `echo2024` (study mode only)

## 🎯 Usage

### Study Mode
1. **Crack the Core**: Systematic pathology review
2. **Flashcards**: Spaced repetition learning
3. **Lessons**: Comprehensive reading materials
4. **Video Teaching**: Educational content

### Reference Mode
1. **Quick Search**: AI-powered medical queries
2. **Differential Dx**: Clinical decision support
3. **AJR Articles**: Medical literature search
4. **Imaging Guide**: Best practice recommendations

### Admin Functions (admin users only)
- Upload images and documents
- Scan directories for content
- Manage system settings

## 📁 Project Structure

```
radiology-ai-assistant/
├── streamlit_app.py          # Deployment entry point
├── requirements.txt          # Python dependencies
├── src/
│   ├── ui/                   # User interface components
│   ├── auth/                 # Authentication system
│   ├── retrieval/            # RAG and search systems
│   ├── study/                # Flashcards and study tools
│   ├── multimedia/           # Image/video processing
│   └── llm/                  # Language model integration
├── data/                     # Application data
└── .streamlit/              # Streamlit configuration
```

## 🛠️ Configuration

### Environment Variables
- `ADMIN_PASSWORD`: Override default admin password
- `OLLAMA_HOST`: Custom Ollama server endpoint

### Streamlit Configuration
Configuration in `.streamlit/config.toml`:
- Dark theme with medical color scheme
- Performance optimizations
- Security settings

## 🔒 Security Features

- **User Authentication**: Secure login system
- **Role-based Access**: Admin vs user permissions
- **Session Management**: Automatic timeout
- **Input Sanitization**: XSS protection

## 📊 Performance

### Optimizations
- Lazy loading of AI models
- Efficient vector similarity search
- Cached embeddings
- Streamlined duplicate removal

### System Requirements
- **Minimum**: 8GB RAM, 4-core CPU
- **Recommended**: 16GB RAM, 8-core CPU
- **Optimal**: 32GB RAM, GPU acceleration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Anki for flashcard inspiration
- OpenAI for CLIP model
- Streamlit team for the framework
- Medical education community

## 🐛 Issues & Support

For issues, feature requests, or questions:
1. Check existing issues
2. Create a new issue with detailed description
3. Include system information and error logs

## 🔄 Recent Updates

### v2.0 Features
- ✅ Streamlined 2-mode interface (Study/Reference)
- ✅ Advanced image processing with CLIP
- ✅ Role-based authentication system
- ✅ Flashcard deduplication (214 duplicates removed)
- ✅ Enhanced RAG search with visual results
- ✅ Performance optimizations

---

**ECHO Radiology Assistant** - Empowering medical education through AI 🩻