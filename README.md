# TTS Server

Text-to-speech server using Pocket TTS (Kyutai). Supports predefined voices and custom voice cloning.

---

## .env
Create a .env file in the root of project
```
HF_TOKEN=hugginface_token
# Get the huggingface_token from https://huggingface.co/settings/tokens and allow access to the required repositories.
```

## start.py

**What it does:** A simple script to try out Pocket TTS without running a server. It loads the model, picks a voice, generates speech from text, and saves the result as a WAV file.

**When to use:** Quick tests, debugging, or when you want to generate one-off audio files from the command line.

**Usage:**
```bash
source venv/bin/activate
python3 -m start.py
```

Edit `start.py` to change the voice (`"alba"`, `"marius"`, etc.) or the text. Output is written to `output-2.wav` by default.

---

## export_voice.py

**What it does:** Converts a WAV voice sample into a `.safetensors` file. Pocket TTS can then load this file directly instead of re-encoding the WAV every time, which speeds up voice loading.

**When to use:** After adding a new custom voice (your own recording or any WAV sample). Run once per voice; the server can reuse the safetensors file.

**Usage:**
```bash
source venv/bin/activate
python3 -m export_voice
# Or with custom paths:
python3 -m export_voice.py --input voices/sources/my-voice.wav --output voices/safetensors/my-voice.safetensors
# --input and --output are optional
```

**Requirements:** Voice cloning needs a HuggingFace token. Put `HF_TOKEN=hf_xxxx` in a `.env` file, or run `huggingface-cli login`. Use 3–10 seconds of clear speech in the source WAV for better results.

---

## HTTP Server (server.py)

**What it does:** FastAPI server with `POST /voice/generate` that returns WAV audio from JSON input.

**How to run:**
```bash
cd /Users/harikrishnanv/Documents/personal-projects/RSS-Feeder/TTS-server
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Example request:**
```bash
curl -X POST http://localhost:8000/voice/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "voice": "alba"}' \
  --output speech.wav
```