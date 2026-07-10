# 🎙️ AI Pronunciation Coach

An AI-powered web application that evaluates English pronunciation from uploaded speech recordings.

The application analyzes a **30–45 second English audio recording**, generates an overall pronunciation score, identifies words that may have been mispronounced or unclear, and provides actionable feedback using automatic speech recognition (ASR).

**[Open the app →](https://pronunciation-coach-vyqf.onrender.com/)**

---

## Demo

Deploy on:

- Render
- Railway
- Fly.io
- Vercel (Frontend) + Render (Backend)

---

## Features

- Upload English audio recordings (30–45 seconds)
- Automatic speech transcription
- Pronunciation score (0–100)
- Confidence-based pronunciation assessment
- Detect unclear or mispronounced words
- Detect hesitation and long pauses
- Generate detailed pronunciation feedback
- REST API built with FastAPI
- Lightweight deployment optimized for free-tier cloud services

---

## Tech Stack

### Backend

- Python 3.11+
- FastAPI
- Uvicorn

### Speech Processing

- Faster Whisper
- Whisper tiny.en model
- SoundFile

### Pronunciation Analysis

- CMU Pronouncing Dictionary
- Pronouncing

### Deployment

- Docker
- Render

---

## Project Structure

```
.
├── main.py                 # FastAPI application
├── scoring.py              # Pronunciation scoring engine
├── requirements.txt
├── Dockerfile
├── render.yaml
├── static/
│   ├── index.html
└── README.md
```

---

# How It Works

The application performs pronunciation assessment in four stages.

## 1. Audio Upload

Users upload an English speech recording.

Supported formats:

- WAV
- MP3
- M4A
- OGG
- WEBM
- MP4
- MPEG

Maximum file size:

**25 MB**

---

## 2. Audio Validation

The backend verifies:

- supported format
- file size
- recording duration

Accepted duration:

**30–45 seconds**

---

## 3. Speech Recognition

The Faster Whisper model transcribes speech while producing:

- transcript
- word timestamps
- word confidence scores

---

## 4. Pronunciation Analysis

Instead of comparing against a reference script, this application performs **unscripted pronunciation assessment**.

Each spoken word is evaluated using three independent signals:

### 1. ASR Confidence

Whisper provides a confidence probability for every recognized word.

Lower confidence often indicates:

- unclear articulation
- slurred pronunciation
- inaccurate pronunciation

---

### 2. English Lexicon Validation

Recognized words are checked against the **CMU Pronouncing Dictionary**.

Words not found in the dictionary are flagged as:

- not recognized as English words

---

### 3. Long Pause Detection

The system measures silence between consecutive words.

Long pauses may indicate:

- hesitation
- uncertainty
- articulation difficulty

---

# Scoring Algorithm

Overall pronunciation score is computed from:

```
Score =
100 × Mean Word Confidence
− Penalty for flagged words
```

The final score is normalized between:

```
0 – 100
```

Score interpretation:

| Score | Rating |
|--------|---------|
| 85–100 | Excellent |
| 70–84 | Good |
| 50–69 | Fair |
| 0–49 | Needs Practice |

---

# API

## Health Check

```
GET /api/health
```

Response

```json
{
  "status": "ok",
  "service": "pronunciation-coach"
}
```

---

## Analyze Audio

```
POST /api/analyze
```

### Form Data

```
file=<audio file>
```

---

### Example Response

```json
{
  "duration_seconds": 38.2,
  "overall_score": 86,
  "score_band": "Excellent",
  "transcript": "...",
  "mean_confidence": 0.89,
  "flagged_word_count": 3,
  "total_word_count": 64,
  "feedback": [
    "Low-confidence words worth re-practicing: development, architecture"
  ],
  "words": [
    {
      "word": "development",
      "confidence": 0.54,
      "issues": [
        "mispronounced_or_unclear"
      ],
      "flagged": true
    }
  ]
}
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/Jagadeeshwar45/Pronunciation-Coach.git

cd Pronunciation-Coach
```

Create virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Run Locally

```bash
uvicorn main:app --reload
```

Visit

```
http://127.0.0.1:8000
```

---

# Deployment

The project includes:

- Dockerfile
- render.yaml

Deploy directly to **Render** by connecting the GitHub repository.

---

# Performance Optimizations

To support deployment on free-tier cloud instances:

- Whisper model loads lazily
- Tiny English model reduces memory usage
- CPU INT8 inference
- Single-worker inference lock prevents out-of-memory crashes
- Temporary audio files are deleted after processing

---

# Privacy

The application is designed with privacy in mind.

- Uploaded audio is stored only in a temporary directory.
- Files are automatically deleted after analysis.
- No recordings are permanently stored.
- No database is used.

---

# Limitations

This project performs **unscripted pronunciation assessment**.

Unlike scripted pronunciation systems, it does **not** compare speech against a predefined reference text.

Instead, it estimates pronunciation quality using:

- ASR confidence
- lexical validation
- hesitation detection

This provides practical feedback while remaining lightweight and fully automated.

---

# Future Improvements

- Phoneme-level pronunciation assessment
- IPA-based pronunciation comparison
- Speaker accent adaptation
- Detailed fluency metrics
- Speech rate analysis
- Interactive pronunciation practice
- Waveform visualization
- AI-generated pronunciation tips
- Support for multiple languages

---

# Dependencies

- FastAPI
- Faster Whisper
- SoundFile
- Pronouncing
- Uvicorn
- Python Multipart