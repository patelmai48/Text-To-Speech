# VoxAI Studio - Full Stack AI Text-to-Speech Web Application 🎙️✨

A modern, production-ready Full Stack AI Text-to-Speech (TTS) Web Application built with **Python Flask**, **SQLite/PostgreSQL**, **SQLAlchemy**, **JWT Authentication**, **Flask-Limiter**, **Docker**, and a high-end **Glassmorphism UI** powered by Vanilla HTML5, CSS3, and JavaScript.

---

## 🌟 Key Features

### 🔐 Authentication & Security
- **User Registration & Login**: Full account creation with email verification & password recovery support.
- **JWT Protection**: Secure stateful JWT access tokens and authorization headers (`Bearer <token>`).
- **Security Headers & CSP**: Standard security headers and Content Security Policy (CSP) powered by **Flask-Talisman**.
- **API Rate Limiting**: Built-in request rate limiting using **Flask-Limiter** with IP tracking (`get_remote_address`) to protect endpoints against brute-force attacks and abuse.
- **Password Hashing**: Industry-standard salted hashing powered by `Werkzeug.security`.
- **Google OAuth 2.0 Integration**:
  - Official Google Identity Services popup & One-Tap integration.
  - **Cryptographic Backend Verification**: Every Google ID token is verified directly against Google OAuth servers (`oauth2.googleapis.com`).
  - **Strict Email Verification**: Enforces Google's `email_verified` claim to reject unverified email addresses.
  - **Seamless Account Provisioning**: Auto-creates verified, secure user accounts upon authentic Google Sign-In without manual registration forms.
- **Password Visibility Toggles**: Interactive `👁` show/hide toggles across all password input fields.
- **Account Deletion Safety**: Redesigned Danger Zone requiring explicit `"DELETE"` text confirmation before account removal.

### 🎛️ AI Text-to-Speech Core Engine
- **Multi-Language & Accent Voice Selection**: Synthesize speech in US English, UK English, Spanish, French, German, Hindi, Japanese, Chinese, Italian, Russian, and more.
- **High-Quality Neural Voices**: Integrated `edge-tts` to support high-quality natural-sounding neural voices.
- **Audio Controls**: Fine-tune Playback Speed (0.5x – 2.0x), Voice Pitch, and Volume.
- **Unlimited Text Synthesis Capacity**: Removed 3,000 character limit cap; supports unlimited text input lengths with dynamic character formatting.
- **Clean Speech Sanitization**: Automated text filter strips emojis (`🌿`, `🥗`, `💻`, `✨`), markdown bullets (`•`, `*`, `#`), and special formatting before audio generation for 100% error-free synthesis.
- **Conversion Progress Bar**: Live modal progress bar showing completion percentage and estimated remaining seconds during speech generation.
- **Speech Audio Waveform**: Real-time HTML5 Canvas visualizer animated using Web Audio API frequency analysis.

### 🪄 Dual-Mode AI Summarizer & Saved Summaries System
- **Topic & Question Prompts ("Big Question Summaries")**:
  - Generates in-depth, multi-section guides (Overview, Ingredients/Materials, Step-by-Step Instructions, Benefits, and Pro Tips) for any question or topic.
  - Features specialized knowledge for **DSA & Coding Sheets** (comparing Striver A2Z vs NeetCode 150), **Skincare & Homemade Face Packs**, **Health & Fitness**, and **Software Engineering**.
- **Long Text Condenser**: Automatically condenses long paragraphs into a concise `📌 Core Takeaways & Summary` bulleted format that preserves the **EXACT core meaning and essential facts** of the original text.
- **Dedicated Summaries Tab & Page**:
  - Database model `Summary` & CRUD REST endpoints (`GET`, `POST`, `DELETE`).
  - Search bar to filter saved summaries.
  - **Convert in Studio**: Loads summary text directly into TTS Studio and automatically synthesizes & speaks the voice audio immediately.

### 📊 Dashboard & History Management
- **User Analytics**: Tracks Total Conversions, Total Characters Processed, Favorite Voices, and Last Login timestamp.
- **Conversion History Quick Actions**: Every history item features quick action buttons: **Download MP3**, **Duplicate Script**, and **Edit in Studio**.
- **Rich Empty States**: Engaging SVG illustrations and primary call-to-action buttons ("Generate your first speech", "Explore Voices", "Generate Summaries") across History, Favorites, and Summaries pages.
- **Export Options**: Export conversion history to **CSV** or styled **PDF** reports with a single click, powered by a dedicated reporting service (`services/reporting.py`).

### 🐳 Containerization, Database Migrations & CI/CD
- **Docker & Docker Compose**: Multi-stage lightweight production Docker container setup with non-root security context (`voxaiuser`).
- **Database Migrations & Indexing**: Powered by **Flask-Migrate** (Alembic) with database indexing on key foreign key columns.
- **Automated Testing Suite**: Full **Pytest** test suite (`tests/`) covering Authentication, Speech Synthesis, PDF/CSV Export, Health checks, and Error handlers.
- **GitHub Actions CI/CD Pipeline**: Automated workflow (`.github/workflows/ci.yml`) for automated linting, test execution, and code coverage reporting on `push` and `pull_request`.
- **Gunicorn Production Server**: Configured WSGI server with multi-worker threading (`wsgi.py`).
- **PostgreSQL Integration**: Environment-switchable database layer supporting both SQLite (local dev) and PostgreSQL (production).
- **Health Monitoring**: Integrated `/health` endpoint for container health check probes.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Vanilla Glassmorphism, CSS Custom Properties), JavaScript (Vanilla ES6+), Web Audio API, Canvas API |
| **Backend** | Python 3.14+, Flask 3.1+, Flask-SQLAlchemy, Flask-Migrate, Flask-CORS, Flask-Limiter, Flask-Talisman, PyJWT, gTTS, edge-tts, Gunicorn |
| **Database** | SQLite3 (Development) / PostgreSQL (Production) |
| **Testing** | Pytest, pytest-cov |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) |
| **Containerization** | Docker, Docker Compose |
| **Reporting** | ReportLab (PDF Generation), Python `csv` module |
| **Security** | Werkzeug Security, JWT Tokens, Content Security Policy, Environment Variables (`python-dotenv`) |

