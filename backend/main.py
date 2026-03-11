from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from TTS.api import TTS
except ImportError:  # pragma: no cover
    TTS = None

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "audio"
MODELS_DIR = BASE_DIR / "models"
FRONTEND_DIR = BASE_DIR / "frontend"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Voice Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

_tts_engine = None


class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def get_tts_engine() -> TTS:
    global _tts_engine

    if TTS is None:
        raise HTTPException(
            status_code=500,
            detail="Coqui TTS is not installed. Run: pip install -r backend/requirements.txt",
        )

    if _tts_engine is None:
        _tts_engine = TTS(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            progress_bar=False,
            gpu=False,
        )

    return _tts_engine


@app.post("/generate")
def generate_speech(payload: GenerateRequest) -> dict:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    engine = get_tts_engine()
    filename = f"{uuid4().hex}.wav"
    output_path = AUDIO_DIR / filename

    engine.tts_to_file(text=text, file_path=str(output_path))

    return {
        "message": "Audio generated successfully.",
        "audio_url": f"/audio/{filename}",
        "filename": filename,
    }


@app.get("/audio/{filename}")
def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")
