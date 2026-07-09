# Pronunciation Coach

Upload 30-45 seconds of spoken English, get a pronunciation score plus
word-level highlights of what went wrong. See `ARCHITECTURE.md` for full
technical + DPDP details.

## Stack

- **Backend**: FastAPI + faster-whisper (local, CPU, no external API key needed)
- **Frontend**: single static HTML/CSS/JS file, no build step, served by the same FastAPI app
- **Deploy target**: any Docker-friendly host — instructions below for Render (free tier), plus notes for Railway/Fly.io

## Run locally

```bash
cd app
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000 — the frontend and API are served from the same
origin, so there's nothing else to configure.

First request will be slow (Whisper model download + load); subsequent
requests are fast.

## Run with Docker

```bash
cd app
docker build -t pronunciation-coach .
docker run -p 8000:8000 pronunciation-coach
```

Open http://localhost:8000

## Deploy to Render (recommended — free tier, one click)

1. Push this repo to GitHub.
2. In Render: **New > Blueprint**, point it at your repo. Render will read
   `render.yaml` at the repo root and provision the Docker web service
   automatically.
3. Wait for the build (first build installs ffmpeg + downloads model
   weights on first request — can take a few minutes).
4. Your public URL will be `https://<service-name>.onrender.com`.

Manual alternative (no blueprint): **New > Web Service**, connect the repo,
set:
- Environment: Docker
- Dockerfile path: `app/Dockerfile`
- Docker build context: `app`
- Health check path: `/api/health`

## Deploy to Railway / Fly.io (alternatives)

Both support "deploy from Dockerfile" directly:

- **Railway**: New Project → Deploy from GitHub repo → set root directory to
  `app` (it auto-detects the Dockerfile).
- **Fly.io**: `cd app && fly launch` (accept the detected Dockerfile), then
  `fly deploy`.

## API

`POST /api/analyze` — multipart form, field name `file`, audio file 30-45s.

Response:
```json
{
  "duration_seconds": 34.2,
  "transcript": "the quick brown fox ...",
  "overall_score": 78,
  "score_band": "Good",
  "mean_confidence": 0.81,
  "flagged_word_count": 4,
  "total_word_count": 62,
  "words": [
    {"word": "quick", "start": 0.42, "end": 0.71, "confidence": 0.93, "issues": [], "flagged": false}
  ],
  "feedback": ["Low-confidence words worth re-practicing: fox, jumps"]
}
```

`GET /api/health` — liveness check.
