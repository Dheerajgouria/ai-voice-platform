# AI Voice Generator

Simple full-stack AI voice generator using:

- **Frontend:** HTML + Tailwind CSS + JavaScript
- **Backend:** FastAPI
- **TTS Model:** Coqui TTS

## Project structure

- `frontend/` - static web UI
- `backend/` - FastAPI application
- `audio/` - generated WAV files
- `models/` - model cache/storage directory

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

## API

### `POST /generate`

Request:

```json
{ "text": "Hello from AI voice generator" }
```

Response:

```json
{
  "message": "Audio generated successfully.",
  "audio_url": "/audio/<generated-file>.wav",
  "filename": "<generated-file>.wav"
}
```
