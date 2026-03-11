# AI Voice Generator (Auth + XTTS + History)

Full-stack voice generator with:

- FastAPI backend
- SQLite user login system
- Coqui TTS + XTTS voice cloning
- Tailwind frontend dashboard
- Generated audio history per user

## Project structure

- `frontend/` - login + generation dashboard UI
- `backend/` - FastAPI app and dependencies
- `audio/` - generated WAV files and uploaded speaker samples
- `models/` - model cache directory

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Render deployment

Build command:

```bash
pip install -r backend/requirements.txt
```

Start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Main API endpoints

- `POST /auth/register` - create user account
- `POST /auth/login` - login and get Bearer token
- `POST /generate` - generate audio (default TTS or XTTS cloning)
- `GET /history` - authenticated generated audio history
- `GET /audio/{filename}` - serve generated WAV file

## Voice cloning (XTTS)

For cloning, send multipart form data to `/generate`:

- `text` (required)
- `speaker_audio` (required for clone mode)

The frontend does this automatically when **Voice Mode = Clone voice with XTTS**.
