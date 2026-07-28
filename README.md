# VoxAI Studio - Full Stack AI Text-to-Speech Web Application 🎙️✨

A modern, production-ready Full Stack AI Text-to-Speech (TTS) Web Application built with **Python Flask**, **SQLite**, **SQLAlchemy**, **JWT Authentication**, and a high-end **Glassmorphism UI** powered by Vanilla HTML5, CSS3, and JavaScript.

---

## 🌟 Key Features

### 🔐 Authentication & Authorization
- **User Registration & Login**: Account creation with input validation.
- **JWT Protection**: Secure stateful JWT access tokens and authorization headers (`Bearer <token>`).
- **Password Hashing**: Industry-standard salted hashing powered by `Werkzeug.security`.
- **Google Sign-In Selector Modal**: A custom simulated Google authentication interface offering quick account selections (such as `pmahi4834@gmail.com`) or custom email entries for instant signup/login.

### 🎛️ AI Text-to-Speech Core Engine
- **Multi-Language & Accent Voice Selection**: Synthesize speech in US English, UK English, Spanish, French, German, Hindi, Japanese, Chinese, Italian, Russian, and more.
- **High-Quality Neural Voices**: Integrated `edge-tts` to support high-quality natural-sounding neural voices.
- **Audio Controls**: Fine-tune Playback Speed (0.5x – 2.0x), Voice Pitch, and Volume.
- **Speech Audio Waveform**: Real-time HTML5 Canvas visualizer animated using Web Audio API frequency analysis.
- **Draft Auto-save**: Automatically saves draft text locally so work is never lost.
- **Character Counter**: Live character limit counter with warning indicators.
- **AI Text Summarizer**: AI-driven extractive text summarization before converting to speech.

### 📊 Dashboard & History Management
- **User Analytics**: Tracks Total Conversions, Total Characters Processed, Favorite Voices, and Last Login timestamp.
- **Conversion History**: Logs every audio generation into SQLite database.
- **Search & Filter**: Real-time history search by text keywords.
- **Export Options**: Export conversion history to **CSV** or styled **PDF** reports with a single click.

### 🎨 Design & Accessibility
- **Modern Glassmorphism UI**: Backdrop blurs, ambient animated glowing background orbs, smooth transitions, and vibrant gradient accents.
- **Dark & Light Mode Switcher**: Seamless theme toggle with local storage memory.
- **Optimized Light Mode Aesthetics**:
  - Warm cream/beige background (`#FAF6EB`) input areas and dropdown selects with high-contrast text to improve readability.
  - Vibrant welcome back banner utilizing a gradient (Indigo-to-Blue) with solid black text overlay.
  - Large, gold-styled **Favorite** star button and icon for highlighted visual hierarchy.
- **Toast Notifications**: Non-intrusive interactive alert toasts for all feedback and errors.
- **Keyboard Shortcuts**:
  - `Ctrl + Enter`: Convert text to speech.
  - `Space`: Toggle Audio Play / Pause.
  - `Ctrl + K`: Focus script text editor.
  - `Esc`: Clear focus / editor.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Vanilla Glassmorphism, CSS Custom Properties), JavaScript (Vanilla ES6+), Web Audio API, Canvas API |
| **Backend** | Python 3.14+, Flask 3.0+, Flask-SQLAlchemy, Flask-CORS, PyJWT, gTTS, edge-tts |
| **Database** | SQLite3 |
| **Reporting** | ReportLab (PDF Generation), Python `csv` module |
| **Security** | Werkzeug Security, JWT Tokens, Environment Variables (`python-dotenv`) |

---

## 📁 Project Architecture

```
tts-app/
├── app.py                     # Main Flask application initialization & blueprint registration
├── config.py                  # Environment & database configuration management
├── models.py                  # SQLAlchemy models (User, History, Favorite)
├── requirements.txt           # Python package dependencies
├── .env                       # Local environment variables
├── .env.example               # Environment template file
├── database.db                # SQLite database (auto-generated)
├── README.md                  # Detailed documentation
│
├── services/
│   ├── __init__.py
│   └── speech.py              # gTTS audio synthesis & text summarizer service
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Authentication endpoints (/register, /login, /me)
│   ├── tts.py                 # Speech, History, Export CSV/PDF, Favorites endpoints
│   └── profile.py             # User profile, statistics & account deletion
│
├── static/
│   ├── css/
│   │   └── style.css          # Glassmorphism design system & responsive layout
│   ├── js/
│   │   ├── api.js             # Fetch API client, JWT header & Toast notification system
│   │   ├── auth.js            # Login & registration forms controller
│   │   └── app.js             # Main SPA controller, Audio player & Canvas waveform
│   └── audio/                 # Generated MP3 audio storage directory
│
└── templates/
    ├── index.html             # Dashboard & main interactive studio SPA
    ├── login.html             # Standalone login template
    └── register.html          # Standalone registration template
```

---

## 🔌 REST API Endpoints

### Authentication
- `POST /api/register` - Create a new user account
- `POST /api/login` - Authenticate and return JWT token
- `GET /api/me` - Get current authenticated user details

### Text-to-Speech & History
- `GET /api/voices` - List available voice accents and languages
- `POST /api/tts` - Synthesize text into speech and log history
- `POST /api/tts/summarize` - Summarize long text before synthesis
- `GET /api/history` - Retrieve user conversion history (supports `?search=`)
- `DELETE /api/history/:id` - Delete single history record & audio file
- `DELETE /api/history` - Clear all history records
- `GET /api/history/export/csv` - Download history as CSV
- `GET /api/history/export/pdf` - Download history as PDF report

### Favorites
- `GET /api/favorites` - Get favorite voices & languages
- `POST /api/favorites` - Save item to favorites
- `DELETE /api/favorites/:id` - Remove item from favorites

### Profile
- `GET /api/profile` - User profile details & analytics metrics
- `PUT /api/profile` - Update username and email
- `PUT /api/profile/password` - Change account password
- `DELETE /api/profile` - Delete user account

---

## 🚀 Quick Start Guide

### 1. Clone & Navigate
```bash
git clone https://github.com/your-username/voxai-tts.git
cd voxai-tts
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 5. Launch the Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🚀 Live Demo

https://text-to-speech-efmm.onrender.com


## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
