import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
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
DB_PATH = BASE_DIR / "backend" / "app.db"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Voice Generator", version="2.0.0")

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
_xtts_engine = None


class AuthPayload(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audio_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                voice_mode TEXT NOT NULL,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return secrets.compare_digest(check, digest)


def get_user_from_token(authorization: Optional[str] = Header(default=None)) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token.")

    with get_db() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.username
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session token.")

    return row


@app.post("/auth/register")
def register(payload: AuthPayload) -> dict:
    username = payload.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    pw_hash = hash_password(payload.password)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, pw_hash, datetime.utcnow().isoformat()),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username already exists.") from exc

    return {"message": "Account created successfully."}


@app.post("/auth/login")
def login(payload: AuthPayload) -> dict:
    username = payload.username.strip().lower()

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if row is None or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, row["id"], datetime.utcnow().isoformat()),
        )

    return {"token": token, "username": row["username"]}


def get_tts_engine() -> TTS:
    global _tts_engine

    if TTS is None:
        raise HTTPException(status_code=500, detail="Coqui TTS is not installed. Run pip install -r backend/requirements.txt")

    if _tts_engine is None:
        _tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

    return _tts_engine


def get_xtts_engine() -> TTS:
    global _xtts_engine

    if TTS is None:
        raise HTTPException(status_code=500, detail="Coqui TTS is not installed. Run pip install -r backend/requirements.txt")

    if _xtts_engine is None:
        _xtts_engine = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

    return _xtts_engine


@app.post("/generate")
async def generate_speech(
    text: str = Form(...),
    speaker_audio: Optional[UploadFile] = File(default=None),
    current_user: sqlite3.Row = Depends(get_user_from_token),
) -> dict:
    clean_text = text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    filename = f"{uuid4().hex}.wav"
    output_path = AUDIO_DIR / filename

    voice_mode = "default"

    if speaker_audio and speaker_audio.filename:
        voice_mode = "xtts-clone"
        speaker_suffix = Path(speaker_audio.filename).suffix.lower() or ".wav"
        speaker_path = AUDIO_DIR / f"speaker_{uuid4().hex}{speaker_suffix}"
        raw = await speaker_audio.read()
        speaker_path.write_bytes(raw)

        xtts_engine = get_xtts_engine()
        xtts_engine.tts_to_file(
            text=clean_text,
            speaker_wav=str(speaker_path),
            language="en",
            file_path=str(output_path),
        )
    else:
        tts_engine = get_tts_engine()
        tts_engine.tts_to_file(text=clean_text, file_path=str(output_path))

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO audio_history (user_id, text, voice_mode, filename, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (current_user["id"], clean_text, voice_mode, filename, datetime.utcnow().isoformat()),
        )

    return {
        "message": "Audio generated successfully.",
        "audio_url": f"/audio/{filename}",
        "filename": filename,
        "voice_mode": voice_mode,
    }


@app.get("/history")
def get_history(current_user: sqlite3.Row = Depends(get_user_from_token)) -> dict:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, text, voice_mode, filename, created_at
            FROM audio_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 50
            """,
            (current_user["id"],),
        ).fetchall()

    items = [
        {
            "id": row["id"],
            "text": row["text"],
            "voice_mode": row["voice_mode"],
            "filename": row["filename"],
            "audio_url": f"/audio/{row['filename']}",
            "created_at": row["created_at"],
        }
        for row in rows
    ]

    return {"items": items}


@app.get("/audio/{filename}")
def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
