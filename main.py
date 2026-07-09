import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from scoring import analyze_audio

app = FastAPI(title="Pronunciation Coach API")

# In production, replace "*" with your actual frontend origin if you split
# frontend/backend into separate deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".mp4", ".mpga", ".mpeg"}
MAX_FILE_SIZE_MB = 25


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "pronunciation-coach"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # DPDP note: audio is written to a per-request temp directory and is
    # deleted (finally block below) as soon as scoring finishes, whether it
    # succeeds or fails. Nothing is written to a database or persistent disk.
    tmp_dir = tempfile.mkdtemp(prefix="pron_")
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")

    try:
        size = 0
        with open(tmp_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")
                f.write(chunk)

        result = analyze_audio(tmp_path)
        return JSONResponse(result)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# Serve the frontend (single-page static app) at "/".
# This route is mounted last so /api/* routes above always take priority.
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