---

## 📁 Project Architecture

```
tts-app/
├── app.py                     # Main Flask application initialization & blueprint registration
├── config.py                  # Environment & database configuration management
├── models.py                  # SQLAlchemy models (User, History, Favorite, Summary) with indexing
├── wsgi.py                    # Production WSGI application entry point for Gunicorn
├── pytest.ini                 # Pytest configuration & coverage options
├── Dockerfile                 # Multi-stage production Docker container configuration
├── docker-compose.yml         # Container orchestration (Web app + PostgreSQL database)
├── .dockerignore              # Excluded files from Docker context
├── requirements.txt           # Python package dependencies
├── .env                       # Local environment variables
├── .env.example               # Environment template file
├── database.db                # SQLite database (auto-generated)
├── README.md                  # Detailed documentation
│
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI automated build & test pipeline
│
├── tests/                     # Pytest automated test suite
│   ├── conftest.py            # Test app fixtures & authenticated headers
│   ├── test_auth.py           # Registration, login, password recovery & Google auth tests
│   ├── test_tts.py            # Voices, speech synthesis, history, summary & export tests
│   └── test_health.py         # System health check & error handler tests
│
├── services/
│   ├── __init__.py
│   ├── speech.py              # Speech synthesis, text sanitization & dual-mode AI summarizer
│   └── reporting.py           # Dedicated PDF generation & CSV export reporting service
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Authentication, password recovery & Google OAuth endpoints
│   ├── tts.py                 # Speech, History, Summaries, Export CSV/PDF, Favorites endpoints
│   └── profile.py             # User profile, statistics & account deletion
│
├── static/
│   ├── css/
│   │   └── style.css          # Glassmorphism design system, modals & responsive layout
│   ├── js/
│   │   ├── api.js             # Fetch API client, JWT header & Toast notification system
│   │   ├── auth.js            # Login, registration, password visibility & Google account manager
│   │   └── app.js             # Main SPA controller, Audio player & Canvas waveform
│   └── audio/                 # Generated MP3 audio storage directory
│
└── templates/
    ├── index.html             # Dashboard, TTS Studio, History, Favorites & Summaries SPA
    ├── login.html             # Standalone login & Google OAuth modal template
    └── register.html          # Standalone registration template
```

---

## 🔌 REST API Endpoints

### System & Health
- `GET /health` - Service health status check

### Authentication
- `POST /api/register` - Create a new user account
- `POST /api/login` - Authenticate and return JWT token
- `POST /api/auth/google` - Authenticate with Google identity / simulation
- `POST /api/auth/forgot-password` - Request a password reset code
- `POST /api/auth/reset-password` - Verify code & reset password
- `POST /api/auth/verify-email` - Verify user email address
- `GET /api/me` - Get current authenticated user details

### Text-to-Speech & History
- `GET /api/voices` - List available voice accents and languages
- `POST /api/tts` - Synthesize text into speech and log history (Rate limited)
- `POST /api/tts/summarize` - Summarize text/topics and auto-save to Summaries
- `GET /api/history` - Retrieve user conversion history (supports `?search=`)
- `DELETE /api/history/:id` - Delete single history record & audio file
- `DELETE /api/history` - Clear all history records
- `GET /api/history/export/csv` - Download history as CSV
- `GET /api/history/export/pdf` - Download history as PDF report

### Summaries
- `GET /api/summaries` - List saved AI summaries for current user
- `DELETE /api/summaries/:id` - Delete a saved summary

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

## 🧪 Running Automated Tests

Run the complete Pytest suite with code coverage:

```bash
# Run pytest with terminal coverage summary
pytest
```

---

## 🚀 Quick Start Guide

### Local Development (Virtual Environment)

#### 1. Clone & Navigate
```bash
git clone https://github.com/patelmai48/Text-To-Speech.git
cd Text-To-Speech
```

#### 2. Create & Activate Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment & Google OAuth (Optional)
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```
To enable Google Sign-In:
1. Obtain an OAuth 2.0 Client ID from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Set Application type to **Web application**.
3. Add `http://localhost:5000` and `http://127.0.0.1:5000` under **Authorized JavaScript origins**.
4. Paste your Client ID into `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```

#### 5. Launch the Application
```bash
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

### 🐳 Docker & Docker Compose Deployment

To run the application along with a PostgreSQL database in production mode:

```bash
# Build and start services in detached mode
docker-compose up --build -d
```
Access the application at **`http://localhost:5000`**.

To stop the containers:
```bash
docker-compose down
```

---

## 🚀 Live Demo

https://text-to-speech-efmm.onrender.com

## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
