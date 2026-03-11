# AI Voice Generator

Simple full-stack AI voice generator using:

- **Frontend:** HTML + Tailwind CSS + JavaScript
- **Backend:** FastAPI
- **TTS Model:** Coqui TTS

## Project structure

- `frontend/` - static web UI
- `backend/` - FastAPI application and dependencies
- `audio/` - generated WAV files
- `models/` - model cache/storage directory

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

## API

### `POST /generate`

Request body:

```json
{ "text": "Hello from AI voice generator" }
```

Response body:

```json
{
  "message": "Audio generated successfully.",
  "audio_url": "/audio/<generated-file>.wav",
  "filename": "<generated-file>.wav"
}
```

The frontend sends text to `/generate` using `fetch`, then uses `audio_url` to play audio in the HTML audio player or download the file.
