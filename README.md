# Ena Flask Server 🧠🌈

This is the backend server for **Ena**, an emotionally intelligent AI chatbot built using Flask and Groq’s LLaMA 3 API. Ena analyzes user input to detect emotional tone, energy level, and context, and responds with empathy and contextual intelligence.

### 🌐 Live Demo
> https://tinyurl.com/Ena-emotion
---

## 💡 Features

- 🧠 Emotion-aware cognitive engine
- 📊 Sentiment & entropy analysis using `TextBlob` and Shannon entropy
- 🤖 Responses powered by `Groq LLaMA3` models (via OpenAI-compatible API)
- 🔒 Secure API key handling using environment variables
- 🌍 CORS-enabled Flask API for frontend integration

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A Groq API key (e.g., `gsk_...`)
- Flask-compatible deployment (Render, Railway, etc.)

### 🔧 Installation

```bash
git clone https://github.com/BaconKage/ena-flask-server.git
cd ena-flask-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
