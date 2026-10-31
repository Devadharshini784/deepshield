# 🔍 ThreatLens

> Detect scams. Understand the risks. Organize your evidence.

ThreatLens is a multimodal AI-powered scam detection system that analyzes screenshots, emails, and call recordings to identify potential scams, explain its findings, and generate PDF reports for cybercrime complaints.

---

## Features

- 🖼️ **Screenshot Analysis**: Extracts text using OCR, detects payment scam patterns, scans QR codes, and analyzes suspicious images.
- 📧 **Email Analysis**: Identifies suspicious senders, malicious links, and phishing language.
- 🎙️ **Audio Analysis**: Transcribes calls, identifies speakers, and detects suspicious money requests and pressure tactics.
- 🤖 **Hybrid AI Detection**: Combines rule-based detection, DistilBERT, and Google Gemini.
- 🔍 **Explainable Results**: Provides risk scores, detection reasons, and recommended actions.
- 🔗 **Combined Evidence Analysis**: Compares information across screenshots, emails, and recordings to identify inconsistencies.
- 📄 **PDF Report Generation**: Creates downloadable reports containing findings and extracted evidence.
- 🔐 **User Authentication**: Secure registration and login using JWT and bcrypt.

---

## Tech Stack

**Frontend**
- React + Vite
- Tailwind CSS
- React Router DOM
- Axios

**Backend**
- Python + Flask
- Flask-CORS
- PyJWT + bcrypt

**Database**
- MongoDB + PyMongo

**AI / ML**
- Hugging Face Transformers (DistilBERT)
- Google Gemini API
- OpenAI Whisper
- pyannote.audio

**Image Processing & Reports**
- Tesseract OCR
- OpenCV + pyzbar
- ReportLab

---

## How It Works

1. **Upload Evidence**: Submit a screenshot, email, or call recording.
2. **Analyze Content**: Extract text and inspect suspicious patterns using detection rules and AI models.
3. **Evaluate Risk**: Generate a risk score and classify the evidence as Low, Medium, or High risk.
4. **Explain the Verdict**: Display the reasons behind the detection and suggest appropriate actions.
5. **Generate a Report**: Download a PDF containing the findings and relevant evidence.

---

## Getting Started Locally

### Prerequisites

- Python 3.11
- Node.js and npm
- MongoDB
- Tesseract OCR
- FFmpeg
- Google Gemini API key
- Hugging Face token for speaker diarization

### Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/ThreatLens.git
cd ThreatLens
```

### Setup Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `backend/.env` file:

```env
MONGO_URI=mongodb://localhost:27017/
DB_NAME=ThreatLens_db
JWT_SECRET=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
```

Start the backend:

```bash
python app.py
```

### Setup Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access the application.

**Note:** The trained DistilBERT classifier must be added to `backend/models/scam_classifier/`. Audio analysis also requires the relevant models and dependencies to be configured.

---

## Risk Levels

| Level | Score |
|---|---|
| 🟢 Low | Below 40 |
| 🟡 Medium | 40–69 |
| 🔴 High | 70 and above |

---

## Project Structure

```text
ThreatLens/
├── backend/
│   ├── app.py
│   ├── modules/
│   │   ├── auth/
│   │   ├── screenshot_analyzer/
│   │   ├── email_analyzer/
│   │   ├── audio_analyzer/
│   │   ├── explainable_ai/
│   │   ├── report_generator/
│   │   └── shared/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       └── components/
└── README.md
```

---

## Future Improvements

- 🌐 Support for regional Indian languages
- 🎭 AI-generated voice and deepfake detection
- 📊 Improved detection using larger datasets
- ☁️ Cloud deployment and browser extension support

---

## Limitations

- Screenshots alone cannot verify whether a payment occurred.
- Detection accuracy depends on the evidence, language, and available models.
- AI predictions may be incorrect. Always verify suspicious transactions independently.

ThreatLens is an investigative aid and does not replace professional or legal advice.

---

## Built By

**Subhashini and Devadharshini**

> Built with React, Flask, MongoDB, and AI to make scam investigation more accessible. 🚀

---

⭐ Star this repository if you find it useful!

